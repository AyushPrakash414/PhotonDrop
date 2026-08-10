"""
PhotonDrop — Sender Entry Point

Launch the PhotonDrop Sender desktop application.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from shared.constants import LOG_DATE_FORMAT, LOG_FORMAT


def main() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    app = QApplication(sys.argv)
    app.setApplicationName("PhotonDrop Sender")

    from sender.ui.main_window import SenderWindow

    window = SenderWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
