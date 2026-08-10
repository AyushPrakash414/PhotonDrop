"""
PhotonDrop — Visual Data Region Detector

Locates the QR code / data region within a raw camera frame
using contour analysis.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def find_data_region(
    frame: np.ndarray,
    min_area_ratio: float = 0.02,
    max_area_ratio: float = 0.95,
) -> Optional[np.ndarray]:
    """Attempt to find a rectangular data region (QR code area) in the frame.

    Uses adaptive thresholding and contour detection to locate the
    largest approximately-rectangular region.

    Parameters
    ----------
    frame : np.ndarray
        Grayscale preprocessed camera frame.
    min_area_ratio : float
        Minimum region area as a fraction of the total frame area.
    max_area_ratio : float
        Maximum region area as a fraction of the total frame area.

    Returns
    -------
    np.ndarray or None
        4×2 array of corner points (TL, TR, BR, BL) if found, else None.
    """
    h, w = frame.shape[:2]
    total_area = h * w

    # Binarise
    binary = cv2.adaptiveThreshold(
        frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 10
    )

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    best: Optional[np.ndarray] = None
    best_area = 0.0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area_ratio * total_area or area > max_area_ratio * total_area:
            continue

        # Approximate the contour to a polygon
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

        if len(approx) == 4 and area > best_area:
            best = approx.reshape(4, 2)
            best_area = area

    if best is not None:
        best = _order_points(best)

    return best


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 corner points as: TL, TR, BR, BL."""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    rect[0] = pts[np.argmin(s)]   # TL has smallest sum
    rect[2] = pts[np.argmax(s)]   # BR has largest sum
    rect[1] = pts[np.argmin(d)]   # TR has smallest difference
    rect[3] = pts[np.argmax(d)]   # BL has largest difference
    return rect


def crop_data_region(
    frame: np.ndarray,
    corners: np.ndarray,
    output_size: Tuple[int, int] = (400, 400),
) -> np.ndarray:
    """Crop and perspective-correct the data region from a frame.

    Parameters
    ----------
    frame : np.ndarray
        Original frame (grayscale or BGR).
    corners : np.ndarray
        4×2 corner points from ``find_data_region``.
    output_size : tuple
        (width, height) of the output rectified region.

    Returns
    -------
    np.ndarray
        Rectified data region.
    """
    from visual.preprocessing import warp_perspective
    return warp_perspective(frame, corners, output_size)
