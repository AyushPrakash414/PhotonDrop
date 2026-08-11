"""
PhotonDrop — Packet Processor

Validates decoded optical frames: checks 24B magic, version, file ID,
and filters duplicate symbol seeds matching lightspeed-share-main.
"""

from __future__ import annotations

import logging
from typing import Optional, Set

from shared.constants import FRAME_DATA, FRAME_MANIFEST
from shared.models import Packet, TransferStats
from shared.serialization import deserialize_packet

logger = logging.getLogger(__name__)


class PacketProcessor:
    """Validates and filters incoming decoded optical frames."""

    def __init__(self):
        self._current_file_id: Optional[int] = None
        self._received_seeds: Set[int] = set()
        self.stats = TransferStats()

    def set_session(self, file_id: int) -> None:
        """Lock the processor to a specific file ID."""
        self._current_file_id = file_id & 0xFFFFFFFF
        self._received_seeds.clear()

    def process_raw(self, data: bytes | str) -> Optional[Packet]:
        """Deserialize and validate raw frame data or Base64 string."""
        self.stats.total_frames += 1

        packet = deserialize_packet(data)
        if packet is None:
            self.stats.invalid_frames += 1
            return None

        # File ID filtering
        if self._current_file_id is not None:
            if packet.header.packet_type != FRAME_MANIFEST:
                if packet.header.file_id != self._current_file_id:
                    self.stats.invalid_frames += 1
                    return None

        # Duplicate detection for DATA packets
        if packet.header.packet_type == FRAME_DATA:
            seed = packet.header.seed
            if seed in self._received_seeds:
                self.stats.duplicate_frames += 1
                return None
            self._received_seeds.add(seed)
            self.stats.unique_symbols += 1
            self.stats.new_frames += 1
            self.stats.payload_bytes += len(packet.payload)
        else:
            self.stats.new_frames += 1

        return packet

    def reset(self) -> None:
        """Reset the processor for a new transfer."""
        self._current_file_id = None
        self._received_seeds.clear()
        self.stats = TransferStats()
