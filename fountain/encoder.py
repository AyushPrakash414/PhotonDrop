"""
PhotonDrop — Fountain Encoder (LT Code)

Generates an endless stream of fountain-coded symbols from K source blocks
using Mulberry32 PRNG matching lightspeed-share-main codec.ts.
"""

from __future__ import annotations

from typing import Iterator, List

from fountain.symbols import chunk_indices_for_seed, xor_bytes
from shared.models import EncodedSymbol


def encode_symbol_payload(chunks: List[bytes], seed: int) -> bytes:
    """Encode a single fountain symbol payload from source chunks and seed.

    Matches lightspeed-share-main encodeSymbol function exactly.
    """
    indices = chunk_indices_for_seed(seed, len(chunks))
    symbol = bytearray(len(chunks[0]))
    for idx in indices:
        xor_bytes(symbol, chunks[idx])
    return bytes(symbol)


class FountainEncoder:
    """LT Fountain Encoder.

    Given K source blocks, produces an endless stream of encoded symbols.
    Matches lightspeed-share-main systematic prefix and PRNG distribution.
    """

    def __init__(
        self,
        blocks: List[bytes],
        session_id: bytes = b"",
    ):
        if not blocks:
            raise ValueError("Must supply at least one source block")
        self.blocks = blocks
        self.K = len(blocks)
        self.session_id = session_id
        self._next_id = 0

    def generate_symbol(self) -> EncodedSymbol:
        """Generate the next encoded symbol."""
        symbol_id = self._next_id
        self._next_id += 1

        indices = chunk_indices_for_seed(symbol_id, self.K)
        data = encode_symbol_payload(self.blocks, symbol_id)

        return EncodedSymbol(
            symbol_id=symbol_id,
            degree=len(indices),
            block_indices=indices,
            data=data,
        )

    def generate(self, count: int | None = None) -> Iterator[EncodedSymbol]:
        """Generate encoded symbols endlessly or up to count."""
        produced = 0
        while count is None or produced < count:
            yield self.generate_symbol()
            produced += 1

    @property
    def symbols_generated(self) -> int:
        """Number of symbols generated so far."""
        return self._next_id
