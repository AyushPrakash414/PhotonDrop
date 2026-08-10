"""
PhotonDrop — Data Models

Dataclasses for file metadata, packet headers, encoded symbols,
transfer statistics, and receiver session state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import List, Optional


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
    file_id: str                   # unique per-file identifier
    session_id: bytes              # 128-bit session identifier (16 bytes)
    file_name: str                 # sanitized original file name
    file_size: int                 # total file size in bytes
    mime_type: str                 # detected MIME type
    block_size: int                # size of each source block in bytes
    total_source_blocks: int       # total number of source blocks (K)
    sha256: str                    # hex-encoded SHA-256 of the original file

    @staticmethod
    def generate_session_id() -> bytes:
        """Generate a cryptographically random 128-bit session ID."""
        return uuid.uuid4().bytes

    @staticmethod
    def generate_file_id() -> str:
        """Generate a unique file identifier."""
        return uuid.uuid4().hex[:16]


# ─── Packet Header ────────────────────────────────────────────────

@dataclass
class PacketHeader:
    """Wire-protocol header for every PhotonDrop packet."""
    magic: bytes                   # 5 bytes: b"PDROP"
    version: int                   # protocol version (uint8)
    packet_type: int               # one of PACKET_TYPE_* (uint8)
    session_id: bytes              # 16 bytes
    file_id: str                   # 16-char hex string
    symbol_id: int                 # encoded symbol identifier (uint32)
    source_block_count: int        # K — total number of source blocks (uint16)
    payload_length: int            # length of the payload section (uint16)


# ─── Packet ────────────────────────────────────────────────────────

@dataclass
class Packet:
    """A complete PhotonDrop wire packet: header + payload + checksum."""
    header: PacketHeader
    payload: bytes                 # raw payload bytes
    checksum: int                  # CRC32 checksum (uint32)

    def human_readable(self) -> str:
        """Return a debug-friendly string representation."""
        from shared.constants import PACKET_TYPE_NAMES
        ptype = PACKET_TYPE_NAMES.get(self.header.packet_type, f"0x{self.header.packet_type:02x}")
        return (
            f"Packet(type={ptype}, "
            f"session={self.header.session_id.hex()[:8]}…, "
            f"symbol={self.header.symbol_id}, "
            f"payload={self.header.payload_length}B, "
            f"crc=0x{self.checksum:08x})"
        )


# ─── Fountain Symbol ──────────────────────────────────────────────

@dataclass
class EncodedSymbol:
    """An LT fountain-coded encoded symbol."""
    symbol_id: int                 # unique symbol identifier
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
