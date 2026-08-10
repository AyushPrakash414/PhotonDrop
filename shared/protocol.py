"""
PhotonDrop — Packet Protocol Factory

High-level routines to create and parse the different PhotonDrop
packet types: SESSION_START, FILE_METADATA, DATA, SESSION_END,
and TRANSFER_COMPLETE.
"""

from __future__ import annotations

import json
from typing import Optional

from shared.constants import (
    MAGIC,
    PACKET_TYPE_DATA,
    PACKET_TYPE_FILE_METADATA,
    PACKET_TYPE_SESSION_END,
    PACKET_TYPE_SESSION_START,
    PACKET_TYPE_TRANSFER_COMPLETE,
    PROTOCOL_VERSION,
)
from shared.models import EncodedSymbol, FileMetadata, Packet, PacketHeader
from shared.serialization import deserialize_packet, serialize_packet


# ─── Packet Builders ──────────────────────────────────────────────


def build_session_start_packet(session_id: bytes) -> Packet:
    """Create a SESSION_START packet announcing a new transfer session."""
    header = PacketHeader(
        magic=MAGIC,
        version=PROTOCOL_VERSION,
        packet_type=PACKET_TYPE_SESSION_START,
        session_id=session_id,
        file_id="0" * 16,
        symbol_id=0,
        source_block_count=0,
        payload_length=0,
    )
    return Packet(header=header, payload=b"", checksum=0)


def build_file_metadata_packet(metadata: FileMetadata) -> Packet:
    """Create a FILE_METADATA packet containing file information as JSON payload."""
    meta_dict = {
        "file_id": metadata.file_id,
        "file_name": metadata.file_name,
        "file_size": metadata.file_size,
        "mime_type": metadata.mime_type,
        "block_size": metadata.block_size,
        "total_source_blocks": metadata.total_source_blocks,
        "sha256": metadata.sha256,
    }
    payload = json.dumps(meta_dict, separators=(",", ":")).encode("utf-8")

    header = PacketHeader(
        magic=MAGIC,
        version=PROTOCOL_VERSION,
        packet_type=PACKET_TYPE_FILE_METADATA,
        session_id=metadata.session_id,
        file_id=metadata.file_id,
        symbol_id=0,
        source_block_count=metadata.total_source_blocks,
        payload_length=len(payload),
    )
    return Packet(header=header, payload=payload, checksum=0)


def build_data_packet(
    session_id: bytes,
    file_id: str,
    symbol: EncodedSymbol,
    source_block_count: int,
) -> Packet:
    """Create a DATA packet carrying a single fountain-encoded symbol.

    The payload is the raw XOR'd symbol data.  The symbol_id allows the
    receiver to regenerate the same PRNG block selection deterministically.
    """
    header = PacketHeader(
        magic=MAGIC,
        version=PROTOCOL_VERSION,
        packet_type=PACKET_TYPE_DATA,
        session_id=session_id,
        file_id=file_id,
        symbol_id=symbol.symbol_id,
        source_block_count=source_block_count,
        payload_length=len(symbol.data),
    )
    return Packet(header=header, payload=symbol.data, checksum=0)


def build_session_end_packet(session_id: bytes, file_id: str) -> Packet:
    """Create a SESSION_END packet signalling the sender has finished."""
    header = PacketHeader(
        magic=MAGIC,
        version=PROTOCOL_VERSION,
        packet_type=PACKET_TYPE_SESSION_END,
        session_id=session_id,
        file_id=file_id,
        symbol_id=0,
        source_block_count=0,
        payload_length=0,
    )
    return Packet(header=header, payload=b"", checksum=0)


def build_transfer_complete_packet(session_id: bytes, file_id: str) -> Packet:
    """Create a TRANSFER_COMPLETE notification packet."""
    header = PacketHeader(
        magic=MAGIC,
        version=PROTOCOL_VERSION,
        packet_type=PACKET_TYPE_TRANSFER_COMPLETE,
        session_id=session_id,
        file_id=file_id,
        symbol_id=0,
        source_block_count=0,
        payload_length=0,
    )
    return Packet(header=header, payload=b"", checksum=0)


# ─── Metadata Parser ─────────────────────────────────────────────


def parse_file_metadata_payload(
    payload: bytes, session_id: bytes
) -> Optional[FileMetadata]:
    """Parse the JSON payload of a FILE_METADATA packet into a FileMetadata."""
    try:
        d = json.loads(payload.decode("utf-8"))
        return FileMetadata(
            file_id=d["file_id"],
            session_id=session_id,
            file_name=d["file_name"],
            file_size=d["file_size"],
            mime_type=d["mime_type"],
            block_size=d["block_size"],
            total_source_blocks=d["total_source_blocks"],
            sha256=d["sha256"],
        )
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
        return None
