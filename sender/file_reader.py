"""
PhotonDrop — File Reader

Reads a target file, extracts metadata, computes SHA-256, and splits
the contents into fixed-size source blocks for fountain encoding.
"""

from __future__ import annotations

import math
import mimetypes
import os
import re
from pathlib import Path
from typing import List, Tuple, Union

from shared.constants import DEFAULT_BLOCK_SIZE, MAX_FILE_SIZE, MAX_FILENAME_LEN
from shared.hashing import compute_sha256, compute_sha256_file
from shared.models import FileMetadata


def sanitize_filename(name: str) -> str:
    """Sanitize a filename to prevent path-traversal attacks.

    Strips directory components, removes dangerous characters, and
    truncates to MAX_FILENAME_LEN.
    """
    # Take only the basename (strip any directory path)
    name = os.path.basename(name)
    # Remove path-traversal sequences
    name = name.replace("..", "").replace("/", "").replace("\\", "")
    # Remove control characters and other unsafe chars
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "_", name)
    # Ensure non-empty
    if not name or name.strip(". ") == "":
        name = "received_file"
    return name[:MAX_FILENAME_LEN]


def read_file(file_path: Union[str, Path]) -> bytes:
    """Read a file entirely into memory as raw bytes.

    Raises ValueError if the file exceeds MAX_FILE_SIZE.
    """
    file_path = Path(file_path)
    size = file_path.stat().st_size
    if size > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large: {size:,} bytes exceeds limit of {MAX_FILE_SIZE:,} bytes"
        )
    with open(file_path, "rb") as f:
        return f.read()


def split_into_blocks(data: bytes, block_size: int = DEFAULT_BLOCK_SIZE) -> List[bytes]:
    """Split raw bytes into fixed-size source blocks.

    The last block is zero-padded to ``block_size`` so that all blocks
    are the same length (required by the XOR-based fountain encoder).
    """
    blocks: List[bytes] = []
    for offset in range(0, len(data), block_size):
        block = data[offset : offset + block_size]
        if len(block) < block_size:
            block = block + b"\x00" * (block_size - len(block))
        blocks.append(block)
    return blocks


def prepare_file(
    file_path: Union[str, Path],
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> Tuple[FileMetadata, List[bytes], bytes]:
    """Full file-preparation pipeline.

    Returns:
        metadata:  FileMetadata dataclass
        blocks:    list of equal-length source blocks
        raw_data:  the original file bytes (needed for final SHA-256 comparison)
    """
    file_path = Path(file_path)
    raw_data = read_file(file_path)

    file_name = sanitize_filename(file_path.name)
    file_size = len(raw_data)
    mime_type, _ = mimetypes.guess_type(file_path.name)
    if mime_type is None:
        mime_type = "application/octet-stream"

    sha256 = compute_sha256(raw_data)
    blocks = split_into_blocks(raw_data, block_size)
    total_source_blocks = len(blocks)

    session_id = FileMetadata.generate_session_id()
    file_id = FileMetadata.generate_file_id()

    metadata = FileMetadata(
        file_id=file_id,
        session_id=session_id,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type,
        block_size=block_size,
        total_source_blocks=total_source_blocks,
        sha256=sha256,
    )

    return metadata, blocks, raw_data
