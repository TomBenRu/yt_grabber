"""Metadaten-Handler für das Speichern und Laden von Video-Metadaten."""

import json
from pathlib import Path
from typing import Optional

from models.video_info import VideoInfo


class MetadataHandler:
    """Handler für das Speichern und Laden von Video-Metadaten."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialisiert den Metadata-Handler."""
        self.storage_dir = storage_dir or (Path.home() / "Downloads" / "yt_grabber")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.library_file = self.storage_dir / "library.json"

    def save_metadata(self, video_info: VideoInfo) -> bool:
        """
        Speichert Metadaten eines Videos.

        Args:
            video_info: Das VideoInfo-Objekt mit den Metadaten

        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            # Lade existierende Bibliothek
            library = self.load_library()

            # Füge neues Video hinzu oder aktualisiere existierendes
            video_id = video_info.video_id
            library[video_id] = video_info.to_dict()

            # Speichere Bibliothek
            with open(self.library_file, "w", encoding="utf-8") as f:
                json.dump(library, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Metadaten: {e}")
            return False

    def load_library(self) -> dict:
        """
        Lädt die gesamte Video-Bibliothek.

        Returns:
            Dictionary mit Video-ID als Schlüssel und Metadaten als Wert
        """
        if not self.library_file.exists():
            return {}

        try:
            with open(self.library_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Bibliothek: {e}")
            return {}

    def get_video_metadata(self, video_id: str) -> Optional[VideoInfo]:
        """
        Lädt Metadaten für ein bestimmtes Video.

        Args:
            video_id: Die Video-ID

        Returns:
            VideoInfo-Objekt oder None wenn nicht gefunden
        """
        library = self.load_library()
        if video_id in library:
            return VideoInfo.from_dict(library[video_id])
        return None

    def remove_metadata(self, video_id: str) -> bool:
        """
        Entfernt Metadaten für ein Video.

        Args:
            video_id: Die Video-ID

        Returns:
            True wenn erfolgreich
        """
        try:
            library = self.load_library()
            if video_id in library:
                del library[video_id]
                with open(self.library_file, "w", encoding="utf-8") as f:
                    json.dump(library, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Fehler beim Entfernen der Metadaten: {e}")
            return False

    def get_all_videos(self) -> list[VideoInfo]:
        """
        Lädt alle Videos aus der Bibliothek.

        Returns:
            Liste von VideoInfo-Objekten
        """
        library = self.load_library()
        videos = []
        for data in library.values():
            videos.append(VideoInfo.from_dict(data))
        return videos

    def search_videos(self, query: str) -> list[VideoInfo]:
        """
        Sucht Videos in der Bibliothek nach Titel oder Uploader.

        Args:
            query: Der Suchbegriff

        Returns:
            Liste von passenden VideoInfo-Objekten
        """
        library = self.load_library()
        query_lower = query.lower()
        results = []

        for data in library.values():
            title = data.get("title", "").lower()
            uploader = data.get("uploader", "").lower()
            if query_lower in title or query_lower in uploader:
                results.append(VideoInfo.from_dict(data))

        return results
