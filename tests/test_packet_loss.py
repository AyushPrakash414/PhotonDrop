"""
PhotonDrop — Packet Loss Simulation Tests

Simulates harsh optical loss conditions (5% to 50% frame drop) to
assert robust fountain recovery.
"""

import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from fountain.decoder import FountainDecoder
from fountain.encoder import FountainEncoder


class TestPacketLoss:
    """Test fountain coding under simulated packet loss."""

    def _run_with_loss(self, K: int, block_size: int, loss_rate: float, overhead: float = 3.0):
        """Encode, drop symbols at *loss_rate*, and attempt decoding."""
        session_id = os.urandom(16)
        blocks = [os.urandom(block_size) for _ in range(K)]

        encoder = FountainEncoder(blocks, session_id)
        decoder = FountainDecoder(K, block_size, session_id)

        max_symbols = int(K * overhead)
        received = 0
        dropped = 0

        for symbol in encoder.generate(max_symbols):
            if random.random() < loss_rate:
                dropped += 1
                continue
            decoder.add_symbol(symbol)
            received += 1
            if decoder.is_complete():
                break

        return decoder.is_complete(), decoder.reconstruct(), blocks, received, dropped

    @pytest.mark.parametrize("loss_rate", [0.05, 0.10, 0.20, 0.30])
    def test_loss_recovery(self, loss_rate: float):
        K = 50
        block_size = 128
        # Use higher overhead for higher loss rates
        overhead = 4.0 + loss_rate * 10

        complete, recovered, original, received, dropped = self._run_with_loss(
            K, block_size, loss_rate, overhead
        )
        assert complete, (
            f"Failed at {loss_rate*100:.0f}% loss: "
            f"received {received}, dropped {dropped}"
        )
        assert recovered == original

    def test_50_percent_loss(self):
        """Even 50% loss should succeed with enough overhead."""
        K = 20
        block_size = 64
        complete, recovered, original, received, dropped = self._run_with_loss(
            K, block_size, loss_rate=0.50, overhead=10.0
        )
        assert complete, f"50% loss failed: received {received}, dropped {dropped}"
        assert recovered == original

    def test_zero_loss(self):
        """Baseline: no loss should always work."""
        K = 30
        block_size = 128
        complete, recovered, original, _, _ = self._run_with_loss(
            K, block_size, loss_rate=0.0, overhead=5.0
        )
        assert complete
        assert recovered == original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
