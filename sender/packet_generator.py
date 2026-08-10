"""
PhotonDrop — Packet Generator

Wraps fountain-encoded symbols and file metadata into serialized
PhotonDrop wire packets ready for visual encoding.
"""

from __future__ import annotations

import logging
from typing import Iterator, List

from fountain.encoder import FountainEncoder
from shared.models import EncodedSymbol, FileMetadata, Packet
from shared.protocol import (
    build_data_packet,
    build_file_metadata_packet,
    build_session_start_packet,
    build_session_end_packet,
)
from shared.serialization import serialize_packet

logger = logging.getLogger(__name__)


class PacketGenerator:
    """Generates a stream of serialized wire packets for a file transfer.

    Produces packets in order:
      1. SESSION_START
      2. FILE_METADATA
      3. DATA symbols (unlimited fountain stream)

    The caller drives the loop and decides when to stop generating
    DATA packets (e.g. after receiver confirms completion, or after
    a configured symbol count / time limit).
    """

    def __init__(self, metadata: FileMetadata, blocks: List[bytes]):
        self.metadata = metadata
        self.blocks = blocks
        self.encoder = FountainEncoder(
            blocks=blocks,
            session_id=metadata.session_id,
        )

    def session_start_bytes(self) -> bytes:
        """Serialize the SESSION_START packet."""
        pkt = build_session_start_packet(self.metadata.session_id)
        return serialize_packet(pkt)

    def metadata_bytes(self) -> bytes:
        """Serialize the FILE_METADATA packet."""
        pkt = build_file_metadata_packet(self.metadata)
        return serialize_packet(pkt)

    def next_data_bytes(self) -> bytes:
        """Generate and serialize the next DATA packet."""
        symbol = self.encoder.generate_symbol()
        pkt = build_data_packet(
            session_id=self.metadata.session_id,
            file_id=self.metadata.file_id,
            symbol=symbol,
            source_block_count=self.metadata.total_source_blocks,
        )
        return serialize_packet(pkt)

    def data_stream(self, count: int | None = None) -> Iterator[bytes]:
        """Generate a stream of serialized DATA packets.

        Parameters
        ----------
        count : int or None
            Number of data packets.  None = unlimited.
        """
        produced = 0
        while count is None or produced < count:
            yield self.next_data_bytes()
            produced += 1

    @property
    def symbols_generated(self) -> int:
        return self.encoder.symbols_generated
