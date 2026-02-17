"""Main ViewModel für MVVM-Verbindung."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal

from models.video_info import VideoInfo
from services.download_manager import DownloadManager
from services.metadata_handler import MetadataHandler
from utils.url_validator import UrlValidator


class MainViewModel(QObject):
    """ViewModel für das Hauptfenster - verbindet Modelle mit Views."""

    # Signale für UI-Updates
    download_added = Signal(str, VideoInfo)  # task_id, VideoInfo
    metadata_updated = Signal(str, VideoInfo)  # task_id, VideoInfo (bei Metadaten-Update)
    progress_updated = Signal(str, float, float)  # task_id, progress, speed
    status_changed = Signal(str, str)  # task_id, status
    download_completed = Signal(str, dict)  # task_id, metadata
    download_error = Signal(str, str)  # task_id, error message
    queue_updated = Signal()  # Downloads-Warteschlange aktualisiert

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialisiert das ViewModel."""
        super().__init__()
        self.output_dir = output_dir or Path.home() / "Downloads"

        # Services initialisieren
        self.download_manager = DownloadManager(self.output_dir)
        self.metadata_handler = MetadataHandler()

        # Download-Tracking
        self.downloads: dict[str, VideoInfo] = {}

        # Signale verbinden
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Verbindet die Signale des DownloadManagers mit dem ViewModel."""
        self.download_manager.info_extracted.connect(self._on_info_extracted)
        self.download_manager.progress_updated.connect(self._on_progress)
        self.download_manager.status_changed.connect(self._on_status_changed)
        self.download_manager.download_finished.connect(self._on_download_finished)
        self.download_manager.download_error.connect(self._on_download_error)

    def add_download(self, url: str, quality: str = "best") -> Optional[str]:
        """
        Fügt einen neuen Download hinzu.

        Args:
            url: Die YouTube-URL
            quality: Gewünschte Qualität

        Returns:
            Die Task-ID oder None wenn ungültige URL
        """
        if not UrlValidator.is_valid_youtube_url(url):
            self.download_error.emit("", "Ungültige YouTube-URL")
            return None

        # Erstelle temporäres VideoInfo für Anzeige
        video_id = UrlValidator.extract_video_id(url) or ""
        temp_video = VideoInfo(
            video_id=video_id,
            title="Wird geladen...",
            uploader="",
            url=url,
            quality=quality,
            status="pending",
        )

        # Download starten
        task_id = self.download_manager.add_download(url, quality)

        if task_id:
            self.downloads[task_id] = temp_video
            self.download_added.emit(task_id, temp_video)
            self.queue_updated.emit()

        return task_id

    def cancel_download(self, task_id: str) -> bool:
        """Bricht einen Download ab."""
        if task_id in self.downloads:
            self.download_manager.cancel_download(task_id)
            self.downloads[task_id].status = "cancelled"
            self.status_changed.emit(task_id, "cancelled")
            return True
        return False

    def remove_download(self, task_id: str) -> bool:
        """Entfernt einen Download aus der Warteschlange."""
        if task_id in self.downloads:
            # Wenn noch aktiv, abbrechen
            if self.downloads[task_id].status in ("pending", "downloading"):
                self.cancel_download(task_id)

            del self.downloads[task_id]
            self.queue_updated.emit()
            return True
        return False

    def get_download(self, task_id: str) -> Optional[VideoInfo]:
        """Gibt die VideoInfo für eine Task-ID zurück."""
        return self.downloads.get(task_id)

    def get_all_downloads(self) -> list[tuple[str, VideoInfo]]:
        """Gibt alle Downloads zurück."""
        return list(self.downloads.items())

    def get_active_count(self) -> int:
        """Gibt die Anzahl aktiver Downloads zurück."""
        return sum(
            1 for v in self.downloads.values()
            if v.status in ("pending", "downloading")
        )

    def get_completed_count(self) -> int:
        """Gibt die Anzahl abgeschlossener Downloads zurück."""
        return sum(1 for v in self.downloads.values() if v.status == "completed")

    # Private Event-Handler

    def _on_info_extracted(self, task_id: str, video_info: VideoInfo) -> None:
        """Wird aufgerufen wenn Metadaten extrahiert wurden."""
        if task_id in self.downloads:
            # Update VideoInfo mit echten Daten
            self.downloads[task_id].video_id = video_info.video_id
            self.downloads[task_id].title = video_info.title
            self.downloads[task_id].uploader = video_info.uploader
            self.downloads[task_id].duration = video_info.duration
            self.downloads[task_id].thumbnail_url = video_info.thumbnail_url
            # Verwende metadata_updated statt download_added für bestehendes Widget
            self.metadata_updated.emit(task_id, self.downloads[task_id])

    def _on_progress(self, task_id: str, progress: float, speed: float) -> None:
        """Wird aufgerufen wenn sich der Fortschritt ändert."""
        if task_id in self.downloads:
            self.downloads[task_id].progress = progress
            self.downloads[task_id].speed = speed
            self.progress_updated.emit(task_id, progress, speed)

    def _on_status_changed(self, task_id: str, status: str) -> None:
        """Wird aufgerufen wenn sich der Status ändert."""
        if task_id in self.downloads:
            self.downloads[task_id].status = status
            self.status_changed.emit(task_id, status)

    def _on_download_finished(self, task_id: str, metadata: dict) -> None:
        """Wird aufgerufen wenn ein Download abgeschlossen wurde."""
        if task_id in self.downloads:
            video_info = self.downloads[task_id]
            video_info.status = "completed"
            video_info.progress = 100.0

            # Speichere Metadaten
            full_info = VideoInfo.from_dict(metadata)
            full_info.downloaded_at = datetime.now()
            self.metadata_handler.save_metadata(full_info)

            self.download_completed.emit(task_id, metadata)

    def _on_download_error(self, task_id: str, error: str) -> None:
        """Wird aufgerufen wenn ein Fehler aufgetreten ist."""
        if task_id in self.downloads:
            self.downloads[task_id].status = "error"
            self.downloads[task_id].error_message = error
            self.download_error.emit(task_id, error)

