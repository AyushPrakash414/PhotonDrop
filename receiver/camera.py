"""
PhotonDrop — Camera Capture

Non-blocking OpenCV camera capture running in a background daemon thread.
Emits raw frames for the receiver pipeline.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraWorker:
    """Background worker that captures frames from an OpenCV camera."""

    def __init__(self, camera_index: int = 0, target_fps: int = 60):
        self.camera_index = camera_index
        self.target_fps = target_fps
        self._running = False
        self.on_frame: Optional[Callable] = None
        self.on_fps: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_finished: Optional[Callable] = None

    def run(self) -> None:
        """Main capture loop — runs in a background daemon thread."""
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            err_msg = f"Cannot open camera {self.camera_index}"
            logger.error(err_msg)
            if self.on_error:
                self.on_error(err_msg)
            if self.on_finished:
                self.on_finished()
            return

        # Attempt to set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, self.target_fps)

        self._running = True
        frame_interval = 1.0 / self.target_fps
        frame_count = 0
        t_start = time.monotonic()

        logger.info("Camera %d opened — capturing at %d FPS target", self.camera_index, self.target_fps)

        try:
            while self._running:
                t0 = time.monotonic()
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Camera read failed — retrying")
                    time.sleep(0.01)
                    continue

                if self.on_frame:
                    self.on_frame(frame)
                frame_count += 1

                # Update FPS every 30 frames
                if frame_count % 30 == 0:
                    elapsed = time.monotonic() - t_start
                    fps = frame_count / elapsed if elapsed > 0 else 0
                    if self.on_fps:
                        self.on_fps(fps)

                # Throttle
                dt = time.monotonic() - t0
                sleep = frame_interval - dt
                if sleep > 0:
                    time.sleep(sleep)
        finally:
            cap.release()
            logger.info("Camera released")
            if self.on_finished:
                self.on_finished()

    def stop(self) -> None:
        self._running = False


class CameraCapture:
    """Manages the camera background thread lifecycle."""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._worker: Optional[CameraWorker] = None

    def start(
        self,
        camera_index: int = 0,
        on_frame: Optional[Callable] = None,
        on_fps: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> None:
        self.stop()
        self._worker = CameraWorker(camera_index)
        self._worker.on_frame = on_frame
        self._worker.on_fps = on_fps
        self._worker.on_error = on_error

        self._thread = threading.Thread(
            target=self._worker.run,
            daemon=True,
            name="PhotonDrop-CameraCapture",
        )
        self._thread.start()

    def stop(self) -> None:
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._worker = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
