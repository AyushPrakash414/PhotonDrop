"""
PhotonDrop — Receiver API Routes

REST endpoints for controlling the receiver camera and decoding engine.
Wraps the existing core Receiver instance.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from receiver.receiver import Receiver
from shared.models import ReceiverState

router = APIRouter(prefix="/api/receiver", tags=["receiver"])

# Global Receiver instance wrapping core PhotonDrop receiver engine
global_receiver = Receiver(output_dir=Path("received_files"))


class StartReceiverRequest(BaseModel):
    camera_index: int = 0
    mode: str = "browser"


class ProcessFrameRequest(BaseModel):
    frame_b64: str


@router.post("/frame")
async def process_browser_frame(req: ProcessFrameRequest) -> Dict[str, Any]:
    """Process a base64-encoded frame captured by a mobile or web browser camera."""
    try:
        b64_data = req.frame_b64
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]

        raw_bytes = base64.b64decode(b64_data)
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        import cv2
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is not None:
            from backend.api.websocket import _on_receiver_preview
            _on_receiver_preview(frame)
            global_receiver.process_frame(frame)
            return {"status": "processed", "state": global_receiver.state.name}
        else:
            return {"status": "invalid_image"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/start")
async def start_receiving(req: StartReceiverRequest = StartReceiverRequest()) -> Dict[str, Any]:
    """Start receiver camera acquisition and visual decoding loop."""
    from backend.api.websocket import _on_receiver_preview

    if req.mode == "browser":
        global_receiver.start_external_stream(on_preview_frame=_on_receiver_preview)
        return {"status": "browser_ready", "mode": "browser"}

    if req.mode != "server":
        raise HTTPException(status_code=400, detail="Receiver mode must be 'browser' or 'server'")

    if global_receiver.camera.is_running:
        return {"status": "already_running"}

    global_receiver.start(camera_index=req.camera_index, on_preview_frame=_on_receiver_preview)
    return {"status": "started", "mode": "server", "camera_index": req.camera_index}


@router.post("/stop")
async def stop_receiving() -> Dict[str, Any]:
    """Stop camera acquisition."""
    global_receiver.stop()
    return {"status": "stopped"}


@router.post("/reset")
async def reset_receiver() -> Dict[str, Any]:
    """Reset receiver state for a new transfer."""
    global_receiver.stop()
    global_receiver.reset()
    return {"status": "reset", "state": "IDLE"}


@router.get("/status")
async def get_receiver_status() -> Dict[str, Any]:
    """Get current receiver state and stats."""
    meta = global_receiver.reconstruction.session.file_metadata
    meta_dict = None
    if meta:
        meta_dict = {
            "file_id": meta.file_id,
            "session_id": meta.session_id.hex(),
            "file_name": meta.file_name,
            "file_size": meta.file_size,
            "mime_type": meta.mime_type,
            "block_size": meta.block_size,
            "total_source_blocks": meta.total_source_blocks,
            "sha256": meta.sha256,
        }

    stats = global_receiver.processor.stats

    return {
        "is_active": global_receiver.is_active,
        "state": global_receiver.state.name,
        "progress": round(global_receiver.progress * 100, 2),
        "metadata": meta_dict,
        "stats": {
            "total_frames": stats.total_frames,
            "new_frames": stats.new_frames,
            "duplicate_frames": stats.duplicate_frames,
            "invalid_frames": stats.invalid_frames,
            "unique_symbols": stats.unique_symbols,
            "payload_bytes": stats.payload_bytes,
            "capture_fps": round(stats.capture_fps, 1),
            "decode_fps": round(stats.decode_fps, 1),
            "goodput_kbs": round(stats.goodput / 1024, 1) if stats.goodput > 0 else 0,
            "elapsed_time": round(stats.elapsed_time, 1),
        },
    }
