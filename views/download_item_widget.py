"""Download Item Widget für einzelne Downloads in der Warteschlange."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.video_info import VideoInfo
from viewmodels.main_viewmodel import MainViewModel


class DownloadItemWidget(QWidget):
    """Widget für die Anzeige eines einzelnen Downloads."""

    cancel_clicked = Signal(str)
    remove_clicked = Signal(str)

    def __init__(self, task_id: str, video_info: VideoInfo, view_model: MainViewModel):
        """Initialisiert das Download-Item-Widget."""
        super().__init__()

        self.task_id = task_id
        self.video_info = video_info
        self.view_model = view_model

        self._setup_ui()
        self._update_display()

    def _setup_ui(self) -> None:
        """Richtet die UI-Komponenten ein."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Titel und Uploader
        title_layout = QHBoxLayout()
        self.title_label = QLabel("Wird geladen...")
        self.title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.status_label = QLabel("Warte...")
        self.status_label.setStyleSheet("color: gray;")
        title_layout.addWidget(self.status_label)

        layout.addLayout(title_layout)

        # Uploader
        self.uploader_label = QLabel("")
        self.uploader_label.setStyleSheet("color: gray; font-size: 10pt;")
        layout.addWidget(self.uploader_label)

        # Fortschrittsbalken
        self.progress_bar = QLabel()
        self.progress_bar.setText("0%")
        layout.addWidget(self.progress_bar)

        # Geschwindigkeit
        self.speed_label = QLabel("")
        layout.addWidget(self.speed_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(lambda: self.cancel_clicked.emit(self.task_id))

        self.remove_button = QPushButton("Entfernen")
        self.remove_button.clicked.connect(lambda: self.remove_clicked.emit(self.task_id))

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.remove_button)

        layout.addLayout(button_layout)

    def _update_display(self) -> None:
        """Aktualisiert die Anzeige mit den VideoInfo-Daten."""
        self.title_label.setText(self.video_info.title or "Wird geladen...")
        self.uploader_label.setText(self.video_info.uploader or "")

    def update_metadata(self, video_info: VideoInfo) -> None:
        """Aktualisiert die Metadaten (Titel, Uploader)."""
        self.video_info = video_info
        self._update_display()

    def update_metadata(self, video_info: VideoInfo) -> None:
        """Aktualisiert die Metadaten (Titel, Uploader)."""
        self.video_info = video_info
        self._update_display()

    def update_progress(self, progress: float, speed: float) -> None:
        """Aktualisiert den Fortschritt."""
        self.progress_bar.setText(f"Fortschritt: {progress:.1f}%")

        # Geschwindigkeit formatieren
        if speed > 0:
            speed_str = self._format_speed(speed)
            self.speed_label.setText(f"Geschwindigkeit: {speed_str}")
        else:
            self.speed_label.setText("")

    def update_status(self, status: str) -> None:
        """Aktualisiert den Status."""
        status_map = {
            "pending": "Warte...",
            "downloading": "Wird heruntergeladen...",
            "completed": "Abgeschlossen",
            "error": "Fehler",
            "cancelled": "Abgebrochen",
        }
        self.status_label.setText(status_map.get(status, status))

        # Button-Status aktualisieren
        if status in ("completed", "error", "cancelled"):
            self.cancel_button.setEnabled(False)
        else:
            self.cancel_button.setEnabled(True)

    def update_completed(self) -> None:
        """Markiert den Download als abgeschlossen."""
        self.status_label.setText("Abgeschlossen")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.progress_bar.setText("100%")
        self.speed_label.setText("")
        self.cancel_button.setEnabled(False)

    def update_error(self, error: str) -> None:
        """Zeigt einen Fehler an."""
        self.status_label.setText(f"Fehler: {error}")
        self.status_label.setStyleSheet("color: red;")
        self.cancel_button.setEnabled(False)

    def _format_speed(self, speed: float) -> str:
        """Formatiert die Geschwindigkeit."""
        for unit in ["B/s", "KB/s", "MB/s"]:
            if speed < 1024:
                return f"{speed:.1f} {unit}"
            speed /= 1024
        return f"{speed:.1f} GB/s"
