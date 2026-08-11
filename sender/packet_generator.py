"""
PhotonDrop — Packet Generator

Wraps fountain-encoded symbols and file metadata into optical frame Base64
payloads matching lightspeed-share-main interleave schedule (1 Manifest : 13 Data frames).
"""

from __future__ import annotations

import logging
from typing import Iterator, List

from fountain.encoder import FountainEncoder, encode_symbol_payload
from shared.models import FileMetadata
from shared.serialization import build_data_frame, build_manifest_frame

logger = logging.getLogger(__name__)


class PacketGenerator:
    """Generates an optical frame stream matching lightspeed-share-main send.tsx.

    Schedule:
      - Frame 0 (index % 14 == 0): Manifest frame (JSON payload)
      - Frames 1..13 (index % 14 != 0): Data frames (Fountain symbol payload with incremental seed)
    """

    def __init__(self, metadata: FileMetadata, blocks: List[bytes]):
        self.metadata = metadata
        self.blocks = blocks
        self.encoder = FountainEncoder(blocks=blocks, session_id=metadata.session_id)
        self.frame_index = 0
        self.seed = 0

    def manifest_dict(self) -> dict:
        return {
            "fileId": self.metadata.file_id,
            "name": self.metadata.file_name,
            "size": self.metadata.file_size,
            "mime": self.metadata.mime_type,
            "digest": self.metadata.sha256,
            "chunks": self.metadata.total_source_blocks,
            "chunkSize": self.metadata.block_size,
        }

    def manifest_bytes(self) -> bytes:
        """Returns Base64 manifest frame string as bytes."""
        return build_manifest_frame(self.metadata.file_id, self.manifest_dict()).encode("ascii")

    def session_start_bytes(self) -> bytes:
        """Alias for manifest_bytes."""
        return self.manifest_bytes()

    def metadata_bytes(self) -> bytes:
        """Alias for manifest_bytes."""
        return self.manifest_bytes()

    def next_frame_str(self) -> str:
        """Generate next optical frame string matching lightspeed-share-main."""
        idx = self.frame_index
        self.frame_index += 1

        if idx % 14 == 0:
            return build_manifest_frame(self.metadata.file_id, self.manifest_dict())
        else:
            current_seed = self.seed
            self.seed += 1
            payload = encode_symbol_payload(self.blocks, current_seed)
            return build_data_frame(
                file_id=self.metadata.file_id,
                chunks=self.metadata.total_source_blocks,
                chunk_size=self.metadata.block_size,
                size=self.metadata.file_size,
                seed=current_seed,
                payload=payload,
            )

    def next_data_bytes(self) -> bytes:
        """Generate next optical frame as bytes."""
        return self.next_frame_str().encode("ascii")

    def data_stream(self, count: int | None = None) -> Iterator[bytes]:
        """Generate a stream of optical frame bytes."""
        produced = 0
        while count is None or produced < count:
            yield self.next_data_bytes()
            produced += 1

    @property
    def symbols_generated(self) -> int:
        return self.seed
