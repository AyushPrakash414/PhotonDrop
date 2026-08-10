"""
PhotonDrop — Status & Settings API Routes

Endpoints for transfer history, settings management, and system health.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["settings"])

_SETTINGS_FILE = Path("settings.json")
_HISTORY_FILE = Path("activity_history.json")


class SettingsModel(BaseModel):
    camera_resolution: str = "1280x720"
    target_camera_fps: int = 60
    target_sender_fps: int = 30
    qr_error_correction: str = "M"
    download_path: str = "received_files"
    theme: str = "system"


def get_default_settings() -> Dict[str, Any]:
    return SettingsModel().model_dump()


def load_settings() -> Dict[str, Any]:
    if _SETTINGS_FILE.exists():
        try:
            return json.loads(_SETTINGS_FILE.read_text("utf-8"))
        except Exception:
            pass
    return get_default_settings()


def save_settings(data: Dict[str, Any]) -> None:
    _SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_history() -> List[Dict[str, Any]]:
    if _HISTORY_FILE.exists():
        try:
            return json.loads(_HISTORY_FILE.read_text("utf-8"))
        except Exception:
            pass
    return []


def add_history_item(item: Dict[str, Any]) -> None:
    history = load_history()
    history.insert(0, item)
    _HISTORY_FILE.write_text(json.dumps(history[:100], indent=2), encoding="utf-8")


@router.get("/settings")
async def get_settings() -> Dict[str, Any]:
    return load_settings()


@router.post("/settings")
async def update_settings(settings: SettingsModel) -> Dict[str, Any]:
    data = settings.model_dump()
    save_settings(data)
    return {"status": "saved", "settings": data}


@router.get("/activity")
async def get_activity() -> List[Dict[str, Any]]:
    return load_history()
