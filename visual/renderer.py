"""
PhotonDrop — Frame Renderer

Formats QR code images for high-visibility on-screen display,
adding margins, background contrast, and optional status overlays.
"""

from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np


def render_frame(
    qr_image: np.ndarray,
    canvas_size: Tuple[int, int] = (800, 800),
    bg_color: int = 255,
    margin: int = 40,
) -> np.ndarray:
    """Place a QR image centred on a white canvas with margins.

    Parameters
    ----------
    qr_image : np.ndarray
        Grayscale QR code image.
    canvas_size : tuple of (width, height)
        Output canvas dimensions in pixels.
    bg_color : int
        Background intensity (0=black, 255=white).
    margin : int
        Minimum margin around the QR code.

    Returns
    -------
    np.ndarray
        Grayscale canvas image.
    """
    cw, ch = canvas_size
    canvas = np.full((ch, cw), bg_color, dtype=np.uint8)

    qh, qw = qr_image.shape[:2]
    # Scale QR to fit within canvas minus margins
    max_w = cw - 2 * margin
    max_h = ch - 2 * margin
    scale = min(max_w / qw, max_h / qh, 1.0)

    if scale < 1.0:
        new_w = int(qw * scale)
        new_h = int(qh * scale)
        qr_resized = cv2.resize(
            qr_image, (new_w, new_h), interpolation=cv2.INTER_NEAREST
        )
    else:
        qr_resized = qr_image
        new_w, new_h = qw, qh

    # Centre on canvas
    x_offset = (cw - new_w) // 2
    y_offset = (ch - new_h) // 2
    canvas[y_offset : y_offset + new_h, x_offset : x_offset + new_w] = qr_resized

    return canvas


def render_frame_with_status(
    qr_image: np.ndarray,
    status_text: str = "",
    canvas_size: Tuple[int, int] = (800, 860),
    bg_color: int = 255,
    margin: int = 40,
) -> np.ndarray:
    """Render a QR frame with an optional status bar at the bottom.

    Parameters
    ----------
    qr_image : np.ndarray
        Grayscale QR code image.
    status_text : str
        Text to display below the QR code.
    canvas_size : tuple of (width, height)
        Total output dimensions (includes status bar).
    bg_color : int
        Background intensity.
    margin : int
        Margin around the QR code.

    Returns
    -------
    np.ndarray
        BGR canvas image (3-channel) for display.
    """
    cw, ch = canvas_size
    status_height = 60
    qr_canvas_h = ch - status_height

    # Render QR portion
    qr_canvas = render_frame(qr_image, (cw, qr_canvas_h), bg_color, margin)

    # Convert to BGR
    canvas = cv2.cvtColor(qr_canvas, cv2.COLOR_GRAY2BGR)

    # Add status bar
    status_bar = np.full((status_height, cw, 3), (40, 40, 40), dtype=np.uint8)
    if status_text:
        cv2.putText(
            status_bar,
            status_text,
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
    canvas = np.vstack([canvas, status_bar])

    return canvas
