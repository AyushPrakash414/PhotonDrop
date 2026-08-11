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
        self._external_stream_active = False

    @property
    def state(self) -> ReceiverState:
        return self.reconstruction.state

    @property
    def progress(self) -> float:
        return self.reconstruction.progress

    @property
    def is_active(self) -> bool:
        return self.camera.is_running or self._external_stream_active

    def start_external_stream(
        self,
        on_state_change: Optional[Callable] = None,
        on_stats_update: Optional[Callable] = None,
        on_preview_frame: Optional[Callable] = None,
    ) -> None:
        """Start receiving frames supplied by the browser/mobile frontend."""
        self.stop()
        self._on_state_change = on_state_change
        self._on_stats_update = on_stats_update
        self._on_preview_frame = on_preview_frame
        self._decode_count = 0
        self._decode_start = time.monotonic()
        self._external_stream_active = True

        if self.reconstruction.state in (
            ReceiverState.IDLE,
            ReceiverState.COMPLETE,
            ReceiverState.ERROR,
        ):
            if self.reconstruction.state in (ReceiverState.COMPLETE, ReceiverState.ERROR):
                self.reset()
                self._external_stream_active = True
            self.reconstruction.session.state = ReceiverState.SEARCHING
            self._notify_state()

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
        self._external_stream_active = False
        self.camera.stop()

    def process_frame(self, frame: np.ndarray) -> None:
        """Process an external frame (e.g., received from a mobile/browser camera stream)."""
        if not self.is_active:
            self.start_external_stream(on_preview_frame=self._on_preview_frame)
        if self.reconstruction.state == ReceiverState.IDLE:
            self.reconstruction.session.state = ReceiverState.SEARCHING
            self._notify_state()
        self._on_camera_frame(frame)

    def _on_camera_frame(self, frame: np.ndarray) -> None:
        """Process each camera frame through the full pipeline."""
        # Send preview to UI
        if self._on_preview_frame:
            self._on_preview_frame(frame)

        # Track capture metrics on every incoming frame
        self._decode_count += 1
        elapsed = time.monotonic() - self._decode_start
        if elapsed > 0:
            self.processor.stats.capture_fps = self._decode_count / elapsed
            self.processor.stats.elapsed_time = elapsed

        # Multi-pass visual decode (tries raw frame, grayscale, CLAHE, and thresholding)
        raw_bytes = decode_frame_to_bytes(frame, self.transport)
        if raw_bytes is None:
            self.processor.stats.invalid_frames += 1
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

        # Update decode FPS & goodput
        if elapsed > 0:
            self.processor.stats.decode_fps = self._decode_count / elapsed
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
        self._external_stream_active = False
        self.processor.reset()
        self.reconstruction.reset()
