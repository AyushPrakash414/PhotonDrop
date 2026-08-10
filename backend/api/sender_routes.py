"""
PhotonDrop — Sender API Routes

REST endpoints for selecting files and controlling the sender
transmission engine. Wraps the existing core Sender instance.
"""

from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from sender.sender import Sender
from shared.models import FileMetadata

router = APIRouter(prefix="/api/sender", tags=["sender"])

# Global Sender instance wrapping core PhotonDrop sender engine
global_sender = Sender()


class StartTransmissionRequest(BaseModel):
    target_fps: int = 30


@router.post("/select-file")
async def select_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload/select a file to prepare for optical transmission."""
    try:
        # Save uploaded file to a temporary location
        temp_dir = Path(tempfile.gettempdir()) / "photondrop_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / file.filename

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Load file into existing core Sender engine
        meta: FileMetadata = global_sender.load_file(file_path)

        return {
            "status": "success",
            "metadata": {
                "file_id": meta.file_id,
                "session_id": meta.session_id.hex(),
                "file_name": meta.file_name,
                "file_size": meta.file_size,
                "mime_type": meta.mime_type,
                "block_size": meta.block_size,
                "total_source_blocks": meta.total_source_blocks,
                "sha256": meta.sha256,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/select-local-path")
async def select_local_path(payload: Dict[str, str]) -> Dict[str, Any]:
    """Select a local file path on the machine."""
    path_str = payload.get("path")
    if not path_str or not os.path.exists(path_str):
        raise HTTPException(status_code=404, detail="File path does not exist")

    try:
        meta: FileMetadata = global_sender.load_file(path_str)
        return {
            "status": "success",
            "metadata": {
                "file_id": meta.file_id,
                "session_id": meta.session_id.hex(),
                "file_name": meta.file_name,
                "file_size": meta.file_size,
                "mime_type": meta.mime_type,
                "block_size": meta.block_size,
                "total_source_blocks": meta.total_source_blocks,
                "sha256": meta.sha256,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start")
async def start_transmission(req: StartTransmissionRequest = StartTransmissionRequest()) -> Dict[str, Any]:
    """Start optical transmission loop."""
    if global_sender.metadata is None:
        raise HTTPException(status_code=400, detail="No file selected")

    if global_sender.is_transmitting:
        return {"status": "already_running"}

    from backend.api.websocket import _on_sender_frame
    global_sender.start_transmission(target_fps=req.target_fps, on_frame=_on_sender_frame)
    return {"status": "started", "target_fps": req.target_fps}


@router.post("/stop")
async def stop_transmission() -> Dict[str, Any]:
    """Stop optical transmission loop."""
    global_sender.stop_transmission()
    return {"status": "stopped"}


@router.get("/status")
async def get_sender_status() -> Dict[str, Any]:
    """Get current sender transmission state."""
    meta = global_sender.metadata
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

    return {
        "is_transmitting": global_sender.is_transmitting,
        "metadata": meta_dict,
    }
