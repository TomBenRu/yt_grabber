"""Main Window GUI für YouTube Grabber."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.video_info import VideoInfo
from viewmodels.main_viewmodel import MainViewModel
from views.download_item_widget import DownloadItemWidget


class MainWindow(QMainWindow):
    """Hauptfenster der YouTube Grabber Anwendung."""

    def __init__(self):
        """Initialisiert das Hauptfenster."""
        super().__init__()

        self.view_model = MainViewModel()

        self.setWindowTitle("YouTube Grabber")
        self.setMinimumSize(800, 600)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Richtet die UI-Komponenten ein."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Eingabebereich (Top)
        input_layout = self._create_input_section()
        main_layout.addLayout(input_layout)

        # Download-Warteschlange (Middle - Hauptbereich)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.download_list = QListWidget()
        scroll_area.setWidget(self.download_list)
        main_layout.addWidget(scroll_area)

        # Statusleiste (Bottom)
        status_layout = self._create_status_bar()
        main_layout.addLayout(status_layout)

    def _create_input_section(self) -> QHBoxLayout:
        """Erstellt den Eingabebereich."""
        layout = QHBoxLayout()

        # URL-Eingabe
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube-URL eingeben...")
        self.url_input.returnPressed.connect(self._on_add_clicked)

        # Qualitätsauswahl
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["best", "1080p", "720p", "480p", "360p", "audio"])
        self.quality_combo.setCurrentText("best")

        # Download-Button
        self.add_button = QPushButton("Download hinzufügen")
        self.add_button.clicked.connect(self._on_add_clicked)

        layout.addWidget(QLabel("URL:"))
        layout.addWidget(self.url_input, 1)
        layout.addWidget(QLabel("Qualität:"))
        layout.addWidget(self.quality_combo)
        layout.addWidget(self.add_button)

        return layout

    def _create_status_bar(self) -> QHBoxLayout:
        """Erstellt die Statusleiste."""
        layout = QHBoxLayout()

        self.status_label = QLabel("Bereit")
        self.progress_label = QLabel("0 von 0 abgeschlossen")

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.progress_label)

        return layout

    def _connect_signals(self) -> None:
        """Verbindet die ViewModel-Signale mit Slots."""
        self.view_model.download_added.connect(self._on_download_added)
        self.view_model.metadata_updated.connect(self._on_metadata_updated)
        self.view_model.progress_updated.connect(self._on_progress_updated)
        self.view_model.status_changed.connect(self._on_status_changed)
        self.view_model.download_completed.connect(self._on_download_completed)
        self.view_model.download_error.connect(self._on_download_error)

    def _on_add_clicked(self) -> None:
        """Wird aufgerufen wenn der Hinzufügen-Button geklickt wird."""
        url = self.url_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie eine YouTube-URL ein.")
            return

        quality = self.quality_combo.currentText()
        self.view_model.add_download(url, quality)

        # URL-Eingabe leeren
        self.url_input.clear()
        self.status_label.setText("Download wird gestartet...")

    def _on_download_added(self, task_id: str, video_info: VideoInfo) -> None:
        """Wird aufgerufen wenn ein Download zur Warteschlange hinzugefügt wurde."""
        # Erstelle Widget für Download-Item
        item_widget = DownloadItemWidget(task_id, video_info, self.view_model)
        item_widget.cancel_clicked.connect(self._on_cancel_clicked)
        item_widget.remove_clicked.connect(self._on_remove_clicked)

        # Füge zur Liste hinzu
        item = QListWidgetItem()
        item.setSizeHint(item_widget.sizeHint())
        self.download_list.addItem(item)
        self.download_list.setItemWidget(item, item_widget)

        self._update_status()

    def _on_metadata_updated(self, task_id: str, video_info: VideoInfo) -> None:
        """Wird aufgerufen wenn Metadaten eines Downloads aktualisiert wurden."""
        self._update_item_widget(task_id, lambda w: w.update_metadata(video_info))

    def _on_progress_updated(self, task_id: str, progress: float, speed: float) -> None:
        """Wird aufgerufen wenn sich der Fortschritt ändert."""
        self._update_item_widget(task_id, lambda w: w.update_progress(progress, speed))

    def _on_status_changed(self, task_id: str, status: str) -> None:
        """Wird aufgerufen wenn sich der Status ändert."""
        self._update_item_widget(task_id, lambda w: w.update_status(status))
        self._update_status()

    def _on_download_completed(self, task_id: str, metadata: dict) -> None:
        """Wird aufgerufen wenn ein Download abgeschlossen wurde."""
        self._update_item_widget(task_id, lambda w: w.update_completed())
        self._update_status()
        QMessageBox.information(self, "Download abgeschlossen", "Das Video wurde erfolgreich heruntergeladen.")

    def _on_download_error(self, task_id: str, error: str) -> None:
        """Wird aufgerufen wenn ein Fehler aufgetreten ist."""
        self._update_item_widget(task_id, lambda w: w.update_error(error))
        self._update_status()
        QMessageBox.warning(self, "Download-Fehler", error)

    def _on_cancel_clicked(self, task_id: str) -> None:
        """Wird aufgerufen wenn der Abbrechen-Button geklickt wird."""
        self.view_model.cancel_download(task_id)

    def _on_remove_clicked(self, task_id: str) -> None:
        """Wird aufgerufen wenn der Entfernen-Button geklickt wird."""
        # Finde und entferne das Item
        for i in range(self.download_list.count()):
            item = self.download_list.item(i)
            widget = self.download_list.itemWidget(item)
            if widget and widget.task_id == task_id:
                self.download_list.takeItem(i)
                break

        self.view_model.remove_download(task_id)
        self._update_status()

    def _update_item_widget(self, task_id: str, update_func) -> None:
        """Aktualisiert ein bestimmtes Download-Item-Widget."""
        for i in range(self.download_list.count()):
            item = self.download_list.item(i)
            widget = self.download_list.itemWidget(item)
            if widget and widget.task_id == task_id:
                update_func(widget)
                break

    def _update_status(self) -> None:
        """Aktualisiert die Statusanzeige."""
        active = self.view_model.get_active_count()
        completed = self.view_model.get_completed_count()
        total = len(self.view_model.downloads)

        if active > 0:
            self.status_label.setText(f"{active} Download(s) aktiv...")
        else:
            self.status_label.setText("Bereit")

        self.progress_label.setText(f"{completed} von {total} abgeschlossen")
