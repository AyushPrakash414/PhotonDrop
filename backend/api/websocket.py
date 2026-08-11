"""
PhotonDrop — Real-time WebSockets Stream

Pushes live frames and metrics to the React frontend:
  - Sender: QR frame image (base64 JPEG) + live Display FPS & Goodput
  - Receiver: Camera preview frame (base64 JPEG) + state machine + real-time stats
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Optional, Set

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.receiver_routes import global_receiver
from backend.api.sender_routes import global_sender
from shared.models import ReceiverState
from visual.renderer import render_frame

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

_active_websockets: Set[WebSocket] = set()

_latest_sender_frame: Optional[np.ndarray] = None
_latest_receiver_frame: Optional[np.ndarray] = None


def _on_sender_frame(img: np.ndarray) -> None:
    global _latest_sender_frame
    _latest_sender_frame = img


def _on_receiver_preview(frame: np.ndarray) -> None:
    global _latest_receiver_frame
    _latest_receiver_frame = frame


def _frame_to_base64_jpeg(frame: np.ndarray, quality: int = 80) -> str:
    """Compress numpy image to base64 encoded JPEG string."""
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return base64.b64encode(buffer).decode("utf-8")


def _frame_to_base64_png(frame: np.ndarray) -> str:
    """Encode high-contrast QR frames losslessly for browser display."""
    _, buffer = cv2.imencode(".png", frame)
    return base64.b64encode(buffer).decode("utf-8")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket streaming endpoint for the React frontend."""
    await websocket.accept()
    _active_websockets.add(websocket)
    logger.info("React WebSocket client connected")

    try:
        while True:
            # Gather Sender State
            sender_frame_b64 = None
            sender_stats = None
            if global_sender.is_transmitting:
                if _latest_sender_frame is not None:
                    rendered = render_frame(_latest_sender_frame, canvas_size=(400, 400))
                    sender_frame_b64 = _frame_to_base64_png(rendered)

                if global_sender.engine._worker:
                    stats = global_sender.engine._worker._stats
                    sender_stats = {
                        "display_fps": round(stats.display_fps, 1),
                        "goodput_kbs": round(stats.goodput / 1024, 1) if stats.goodput > 0 else 0,
                        "symbols": stats.total_frames,
                        "elapsed_time": round(stats.elapsed_time, 1),
                    }

            # Gather Receiver State
            receiver_frame_b64 = None
            receiver_payload = None
            is_receiver_active = global_receiver.is_active or global_receiver.state != ReceiverState.IDLE
            if is_receiver_active:
                if _latest_receiver_frame is not None:
                    receiver_frame_b64 = _frame_to_base64_jpeg(_latest_receiver_frame, quality=70)

                stats = global_receiver.processor.stats
                meta = global_receiver.reconstruction.session.file_metadata
                receiver_payload = {
                    "state": global_receiver.state.name,
                    "progress": round(global_receiver.progress * 100, 2),
                    "file_name": meta.file_name if meta else None,
                    "file_size": meta.file_size if meta else None,
                    "total_blocks": meta.total_source_blocks if meta else None,
                    "sha256": meta.sha256 if meta else None,
                    "capture_fps": round(stats.capture_fps, 1),
                    "decode_fps": round(stats.decode_fps, 1),
                    "goodput_kbs": round(stats.goodput / 1024, 1) if stats.goodput > 0 else 0,
                    "unique_symbols": stats.unique_symbols,
                    "duplicates": stats.duplicate_frames,
                    "invalid": stats.invalid_frames,
                    "elapsed_time": round(stats.elapsed_time, 1),
                }

            payload = {
                "type": "telemetry",
                "sender": {
                    "is_transmitting": global_sender.is_transmitting,
                    "frame_b64": sender_frame_b64,
                    "stats": sender_stats,
                },
                "receiver": {
                    "is_active": is_receiver_active,
                    "frame_b64": receiver_frame_b64,
                    "data": receiver_payload,
                },
            }

            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.066)  # ~15 Hz push rate to React UI

    except WebSocketDisconnect:
        logger.info("React WebSocket client disconnected")
    except Exception as e:
        logger.debug("WebSocket exception: %s", e)
    finally:
        _active_websockets.discard(websocket)
