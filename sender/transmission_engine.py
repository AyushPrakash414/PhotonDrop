"""
PhotonDrop — Transmission Engine

Drives the high-speed loop that continuously generates fountain-coded
packets, encodes them as QR images, and signals the UI to display them.

Runs in a background thread so the PySide6 event loop remains responsive.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, List, Optional

try:
    from PySide6.QtCore import QObject, QThread, Signal
except ImportError:
    class QObject:
        def __init__(self, *args, **kwargs): pass
        def moveToThread(self, thread): pass

    class QThread:
        class _Signal:
            def connect(self, slot): pass
        def __init__(self, *args, **kwargs):
            self.started = self._Signal()
        def start(self): pass
        def quit(self): pass
        def wait(self, msec=3000): pass
        def isRunning(self): return False

    class Signal:
        def __init__(self, *args, **kwargs): pass
        def emit(self, *args, **kwargs): pass
        def connect(self, slot): pass

from sender.packet_generator import PacketGenerator
from shared.models import FileMetadata, TransferStats
from visual.encoder import QRTransport, VisualTransport

logger = logging.getLogger(__name__)


class TransmissionWorker(QObject):
    """Worker that runs in a QThread producing QR frames."""

    # Signals
    frame_ready = Signal(object)       # numpy array (the QR image)
    stats_updated = Signal(object)     # TransferStats snapshot
    finished = Signal()

    def __init__(
        self,
        metadata: FileMetadata,
        blocks: List[bytes],
        target_fps: int = 30,
        transport: Optional[VisualTransport] = None,
    ):
        super().__init__()
        self.metadata = metadata
        self.blocks = blocks
        self.target_fps = target_fps
        self.transport = transport or QRTransport(error_correction="M", box_size=4, border=2)
        self._running = False
        self._stats = TransferStats()

    def run(self) -> None:
        """Main transmission loop — call from QThread.started signal."""
        self._running = True
        gen = PacketGenerator(self.metadata, self.blocks)

        # Pre-encode session start and metadata images
        session_start_img = self.transport.encode(gen.session_start_bytes())
        metadata_img = self.transport.encode(gen.metadata_bytes())

        # Emit initial header frames
        self.frame_ready.emit(session_start_img)
        time.sleep(0.1)
        self.frame_ready.emit(metadata_img)
        time.sleep(0.1)

        frame_interval = 1.0 / self.target_fps
        start_time = time.monotonic()
        frame_count = 0

        for data_bytes in gen.data_stream():
            if not self._running:
                break

            # Periodically re-emit metadata every 30 frames (~1 sec) so late-joining receivers lock on immediately
            if frame_count > 0 and frame_count % 30 == 0:
                self.frame_ready.emit(metadata_img)
                time.sleep(frame_interval)

            t0 = time.monotonic()
            img = self.transport.encode(data_bytes)
            self.frame_ready.emit(img)
            frame_count += 1

            # Update stats periodically
            elapsed = time.monotonic() - start_time
            self._stats.total_frames = frame_count + 2  # +2 for session/meta
            self._stats.display_fps = frame_count / elapsed if elapsed > 0 else 0
            self._stats.elapsed_time = elapsed
            self._stats.payload_bytes = gen.symbols_generated * self.metadata.block_size
            self._stats.goodput = self._stats.payload_bytes / elapsed if elapsed > 0 else 0

            if frame_count % 10 == 0:
                self.stats_updated.emit(self._stats)

            # Throttle to target FPS
            encode_time = time.monotonic() - t0
            sleep_time = frame_interval - encode_time
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.finished.emit()

    def stop(self) -> None:
        """Signal the worker to stop after the current frame."""
        self._running = False


class TransmissionEngine:
    """Manages the QThread lifecycle for the transmission worker."""

    def __init__(self):
        self._thread: Optional[QThread] = None
        self._worker: Optional[TransmissionWorker] = None

    def start(
        self,
        metadata: FileMetadata,
        blocks: List[bytes],
        target_fps: int = 30,
        on_frame: Optional[Callable] = None,
        on_stats: Optional[Callable] = None,
        on_finished: Optional[Callable] = None,
    ) -> None:
        """Start the transmission in a background thread."""
        self.stop()

        self._thread = QThread()
        self._worker = TransmissionWorker(metadata, blocks, target_fps)
        self._worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)

        if on_frame:
            self._worker.frame_ready.connect(on_frame)
        if on_stats:
            self._worker.stats_updated.connect(on_stats)
        if on_finished:
            self._worker.finished.connect(on_finished)

        self._thread.start()
        logger.info("Transmission started at %d FPS target", target_fps)

    def stop(self) -> None:
        """Stop the transmission thread."""
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
