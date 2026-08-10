"""
PhotonDrop — Camera Capture

Non-blocking OpenCV camera capture running in a background QThread.
Emits raw frames for the receiver pipeline.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)


class CameraWorker(QObject):
    """Background worker that captures frames from an OpenCV camera."""

    frame_captured = Signal(object)   # np.ndarray (BGR)
    fps_updated = Signal(float)
    error = Signal(str)
    finished = Signal()

    def __init__(self, camera_index: int = 0, target_fps: int = 60):
        super().__init__()
        self.camera_index = camera_index
        self.target_fps = target_fps
        self._running = False

    def run(self) -> None:
        """Main capture loop — connect to QThread.started."""
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.error.emit(f"Cannot open camera {self.camera_index}")
            self.finished.emit()
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

        while self._running:
            t0 = time.monotonic()
            ret, frame = cap.read()
            if not ret:
                logger.warning("Camera read failed — retrying")
                time.sleep(0.01)
                continue

            self.frame_captured.emit(frame)
            frame_count += 1

            # Update FPS every 30 frames
            if frame_count % 30 == 0:
                elapsed = time.monotonic() - t_start
                fps = frame_count / elapsed if elapsed > 0 else 0
                self.fps_updated.emit(fps)

            # Throttle
            dt = time.monotonic() - t0
            sleep = frame_interval - dt
            if sleep > 0:
                time.sleep(sleep)

        cap.release()
        logger.info("Camera released")
        self.finished.emit()

    def stop(self) -> None:
        self._running = False


class CameraCapture:
    """Manages the camera QThread lifecycle."""

    def __init__(self):
        self._thread: Optional[QThread] = None
        self._worker: Optional[CameraWorker] = None

    def start(
        self,
        camera_index: int = 0,
        on_frame=None,
        on_fps=None,
        on_error=None,
    ) -> None:
        self.stop()
        self._thread = QThread()
        self._worker = CameraWorker(camera_index)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)

        if on_frame:
            self._worker.frame_captured.connect(on_frame)
        if on_fps:
            self._worker.fps_updated.connect(on_fps)
        if on_error:
            self._worker.error.connect(on_error)

        self._thread.start()

    def stop(self) -> None:
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)
        self._thread = None
        self._worker = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()
