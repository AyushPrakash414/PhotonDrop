"""
PhotonDrop — Packet Protocol Factory

High-level routines to create and parse PhotonDrop packets and Manifest payloads,
matching lightspeed-share-main specifications.
"""

from __future__ import annotations

import json
from typing import Optional

from shared.constants import (
    FRAME_DATA,
    FRAME_MANIFEST,
    MAGIC_0,
    MAGIC_1,
    PROTOCOL_VERSION,
)
from shared.models import EncodedSymbol, FileMetadata, Packet, PacketHeader
from shared.serialization import (
    build_data_frame,
    build_manifest_frame,
    deserialize_packet,
    serialize_packet,
)


# ─── Packet Builders ──────────────────────────────────────────────


def build_file_metadata_packet(metadata: FileMetadata) -> Packet:
    """Create a MANIFEST packet containing file information as JSON payload."""
    manifest_dict = {
        "name": metadata.file_name,
        "size": metadata.file_size,
        "mime": metadata.mime_type,
        "digest": metadata.sha256,
        "chunks": metadata.total_source_blocks,
        "chunkSize": metadata.block_size,
    }
    payload = json.dumps(manifest_dict, separators=(",", ":")).encode("utf-8")

    header = PacketHeader(
        magic_0=MAGIC_0,
        magic_1=MAGIC_1,
        version=PROTOCOL_VERSION,
        packet_type=FRAME_MANIFEST,
        file_id=metadata.file_id,
        chunks=metadata.total_source_blocks,
        chunk_size=metadata.block_size,
        size=metadata.file_size,
        seed=0,
    )
    return Packet(header=header, payload=payload)


def build_data_packet(
    session_id: bytes,
    file_id: int,
    symbol: EncodedSymbol,
    source_block_count: int,
    file_size: int = 0,
) -> Packet:
    """Create a DATA packet carrying a single fountain-encoded symbol."""
    header = PacketHeader(
        magic_0=MAGIC_0,
        magic_1=MAGIC_1,
        version=PROTOCOL_VERSION,
        packet_type=FRAME_DATA,
        file_id=file_id & 0xFFFFFFFF if isinstance(file_id, int) else 0,
        chunks=source_block_count,
        chunk_size=len(symbol.data),
        size=file_size,
        seed=symbol.symbol_id & 0xFFFFFFFF,
    )
    return Packet(header=header, payload=symbol.data)


def build_session_start_packet(session_id: bytes) -> Packet:
    """Legacy helper returning an empty manifest packet."""
    header = PacketHeader(
        magic_0=MAGIC_0,
        magic_1=MAGIC_1,
        version=PROTOCOL_VERSION,
        packet_type=FRAME_MANIFEST,
        file_id=0,
        chunks=0,
        chunk_size=0,
        size=0,
        seed=0,
    )
    return Packet(header=header, payload=b"{}")


def build_session_end_packet(session_id: bytes, file_id: Any) -> Packet:
    """Legacy helper."""
    return build_session_start_packet(session_id)


def build_transfer_complete_packet(session_id: bytes, file_id: Any) -> Packet:
    """Legacy helper."""
    return build_session_start_packet(session_id)


# ─── Metadata Parser ─────────────────────────────────────────────


def parse_file_metadata_payload(
    payload: bytes, session_id: bytes, header_file_id: int = 0
) -> Optional[FileMetadata]:
    """Parse the JSON payload of a MANIFEST packet into FileMetadata."""
    try:
        d = json.loads(payload.decode("utf-8"))
        file_name = d.get("name") or d.get("file_name") or "unnamed_file"
        file_size = d.get("size") or d.get("file_size") or 0
        mime_type = d.get("mime") or d.get("mime_type") or "application/octet-stream"
        digest = d.get("digest") or d.get("sha256") or ""
        chunks = d.get("chunks") or d.get("total_source_blocks") or 1
        chunk_size = d.get("chunkSize") or d.get("block_size") or 512
        file_id_val = d.get("fileId") or d.get("file_id") or header_file_id
        if not file_id_val:
            file_id_val = FileMetadata.generate_file_id()

        return FileMetadata(
            file_id=file_id_val,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            block_size=chunk_size,
            total_source_blocks=chunks,
            sha256=digest,
        )
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
        return None
