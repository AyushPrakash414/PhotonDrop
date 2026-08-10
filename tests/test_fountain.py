"""
PhotonDrop — Fountain Coding Unit Tests

Tests LT fountain encoder/decoder: complete reconstruction under
various conditions including symbol loss, duplicates, and random ordering.
"""

import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from fountain.decoder import FountainDecoder
from fountain.encoder import FountainEncoder
from fountain.degree_distribution import DegreeSampler, robust_soliton_distribution
from fountain.symbols import derive_seed, select_blocks, xor_blocks


class TestDegreeDistribution:
    def test_distribution_sums_to_one(self):
        for K in [5, 10, 50, 100]:
            mu = robust_soliton_distribution(K)
            total = sum(mu[1:])
            assert abs(total - 1.0) < 1e-9, f"K={K}: sum={total}"

    def test_sampler_degrees_in_range(self):
        K = 20
        sampler = DegreeSampler(K)
        rng = random.Random(42)
        for _ in range(1000):
            d = sampler.sample(rng)
            assert 1 <= d <= K


class TestSymbols:
    def test_deterministic_seed(self):
        sid = b"\x01" * 16
        s1 = derive_seed(sid, 0)
        s2 = derive_seed(sid, 0)
        assert s1 == s2

    def test_different_ids_different_seeds(self):
        sid = b"\x02" * 16
        assert derive_seed(sid, 0) != derive_seed(sid, 1)

    def test_block_selection_deterministic(self):
        b1 = select_blocks(12345, 3, 10)
        b2 = select_blocks(12345, 3, 10)
        assert b1 == b2

    def test_xor_blocks(self):
        a = b"\xff\x00\xaa"
        b = b"\x00\xff\x55"
        result = xor_blocks([a, b])
        assert result == b"\xff\xff\xff"

    def test_xor_identity(self):
        a = b"\xab\xcd\xef"
        result = xor_blocks([a, a])
        assert result == b"\x00\x00\x00"


class TestFountainRoundTrip:
    """Test complete encoder → decoder reconstruction."""

    def _run_roundtrip(self, K: int, block_size: int, overhead: float = 5.0):
        """Helper: generate K blocks, encode, decode, verify."""
        session_id = os.urandom(16)
        blocks = [os.urandom(block_size) for _ in range(K)]

        encoder = FountainEncoder(blocks, session_id)
        decoder = FountainDecoder(K, block_size, session_id)

        max_symbols = int(K * overhead)
        for symbol in encoder.generate(max_symbols):
            decoder.add_symbol(symbol)
            if decoder.is_complete():
                break

        assert decoder.is_complete(), (
            f"Failed to decode: recovered {decoder.recovered_count()}/{K} "
            f"after {max_symbols} symbols"
        )
        recovered = decoder.reconstruct()
        assert recovered == blocks

    def test_small_file(self):
        self._run_roundtrip(K=5, block_size=64)

    def test_medium_file(self):
        self._run_roundtrip(K=20, block_size=128)

    def test_large_file(self):
        self._run_roundtrip(K=100, block_size=256, overhead=2.5)

    def test_single_block(self):
        self._run_roundtrip(K=1, block_size=256)

    def test_two_blocks(self):
        self._run_roundtrip(K=2, block_size=128)

    def test_shuffled_symbols(self):
        """Symbols arrive in random order — should still decode."""
        K = 30
        block_size = 128
        session_id = os.urandom(16)
        blocks = [os.urandom(block_size) for _ in range(K)]

        encoder = FountainEncoder(blocks, session_id)
        symbols = list(encoder.generate(int(K * 5.0)))
        random.shuffle(symbols)

        decoder = FountainDecoder(K, block_size, session_id)
        for sym in symbols:
            decoder.add_symbol(sym)
            if decoder.is_complete():
                break

        assert decoder.is_complete()
        assert decoder.reconstruct() == blocks

    def test_duplicate_symbols_ignored(self):
        """Feeding the same symbol multiple times should not break decoding."""
        K = 10
        block_size = 64
        session_id = os.urandom(16)
        blocks = [os.urandom(block_size) for _ in range(K)]

        encoder = FountainEncoder(blocks, session_id)
        symbols = list(encoder.generate(int(K * 4.0)))

        # Duplicate each symbol 3 times
        duplicated = []
        for s in symbols:
            duplicated.extend([s, s, s])

        decoder = FountainDecoder(K, block_size, session_id)
        for sym in duplicated:
            decoder.add_symbol(sym)
            if decoder.is_complete():
                break

        assert decoder.is_complete()
        assert decoder.reconstruct() == blocks


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
