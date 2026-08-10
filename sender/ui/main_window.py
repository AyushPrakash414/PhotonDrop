"""
PhotonDrop — Sender Main Window (PySide6)

A clean desktop UI for selecting a file, starting transmission,
and displaying real-time QR frames with statistics.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sender.sender import Sender
from shared.models import TransferStats
from visual.renderer import render_frame

logger = logging.getLogger(__name__)


def _np_to_qpixmap(img: np.ndarray) -> QPixmap:
    """Convert a numpy image (grayscale or BGR) to QPixmap."""
    if len(img.shape) == 2:
        h, w = img.shape
        qimg = QImage(img.data, w, h, w, QImage.Format.Format_Grayscale8)
    else:
        h, w, ch = img.shape
        bytes_per_line = ch * w
        if ch == 3:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        else:
            qimg = QImage(img.data, w, h, bytes_per_line, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


class SenderWindow(QMainWindow):
    """PhotonDrop Sender GUI."""

    def __init__(self):
        super().__init__()
        self.sender = Sender()
        self.setWindowTitle("PhotonDrop — Sender")
        self.setMinimumSize(900, 750)
        self._build_ui()
        self._apply_dark_theme()

    # ── UI Construction ─────────────────────────────────────────────

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

        subtitle = QLabel("Offline Optical File Transfer")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #90a4ae;")
        root.addWidget(subtitle)

        # File selection row
        file_row = QHBoxLayout()
        self.btn_select = QPushButton("  Select File  ")
        self.btn_select.setFont(QFont("Segoe UI", 11))
        self.btn_select.setStyleSheet(self._button_style("#0091ea"))
        self.btn_select.clicked.connect(self._on_select_file)
        file_row.addWidget(self.btn_select)

        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setFont(QFont("Segoe UI", 10))
        self.lbl_file.setStyleSheet("color: #b0bec5; padding-left: 8px;")
        file_row.addWidget(self.lbl_file, stretch=1)
        root.addLayout(file_row)

        # File info
        self.lbl_info = QLabel("")
        self.lbl_info.setFont(QFont("Consolas", 9))
        self.lbl_info.setStyleSheet("color: #78909c; padding: 4px;")
        root.addWidget(self.lbl_info)

        # Start / Stop button
        self.btn_start = QPushButton("  START TRANSMISSION  ")
        self.btn_start.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.btn_start.setStyleSheet(self._button_style("#00c853"))
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._on_toggle_transmission)
        root.addWidget(self.btn_start, alignment=Qt.AlignmentFlag.AlignCenter)

        # QR display
        self.lbl_qr = QLabel()
        self.lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_qr.setMinimumSize(400, 400)
        self.lbl_qr.setStyleSheet(
            "background-color: #263238; border: 2px solid #37474f; border-radius: 8px;"
        )
        root.addWidget(self.lbl_qr, stretch=1)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet(
            "QProgressBar { background: #37474f; border-radius: 4px; height: 18px; }"
            "QProgressBar::chunk { background: #00e676; border-radius: 4px; }"
        )
        root.addWidget(self.progress)

        # Stats row
        self.lbl_stats = QLabel("FPS: —  |  Symbols: —  |  Goodput: —")
        self.lbl_stats.setFont(QFont("Consolas", 10))
        self.lbl_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stats.setStyleSheet("color: #4db6ac; padding: 4px;")
        root.addWidget(self.lbl_stats)

    # ── Theming ─────────────────────────────────────────────────────

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
    def _on_select_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Transfer")
        if not path:
            return
        try:
            meta = self.sender.load_file(path)
            self.lbl_file.setText(meta.file_name)
            self.lbl_info.setText(
                f"Size: {meta.file_size:,} bytes  |  Blocks: {meta.total_source_blocks}"
                f"  |  Type: {meta.mime_type}\nSHA-256: {meta.sha256}"
            )
            self.btn_start.setEnabled(True)
        except Exception as e:
            self.lbl_file.setText(f"Error: {e}")
            self.btn_start.setEnabled(False)

    @Slot()
    def _on_toggle_transmission(self) -> None:
        if self.sender.is_transmitting:
            self.sender.stop_transmission()
            self.btn_start.setText("  START TRANSMISSION  ")
            self.btn_start.setStyleSheet(self._button_style("#00c853"))
        else:
            self.sender.start_transmission(
                target_fps=30,
                on_frame=self._on_frame,
                on_stats=self._on_stats,
                on_finished=self._on_finished,
            )
            self.btn_start.setText("  STOP  ")
            self.btn_start.setStyleSheet(self._button_style("#ff1744"))

    @Slot(object)
    def _on_frame(self, qr_image: np.ndarray) -> None:
        rendered = render_frame(qr_image, canvas_size=(400, 400))
        pixmap = _np_to_qpixmap(rendered)
        self.lbl_qr.setPixmap(pixmap)

    @Slot(object)
    def _on_stats(self, stats: TransferStats) -> None:
        fps = f"{stats.display_fps:.1f}"
        goodput = f"{stats.goodput / 1024:.1f} KB/s" if stats.goodput > 0 else "—"
        self.lbl_stats.setText(
            f"FPS: {fps}  |  Symbols: {stats.total_frames}  |  "
            f"Goodput: {goodput}  |  Elapsed: {stats.elapsed_time:.1f}s"
        )

    @Slot()
    def _on_finished(self) -> None:
        self.btn_start.setText("  START TRANSMISSION  ")
        self.btn_start.setStyleSheet(self._button_style("#00c853"))
        self.lbl_stats.setText("Transmission complete")
