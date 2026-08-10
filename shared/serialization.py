"""
PhotonDrop — Binary Serialization

Packs and unpacks PhotonDrop wire-protocol packets using Python's
struct module for compact binary encoding.

Wire format (all multi-byte fields are big-endian):

    Offset  Size   Field
    ──────  ─────  ──────────────────────
     0       5     MAGIC  ("PDROP")
     5       1     VERSION (uint8)
     6       1     PACKET_TYPE (uint8)
     7      16     SESSION_ID (16 bytes)
    23      16     FILE_ID (16 ASCII chars)
    39       4     SYMBOL_ID (uint32)
    43       2     SOURCE_BLOCK_COUNT (uint16)
    45       2     PAYLOAD_LENGTH (uint16)
    47       N     PAYLOAD (N = PAYLOAD_LENGTH)
    47+N     4     CHECKSUM (CRC32 uint32)
    ──────  ─────  ──────────────────────
    Total:  51 + N bytes

The CHECKSUM covers bytes [0 … 47+N-1]  (everything before the checksum).
"""

from __future__ import annotations

import struct
from typing import Optional

from shared.checksum import compute_crc32, verify_crc32
from shared.constants import (
    MAGIC,
    MAX_PACKET_SIZE,
    MAX_PAYLOAD_SIZE,
    PROTOCOL_VERSION,
)
from shared.models import Packet, PacketHeader


# ─── Header struct format (big-endian) ────────────────────────────
# 5s  = MAGIC
# B   = VERSION
# B   = PACKET_TYPE
# 16s = SESSION_ID
# 16s = FILE_ID (ASCII)
# I   = SYMBOL_ID      (uint32)
# H   = SOURCE_BLOCK_COUNT (uint16)
# H   = PAYLOAD_LENGTH     (uint16)
_HEADER_FMT = "!5sBB16s16sIHH"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)   # 47 bytes

_CHECKSUM_FMT = "!I"
_CHECKSUM_SIZE = struct.calcsize(_CHECKSUM_FMT)  # 4 bytes


def serialize_packet(packet: Packet) -> bytes:
    """Serialize a Packet into a compact binary byte string.

    The checksum is computed over the header + payload and appended at
    the end.  Any checksum value stored in ``packet.checksum`` is
    replaced with the freshly computed one.
    """
    file_id_bytes = packet.header.file_id.encode("ascii").ljust(16, b"\x00")[:16]

    header_bytes = struct.pack(
        _HEADER_FMT,
        packet.header.magic,
        packet.header.version,
        packet.header.packet_type,
        packet.header.session_id,
        file_id_bytes,
        packet.header.symbol_id,
        packet.header.source_block_count,
        packet.header.payload_length,
    )

    body = header_bytes + packet.payload
    crc = compute_crc32(body)
    return body + struct.pack(_CHECKSUM_FMT, crc)


def deserialize_packet(data: bytes) -> Optional[Packet]:
    """Deserialize binary data into a Packet.

    Returns ``None`` if the data is too short, the magic is wrong,
    the version is unsupported, or the checksum fails.
    """
    if len(data) < _HEADER_SIZE + _CHECKSUM_SIZE:
        return None

    # Unpack header
    (
        magic,
        version,
        packet_type,
        session_id,
        file_id_raw,
        symbol_id,
        source_block_count,
        payload_length,
    ) = struct.unpack_from(_HEADER_FMT, data, 0)

    # Validate magic
    if magic != MAGIC:
        return None

    # Validate version
    if version != PROTOCOL_VERSION:
        return None

    # Validate payload length
    expected_total = _HEADER_SIZE + payload_length + _CHECKSUM_SIZE
    if len(data) < expected_total:
        return None
    if payload_length > MAX_PAYLOAD_SIZE:
        return None

    # Extract payload
    payload = data[_HEADER_SIZE : _HEADER_SIZE + payload_length]

    # Extract and verify checksum
    crc_offset = _HEADER_SIZE + payload_length
    (checksum,) = struct.unpack_from(_CHECKSUM_FMT, data, crc_offset)
    body = data[:crc_offset]
    if not verify_crc32(body, checksum):
        return None

    file_id = file_id_raw.rstrip(b"\x00").decode("ascii", errors="replace")

    header = PacketHeader(
        magic=magic,
        version=version,
        packet_type=packet_type,
        session_id=session_id,
        file_id=file_id,
        symbol_id=symbol_id,
        source_block_count=source_block_count,
        payload_length=payload_length,
    )

    return Packet(header=header, payload=payload, checksum=checksum)


def get_header_size() -> int:
    """Return the fixed header size in bytes."""
    return _HEADER_SIZE


def get_overhead() -> int:
    """Return total per-packet overhead (header + checksum) in bytes."""
    return _HEADER_SIZE + _CHECKSUM_SIZE
