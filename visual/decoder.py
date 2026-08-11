"""
PhotonDrop — Visual Decoder

Decodes visual frames (QR codes) back into Base64 packet strings or binary data.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from shared.models import Packet
from shared.serialization import deserialize_packet
from visual.encoder import QRTransport, VisualTransport
from visual.preprocessing import adaptive_threshold, enhance_contrast, to_grayscale

logger = logging.getLogger(__name__)


def decode_frame_to_bytes(
    frame: np.ndarray,
    transport: Optional[VisualTransport] = None,
) -> Optional[bytes]:
    """Decode a camera frame into optical frame bytes using multi-pass detection."""
    if transport is None:
        transport = QRTransport()

    # Pass 1: Raw frame directly
    res = transport.decode(frame)
    if res is not None:
        return res

    # Pass 2: Grayscale
    gray = to_grayscale(frame)
    res = transport.decode(gray)
    if res is not None:
        return res

    # Pass 3: CLAHE contrast enhancement
    try:
        enhanced = enhance_contrast(gray)
        res = transport.decode(enhanced)
        if res is not None:
            return res
    except Exception:
        pass

    # Pass 4: Adaptive thresholding
    try:
        thresh = adaptive_threshold(gray)
        res = transport.decode(thresh)
        if res is not None:
            return res
    except Exception:
        pass

    return None


def decode_frame_to_packet(
    frame: np.ndarray,
    transport: Optional[VisualTransport] = None,
) -> Optional[Packet]:
    """Decode a camera frame all the way into a validated Packet."""
    raw = decode_frame_to_bytes(frame, transport)
    if raw is None:
        return None

    packet = deserialize_packet(raw)
    if packet is None:
        logger.debug("Frame decoded but packet deserialization failed")
        return None

    return packet
