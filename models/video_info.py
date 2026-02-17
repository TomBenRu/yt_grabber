"""Datenmodell für Video-Informationen."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VideoInfo:
    """Datenmodell für Video-Informationen von YouTube."""

    video_id: str
    title: str
    uploader: str
    upload_date: Optional[str] = None
    duration: int = 0
    filename: str = ""
    filepath: str = ""
    file_size: int = 0
    quality: str = "best"
    thumbnail_url: str = ""
    downloaded_at: Optional[datetime] = None
    url: str = ""

    # Status-Felder (nicht in Metadaten gespeichert)
    status: str = "pending"  # pending, downloading, completed, error, cancelled
    progress: float = 0.0
    speed: float = 0.0  # Bytes pro Sekunde
    error_message: str = ""

    def to_dict(self) -> dict:
        """Konvertiert das Model in ein Dictionary für JSON-Speicherung."""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "uploader": self.uploader,
            "upload_date": self.upload_date,
            "duration": self.duration,
            "filename": self.filename,
            "filepath": self.filepath,
            "file_size": self.file_size,
            "quality": self.quality,
            "thumbnail_url": self.thumbnail_url,
            "downloaded_at": self.downloaded_at.isoformat() if self.downloaded_at else None,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoInfo":
        """Erstellt ein VideoInfo-Objekt aus einem Dictionary."""
        downloaded_at = None
        if data.get("downloaded_at"):
            downloaded_at = datetime.fromisoformat(data["downloaded_at"])

        return cls(
            video_id=data["video_id"],
            title=data["title"],
            uploader=data.get("uploader", ""),
            upload_date=data.get("upload_date"),
            duration=data.get("duration", 0),
            filename=data.get("filename", ""),
            filepath=data.get("filepath", ""),
            file_size=data.get("file_size", 0),
            quality=data.get("quality", "best"),
            thumbnail_url=data.get("thumbnail_url", ""),
            downloaded_at=downloaded_at,
            url=data.get("url", ""),
        )

    def format_duration(self) -> str:
        """Formatiert die Dauer als MM:SS oder HH:MM:SS."""
        minutes, seconds = divmod(self.duration, 60)
        if self.duration >= 3600:
            hours, minutes = divmod(minutes, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def format_file_size(self) -> str:
        """Formatiert die Dateigröße lesbar."""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def format_speed(self) -> str:
        """Formatiert die Download-Geschwindigkeit."""
        speed = self.speed
        for unit in ["B/s", "KB/s", "MB/s"]:
            if speed < 1024:
                return f"{speed:.1f} {unit}"
            speed /= 1024
            if unit == "MB/s":
                break
        return f"{speed:.1f} GB/s"
