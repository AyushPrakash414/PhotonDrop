"""
PhotonDrop — Visual Transport (QR Encoder & Decoder)

Encodes optical frame Base64 payloads into high-visibility QR code images.
Decodes camera frames back into Base64 strings with multi-stage OpenCV detection.
Matches lightspeed-share-main optical frame rendering.
"""

from __future__ import annotations

import logging
from typing import Optional, Union

import cv2
import numpy as np
import qrcode
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

logger = logging.getLogger(__name__)

_EC_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


class VisualTransport:
    """Abstract base class for visual transport mechanisms."""

    def encode(self, packet_bytes: Union[bytes, str]) -> np.ndarray:
        raise NotImplementedError

    def decode(self, frame: np.ndarray) -> Optional[bytes]:
        raise NotImplementedError


class QRTransport(VisualTransport):
    """QR Code visual transport mechanism.

    Encodes optical frame text/Base64 into a grayscale QR code image array.
    """

    def __init__(
        self,
        error_correction: str = "M",
        box_size: int = 4,
        border: int = 2,
        version: Optional[int] = None,
    ):
        self.error_correction = _EC_MAP.get(error_correction.upper(), ERROR_CORRECT_M)
        self.box_size = box_size
        self.border = border
        self.version = version

    def encode(self, packet_bytes: Union[bytes, str]) -> np.ndarray:
        """Encode optical packet data (Base64 string or bytes) into a QR code numpy array."""
        if isinstance(packet_bytes, bytes):
            try:
                text_str = packet_bytes.decode("ascii")
            except Exception:
                import base64
                text_str = base64.b64encode(packet_bytes).decode("ascii")
        else:
            text_str = str(packet_bytes)

        qr = qrcode.QRCode(
            version=self.version,
            error_correction=self.error_correction,
            box_size=self.box_size,
            border=self.border,
        )
        qr.add_data(text_str)
        qr.make(fit=True)

        pil_img = qr.make_image(fill_color="black", back_color="white")
        pil_img = pil_img.convert("L")  # grayscale uint8

        return np.array(pil_img, dtype=np.uint8)

    def decode(self, frame: np.ndarray) -> Optional[bytes]:
        """Decode a QR code from a camera frame, returning string bytes."""
        raw_str = self._decode_pyzbar(frame)
        if raw_str is None:
            raw_str = self._decode_opencv(frame)

        if raw_str is None:
            return None

        if isinstance(raw_str, str):
            return raw_str.encode("ascii")
        return raw_str

    def _decode_opencv(self, frame: np.ndarray) -> Optional[str]:
        """Attempt QR decode using OpenCV's built-in detector."""
        try:
            detector = cv2.QRCodeDetector()
            
            # Convert to grayscale if 3-channel BGR
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame

            # Pass 1: Direct grayscale decode
            data_str, _, _ = detector.detectAndDecode(gray)
            if data_str:
                return data_str

            # Pass 2: Multi-detect
            retval, decoded_info, _, _ = detector.detectAndDecodeMulti(gray)
            if retval and decoded_info:
                for info in decoded_info:
                    if info:
                        return info

            # Pass 3: Bounding box crop around QR code
            mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
            coords = cv2.findNonZero(mask)
            if coords is not None:
                x, y, w, h = cv2.boundingRect(coords)
                pad = 12
                x0, y0 = max(0, x - pad), max(0, y - pad)
                x1, y1 = min(gray.shape[1], x + w + pad), min(gray.shape[0], y + h + pad)
                cropped = gray[y0:y1, x0:x1]
                data_str, _, _ = detector.detectAndDecode(cropped)
                if data_str:
                    return data_str
        except Exception:
            pass
        return None

    def _decode_pyzbar(self, frame: np.ndarray) -> Optional[str]:
        """Attempt QR decode using pyzbar."""
        try:
            from pyzbar.pyzbar import decode as pyzbar_decode
            results = pyzbar_decode(frame)
            if results:
                d = results[0].data
                return d.decode("utf-8") if isinstance(d, bytes) else str(d)
        except Exception:
            pass
        return None
