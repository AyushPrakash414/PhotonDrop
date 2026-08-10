"""
PhotonDrop — Receiver Orchestrator

Ties together camera capture, visual decoding, packet processing,
fountain decoding, and file reconstruction.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from receiver.camera import CameraCapture
from receiver.packet_processor import PacketProcessor
from receiver.reconstruction import Reconstruction
from shared.models import ReceiverState, TransferStats
from visual.decoder import decode_frame_to_bytes
from visual.encoder import QRTransport, VisualTransport
from visual.preprocessing import preprocess_frame

logger = logging.getLogger(__name__)


class Receiver:
    """PhotonDrop Receiver — orchestrates camera-to-file reception."""

    def __init__(self, output_dir: Path = Path("received_files")):
        self.camera = CameraCapture()
        self.processor = PacketProcessor()
        self.reconstruction = Reconstruction(output_dir=output_dir)
        self.transport: VisualTransport = QRTransport()

        self._on_state_change: Optional[Callable] = None
        self._on_stats_update: Optional[Callable] = None
        self._on_preview_frame: Optional[Callable] = None

        self._decode_count = 0
        self._decode_start = 0.0

    @property
    def state(self) -> ReceiverState:
        return self.reconstruction.state

    @property
    def progress(self) -> float:
        return self.reconstruction.progress

    def start(
        self,
        camera_index: int = 0,
        on_state_change: Optional[Callable] = None,
        on_stats_update: Optional[Callable] = None,
        on_preview_frame: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> None:
        """Start receiving: open camera and begin processing frames."""
        self._on_state_change = on_state_change
        self._on_stats_update = on_stats_update
        self._on_preview_frame = on_preview_frame
        self._decode_count = 0
        self._decode_start = time.monotonic()

        self.reconstruction.session.state = ReceiverState.SEARCHING
        self._notify_state()

        self.camera.start(
            camera_index=camera_index,
            on_frame=self._on_camera_frame,
            on_fps=self._on_camera_fps,
            on_error=on_error,
        )

    def stop(self) -> None:
        """Stop receiving and release the camera."""
        self.camera.stop()

    def process_frame(self, frame: np.ndarray) -> None:
        """Process an external frame (e.g., received from a mobile/browser camera stream)."""
        if self.reconstruction.state == ReceiverState.IDLE:
            self.reconstruction.session.state = ReceiverState.SEARCHING
            self._notify_state()
        self._on_camera_frame(frame)

    def _on_camera_frame(self, frame: np.ndarray) -> None:
        """Process each camera frame through the full pipeline."""
        # Send preview to UI
        if self._on_preview_frame:
            self._on_preview_frame(frame)

        # Preprocess
        processed = preprocess_frame(frame, max_dim=800)

        # Attempt visual decode
        raw_bytes = decode_frame_to_bytes(processed, self.transport)
        if raw_bytes is None:
            return

        # Validate and filter
        packet = self.processor.process_raw(raw_bytes)
        if packet is None:
            return

        # Feed to reconstruction state machine
        prev_state = self.reconstruction.state
        self.reconstruction.feed_packet(packet)

        # Track session lock
        if self.reconstruction.session.session_id and self.processor._current_session is None:
            self.processor.set_session(self.reconstruction.session.session_id)

        # Update decode FPS
        self._decode_count += 1
        elapsed = time.monotonic() - self._decode_start
        if elapsed > 0:
            self.processor.stats.decode_fps = self._decode_count / elapsed
            self.processor.stats.elapsed_time = elapsed
            self.processor.stats.goodput = (
                self.processor.stats.payload_bytes / elapsed if elapsed > 0 else 0
            )

        # Notify UI
        if self.reconstruction.state != prev_state:
            self._notify_state()

        if self._on_stats_update:
            self._on_stats_update(self.processor.stats)

    def _on_camera_fps(self, fps: float) -> None:
        self.processor.stats.capture_fps = fps

    def _notify_state(self) -> None:
        if self._on_state_change:
            self._on_state_change(self.reconstruction.state)

    def reset(self) -> None:
        """Reset for a new transfer."""
        self.processor.reset()
        self.reconstruction.reset()
