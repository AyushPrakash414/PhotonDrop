"""
PhotonDrop — Binary & Base64 Serialization

Packs and unpacks PhotonDrop wire-protocol frames matching lightspeed-share-main.

Wire format (24 bytes fixed header, big-endian):

    Offset  Size   Field
    ──────  ─────  ───────────────────────────────
     0       1     MAGIC_0 (0x50 'P')
     1       1     MAGIC_1 (0x44 'D')
     2       1     VERSION (1)
     3       1     TYPE (0 = MANIFEST, 1 = DATA)
     4       4     FILE_ID (uint32)
     8       4     CHUNKS / K (uint32)
    12       4     CHUNK_SIZE (uint32)
    16       4     SIZE / Total bytes (uint32)
    20       4     SEED / Symbol ID (uint32)
    24       N     PAYLOAD (JSON for MANIFEST, bytes for DATA)
    ──────  ─────  ───────────────────────────────
    Total:  24 + N bytes

Frames are Base64 encoded for optical QR transport.
"""

from __future__ import annotations

import base64
import json
import struct
from typing import Any, Dict, Optional

from shared.constants import (
    FRAME_DATA,
    FRAME_MANIFEST,
    HEADER_BYTES,
    MAGIC_0,
    MAGIC_1,
    PROTOCOL_VERSION,
)
from shared.models import FileMetadata, Packet, PacketHeader

_HEADER_FMT = "!BBBBIIIII"


def build_manifest_frame(file_id: int, manifest: Dict[str, Any]) -> str:
    """Build a Base64-encoded Manifest optical frame."""
    json_bytes = json.dumps(manifest, separators=(",", ":")).encode("utf-8")
    header_bytes = struct.pack(
        _HEADER_FMT,
        MAGIC_0,
        MAGIC_1,
        PROTOCOL_VERSION,
        FRAME_MANIFEST,
        file_id & 0xFFFFFFFF,
        manifest.get("chunks", 0),
        manifest.get("chunkSize", 0),
        manifest.get("size", 0),
        0,
    )
    frame_bytes = header_bytes + json_bytes
    return base64.b64encode(frame_bytes).decode("ascii")


def build_data_frame(
    file_id: int,
    chunks: int,
    chunk_size: int,
    size: int,
    seed: int,
    payload: bytes,
) -> str:
    """Build a Base64-encoded Data optical frame."""
    header_bytes = struct.pack(
        _HEADER_FMT,
        MAGIC_0,
        MAGIC_1,
        PROTOCOL_VERSION,
        FRAME_DATA,
        file_id & 0xFFFFFFFF,
        chunks,
        chunk_size,
        size,
        seed & 0xFFFFFFFF,
    )
    frame_bytes = header_bytes + payload
    return base64.b64encode(frame_bytes).decode("ascii")


def parse_frame(text: str) -> Optional[Dict[str, Any]]:
    """Parse a Base64 text string into a frame object matching lightspeed-share-main parseFrame."""
    if not text:
        return None
    try:
        raw_bytes = base64.b64decode(text.strip())
    except Exception:
        return None

    if len(raw_bytes) < HEADER_BYTES:
        return None

    m0, m1, ver, ftype, file_id, chunks, chunk_size, size, seed = struct.unpack_from(_HEADER_FMT, raw_bytes, 0)
    if m0 != MAGIC_0 or m1 != MAGIC_1 or ver != PROTOCOL_VERSION:
        return None

    payload = raw_bytes[HEADER_BYTES:]

    if ftype == FRAME_MANIFEST:
        try:
            manifest_dict = json.loads(payload.decode("utf-8"))
            return {
                "type": "manifest",
                "file_id": file_id,
                "manifest": manifest_dict,
            }
        except Exception:
            return None

    if ftype == FRAME_DATA:
        if chunks == 0 or len(payload) != chunk_size:
            return None
        return {
            "type": "data",
            "file_id": file_id,
            "chunks": chunks,
            "chunk_size": chunk_size,
            "size": size,
            "seed": seed,
            "payload": payload,
        }

    return None


def serialize_packet(packet: Packet) -> bytes:
    """Serialize Packet to raw binary 24B header + payload."""
    header_bytes = struct.pack(
        _HEADER_FMT,
        packet.header.magic_0,
        packet.header.magic_1,
        packet.header.version,
        packet.header.packet_type,
        packet.header.file_id & 0xFFFFFFFF,
        packet.header.chunks,
        packet.header.chunk_size,
        packet.header.size,
        packet.header.seed & 0xFFFFFFFF,
    )
    return header_bytes + packet.payload


def deserialize_packet(data: bytes | str) -> Optional[Packet]:
    """Deserialize raw binary data or Base64 string into Packet."""
    text = None
    if isinstance(data, str):
        text = data
    elif isinstance(data, bytes):
        try:
            text = data.decode("ascii").strip()
        except Exception:
            text = None

    if text and text.startswith(("UEQ", "PD")):
        parsed = parse_frame(text)
        if parsed is not None:
            if parsed["type"] == "manifest":
                m = parsed["manifest"]
                header = PacketHeader(
                    magic_0=MAGIC_0,
                    magic_1=MAGIC_1,
                    version=PROTOCOL_VERSION,
                    packet_type=FRAME_MANIFEST,
                    file_id=parsed["file_id"],
                    chunks=m.get("chunks", 0),
                    chunk_size=m.get("chunkSize", 0),
                    size=m.get("size", 0),
                    seed=0,
                )
                payload_bytes = json.dumps(m, separators=(",", ":")).encode("utf-8")
                return Packet(header=header, payload=payload_bytes)
            elif parsed["type"] == "data":
                header = PacketHeader(
                    magic_0=MAGIC_0,
                    magic_1=MAGIC_1,
                    version=PROTOCOL_VERSION,
                    packet_type=FRAME_DATA,
                    file_id=parsed["file_id"],
                    chunks=parsed["chunks"],
                    chunk_size=parsed["chunk_size"],
                    size=parsed["size"],
                    seed=parsed["seed"],
                )
                return Packet(header=header, payload=parsed["payload"])

    if not isinstance(data, bytes) or len(data) < HEADER_BYTES:
        return None

    m0, m1, ver, ftype, file_id, chunks, chunk_size, size, seed = struct.unpack_from(_HEADER_FMT, data, 0)
    if m0 != MAGIC_0 or m1 != MAGIC_1 or ver != PROTOCOL_VERSION:
        return None

    if ftype not in (FRAME_MANIFEST, FRAME_DATA):
        return None

    payload = data[HEADER_BYTES:]
    if ftype == FRAME_DATA and len(payload) != chunk_size:
        return None

    header = PacketHeader(
        magic_0=m0,
        magic_1=m1,
        version=ver,
        packet_type=ftype,
        file_id=file_id,
        chunks=chunks,
        chunk_size=chunk_size,
        size=size,
        seed=seed,
    )
    return Packet(header=header, payload=payload)
