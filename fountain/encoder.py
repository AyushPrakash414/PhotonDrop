"""
PhotonDrop — Fountain Encoder (LT Code)

Generates an unlimited stream of encoded symbols from K source blocks
using the Robust Soliton Distribution for degree selection and
deterministic PRNG-based block selection.
"""

from __future__ import annotations

from typing import Iterator, List

from fountain.degree_distribution import DegreeSampler
from fountain.symbols import symbol_plan, xor_blocks
from shared.models import EncodedSymbol


class FountainEncoder:
    """LT Fountain Encoder.

    Given K source blocks, produces an endless stream of encoded symbols.
    Each symbol is the XOR of a randomly chosen subset of source blocks.
    The subset is determined by a PRNG seeded with (session_id, symbol_id)
    so the receiver can recover the same selection without extra metadata.

    Usage::

        encoder = FountainEncoder(blocks, session_id)
        for symbol in encoder.generate():
            send(symbol)
    """

    def __init__(
        self,
        blocks: List[bytes],
        session_id: bytes,
        c: float = 0.1,
        delta: float = 0.5,
    ):
        if not blocks:
            raise ValueError("Must supply at least one source block")
        self.blocks = blocks
        self.K = len(blocks)
        self.session_id = session_id
        self.sampler = DegreeSampler(self.K, c=c, delta=delta)
        self._next_id = 0

    def generate_symbol(self) -> EncodedSymbol:
        """Generate the next encoded symbol."""
        symbol_id = self._next_id
        self._next_id += 1

        degree, block_indices = symbol_plan(
            self.session_id,
            symbol_id,
            self.K,
            self.sampler,
        )

        # XOR selected blocks
        selected = [self.blocks[i] for i in block_indices]
        data = xor_blocks(selected)

        return EncodedSymbol(
            symbol_id=symbol_id,
            degree=degree,
            block_indices=block_indices,
            data=data,
        )

    def generate(self, count: int | None = None) -> Iterator[EncodedSymbol]:
        """Generate encoded symbols.

        Parameters
        ----------
        count : int or None
            Number of symbols to produce.  If ``None``, generates
            symbols indefinitely (the fountain never runs dry).
        """
        produced = 0
        while count is None or produced < count:
            yield self.generate_symbol()
            produced += 1

    @property
    def symbols_generated(self) -> int:
        """Number of symbols generated so far."""
        return self._next_id
