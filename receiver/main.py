"""
PhotonDrop — Receiver Entry Point

Launch the PhotonDrop Receiver desktop application.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from shared.constants import LOG_DATE_FORMAT, LOG_FORMAT


def main() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    app = QApplication(sys.argv)
    app.setApplicationName("PhotonDrop Receiver")

    from receiver.ui.main_window import ReceiverWindow

    window = ReceiverWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
