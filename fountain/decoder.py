"""
PhotonDrop — Fountain Decoder (LT Code – Belief Propagation)

Recovers K source blocks from a sufficient number of received
encoded symbols using iterative peeling / belief propagation.

Algorithm
---------
1.  Maintain a bipartite graph:
      - left  nodes = unknown source blocks  (K total)
      - right nodes = received encoded symbols

2.  Each encoded symbol has edges to the source blocks it covers
    (determined by ``select_blocks`` with the same seed).

3.  Whenever a degree-1 symbol is found (i.e. it has exactly one
    unresolved neighbour), that source block is immediately
    recovered by XOR'ing the symbol's data.

4.  The recovered block is then XOR'd out of every other symbol
    that references it, potentially reducing their degree to 1
    and triggering a cascade.

5.  Repeat until all K blocks are recovered or no more progress
    can be made.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from fountain.symbols import derive_seed, select_blocks, xor_blocks
from shared.models import EncodedSymbol

logger = logging.getLogger(__name__)


class _PendingSymbol:
    """Internal bookkeeping for a received but not yet fully resolved symbol."""

    __slots__ = ("symbol_id", "data", "unresolved")

    def __init__(self, symbol_id: int, data: bytearray, unresolved: Set[int]):
        self.symbol_id = symbol_id
        self.data = data                # mutable – XOR'd as blocks are recovered
        self.unresolved = unresolved     # set of source block indices still unknown


class FountainDecoder:
    """LT Fountain Decoder using iterative belief propagation.

    Usage::

        decoder = FountainDecoder(K, block_size, session_id)
        for symbol in received_symbols:
            decoder.add_symbol(symbol)
            if decoder.is_complete():
                blocks = decoder.reconstruct()
                break
    """

    def __init__(self, K: int, block_size: int, session_id: bytes):
        """
        Parameters
        ----------
        K : int
            Total number of source blocks.
        block_size : int
            Size of each source block in bytes.
        session_id : bytes
            The 16-byte session identifier (used to derive block selections).
        """
        self.K = K
        self.block_size = block_size
        self.session_id = session_id

        # Recovered source blocks (index → bytes)
        self._recovered: Dict[int, bytes] = {}

        # Pending symbols keyed by symbol_id
        self._pending: Dict[int, _PendingSymbol] = {}

        # Reverse index: source block index → set of pending symbol IDs
        self._block_to_symbols: Dict[int, Set[int]] = {i: set() for i in range(K)}

        # Degree-1 processing queue
        self._ripple: List[int] = []  # symbol IDs with exactly 1 unresolved block

    # ── Public API ─────────────────────────────────────────────────

    def add_symbol(self, symbol: EncodedSymbol) -> None:
        """Feed a received encoded symbol into the decoder.

        The decoder immediately attempts peeling if the symbol's
        effective degree is 1.
        """
        # Determine which source blocks this symbol covers
        seed = derive_seed(self.session_id, symbol.symbol_id)
        block_indices = select_blocks(seed, symbol.degree, self.K)

        # XOR out any already-recovered blocks
        data = bytearray(symbol.data)
        unresolved: Set[int] = set()

        for idx in block_indices:
            if idx in self._recovered:
                # XOR the known block out of this symbol
                recovered = self._recovered[idx]
                for i in range(len(data)):
                    data[i] ^= recovered[i]
            else:
                unresolved.add(idx)

        if not unresolved:
            # All blocks already known — symbol is redundant
            return

        ps = _PendingSymbol(symbol.symbol_id, data, unresolved)
        self._pending[symbol.symbol_id] = ps

        # Register in reverse index
        for idx in unresolved:
            self._block_to_symbols[idx].add(symbol.symbol_id)

        if len(unresolved) == 1:
            self._ripple.append(symbol.symbol_id)

        # Run the peeling cascade
        self._propagate()

    def is_complete(self) -> bool:
        """Return True when all K source blocks have been recovered."""
        return len(self._recovered) == self.K

    def recovered_count(self) -> int:
        """Number of source blocks recovered so far."""
        return len(self._recovered)

    def progress(self) -> float:
        """Recovery progress as a fraction in [0, 1]."""
        return len(self._recovered) / self.K if self.K > 0 else 1.0

    def reconstruct(self) -> Optional[List[bytes]]:
        """Return the list of recovered source blocks in order.

        Returns None if decoding is not yet complete.
        """
        if not self.is_complete():
            return None
        return [self._recovered[i] for i in range(self.K)]

    # ── Internal ───────────────────────────────────────────────────

    def _propagate(self) -> None:
        """Process the ripple: peel degree-1 symbols to recover blocks."""
        while self._ripple:
            sid = self._ripple.pop()
            if sid not in self._pending:
                continue
            ps = self._pending[sid]
            if len(ps.unresolved) != 1:
                continue

            # Recover the single remaining source block
            block_idx = next(iter(ps.unresolved))
            if block_idx in self._recovered:
                # Already recovered via another path
                del self._pending[sid]
                continue

            recovered_block = bytes(ps.data)
            self._recovered[block_idx] = recovered_block
            del self._pending[sid]

            logger.debug("Recovered block %d (%d/%d)", block_idx, len(self._recovered), self.K)

            # XOR the recovered block out of every other pending symbol
            # that references this block
            affected = list(self._block_to_symbols.get(block_idx, []))
            self._block_to_symbols[block_idx] = set()

            for other_sid in affected:
                if other_sid not in self._pending:
                    continue
                other = self._pending[other_sid]
                if block_idx not in other.unresolved:
                    continue

                # XOR out the recovered block
                for i in range(len(other.data)):
                    other.data[i] ^= recovered_block[i]
                other.unresolved.discard(block_idx)

                if not other.unresolved:
                    # Fully resolved — discard
                    del self._pending[other_sid]
                elif len(other.unresolved) == 1:
                    # Became degree-1 → add to ripple
                    self._ripple.append(other_sid)
