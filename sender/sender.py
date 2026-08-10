"""
PhotonDrop — Sender Orchestrator

High-level controller that ties together file reading, fountain
encoding, packet generation, and visual transmission.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, List, Optional, Union

from sender.file_reader import prepare_file
from sender.transmission_engine import TransmissionEngine
from shared.constants import DEFAULT_BLOCK_SIZE
from shared.models import FileMetadata

logger = logging.getLogger(__name__)


class Sender:
    """PhotonDrop Sender — orchestrates file-to-screen transmission."""

    def __init__(self):
        self.engine = TransmissionEngine()
        self.metadata: Optional[FileMetadata] = None
        self.blocks: Optional[List[bytes]] = None
        self.raw_data: Optional[bytes] = None

    def load_file(
        self,
        file_path: Union[str, Path],
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> FileMetadata:
        """Load and prepare a file for transmission.

        Returns the FileMetadata for display in the UI.
        """
        self.metadata, self.blocks, self.raw_data = prepare_file(file_path, block_size)
        logger.info(
            "Loaded: %s (%d bytes, %d blocks, SHA256=%s…)",
            self.metadata.file_name,
            self.metadata.file_size,
            self.metadata.total_source_blocks,
            self.metadata.sha256[:16],
        )
        return self.metadata

    def start_transmission(
        self,
        target_fps: int = 30,
        on_frame: Optional[Callable] = None,
        on_stats: Optional[Callable] = None,
        on_finished: Optional[Callable] = None,
    ) -> None:
        """Begin transmitting visual frames."""
        if self.metadata is None or self.blocks is None:
            raise RuntimeError("No file loaded — call load_file() first")

        self.engine.start(
            metadata=self.metadata,
            blocks=self.blocks,
            target_fps=target_fps,
            on_frame=on_frame,
            on_stats=on_stats,
            on_finished=on_finished,
        )

    def stop_transmission(self) -> None:
        """Stop the current transmission."""
        self.engine.stop()

    @property
    def is_transmitting(self) -> bool:
        return self.engine.is_running
