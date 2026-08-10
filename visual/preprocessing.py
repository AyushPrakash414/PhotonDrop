"""
PhotonDrop — Image Preprocessing

OpenCV-based camera frame preprocessing pipeline:
  - Resize / downscale
  - Grayscale conversion
  - Contrast enhancement (CLAHE)
  - Gaussian noise reduction
  - Adaptive thresholding
"""

from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np


def resize_frame(
    frame: np.ndarray,
    max_dim: int = 1024,
) -> np.ndarray:
    """Downscale a frame so its longest dimension is at most *max_dim*.

    Preserves aspect ratio.  Returns the frame unchanged if already
    small enough.
    """
    h, w = frame.shape[:2]
    if max(h, w) <= max_dim:
        return frame
    scale = max_dim / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)


def to_grayscale(frame: np.ndarray) -> np.ndarray:
    """Convert a BGR frame to grayscale.  No-op if already single-channel."""
    if len(frame.shape) == 2:
        return frame
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def enhance_contrast(gray: np.ndarray, clip_limit: float = 2.0, tile: int = 8) -> np.ndarray:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalisation)."""
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile, tile))
    return clahe.apply(gray)


def reduce_noise(gray: np.ndarray, ksize: int = 3) -> np.ndarray:
    """Apply Gaussian blur for noise reduction."""
    return cv2.GaussianBlur(gray, (ksize, ksize), 0)


def adaptive_threshold(gray: np.ndarray, block_size: int = 51, C: int = 10) -> np.ndarray:
    """Apply adaptive thresholding for binary segmentation."""
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, C
    )


def preprocess_frame(
    frame: np.ndarray,
    max_dim: int = 1024,
    denoise: bool = True,
    enhance: bool = True,
) -> np.ndarray:
    """Full preprocessing pipeline: resize → grayscale → enhance → denoise.

    Returns a grayscale uint8 image ready for QR detection.
    """
    processed = resize_frame(frame, max_dim)
    processed = to_grayscale(processed)
    if enhance:
        processed = enhance_contrast(processed)
    if denoise:
        processed = reduce_noise(processed)
    return processed


def warp_perspective(
    frame: np.ndarray,
    src_points: np.ndarray,
    dst_size: Tuple[int, int] = (400, 400),
) -> np.ndarray:
    """Apply a perspective warp to rectify a skewed data region.

    Parameters
    ----------
    frame : np.ndarray
        Input image.
    src_points : np.ndarray
        4×2 array of source corner points (TL, TR, BR, BL).
    dst_size : tuple
        (width, height) of the output rectified image.

    Returns
    -------
    np.ndarray
        Rectified image.
    """
    w, h = dst_size
    dst_points = np.array(
        [[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32
    )
    M = cv2.getPerspectiveTransform(src_points.astype(np.float32), dst_points)
    return cv2.warpPerspective(frame, M, (w, h))
