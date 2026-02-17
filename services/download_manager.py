"""Download-Manager für YouTube-Videos mit Threading."""

import uuid
from pathlib import Path
from threading import Thread
from typing import Optional

import yt_dlp
import yt_dlp.utils

from PySide6.QtCore import QObject, Signal

from models.video_info import VideoInfo
from utils.file_helper import FileHelper
from utils.url_validator import UrlValidator


class DownloadManager(QObject):
    """Download-Manager für YouTube-Videos mit Threading."""

    # Signale für thread-sichere UI-Updates
    progress_updated = Signal(str, float, float)  # task_id, progress (0-100), speed (bytes/s)
    status_changed = Signal(str, str)  # task_id, status
    download_finished = Signal(str, dict)  # task_id, metadata dict
    download_error = Signal(str, str)  # task_id, error message
    info_extracted = Signal(str, object)  # task_id, VideoInfo

    def __init__(self, output_dir: Optional[Path] = None, max_workers: int = 3):
        """Initialisiert den Download-Manager."""
        super().__init__()
        self.output_dir = output_dir or Path.home() / "Downloads"
        self.max_workers = max_workers
        self.active_downloads: dict[str, Thread] = {}
        self.download_opts: dict[str, yt_dlp.YoutubeDL] = {}

    def add_download(self, url: str, quality: str = "best") -> str | None:
        """
        Fügt einen neuen Download zur Warteschlange hinzu.

        Args:
            url: Die YouTube-URL
            quality: Gewünschte Qualität (best, 1080p, 720p, etc.)

        Returns:
            Die Task-ID oder None wenn URL ungültig
        """
        if not UrlValidator.is_valid_youtube_url(url):
            return None

        task_id = str(uuid.uuid4())
        normalized_url = UrlValidator.normalize_url(url)

        # Starte Download in separatem Thread
        thread = Thread(
            target=self._download_worker,
            args=(task_id, normalized_url, quality),
            daemon=True,
        )
        self.active_downloads[task_id] = thread
        thread.start()

        return task_id

    def cancel_download(self, task_id: str) -> bool:
        """Bricht einen laufenden Download ab."""
        if task_id in self.active_downloads:
            # Signal an yt-dlp senden zum Abbrechen
            if task_id in self.download_opts:
                self.download_opts[task_id].cancel()
            return True
        return False

    def _download_worker(self, task_id: str, url: str, quality: str) -> None:
        """Worker-Thread für den Download."""
        video_info: Optional[VideoInfo] = None

        # Zuerst Metadaten extrahieren
        try:
            video_info = self._extract_info(task_id, url)
            if video_info:
                self.info_extracted.emit(task_id, video_info)
        except Exception as e:
            self.download_error.emit(task_id, f"Fehler beim Laden der Metadaten: {e}")
            return

        # Status auf downloading setzen
        self.status_changed.emit(task_id, "downloading")

        # yt-dlp Optionen
        ydl_opts = {
            "format": self._get_format_selector(quality),
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "progress_hooks": [self._make_progress_hook(task_id)],
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        # Erstelle YoutubeDL-Instanz und speichere Referenz für Abbruch
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            self.download_opts[task_id] = ydl
            try:
                # Video herunterladen
                info = ydl.extract_info(url, download=True)

                if info and video_info:
                    # Update VideoInfo mit finalen Daten
                    video_info.filename = ydl.prepare_filename(info)
                    video_info.filepath = str(self.output_dir / video_info.filename)
                    video_info.file_size = info.get("filesize", 0) or info.get("filesize_approx", 0)
                    video_info.status = "completed"
                    video_info.progress = 100.0

                    # Debug: Ausgabe des tatsächlichen Pfads
                    actual_path = ydl.prepare_filename(info)
                    print(f"DEBUG: Video gespeichert unter: {actual_path}")

                    # Speichere Metadaten
                    metadata = video_info.to_dict()
                    self.download_finished.emit(task_id, metadata)
                    self.status_changed.emit(task_id, "completed")
                else:
                    self.download_error.emit(task_id, "Download fehlgeschlagen")

            except yt_dlp.utils.DownloadCancelled:
                self.status_changed.emit(task_id, "cancelled")
            except yt_dlp.utils.DownloadError as e:
                self.download_error.emit(task_id, str(e))
            except Exception as e:
                self.download_error.emit(task_id, f"Unerwarteter Fehler: {e}")
            finally:
                # Cleanup
                self.active_downloads.pop(task_id, None)
                self.download_opts.pop(task_id, None)

    def _extract_info(self, task_id: str, url: str) -> Optional[VideoInfo]:
        """Extrahiert Metadaten vom Video."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                return None

            video_id = info.get("id") or ""
            title = info.get("title") or "Unbekannt"
            uploader = info.get("uploader") or "Unbekannt"
            upload_date = info.get("upload_date")
            duration = info.get("duration") or 0
            thumbnail = info.get("thumbnail") or ""

            # Bereinige Titel für Dateiname
            safe_title = FileHelper.sanitize_filename(title)
            filename = f"{safe_title}.mp4"

            video_info = VideoInfo(
                video_id=video_id,
                title=title,
                uploader=uploader,
                upload_date=upload_date,
                duration=duration,
                thumbnail_url=thumbnail,
                filename=filename,
                quality="best",
                url=url,
                status="pending",
            )

            return video_info

    def _make_progress_hook(self, task_id: str):
        """Erstellt einen Progress-Hook für yt-dlp."""

        def progress_hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)

                if total > 0:
                    progress = (downloaded / total) * 100
                    speed = d.get("speed", 0) or 0
                    self.progress_updated.emit(task_id, progress, speed)

            elif d["status"] == "finished":
                self.progress_updated.emit(task_id, 100.0, 0)

        return progress_hook

    def _get_format_selector(self, quality: str) -> str:
        """Konvertiert Qualitätsstring zu yt-dlp Format-Selector."""
        # Verwende einzelnes Format statt Merge (kein ffmpeg erforderlich)
        quality_map = {
            "best": "best",
            "1080p": "best[height<=1080]",
            "720p": "best[height<=720]",
            "480p": "best[height<=480]",
            "360p": "best[height<=360]",
            "audio": "bestaudio/best",
        }
        return quality_map.get(quality, "best")
