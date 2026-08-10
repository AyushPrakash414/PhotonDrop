"""
PhotonDrop — Checksum Utilities

Fast CRC32 per-packet integrity checking.
"""

import zlib


def compute_crc32(data: bytes) -> int:
    """Compute a CRC32 checksum for the given data.

    Returns an unsigned 32-bit integer.
    """
    return zlib.crc32(data) & 0xFFFFFFFF


def verify_crc32(data: bytes, expected: int) -> bool:
    """Verify that the CRC32 of *data* matches *expected*."""
    return compute_crc32(data) == (expected & 0xFFFFFFFF)
