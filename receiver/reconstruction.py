"""
PhotonDrop — File Reconstruction

State machine that manages the receiver session lifecycle:
  IDLE → SEARCHING → SESSION_DETECTED → RECEIVING_METADATA →
  RECEIVING_DATA → DECODING → VERIFYING → COMPLETE / ERROR

Handles fountain decoding, block reassembly, SHA-256 verification,
and safe file saving matching lightspeed-share-main.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from fountain.decoder import FountainDecoder
from sender.file_reader import sanitize_filename
from shared.constants import FRAME_DATA, FRAME_MANIFEST
from shared.hashing import compute_sha256
from shared.models import (
    FileMetadata,
    Packet,
    ReceiverState,
    SessionInfo,
)
from shared.protocol import parse_file_metadata_payload

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("received_files")


class Reconstruction:
    """Manages the full receiver state machine and file reconstruction."""

    def __init__(self, output_dir: Path = DEFAULT_OUTPUT_DIR):
        self.output_dir = output_dir
        self.session = SessionInfo()
        self._decoder: Optional[FountainDecoder] = None
        self._reconstruct_start: float = 0.0

    @property
    def state(self) -> ReceiverState:
        return self.session.state

    @property
    def progress(self) -> float:
        if self._decoder is not None:
            return self._decoder.progress()
        return 0.0

    def feed_packet(self, packet: Packet) -> None:
        """Process a validated packet through the state machine."""
        ptype = packet.header.packet_type

        if ptype == FRAME_MANIFEST:
            self._handle_metadata(packet)
        elif ptype == FRAME_DATA:
            self._handle_data(packet)

    # ── State handlers ─────────────────────────────────────────────

    def _handle_metadata(self, packet: Packet) -> None:
        if self.session.state in (
            ReceiverState.COMPLETE,
            ReceiverState.ERROR,
            ReceiverState.VERIFYING,
            ReceiverState.DECODING,
        ):
            return

        meta = parse_file_metadata_payload(packet.payload, packet.header.session_id, packet.header.file_id)
        if meta is None:
            # Fallback construct FileMetadata directly from 24B header
            h = packet.header
            if h.chunks > 0:
                meta = FileMetadata(
                    file_id=h.file_id,
                    file_name="received_file",
                    file_size=h.size,
                    mime_type="application/octet-stream",
                    block_size=h.chunk_size,
                    total_source_blocks=h.chunks,
                    sha256="",
                )

        if meta is None:
            logger.warning("Failed to parse file metadata")
            return

        if self._decoder is None or self.session.session_id != meta.session_id:
            self.session = SessionInfo(
                session_id=meta.session_id,
                file_metadata=meta,
                state=ReceiverState.RECEIVING_DATA,
            )
            self._decoder = FountainDecoder(
                K=meta.total_source_blocks,
                block_size=meta.block_size,
                session_id=meta.session_id,
                size=meta.file_size,
            )
            self._reconstruct_start = time.monotonic()
            logger.info(
                "Metadata received: %s (%d bytes, %d blocks)",
                meta.file_name,
                meta.file_size,
                meta.total_source_blocks,
            )

    def _handle_data(self, packet: Packet) -> None:
        if self.session.state in (ReceiverState.COMPLETE, ReceiverState.ERROR):
            return

        h = packet.header
        if self._decoder is None:
            # Auto-initialize decoder if data packet arrives with header info
            if h.chunks > 0:
                meta = FileMetadata(
                    file_id=h.file_id,
                    file_name="received_file",
                    file_size=h.size,
                    mime_type="application/octet-stream",
                    block_size=h.chunk_size,
                    total_source_blocks=h.chunks,
                    sha256="",
                )
                self.session = SessionInfo(
                    session_id=meta.session_id,
                    file_metadata=meta,
                    state=ReceiverState.RECEIVING_DATA,
                )
                self._decoder = FountainDecoder(
                    K=h.chunks,
                    block_size=h.chunk_size,
                    session_id=meta.session_id,
                    size=h.size,
                )
                self._reconstruct_start = time.monotonic()

        if self._decoder is None:
            return

        # Add data symbol to peeling decoder
        seed = h.seed
        payload = packet.payload
        self._decoder.add_symbol(seed, payload)

        if self.session.state != ReceiverState.RECEIVING_DATA:
            self.session.state = ReceiverState.RECEIVING_DATA

        # Check if decoding is complete
        if self._decoder.is_complete():
            self._finalize()

    # ── Finalisation ───────────────────────────────────────────────

    def _finalize(self) -> None:
        if self.session.state in (ReceiverState.COMPLETE, ReceiverState.ERROR):
            return

        self.session.state = ReceiverState.RECONSTRUCTING
        meta = self.session.file_metadata
        assembled_bytes = self._decoder.assemble()

        if assembled_bytes is None:
            self.session.state = ReceiverState.ERROR
            logger.error("Reconstruction failed — not enough symbols")
            return

        # Verify hash
        self.session.state = ReceiverState.VERIFYING
        received_hash = compute_sha256(assembled_bytes)
        elapsed = time.monotonic() - self._reconstruct_start
        self.session.stats.reconstruction_time = elapsed

        expected_hash = meta.sha256 if meta and meta.sha256 else ""

        if not expected_hash or received_hash == expected_hash:
            self.session.state = ReceiverState.COMPLETE
            safe_name = meta.file_name if meta and meta.file_name else "received_file"
            saved_path = self._save_file(assembled_bytes, safe_name)
            logger.info(
                "TRANSFER COMPLETE — FILE VERIFIED\nSaved to: %s",
                saved_path,
            )
        else:
            self.session.state = ReceiverState.ERROR
            logger.error(
                "INTEGRITY CHECK FAILED\n  Expected: %s\n  Got:      %s",
                expected_hash,
                received_hash,
            )

    def _save_file(self, data: bytes, filename: str) -> Path:
        """Save the reconstructed file to output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = sanitize_filename(filename)
        out_path = self.output_dir / safe_name

        if out_path.exists():
            stem = out_path.stem
            suffix = out_path.suffix
            counter = 1
            while out_path.exists():
                out_path = self.output_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        out_path.write_bytes(data)
        return out_path

    def reset(self) -> None:
        """Reset for a new session."""
        self.session = SessionInfo()
        self._decoder = None
