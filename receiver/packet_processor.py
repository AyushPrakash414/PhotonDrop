"""
PhotonDrop — Packet Processor

Validates decoded packets: checks magic, version, checksum, session ID,
and filters duplicate symbol IDs.
"""

from __future__ import annotations

import logging
from typing import Optional, Set

from shared.constants import (
    MAGIC,
    PACKET_TYPE_DATA,
    PACKET_TYPE_FILE_METADATA,
    PACKET_TYPE_SESSION_START,
    PROTOCOL_VERSION,
)
from shared.models import Packet, TransferStats
from shared.serialization import deserialize_packet

logger = logging.getLogger(__name__)


class PacketProcessor:
    """Validates and filters incoming decoded packets.

    Responsibilities:
      - Magic / version check (handled by deserialize_packet)
      - Session ID filtering
      - Duplicate symbol detection
      - Statistics tracking
    """

    def __init__(self):
        self._current_session: Optional[bytes] = None
        self._received_ids: Set[int] = set()
        self.stats = TransferStats()

    def set_session(self, session_id: bytes) -> None:
        """Lock the processor to a specific session.

        Packets from other sessions will be rejected.
        """
        self._current_session = session_id
        self._received_ids.clear()
        logger.info("Session locked: %s…", session_id.hex()[:8])

    def process_raw(self, data: bytes) -> Optional[Packet]:
        """Deserialize and validate raw packet bytes.

        Returns a validated Packet or None if the packet should be
        discarded (invalid, wrong session, or duplicate).
        """
        self.stats.total_frames += 1

        packet = deserialize_packet(data)
        if packet is None:
            self.stats.invalid_frames += 1
            return None

        # Session filtering
        if self._current_session is not None:
            if packet.header.packet_type not in (PACKET_TYPE_SESSION_START,):
                if packet.header.session_id != self._current_session:
                    logger.debug("Rejected packet from different session")
                    self.stats.invalid_frames += 1
                    return None

        # Duplicate detection for DATA packets
        if packet.header.packet_type == PACKET_TYPE_DATA:
            sid = packet.header.symbol_id
            if sid in self._received_ids:
                self.stats.duplicate_frames += 1
                return None
            self._received_ids.add(sid)
            self.stats.unique_symbols += 1
            self.stats.new_frames += 1
            self.stats.payload_bytes += packet.header.payload_length
        else:
            self.stats.new_frames += 1

        return packet

    def reset(self) -> None:
        """Reset the processor for a new transfer."""
        self._current_session = None
        self._received_ids.clear()
        self.stats = TransferStats()
