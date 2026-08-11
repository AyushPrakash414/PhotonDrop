"""
PhotonDrop — Data Models

Dataclasses for file metadata, packet headers, encoded symbols,
transfer statistics, and receiver session state.
Matches lightspeed-share-main architecture with full test backward compatibility.
"""

from __future__ import annotations

import random
import uuid
import zlib
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Any, List, Optional

from shared.constants import (
    FRAME_DATA,
    FRAME_MANIFEST,
    MAGIC_0,
    MAGIC_1,
    PROTOCOL_VERSION,
)


# ─── Receiver State Machine ───────────────────────────────────────

class ReceiverState(IntEnum):
    """Explicit states for the receiver transfer state machine."""
    IDLE               = auto()
    SEARCHING          = auto()
    SESSION_DETECTED   = auto()
    RECEIVING_METADATA = auto()
    RECEIVING_DATA     = auto()
    DECODING           = auto()
    RECONSTRUCTING     = auto()
    VERIFYING          = auto()
    COMPLETE           = auto()
    ERROR              = auto()


# ─── File Metadata ─────────────────────────────────────────────────

@dataclass
class FileMetadata:
    """Metadata about the file being transferred."""
    file_id: Any                   # uint32 per-file numeric identifier or string
    file_name: str                 # original file name
    file_size: int                 # total file size in bytes
    mime_type: str                 # detected MIME type
    block_size: int                # size of each source block in bytes (chunkSize)
    total_source_blocks: int       # total number of source blocks (chunks / K)
    sha256: str                    # hex-encoded SHA-256 digest of original file
    session_id_bytes: bytes = b""  # optional legacy session_id storage

    def __init__(
        self,
        file_id: Any,
        file_name: str,
        file_size: int,
        mime_type: str,
        block_size: int,
        total_source_blocks: int,
        sha256: str,
        session_id: bytes = b"",
    ):
        if isinstance(file_id, str):
            try:
                self.file_id = int(file_id, 16) & 0xFFFFFFFF
            except Exception:
                self.file_id = zlib.crc32(file_id.encode("utf-8")) & 0xFFFFFFFF
        else:
            self.file_id = int(file_id) & 0xFFFFFFFF

        self.file_name = file_name
        self.file_size = file_size
        self.mime_type = mime_type
        self.block_size = block_size
        self.total_source_blocks = total_source_blocks
        self.sha256 = sha256
        self.session_id_bytes = session_id or self.file_id.to_bytes(4, byteorder="big").rjust(16, b"\x00")

    @property
    def session_id(self) -> bytes:
        """Returns session ID bytes for backward compatibility."""
        return self.session_id_bytes or self.file_id.to_bytes(4, byteorder="big").rjust(16, b"\x00")

    @property
    def file_id_str(self) -> str:
        """Returns hex-encoded file ID string."""
        return f"{self.file_id:08x}"

    @staticmethod
    def generate_session_id() -> bytes:
        """Generate a random 128-bit session ID for backward compatibility."""
        return uuid.uuid4().bytes

    @staticmethod
    def generate_file_id() -> int:
        """Generate a random 32-bit uint32 file ID."""
        return random.randint(1, 0xFFFFFFFF)


# ─── Packet Header ────────────────────────────────────────────────

@dataclass
class PacketHeader:
    """Wire-protocol 24-byte header matching lightspeed-share-main."""
    magic_0: int = MAGIC_0         # 0x50 ('P')
    magic_1: int = MAGIC_1         # 0x44 ('D')
    version: int = PROTOCOL_VERSION # 1
    packet_type: int = FRAME_DATA  # 0 = MANIFEST, 1 = DATA
    file_id: int = 0               # uint32
    chunks: int = 0                # K — total source blocks (uint32)
    chunk_size: int = 0            # block size in bytes (uint32)
    size: int = 0                  # total file size in bytes (uint32)
    seed: int = 0                  # symbol identifier (uint32)

    def __init__(
        self,
        magic_0: int = MAGIC_0,
        magic_1: int = MAGIC_1,
        version: int = PROTOCOL_VERSION,
        packet_type: int = FRAME_DATA,
        file_id: Any = 0,
        chunks: int = 0,
        chunk_size: int = 0,
        size: int = 0,
        seed: int = 0,
        # Backward compatibility kwargs
        magic: bytes = b"",
        session_id: bytes = b"",
        symbol_id: int = 0,
        source_block_count: int = 0,
        payload_length: int = 0,
    ):
        if magic:
            self.magic_0 = magic[0] if len(magic) > 0 else MAGIC_0
            self.magic_1 = magic[1] if len(magic) > 1 else MAGIC_1
        else:
            self.magic_0 = magic_0
            self.magic_1 = magic_1

        self.version = version
        self.packet_type = packet_type

        if isinstance(file_id, str):
            try:
                self.file_id = int(file_id, 16) & 0xFFFFFFFF
            except Exception:
                self.file_id = zlib.crc32(file_id.encode("utf-8")) & 0xFFFFFFFF
        else:
            self.file_id = int(file_id) & 0xFFFFFFFF

        self.chunks = chunks or source_block_count
        self.chunk_size = chunk_size or payload_length
        self.size = size
        self.seed = seed or symbol_id

    @property
    def magic(self) -> bytes:
        return bytes([self.magic_0, self.magic_1])

    @property
    def session_id(self) -> bytes:
        return self.file_id.to_bytes(4, byteorder="big").rjust(16, b"\x00")

    @property
    def symbol_id(self) -> int:
        return self.seed

    @property
    def source_block_count(self) -> int:
        return self.chunks

    @property
    def payload_length(self) -> int:
        return self.chunk_size


# ─── Packet ────────────────────────────────────────────────────────

@dataclass
class Packet:
    """A complete PhotonDrop visual frame packet: 24B header + payload."""
    header: PacketHeader
    payload: bytes                 # raw payload bytes
    checksum: int = 0              # legacy checksum field

    def human_readable(self) -> str:
        """Return a debug-friendly string representation."""
        from shared.constants import PACKET_TYPE_NAMES
        ptype = PACKET_TYPE_NAMES.get(self.header.packet_type, f"0x{self.header.packet_type:02x}")
        return (
            f"Packet(type={ptype}, "
            f"file_id=0x{self.header.file_id:08x}, "
            f"seed={self.header.seed}, "
            f"payload={len(self.payload)}B)"
        )


# ─── Fountain Symbol ──────────────────────────────────────────────

@dataclass
class EncodedSymbol:
    """An LT fountain-coded encoded symbol."""
    symbol_id: int                 # unique symbol identifier (seed)
    degree: int                    # number of source blocks XOR'd
    block_indices: List[int]       # which source blocks were combined
    data: bytes                    # XOR'd payload


# ─── Transfer Statistics ──────────────────────────────────────────

@dataclass
class TransferStats:
    """Real-time statistics tracked during a transfer session."""
    total_frames: int         = 0
    new_frames: int           = 0
    duplicate_frames: int     = 0
    invalid_frames: int       = 0
    dropped_frames: int       = 0
    unique_symbols: int       = 0
    total_symbols: int        = 0
    payload_bytes: int        = 0
    capture_fps: float        = 0.0
    decode_fps: float         = 0.0
    display_fps: float        = 0.0
    goodput: float            = 0.0      # bytes/sec of useful data
    elapsed_time: float       = 0.0
    decode_latency: float     = 0.0
    reconstruction_time: float = 0.0


# ─── Session Info (Receiver side) ─────────────────────────────────

@dataclass
class SessionInfo:
    """Tracks a receiver's knowledge of the current transfer session."""
    session_id: Optional[bytes]         = None
    file_metadata: Optional[FileMetadata] = None
    state: ReceiverState                = ReceiverState.IDLE
    received_symbol_ids: set            = field(default_factory=set)
    stats: TransferStats                = field(default_factory=TransferStats)
