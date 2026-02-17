"""YouTube Grabber - Main Entry Point."""
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


def main() -> int:
    """Startet die YouTube Grabber Anwendung."""
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Grabber")
    app.setOrganizationName("yt_grabber")
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "resources", "main.ico")))

    # Stil setzen
    app.setStyle("Fusion")

    # Import hier, um zirkuläre Importe zu vermeiden
    from views.main_window import MainWindow

    window = MainWindow()
    window.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "resources", "main.ico")))
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
