"""URL-Validator für YouTube-URLs."""

import re
from typing import Optional


class UrlValidator:
    """Validiert YouTube-URLs und extrahiert Video-IDs."""

    # Regex-Patterns für verschiedene YouTube-URL-Formate
    URL_PATTERNS = [
        # Standard: youtube.com/watch?v=VIDEO_ID
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        # Short: youtu.be/VIDEO_ID
        r"(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})",
        # Embed: youtube.com/embed/VIDEO_ID
        r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
        # Shorts: youtube.com/shorts/VIDEO_ID
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
        # Playlist mit Video: youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})",
    ]

    @classmethod
    def extract_video_id(cls, url: str) -> Optional[str]:
        """Extrahiert die Video-ID aus einer YouTube-URL."""
        if not url:
            return None

        for pattern in cls.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    @classmethod
    def is_valid_youtube_url(cls, url: str) -> bool:
        """Prüft ob die URL eine gültige YouTube-URL ist."""
        return cls.extract_video_id(url) is not None

    @classmethod
    def normalize_url(cls, url: str) -> Optional[str]:
        """Normalisiert eine YouTube-URL zum Standardformat."""
        video_id = cls.extract_video_id(url)
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return None
