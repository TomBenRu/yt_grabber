"""File-Hilfsfunktionen für Dateinamen-Sanitization."""

import re
from pathlib import Path


class FileHelper:
    """Hilfsklasse für Dateioperationen."""

    # Zeichen, die in Dateinamen nicht erlaubt sind
    INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')

    @classmethod
    def sanitize_filename(cls, filename: str, max_length: int = 200) -> str:
        """
        Bereinigt einen Dateinamen von ungültigen Zeichen.

        Args:
            filename: Der ursprüngliche Dateiname
            max_length: Maximale Länge des Dateinamens

        Returns:
            Ein bereinigter Dateiname
        """
        # Ersetze ungültige Zeichen durch Unterstrich
        sanitized = cls.INVALID_CHARS.sub("_", filename)

        # Entferne führende/trailing Leerzeichen und Punkte
        sanitized = sanitized.strip(" .")

        # Ersetze mehrere aufeinanderfolgende Unterstriche durch eines
        sanitized = re.sub(r"_+", "_", sanitized)

        # Begrenze die Länge
        if len(sanitized) > max_length:
            # Behalte die Dateierweiterung wenn vorhanden
            name, ext = Path(sanitized).stem, Path(sanitized).suffix
            max_name_length = max_length - len(ext)
            sanitized = name[:max_name_length] + ext

        # Falls der Dateiname leer ist, generiere einen Standardnamen
        if not sanitized:
            sanitized = "video"

        return sanitized

    @classmethod
    def get_safe_path(cls, directory: Path, filename: str) -> Path:
        """
        Erstellt einen sicheren Pfad aus Verzeichnis und Dateiname.

        Args:
            directory: Das Zielverzeichnis
            filename: Der Dateiname

        Returns:
            Ein sicherer Pfad
        """
        sanitized_name = cls.sanitize_filename(filename)
        filepath = directory / sanitized_name

        # Falls Datei bereits existiert, hänge Nummer an
        counter = 1
        stem = Path(sanitized_name).stem
        suffix = Path(sanitized_name).suffix
        while filepath.exists():
            new_name = f"{stem}_{counter}{suffix}"
            filepath = directory / new_name
            counter += 1

        return filepath

    @classmethod
    def format_bytes(cls, bytes_size: int) -> str:
        """Formatiert eine Byte-Größe in einen lesbaren String."""
        size = float(bytes_size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
