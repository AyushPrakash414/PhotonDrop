"""
PhotonDrop — Fountain Decoder (LT Code – Incremental Peeling)

Recovers K source blocks from a sufficient number of received
encoded symbols using incremental peeling matching lightspeed-share-main codec.ts.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from fountain.symbols import chunk_indices_for_seed, xor_bytes
from shared.models import EncodedSymbol

logger = logging.getLogger(__name__)


class FountainDecoder:
    """LT Fountain Peeling Decoder matching lightspeed-share-main codec.ts."""

    def __init__(self, K: int, block_size: int, session_id: bytes = b"", size: int = 0):
        self.chunks = K
        self.chunk_size = block_size
        self.size = size or (K * block_size)
        self.K = K
        self.block_size = block_size

        self.solved: Dict[int, bytearray] = {}
        self.equations: List[Dict[str, Any]] = []
        self.seen_seeds: Set[int] = set()

    @property
    def solved_count(self) -> int:
        return len(self.solved)

    @property
    def complete(self) -> bool:
        return len(self.solved) >= self.chunks

    def is_complete(self) -> bool:
        return self.complete

    def recovered_count(self) -> int:
        return len(self.solved)

    def progress(self) -> float:
        return len(self.solved) / self.chunks if self.chunks > 0 else 1.0

    def has_seed(self, seed: int) -> bool:
        return seed in self.seen_seeds

    def add_symbol_raw(self, seed: int, payload: bytes) -> bool:
        """Add a raw seed & payload symbol to the decoder.

        Returns True if the symbol carried new information.
        """
        if seed in self.seen_seeds or self.complete:
            return False
        self.seen_seeds.add(seed)

        indices = set(chunk_indices_for_seed(seed, self.chunks))
        data = bytearray(payload)

        self._reduce(indices, data)
        if not indices:
            return False

        self.equations.append({"indices": indices, "data": data})
        self._peel()
        return True

    def add_symbol(self, symbol: EncodedSymbol | int, payload: bytes | None = None) -> None:
        """Feed a received symbol into the decoder."""
        if isinstance(symbol, EncodedSymbol):
            self.add_symbol_raw(symbol.symbol_id, symbol.data)
        elif payload is not None:
            self.add_symbol_raw(symbol, payload)

    def _reduce(self, indices: Set[int], data: bytearray) -> None:
        """XOR known solved chunks out of data and remove solved indices."""
        for idx in list(indices):
            if idx in self.solved:
                xor_bytes(data, self.solved[idx])
                indices.remove(idx)

    def _peel(self) -> None:
        """Iterative peeling algorithm matching codec.ts."""
        progressed = True
        while progressed:
            progressed = False
            for i in range(len(self.equations) - 1, -1, -1):
                eq = self.equations[i]
                self._reduce(eq["indices"], eq["data"])
                if not eq["indices"]:
                    self.equations.pop(i)
                    continue
                if len(eq["indices"]) == 1:
                    idx = next(iter(eq["indices"]))
                    self.solved[idx] = eq["data"]
                    self.equations.pop(i)
                    progressed = True

    def assemble(self) -> Optional[bytes]:
        """Assemble recovered blocks into final byte payload, stripped to size."""
        if not self.complete:
            return None
        out = bytearray(self.chunks * self.chunk_size)
        for i in range(self.chunks):
            chunk = self.solved.get(i)
            if chunk is None:
                return None
            out[i * self.chunk_size : (i + 1) * self.chunk_size] = chunk

        return bytes(out[: self.size])

    def reconstruct(self) -> Optional[List[bytes]]:
        """Return list of recovered blocks in order."""
        if not self.complete:
            return None
        return [bytes(self.solved[i]) for i in range(self.chunks)]
