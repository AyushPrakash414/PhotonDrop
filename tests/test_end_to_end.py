"""
PhotonDrop — End-to-End Integration Test

Full pipeline simulation:
  1. Generate a random binary file
  2. SHA-256 the original
  3. Encode via fountain encoder
  4. Serialize to wire packets
  5. Simulate frame loss + shuffling
  6. Deserialize packets
  7. Fountain decode
  8. Reconstruct file
  9. SHA-256 the result
  10. Compare hashes
"""

import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from fountain.decoder import FountainDecoder
from fountain.encoder import FountainEncoder
from fountain.symbols import symbol_plan
from sender.file_reader import split_into_blocks
from shared.constants import (
    PACKET_TYPE_DATA,
    PACKET_TYPE_FILE_METADATA,
    PACKET_TYPE_SESSION_START,
)
from shared.hashing import compute_sha256
from shared.models import EncodedSymbol, FileMetadata
from shared.protocol import (
    build_data_packet,
    build_file_metadata_packet,
    build_session_start_packet,
    parse_file_metadata_payload,
)
from shared.serialization import deserialize_packet, serialize_packet


class TestEndToEnd:
    """Full pipeline: file → encode → serialize → [loss] → decode → verify."""

    def _run_e2e(
        self,
        file_size: int = 5000,
        block_size: int = 128,
        loss_rate: float = 0.10,
        overhead: float = 3.0,
    ):
        # 1. Generate random binary file
        original_data = os.urandom(file_size)
        original_hash = compute_sha256(original_data)

        # 2. Prepare metadata
        session_id = os.urandom(16)
        file_id = "e2etest123456789"
        blocks = split_into_blocks(original_data, block_size)
        K = len(blocks)

        meta = FileMetadata(
            file_id=file_id,
            session_id=session_id,
            file_name="test_file.bin",
            file_size=file_size,
            mime_type="application/octet-stream",
            block_size=block_size,
            total_source_blocks=K,
            sha256=original_hash,
        )

        # 3. Encode: fountain encoder → wire packets
        encoder = FountainEncoder(blocks, session_id)
        max_symbols = int(K * overhead)

        # Build session start + metadata packets
        session_pkt_bytes = serialize_packet(build_session_start_packet(session_id))
        meta_pkt_bytes = serialize_packet(build_file_metadata_packet(meta))

        # Build data packets
        data_packets_bytes = []
        for symbol in encoder.generate(max_symbols):
            pkt = build_data_packet(session_id, file_id, symbol, K)
            data_packets_bytes.append(serialize_packet(pkt))

        # 4. Simulate loss + shuffle
        surviving = []
        for raw in data_packets_bytes:
            if random.random() >= loss_rate:
                surviving.append(raw)
        random.shuffle(surviving)

        # 5. Receiver side: deserialize + decode

        # Process session start
        sess_pkt = deserialize_packet(session_pkt_bytes)
        assert sess_pkt is not None
        assert sess_pkt.header.packet_type == PACKET_TYPE_SESSION_START

        # Process metadata
        meta_pkt = deserialize_packet(meta_pkt_bytes)
        assert meta_pkt is not None
        assert meta_pkt.header.packet_type == PACKET_TYPE_FILE_METADATA

        parsed_meta = parse_file_metadata_payload(meta_pkt.payload, meta_pkt.header.session_id)
        assert parsed_meta is not None
        assert parsed_meta.file_name == "test_file.bin"

        # Set up decoder
        decoder = FountainDecoder(
            K=parsed_meta.total_source_blocks,
            block_size=parsed_meta.block_size,
            session_id=parsed_meta.session_id,
        )

        # Feed data packets
        for raw in surviving:
            pkt = deserialize_packet(raw)
            if pkt is None:
                continue
            if pkt.header.packet_type != PACKET_TYPE_DATA:
                continue

            sid = pkt.header.symbol_id
            degree, block_indices = symbol_plan(parsed_meta.session_id, sid, K)

            symbol = EncodedSymbol(
                symbol_id=sid,
                degree=degree,
                block_indices=block_indices,
                data=pkt.payload,
            )
            decoder.add_symbol(symbol)
            if decoder.is_complete():
                break

        # 6. Reconstruct
        assert decoder.is_complete(), (
            f"Decoding incomplete: {decoder.recovered_count()}/{K} blocks, "
            f"received {len(surviving)} of {len(data_packets_bytes)} packets"
        )

        recovered_blocks = decoder.reconstruct()
        assert recovered_blocks is not None

        recovered_data = b"".join(recovered_blocks)[:file_size]
        recovered_hash = compute_sha256(recovered_data)

        # 7. Verify
        assert recovered_hash == original_hash, (
            f"SHA-256 mismatch!\n"
            f"  Original: {original_hash}\n"
            f"  Received: {recovered_hash}"
        )

        return True

    def test_small_file_no_loss(self):
        assert self._run_e2e(file_size=500, block_size=64, loss_rate=0.0, overhead=5.0)

    def test_small_file_10_percent_loss(self):
        assert self._run_e2e(file_size=1000, block_size=64, loss_rate=0.10, overhead=4.0)

    def test_medium_file_20_percent_loss(self):
        assert self._run_e2e(file_size=5000, block_size=128, loss_rate=0.20, overhead=3.5)

    def test_large_file_10_percent_loss(self):
        assert self._run_e2e(file_size=25000, block_size=256, loss_rate=0.10, overhead=2.5)

    def test_file_not_block_aligned(self):
        """File size is not a multiple of block size — last block is zero-padded."""
        assert self._run_e2e(file_size=999, block_size=128, loss_rate=0.05, overhead=2.5)

    def test_various_file_sizes(self):
        for size in [1, 100, 255, 256, 257, 1024, 4096]:
            assert self._run_e2e(
                file_size=size, block_size=64, loss_rate=0.05, overhead=5.0
            ), f"Failed for file_size={size}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
