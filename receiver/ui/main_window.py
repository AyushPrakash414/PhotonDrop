"""
PhotonDrop — Receiver Main Window (PySide6)

Desktop UI with live camera preview, transfer progress, real-time
metrics (FPS, goodput, duplicates), and verification status.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from receiver.receiver import Receiver
from shared.models import ReceiverState, TransferStats

logger = logging.getLogger(__name__)


def _np_to_qpixmap(img: np.ndarray, max_width: int = 640) -> QPixmap:
    """Convert a numpy BGR image to QPixmap, scaled down if needed."""
    h, w = img.shape[:2]
    if w > max_width:
        scale = max_width / w
        img = cv2.resize(img, (max_width, int(h * scale)))
        h, w = img.shape[:2]

    if len(img.shape) == 2:
        qimg = QImage(img.data, w, h, w, QImage.Format.Format_Grayscale8)
    else:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)


_STATE_LABELS = {
    ReceiverState.IDLE: ("IDLE", "#78909c"),
    ReceiverState.SEARCHING: ("SEARCHING…", "#ffd600"),
    ReceiverState.SESSION_DETECTED: ("SESSION DETECTED", "#00e5ff"),
    ReceiverState.RECEIVING_METADATA: ("RECEIVING METADATA", "#00e5ff"),
    ReceiverState.RECEIVING_DATA: ("RECEIVING DATA", "#00e676"),
    ReceiverState.DECODING: ("DECODING", "#76ff03"),
    ReceiverState.RECONSTRUCTING: ("RECONSTRUCTING", "#76ff03"),
    ReceiverState.VERIFYING: ("VERIFYING…", "#ffab00"),
    ReceiverState.COMPLETE: ("✓ TRANSFER COMPLETE — FILE VERIFIED", "#00e676"),
    ReceiverState.ERROR: ("✗ ERROR", "#ff1744"),
}


class ReceiverWindow(QMainWindow):
    """PhotonDrop Receiver GUI."""

    def __init__(self):
        super().__init__()
        self.receiver = Receiver()
        self.setWindowTitle("PhotonDrop — Receiver")
        self.setMinimumSize(900, 750)
        self._build_ui()
        self._apply_dark_theme()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(12)
        root.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("PhotonDrop")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00e5ff;")
        root.addWidget(title)

        subtitle = QLabel("Point camera at sender screen")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #90a4ae;")
        root.addWidget(subtitle)

        # State label
        self.lbl_state = QLabel("IDLE")
        self.lbl_state.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_state.setStyleSheet("color: #78909c; padding: 8px;")
        root.addWidget(self.lbl_state)

        # Camera preview
        self.lbl_preview = QLabel()
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setMinimumSize(640, 360)
        self.lbl_preview.setStyleSheet(
            "background-color: #263238; border: 2px solid #37474f; border-radius: 8px;"
        )
        root.addWidget(self.lbl_preview, stretch=1)

        # File info
        self.lbl_file_info = QLabel("")
        self.lbl_file_info.setFont(QFont("Segoe UI", 10))
        self.lbl_file_info.setStyleSheet("color: #b0bec5; padding: 4px;")
        root.addWidget(self.lbl_file_info)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        self.progress.setStyleSheet(
            "QProgressBar { background: #37474f; border-radius: 4px; height: 18px; }"
            "QProgressBar::chunk { background: #00e676; border-radius: 4px; }"
        )
        root.addWidget(self.progress)

        # Stats
        self.lbl_stats = QLabel(
            "Capture FPS: —  |  Decode FPS: —  |  Goodput: —  |  Unique: —  |  Dup: —"
        )
        self.lbl_stats.setFont(QFont("Consolas", 9))
        self.lbl_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stats.setStyleSheet("color: #4db6ac; padding: 4px;")
        root.addWidget(self.lbl_stats)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("  Start Receiving  ")
        self.btn_start.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_start.setStyleSheet(self._button_style("#0091ea"))
        self.btn_start.clicked.connect(self._on_toggle)
        btn_row.addWidget(self.btn_start)

        self.btn_reset = QPushButton("  Reset  ")
        self.btn_reset.setFont(QFont("Segoe UI", 11))
        self.btn_reset.setStyleSheet(self._button_style("#455a64"))
        self.btn_reset.clicked.connect(self._on_reset)
        btn_row.addWidget(self.btn_reset)
        root.addLayout(btn_row)

    def _apply_dark_theme(self) -> None:
        self.setStyleSheet(
            "QMainWindow { background-color: #1e272e; }"
            "QWidget { background-color: #1e272e; color: #eceff1; }"
        )

    @staticmethod
    def _button_style(color: str) -> str:
        return (
            f"QPushButton {{ background-color: {color}; color: white;"
            f" border-radius: 6px; padding: 10px 24px; }}"
            f"QPushButton:hover {{ background-color: {color}cc; }}"
            f"QPushButton:disabled {{ background-color: #455a64; color: #78909c; }}"
        )

    # ── Slots ───────────────────────────────────────────────────────

    @Slot()
    def _on_toggle(self) -> None:
        if self.receiver.camera.is_running:
            self.receiver.stop()
            self.btn_start.setText("  Start Receiving  ")
            self.btn_start.setStyleSheet(self._button_style("#0091ea"))
        else:
            self.receiver.start(
                camera_index=0,
                on_state_change=self._on_state_change,
                on_stats_update=self._on_stats_update,
                on_preview_frame=self._on_preview,
                on_error=self._on_error,
            )
            self.btn_start.setText("  Stop  ")
            self.btn_start.setStyleSheet(self._button_style("#ff1744"))

    @Slot()
    def _on_reset(self) -> None:
        self.receiver.stop()
        self.receiver.reset()
        self.lbl_state.setText("IDLE")
        self.lbl_state.setStyleSheet("color: #78909c; padding: 8px;")
        self.lbl_file_info.setText("")
        self.progress.setValue(0)
        self.lbl_stats.setText(
            "Capture FPS: —  |  Decode FPS: —  |  Goodput: —  |  Unique: —  |  Dup: —"
        )
        self.btn_start.setText("  Start Receiving  ")
        self.btn_start.setStyleSheet(self._button_style("#0091ea"))

    @Slot(object)
    def _on_state_change(self, state: ReceiverState) -> None:
        label, color = _STATE_LABELS.get(state, (str(state), "#78909c"))
        self.lbl_state.setText(label)
        self.lbl_state.setStyleSheet(f"color: {color}; padding: 8px;")

        # Update file info when metadata is available
        meta = self.receiver.reconstruction.session.file_metadata
        if meta:
            self.lbl_file_info.setText(
                f"File: {meta.file_name}  |  Size: {meta.file_size:,} bytes"
                f"  |  Blocks: {meta.total_source_blocks}"
            )

    @Slot(object)
    def _on_stats_update(self, stats: TransferStats) -> None:
        cap_fps = f"{stats.capture_fps:.0f}" if stats.capture_fps else "—"
        dec_fps = f"{stats.decode_fps:.1f}" if stats.decode_fps else "—"
        goodput = f"{stats.goodput / 1024:.1f} KB/s" if stats.goodput > 0 else "—"

        self.lbl_stats.setText(
            f"Capture FPS: {cap_fps}  |  Decode FPS: {dec_fps}  |  "
            f"Goodput: {goodput}  |  Unique: {stats.unique_symbols}  |  "
            f"Dup: {stats.duplicate_frames}  |  Invalid: {stats.invalid_frames}  |  "
            f"Elapsed: {stats.elapsed_time:.1f}s"
        )

        # Update progress
        p = self.receiver.progress
        self.progress.setValue(int(p * 1000))

    @Slot(object)
    def _on_preview(self, frame: np.ndarray) -> None:
        pixmap = _np_to_qpixmap(frame, max_width=640)
        self.lbl_preview.setPixmap(pixmap)

    @Slot(str)
    def _on_error(self, msg: str) -> None:
        self.lbl_state.setText(f"ERROR: {msg}")
        self.lbl_state.setStyleSheet("color: #ff1744; padding: 8px;")
