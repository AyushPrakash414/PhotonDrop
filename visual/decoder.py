"""
PhotonDrop — Visual Decoder

Decodes visual frames (QR codes) back into binary packet data and
then deserializes them into Packet objects.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from shared.models import Packet
from shared.serialization import deserialize_packet
from visual.encoder import QRTransport, VisualTransport

logger = logging.getLogger(__name__)


def decode_frame_to_bytes(
    frame: np.ndarray,
    transport: Optional[VisualTransport] = None,
) -> Optional[bytes]:
    """Decode a camera frame into raw binary packet bytes.

    Returns None if no valid visual data is detected.
    """
    if transport is None:
        transport = QRTransport()
    return transport.decode(frame)


def decode_frame_to_packet(
    frame: np.ndarray,
    transport: Optional[VisualTransport] = None,
) -> Optional[Packet]:
    """Decode a camera frame all the way into a validated Packet.

    Returns None if the frame cannot be decoded or the packet
    fails validation (bad magic, checksum, etc.).
    """
    raw = decode_frame_to_bytes(frame, transport)
    if raw is None:
        return None

    packet = deserialize_packet(raw)
    if packet is None:
        logger.debug("Frame decoded but packet deserialization failed")
        return None

    return packet
