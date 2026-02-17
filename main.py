"""YouTube Grabber - Main Entry Point."""

import sys

from PySide6.QtWidgets import QApplication


def main() -> int:
    """Startet die YouTube Grabber Anwendung."""
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Grabber")
    app.setOrganizationName("yt_grabber")

    # Stil setzen
    app.setStyle("Fusion")

    # Import hier, um zirkuläre Importe zu vermeiden
    from views.main_window import MainWindow

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
