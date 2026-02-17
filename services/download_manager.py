"""Download-Manager für YouTube-Videos mit High-Quality (DASH) Support."""

import uuid
import threading
from pathlib import Path
from typing import Optional

import yt_dlp
import yt_dlp.utils
import static_ffmpeg  # Automatisches Management der FFmpeg-Binaries

from PySide6.QtCore import QObject, Signal

# Hinweis: Diese Klassen müssen in deinem Projektpfad vorhanden sein
from models.video_info import VideoInfo
from utils.file_helper import FileHelper
from utils.url_validator import UrlValidator


class DownloadManager(QObject):
    """Download-Manager für YouTube-Videos mit automatischer FFmpeg-Einbindung."""

    # Signale für die UI
    progress_updated = Signal(str, float, float)  # task_id, progress (0-100), speed
    status_changed = Signal(str, str)  # task_id, status (z.B. 'initializing', 'downloading')
    download_finished = Signal(str, dict)  # task_id, metadata
    download_error = Signal(str, str)  # task_id, error_message
    info_extracted = Signal(str, object)  # task_id, VideoInfo

    def __init__(self, output_dir: Optional[Path] = None, max_workers: int = 3):
        super().__init__()

        # Stellt sicher, dass FFmpeg im Pfad der Anwendung verfügbar ist.
        # Beim allerersten Start lädt dieses Paket die Binaries automatisch herunter.
        static_ffmpeg.add_paths()

        self.output_dir = output_dir or Path.home() / "Downloads"
        self.max_workers = max_workers
        self.active_downloads: dict[str, threading.Thread] = {}
        self.download_opts: dict[str, yt_dlp.YoutubeDL] = {}

        # Flag, um zu prüfen, ob FFmpeg bereits im System-Pfad registriert wurde
        self._ffmpeg_ready = False

    def add_download(self, url: str, quality: str = "best") -> str | None:
        """Fügt einen neuen Download hinzu und startet den Worker-Thread."""
        if not UrlValidator.is_valid_youtube_url(url):
            return None

        task_id = str(uuid.uuid4())
        normalized_url = UrlValidator.normalize_url(url)

        thread = threading.Thread(
            target=self._download_worker,
            args=(task_id, normalized_url, quality),
            daemon=True,
        )
        self.active_downloads[task_id] = thread
        thread.start()

        return task_id

    def _download_worker(self, task_id: str, url: str, quality: str) -> None:
        """Kern-Logik für den Download im Hintergrund."""

        # 1. FFmpeg Initialisierung (nur beim allerersten Aufruf nötig)
        if not self._ffmpeg_ready:
            self.status_changed.emit(task_id, "Preparing FFmpeg (Initial setup)...")
            static_ffmpeg.add_paths()  # Lädt Binaries falls nötig
            self._ffmpeg_ready = True

        # 2. Metadaten extrahieren
        video_info: Optional[VideoInfo] = None
        try:
            video_info = self._extract_info(task_id, url)
            if video_info:
                self.info_extracted.emit(task_id, video_info)
        except Exception as e:
            self.download_error.emit(task_id, f"Metadaten-Fehler: {e}")
            return

        self.status_changed.emit(task_id, "downloading")

        # 3. yt-dlp Optionen (Konfiguriert für DASH-Merging)
        ydl_opts = {
            "format": self._get_format_selector(quality),
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",  # Kombiniert Video/Audio zu MP4
            "progress_hooks": [self._make_progress_hook(task_id)],
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            self.download_opts[task_id] = ydl
            try:
                info = ydl.extract_info(url, download=True)

                if info and video_info:
                    # Finale Daten für das VideoInfo-Objekt
                    video_info.filename = ydl.prepare_filename(info)
                    video_info.filepath = str(self.output_dir / video_info.filename)
                    video_info.file_size = info.get("filesize", 0) or info.get("filesize_approx", 0)
                    video_info.status = "completed"
                    video_info.progress = 100.0

                    self.download_finished.emit(task_id, video_info.to_dict())
                    self.status_changed.emit(task_id, "completed")
                else:
                    self.download_error.emit(task_id, "Download fehlgeschlagen")

            except yt_dlp.utils.DownloadCancelled:
                self.status_changed.emit(task_id, "cancelled")
            except Exception as e:
                self.download_error.emit(task_id, f"Fehler: {str(e)}")
            finally:
                self.active_downloads.pop(task_id, None)
                self.download_opts.pop(task_id, None)

    def _get_format_selector(self, quality: str) -> str:
        """Erzwingt das Herunterladen von separaten Video- und Audiostreams."""
        # 'bestvideo+bestaudio' erlaubt Auflösungen > 720p
        quality_map = {
            "best": "bestvideo+bestaudio/best",
            "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
            "audio": "bestaudio/best",
        }
        return quality_map.get(quality, "bestvideo+bestaudio/best")

    def _extract_info(self, task_id: str, url: str) -> Optional[VideoInfo]:
        """Extrahiert Video-Informationen ohne Download."""
        ydl_opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info: return None

            return VideoInfo(
                video_id=info.get("id", ""),
                title=info.get("title", "Unbekannt"),
                uploader=info.get("uploader", "Unbekannt"),
                upload_date=info.get("upload_date"),
                duration=info.get("duration", 0),
                thumbnail_url=info.get("thumbnail", ""),
                filename=f"{FileHelper.sanitize_filename(info.get('title', 'video'))}.mp4",
                quality="best",
                url=url,
                status="pending",
            )

    def _make_progress_hook(self, task_id: str):
        """Erstellt den Hook für Fortschrittsanzeigen."""

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