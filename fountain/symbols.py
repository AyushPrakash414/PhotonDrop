"""
PhotonDrop — Fountain Symbols

Dataclass and helpers for LT-coded encoded symbols.
Symbol metadata is kept minimal because the receiver can
deterministically regenerate block selections from the symbol_id.
"""

from __future__ import annotations

import hashlib
import random
from typing import List

from shared.models import EncodedSymbol


def derive_seed(session_id: bytes, symbol_id: int) -> int:
    """Derive a deterministic 32-bit PRNG seed from session + symbol IDs.

    Both sender and receiver compute the same seed so the receiver
    can regenerate the block selection without explicit transmission
    of block indices.
    """
    raw = session_id + symbol_id.to_bytes(4, "big")
    h = hashlib.sha256(raw).digest()
    return int.from_bytes(h[:4], "big")


def select_blocks(
    seed: int, degree: int, K: int
) -> List[int]:
    """Deterministically select *degree* distinct source block indices.

    Uses a seeded PRNG so both sender and receiver arrive at the
    same selection given the same (seed, degree, K).
    """
    rng = random.Random(seed)
    indices = rng.sample(range(K), min(degree, K))
    indices.sort()
    return indices


def xor_blocks(blocks: List[bytes]) -> bytes:
    """XOR a list of equal-length byte blocks together."""
    if not blocks:
        raise ValueError("Cannot XOR an empty list of blocks")
    result = bytearray(blocks[0])
    for blk in blocks[1:]:
        for i in range(len(result)):
            result[i] ^= blk[i]
    return bytes(result)
