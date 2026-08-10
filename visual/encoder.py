"""
PhotonDrop — Visual Encoder

Abstract VisualTransport base class and QRTransport implementation
that converts binary packets into renderable QR code images.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

try:
    import qrcode
    from qrcode.constants import (
        ERROR_CORRECT_H,
        ERROR_CORRECT_L,
        ERROR_CORRECT_M,
        ERROR_CORRECT_Q,
    )
except ImportError:
    qrcode = None  # type: ignore

from shared.serialization import serialize_packet
from shared.models import Packet

_EC_MAP = {
    "L": ERROR_CORRECT_L if qrcode else 0,
    "M": ERROR_CORRECT_M if qrcode else 1,
    "Q": ERROR_CORRECT_Q if qrcode else 2,
    "H": ERROR_CORRECT_H if qrcode else 3,
}


class VisualTransport(ABC):
    """Abstract base class for visual encoding/decoding transport."""

    @abstractmethod
    def encode(self, packet_bytes: bytes) -> np.ndarray:
        """Encode binary packet data into a visual image (numpy array, BGR/grayscale)."""
        ...

    @abstractmethod
    def decode(self, frame: np.ndarray) -> Optional[bytes]:
        """Decode a visual image back into binary packet data.

        Returns None if the frame cannot be decoded.
        """
        ...


class QRTransport(VisualTransport):
    """QR-code based visual transport.

    Encodes binary packet data into QR code images and decodes
    QR codes from camera frames.
    """

    def __init__(
        self,
        error_correction: str = "M",
        box_size: int = 10,
        border: int = 4,
    ):
        if qrcode is None:
            raise ImportError("qrcode package is required: pip install qrcode[pil]")

        self.error_correction = _EC_MAP.get(error_correction.upper(), ERROR_CORRECT_M)
        self.box_size = box_size
        self.border = border

    def encode(self, packet_bytes: bytes) -> np.ndarray:
        """Encode binary data into a QR code image as a numpy array (grayscale)."""
        qr = qrcode.QRCode(
            version=None,  # auto-select
            error_correction=self.error_correction,
            box_size=self.box_size,
            border=self.border,
        )
        qr.add_data(packet_bytes)
        qr.make(fit=True)

        # Generate PIL image (mode='1' for black/white)
        pil_img = qr.make_image(fill_color="black", back_color="white")
        pil_img = pil_img.convert("L")  # grayscale

        return np.array(pil_img, dtype=np.uint8)

    def decode(self, frame: np.ndarray) -> Optional[bytes]:
        """Decode a QR code from a camera frame.

        Tries OpenCV's QRCodeDetector first, then falls back to pyzbar.
        Returns None if no QR code is detected.
        """
        result = self._decode_opencv(frame)
        if result is not None:
            return result
        return self._decode_pyzbar(frame)

    def _decode_opencv(self, frame: np.ndarray) -> Optional[bytes]:
        """Attempt QR decode using OpenCV's built-in detector."""
        try:
            import cv2
            detector = cv2.QRCodeDetector()
            retval, decoded_info, points, straight_qrcode = detector.detectAndDecodeMulti(frame)
            if retval and decoded_info:
                for info in decoded_info:
                    if info:
                        # OpenCV returns string; encode back to bytes
                        # For binary data, we use detectAndDecode which returns bytes
                        return info.encode("latin-1") if isinstance(info, str) else info
        except Exception:
            pass
        return None

    def _decode_pyzbar(self, frame: np.ndarray) -> Optional[bytes]:
        """Attempt QR decode using pyzbar as fallback."""
        try:
            from pyzbar.pyzbar import decode as pyzbar_decode
            results = pyzbar_decode(frame)
            if results:
                return results[0].data
        except Exception:
            pass
        return None


def encode_packet_to_image(
    packet: Packet,
    transport: Optional[VisualTransport] = None,
) -> np.ndarray:
    """Convenience: serialize a Packet and encode it to a visual image."""
    if transport is None:
        transport = QRTransport()
    packet_bytes = serialize_packet(packet)
    return transport.encode(packet_bytes)
