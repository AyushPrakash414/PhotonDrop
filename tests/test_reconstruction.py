"""
PhotonDrop — File Reconstruction Tests

Tests the file_reader module: splitting into blocks and reassembly.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from sender.file_reader import split_into_blocks, sanitize_filename
from shared.hashing import compute_sha256


class TestBlockSplitting:
    def test_exact_multiple(self):
        data = b"A" * 256
        blocks = split_into_blocks(data, 64)
        assert len(blocks) == 4
        assert all(len(b) == 64 for b in blocks)
        reassembled = b"".join(blocks)
        assert reassembled == data

    def test_non_aligned(self):
        data = b"B" * 100
        blocks = split_into_blocks(data, 64)
        assert len(blocks) == 2
        assert len(blocks[0]) == 64
        assert len(blocks[1]) == 64  # zero-padded
        reassembled = b"".join(blocks)[:100]
        assert reassembled == data

    def test_single_byte(self):
        data = b"\xff"
        blocks = split_into_blocks(data, 64)
        assert len(blocks) == 1
        assert len(blocks[0]) == 64
        assert blocks[0][0] == 0xFF
        assert blocks[0][1:] == b"\x00" * 63

    def test_empty(self):
        blocks = split_into_blocks(b"", 64)
        assert len(blocks) == 0

    def test_reconstruction_preserves_hash(self):
        data = os.urandom(1000)
        block_size = 128
        original_hash = compute_sha256(data)
        blocks = split_into_blocks(data, block_size)
        reassembled = b"".join(blocks)[:len(data)]
        assert compute_sha256(reassembled) == original_hash


class TestFilenameSanitization:
    def test_path_traversal(self):
        assert ".." not in sanitize_filename("../../malicious.exe")

    def test_strips_directory(self):
        result = sanitize_filename("/etc/passwd")
        assert "/" not in result
        assert "\\" not in result

    def test_windows_path(self):
        result = sanitize_filename("C:\\Users\\evil\\file.txt")
        assert "\\" not in result
        assert result == "file.txt"

    def test_empty_becomes_default(self):
        result = sanitize_filename("")
        assert result == "received_file"

    def test_dots_only(self):
        result = sanitize_filename("...")
        assert result == "received_file"

    def test_normal_filename_unchanged(self):
        assert sanitize_filename("photo.jpg") == "photo.jpg"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
