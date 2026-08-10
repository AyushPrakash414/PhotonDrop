"""
PhotonDrop — File Hashing Utilities

SHA-256 computation for full-file integrity verification.
"""

import hashlib
from pathlib import Path
from typing import Union


HASH_ALGO = "sha256"
_BUF_SIZE = 65536  # 64 KB read buffer


def compute_sha256(data: bytes) -> str:
    """Compute the SHA-256 hex digest of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_sha256_file(file_path: Union[str, Path]) -> str:
    """Compute the SHA-256 hex digest of a file on disk.

    Reads the file in 64 KB chunks to handle large files without
    loading the entire file into memory.
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(_BUF_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
