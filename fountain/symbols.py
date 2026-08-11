"""
PhotonDrop — Fountain Symbols & Mathematics

Implements Mulberry32 PRNG, degree sampler, seed-to-chunk index mapping,
and XOR symbol generation matching lightspeed-share-main codec.ts.
"""

from __future__ import annotations

from typing import List


def mulberry32(seed: int):
    """Deterministic PRNG matching lightspeed-share-main codec.ts mulberry32.

    Returns a zero-argument function that outputs a float in range [0, 1).
    """
    a = seed & 0xFFFFFFFF

    def rand() -> float:
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = a
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    return rand


def pick_degree(rand_fn, chunks: int) -> int:
    """Robust-soliton-ish degree distribution matching lightspeed-share-main."""
    if chunks <= 1:
        return 1
    r = rand_fn()
    if r < 0.06:
        return 1
    cumulative = 0.06
    for d in range(2, min(chunks, 40) + 1):
        cumulative += 0.94 / (d * (d - 1))
        if r < cumulative:
            return d
    return 2


def chunk_indices_for_seed(seed: int, chunks: int) -> List[int]:
    """Return list of chunk indices XOR-ed into symbol identified by `seed`.

    Matches lightspeed-share-main chunkIndicesForSeed function:
      - Systematic prefix when seed < chunks: returns [seed]
      - Random selection via mulberry32 PRNG when seed >= chunks
    """
    if seed < chunks:
        return [seed]

    rand_fn = mulberry32((seed + 0x9E3779B9) & 0xFFFFFFFF)
    degree = pick_degree(rand_fn, chunks)
    picked = {}
    guard = 0
    while len(picked) < degree and guard < degree * 32:
        guard += 1
        idx = int(rand_fn() * chunks) % chunks
        picked[idx] = True

    return list(picked.keys())


def xor_bytes(target: bytearray, source: bytes) -> None:
    """XOR source byte array into target bytearray in-place."""
    for i in range(min(len(target), len(source))):
        target[i] ^= source[i]


def xor_blocks(blocks: List[bytes]) -> bytes:
    """XOR a list of equal-length bytes objects together."""
    if not blocks:
        return b""
    result = bytearray(blocks[0])
    for b in blocks[1:]:
        xor_bytes(result, b)
    return bytes(result)


def symbol_plan(
    session_id: bytes,
    symbol_id: int,
    total_blocks: int,
    sampler=None,
) -> tuple[int, List[int]]:
    """Legacy helper for backward compatibility: return (degree, block_indices)."""
    indices = chunk_indices_for_seed(symbol_id, total_blocks)
    return len(indices), indices


def derive_seed(session_id: bytes, symbol_id: int) -> int:
    """Legacy helper: return symbol_id as uint32 seed."""
    return symbol_id & 0xFFFFFFFF


def select_blocks(seed: int, degree: int, total_blocks: int) -> List[int]:
    """Legacy helper for backward compatibility."""
    return chunk_indices_for_seed(seed, total_blocks)
