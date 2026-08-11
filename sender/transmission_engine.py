"""
PhotonDrop — Transmission Engine

Drives the high-speed loop that continuously generates fountain-coded
packets, encodes them as QR images, and signals the UI to display them.

Runs in a background daemon thread so the FastAPI event loop stays responsive.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, List, Optional

from sender.packet_generator import PacketGenerator
from shared.models import FileMetadata, TransferStats
from visual.encoder import QRTransport, VisualTransport

logger = logging.getLogger(__name__)


class TransmissionWorker:
    """Worker that runs in a background thread producing QR frames."""

    def __init__(
        self,
        metadata: FileMetadata,
        blocks: List[bytes],
        target_fps: int = 30,
        transport: Optional[VisualTransport] = None,
        on_frame: Optional[Callable] = None,
        on_stats: Optional[Callable] = None,
        on_finished: Optional[Callable] = None,
    ):
        self.metadata = metadata
        self.blocks = blocks
        self.target_fps = target_fps
        self.transport = transport or QRTransport(error_correction="M", box_size=4, border=2)
        self.on_frame = on_frame
        self.on_stats = on_stats
        self.on_finished = on_finished
        self._running = False
        self._stats = TransferStats()

    def run(self) -> None:
        """Main transmission loop — runs in a background daemon thread."""
        self._running = True
        gen = PacketGenerator(self.metadata, self.blocks)

        try:
            # Pre-encode session start and metadata images
            session_start_img = self.transport.encode(gen.session_start_bytes())
            metadata_img = self.transport.encode(gen.metadata_bytes())

            # Emit initial header frames
            if self.on_frame:
                self.on_frame(session_start_img)
            time.sleep(0.1)
            if self.on_frame:
                self.on_frame(metadata_img)
            time.sleep(0.1)

            frame_interval = 1.0 / self.target_fps
            start_time = time.monotonic()
            frame_count = 0

            for data_bytes in gen.data_stream():
                if not self._running:
                    break

                # Periodically re-emit metadata every 30 frames (~1 sec) so late-joining receivers lock on
                if frame_count > 0 and frame_count % 30 == 0:
                    if self.on_frame:
                        self.on_frame(metadata_img)
                    time.sleep(frame_interval)

                if not self._running:
                    break

                t0 = time.monotonic()
                img = self.transport.encode(data_bytes)
                if self.on_frame:
                    self.on_frame(img)
                frame_count += 1

                # Update stats
                elapsed = time.monotonic() - start_time
                self._stats.total_frames = frame_count + 2  # +2 for session/meta
                self._stats.display_fps = frame_count / elapsed if elapsed > 0 else 0
                self._stats.elapsed_time = elapsed
                self._stats.payload_bytes = gen.symbols_generated * self.metadata.block_size
                self._stats.goodput = self._stats.payload_bytes / elapsed if elapsed > 0 else 0

                if frame_count % 10 == 0 and self.on_stats:
                    self.on_stats(self._stats)

                # Throttle to target FPS
                encode_time = time.monotonic() - t0
                sleep_time = frame_interval - encode_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as e:
            logger.exception("TransmissionWorker error: %s", e)
        finally:
            self._running = False
            if self.on_finished:
                self.on_finished()
            logger.info("Transmission worker finished")

    def stop(self) -> None:
        """Signal the worker to stop after the current frame."""
        self._running = False


class TransmissionEngine:
    """Manages the background thread lifecycle for the transmission worker."""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
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
        """Start the transmission in a background daemon thread."""
        self.stop()

        self._worker = TransmissionWorker(
            metadata=metadata,
            blocks=blocks,
            target_fps=target_fps,
            on_frame=on_frame,
            on_stats=on_stats,
            on_finished=on_finished,
        )

        self._thread = threading.Thread(
            target=self._worker.run,
            daemon=True,
            name="PhotonDrop-TxWorker",
        )
        self._thread.start()
        logger.info("Transmission started at %d FPS target", target_fps)

    def stop(self) -> None:
        """Stop the transmission thread."""
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None
        self._worker = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
