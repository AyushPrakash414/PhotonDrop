"""
PhotonDrop — Protocol Unit Tests

Tests binary packet serialization/deserialization, CRC32 checksum
generation, and packet header validation.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from shared.checksum import compute_crc32, verify_crc32
from shared.constants import (
    MAGIC,
    PACKET_TYPE_DATA,
    PACKET_TYPE_FILE_METADATA,
    PACKET_TYPE_SESSION_START,
    PROTOCOL_VERSION,
)
from shared.models import FileMetadata, PacketHeader, Packet
from shared.protocol import (
    build_data_packet,
    build_file_metadata_packet,
    build_session_start_packet,
    parse_file_metadata_payload,
)
from shared.serialization import deserialize_packet, serialize_packet


class TestChecksum:
    def test_crc32_deterministic(self):
        data = b"PhotonDrop test data"
        c1 = compute_crc32(data)
        c2 = compute_crc32(data)
        assert c1 == c2

    def test_crc32_different_data(self):
        assert compute_crc32(b"aaa") != compute_crc32(b"bbb")

    def test_verify_crc32(self):
        data = b"hello world"
        crc = compute_crc32(data)
        assert verify_crc32(data, crc) is True
        assert verify_crc32(data, crc ^ 1) is False


class TestSerialization:
    def _make_data_packet(self, payload: bytes = b"\x01\x02\x03") -> Packet:
        session_id = b"\x00" * 16
        header = PacketHeader(
            magic=MAGIC,
            version=PROTOCOL_VERSION,
            packet_type=PACKET_TYPE_DATA,
            session_id=session_id,
            file_id="abcdef1234567890",
            symbol_id=42,
            source_block_count=100,
            payload_length=len(payload),
        )
        return Packet(header=header, payload=payload, checksum=0)

    def test_round_trip(self):
        pkt = self._make_data_packet(b"hello")
        raw = serialize_packet(pkt)
        recovered = deserialize_packet(raw)
        assert recovered is not None
        assert recovered.header.magic == MAGIC
        assert recovered.header.version == PROTOCOL_VERSION
        assert recovered.header.packet_type == PACKET_TYPE_DATA
        assert recovered.header.symbol_id == 42
        assert recovered.header.source_block_count == 100
        assert recovered.payload == b"hello"

    def test_corrupted_checksum_rejected(self):
        pkt = self._make_data_packet(b"test")
        raw = bytearray(serialize_packet(pkt))
        # Flip a bit in the checksum (last 4 bytes)
        raw[-1] ^= 0xFF
        assert deserialize_packet(bytes(raw)) is None

    def test_wrong_magic_rejected(self):
        pkt = self._make_data_packet()
        raw = bytearray(serialize_packet(pkt))
        raw[0] = 0xFF  # corrupt magic
        assert deserialize_packet(bytes(raw)) is None

    def test_truncated_packet_rejected(self):
        pkt = self._make_data_packet(b"x" * 10)
        raw = serialize_packet(pkt)
        assert deserialize_packet(raw[:20]) is None

    def test_empty_payload(self):
        pkt = self._make_data_packet(b"")
        raw = serialize_packet(pkt)
        recovered = deserialize_packet(raw)
        assert recovered is not None
        assert recovered.payload == b""
        assert recovered.header.payload_length == 0


class TestProtocolPackets:
    def test_session_start_round_trip(self):
        sid = b"\xaa" * 16
        pkt = build_session_start_packet(sid)
        raw = serialize_packet(pkt)
        recovered = deserialize_packet(raw)
        assert recovered is not None
        assert recovered.header.packet_type == PACKET_TYPE_SESSION_START
        assert recovered.header.session_id == sid

    def test_file_metadata_round_trip(self):
        meta = FileMetadata(
            file_id="abc123def4567890",
            session_id=b"\xbb" * 16,
            file_name="test.pdf",
            file_size=12345,
            mime_type="application/pdf",
            block_size=256,
            total_source_blocks=49,
            sha256="a" * 64,
        )
        pkt = build_file_metadata_packet(meta)
        raw = serialize_packet(pkt)
        recovered = deserialize_packet(raw)
        assert recovered is not None
        assert recovered.header.packet_type == PACKET_TYPE_FILE_METADATA

        parsed = parse_file_metadata_payload(recovered.payload, recovered.header.session_id)
        assert parsed is not None
        assert parsed.file_name == "test.pdf"
        assert parsed.file_size == 12345
        assert parsed.total_source_blocks == 49
        assert parsed.sha256 == "a" * 64


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
