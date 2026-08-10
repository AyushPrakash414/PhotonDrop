"""
PhotonDrop — File Reconstruction

State machine that manages the receiver session lifecycle:
  IDLE → SEARCHING → SESSION_DETECTED → RECEIVING_METADATA →
  RECEIVING_DATA → DECODING → VERIFYING → COMPLETE / ERROR

Handles fountain decoding, block reassembly, SHA-256 verification,
and safe file saving.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

from fountain.decoder import FountainDecoder
from fountain.symbols import derive_seed, select_blocks
from sender.file_reader import sanitize_filename
from shared.constants import (
    PACKET_TYPE_DATA,
    PACKET_TYPE_FILE_METADATA,
    PACKET_TYPE_SESSION_END,
    PACKET_TYPE_SESSION_START,
)
from shared.hashing import compute_sha256
from shared.models import (
    EncodedSymbol,
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

        if ptype == PACKET_TYPE_SESSION_START:
            self._handle_session_start(packet)
        elif ptype == PACKET_TYPE_FILE_METADATA:
            self._handle_metadata(packet)
        elif ptype == PACKET_TYPE_DATA:
            self._handle_data(packet)
        elif ptype == PACKET_TYPE_SESSION_END:
            self._handle_session_end(packet)

    # ── State handlers ─────────────────────────────────────────────

    def _handle_session_start(self, packet: Packet) -> None:
        sid = packet.header.session_id
        if self.session.state not in (ReceiverState.IDLE, ReceiverState.SEARCHING, ReceiverState.COMPLETE, ReceiverState.ERROR):
            # Already in an active session — ignore new sessions
            if sid != self.session.session_id:
                return
        self.session = SessionInfo(session_id=sid, state=ReceiverState.SESSION_DETECTED)
        self._decoder = None
        logger.info("Session detected: %s…", sid.hex()[:8])

    def _handle_metadata(self, packet: Packet) -> None:
        if self.session.state not in (
            ReceiverState.SESSION_DETECTED,
            ReceiverState.RECEIVING_METADATA,
            ReceiverState.RECEIVING_DATA,
        ):
            return

        meta = parse_file_metadata_payload(packet.payload, packet.header.session_id)
        if meta is None:
            logger.warning("Failed to parse file metadata")
            return

        self.session.file_metadata = meta
        self.session.state = ReceiverState.RECEIVING_DATA
        self._decoder = FountainDecoder(
            K=meta.total_source_blocks,
            block_size=meta.block_size,
            session_id=meta.session_id,
        )
        self._reconstruct_start = time.monotonic()
        logger.info(
            "Metadata received: %s (%d bytes, %d blocks)",
            meta.file_name,
            meta.file_size,
            meta.total_source_blocks,
        )

    def _handle_data(self, packet: Packet) -> None:
        if self.session.state != ReceiverState.RECEIVING_DATA:
            return
        if self._decoder is None:
            return

        # Build an EncodedSymbol from the packet
        sid = packet.header.symbol_id
        meta = self.session.file_metadata
        seed = derive_seed(meta.session_id, sid)
        # We need to sample the degree the same way the encoder did
        from fountain.degree_distribution import DegreeSampler
        sampler = DegreeSampler(meta.total_source_blocks)
        import random
        rng = random.Random(seed)
        degree = sampler.sample(rng)
        block_indices = select_blocks(seed, degree, meta.total_source_blocks)

        symbol = EncodedSymbol(
            symbol_id=sid,
            degree=degree,
            block_indices=block_indices,
            data=packet.payload,
        )

        self._decoder.add_symbol(symbol)

        logger.debug(
            "Symbol %d (deg %d) — progress %d/%d",
            sid,
            degree,
            self._decoder.recovered_count(),
            meta.total_source_blocks,
        )

        # Check if decoding is complete
        if self._decoder.is_complete():
            self._finalize()

    def _handle_session_end(self, packet: Packet) -> None:
        if self._decoder is not None and self._decoder.is_complete():
            self._finalize()

    # ── Finalisation ───────────────────────────────────────────────

    def _finalize(self) -> None:
        if self.session.state in (ReceiverState.COMPLETE, ReceiverState.ERROR):
            return

        self.session.state = ReceiverState.RECONSTRUCTING
        meta = self.session.file_metadata
        blocks = self._decoder.reconstruct()

        if blocks is None:
            self.session.state = ReceiverState.ERROR
            logger.error("Reconstruction failed — not enough symbols")
            return

        # Reassemble
        raw = b"".join(blocks)
        raw = raw[: meta.file_size]  # strip zero-padding from last block

        # Verify hash
        self.session.state = ReceiverState.VERIFYING
        received_hash = compute_sha256(raw)
        elapsed = time.monotonic() - self._reconstruct_start
        self.session.stats.reconstruction_time = elapsed

        if received_hash == meta.sha256:
            self.session.state = ReceiverState.COMPLETE
            saved_path = self._save_file(raw, meta.file_name)
            logger.info(
                "TRANSFER COMPLETE — FILE VERIFIED (SHA256 match)\nSaved to: %s",
                saved_path,
            )
        else:
            self.session.state = ReceiverState.ERROR
            logger.error(
                "INTEGRITY CHECK FAILED\n  Expected: %s\n  Got:      %s",
                meta.sha256,
                received_hash,
            )

    def _save_file(self, data: bytes, filename: str) -> Path:
        """Save the reconstructed file to the output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = sanitize_filename(filename)
        out_path = self.output_dir / safe_name

        # Avoid overwriting
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
