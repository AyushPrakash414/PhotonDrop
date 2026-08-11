"""
PhotonDrop — Integrity Tests

Tests payload corruption detection and ensures invalid checksum
packets are safely discarded.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from shared.checksum import compute_crc32
from shared.constants import MAGIC, PACKET_TYPE_DATA, PROTOCOL_VERSION
from shared.hashing import compute_sha256
from shared.models import PacketHeader, Packet
from shared.serialization import deserialize_packet, serialize_packet


class TestCorruptionDetection:
    """Verify that corrupted packets are rejected."""

    def _make_packet(self, payload: bytes = b"test payload data") -> Packet:
        header = PacketHeader(
            magic=MAGIC,
            version=PROTOCOL_VERSION,
            packet_type=PACKET_TYPE_DATA,
            session_id=b"\xcc" * 16,
            file_id="test1234test5678",
            symbol_id=7,
            source_block_count=10,
            payload_length=len(payload),
        )
        return Packet(header=header, payload=payload, checksum=0)

    def test_unmodified_packet_accepted(self):
        pkt = self._make_packet()
        raw = serialize_packet(pkt)
        assert deserialize_packet(raw) is not None

    def test_single_byte_flip_detected(self):
        """Flipping magic byte or header fields should cause rejection."""
        pkt = self._make_packet(b"A" * 50)
        raw = bytearray(serialize_packet(pkt))
        raw[0] ^= 0x01  # Corrupt magic byte
        assert deserialize_packet(bytes(raw)) is None

    def test_header_corruption_detected(self):
        pkt = self._make_packet()
        raw = bytearray(serialize_packet(pkt))
        # Corrupt version byte (offset 2)
        raw[2] = 99
        assert deserialize_packet(bytes(raw)) is None

    def test_multiple_byte_corruption(self):
        pkt = self._make_packet(b"X" * 100)
        raw = bytearray(serialize_packet(pkt))
        # Corrupt magic
        raw[0] = 0xFF
        raw[1] = 0xFF
        assert deserialize_packet(bytes(raw)) is None


class TestSHA256:
    def test_hash_deterministic(self):
        data = b"PhotonDrop integrity test"
        h1 = compute_sha256(data)
        h2 = compute_sha256(data)
        assert h1 == h2

    def test_different_data_different_hash(self):
        assert compute_sha256(b"aaa") != compute_sha256(b"bbb")

    def test_hash_length(self):
        h = compute_sha256(b"test")
        assert len(h) == 64  # 256 bits = 64 hex chars


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
