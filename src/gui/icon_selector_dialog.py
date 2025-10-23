"""Icon selector dialog with grid view and search."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.icon_library_manager import IconLibraryManager, IconMetadata


class IconDownloadWorker(QThread):
    """Worker thread for downloading icons."""

    finished = Signal(Path)
    error = Signal(str)

    def __init__(self, manager: IconLibraryManager, library: str, icon_name: str, size: int = 64):
        super().__init__()
        self.manager = manager
        self.library = library
        self.icon_name = icon_name
        self.size = size

    def run(self) -> None:
        """Download the icon."""
        try:
            path = self.manager.download_icon_from_library(self.library, self.icon_name, self.size)
            if path:
                self.finished.emit(path)
            else:
                self.error.emit("Failed to download icon")
        except Exception as e:
            self.error.emit(str(e))


class IconButton(QPushButton):
    """Button displaying an icon with metadata."""

    def __init__(self, metadata: IconMetadata, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self.setFixedSize(80, 100)
        self.setToolTip(f"{metadata.name}\n{metadata.library}\n{metadata.license}")

        # Set up layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Icon placeholder
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setScaledContents(True)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet(
            "QLabel { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; }"
        )
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)

        # Icon name
        name_parts = metadata.name.split(":")
        display_name = name_parts[-1] if len(name_parts) > 1 else metadata.name
        name_label = QLabel(display_name[:10] + "..." if len(display_name) > 10 else display_name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 9px;")
        layout.addWidget(name_label)

        self.setLayout(layout)

        # Load icon if cached
        if metadata.file_path.exists():
            self._load_icon(metadata.file_path)
        else:
            self.icon_label.setText("📦")

    def _load_icon(self, icon_path: Path) -> None:
        """Load and display the icon."""
        if icon_path.suffix == ".svg":
            # Load SVG
            renderer = QSvgRenderer(str(icon_path))
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            from PySide6.QtGui import QPainter

            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            self.icon_label.setPixmap(pixmap)
        else:
            # Load raster image
            pixmap = QPixmap(str(icon_path))
            self.icon_label.setPixmap(
                pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )


class IconSelectorDialog(QDialog):
    """Dialog for selecting icons from various libraries."""

    icon_selected = Signal(str, Path)  # library_name, icon_path

    def __init__(self, manager: IconLibraryManager, initial_query: str = "", parent=None):
        super().__init__(parent)
        self.manager = manager
        self.selected_icon: Optional[tuple[str, IconMetadata]] = None

        self.setWindowTitle("Select Icon")
        self.setMinimumSize(800, 600)

        self.setup_ui()

        # Initial search
        if initial_query:
            self.search_input.setText(initial_query)
            self.search_icons()

    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()

        # Top controls
        top_layout = QHBoxLayout()

        # Library selector
        self.library_combo = QComboBox()
        self.library_combo.addItem("All Libraries")
        for lib in self.manager.get_available_libraries():
            self.library_combo.addItem(lib.title())
        top_layout.addWidget(QLabel("Library:"))
        top_layout.addWidget(self.library_combo)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search icons...")
        self.search_input.returnPressed.connect(self.search_icons)
        top_layout.addWidget(self.search_input, stretch=1)

        # Search button
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self.search_icons)
        top_layout.addWidget(search_btn)

        layout.addLayout(top_layout)

        # Results info
        self.results_label = QLabel("Enter a search query to find icons")
        self.results_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.results_label)

        # Icon grid in scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.icon_container = QWidget()
        self.icon_grid = QGridLayout()
        self.icon_grid.setSpacing(10)
        self.icon_container.setLayout(self.icon_grid)
        self.scroll_area.setWidget(self.icon_container)

        layout.addWidget(self.scroll_area)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(cancel_btn)

        self.select_btn = QPushButton("Select Icon")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(self.select_btn)

        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    def search_icons(self) -> None:
        """Search for icons based on current query."""
        query = self.search_input.text().strip()
        if not query:
            return

        # Clear previous results
        self.clear_grid()
        self.results_label.setText(f"Searching for '{query}'...")

        # Get selected library
        selected_lib = self.library_combo.currentText()

        # Search
        if selected_lib == "All Libraries":
            results = self.manager.search_all_libraries(query, limit_per_library=20)
        else:
            lib_key = selected_lib.lower().replace(" ", "-")
            if lib_key in self.manager.libraries:
                results = {lib_key: self.manager.libraries[lib_key].search_icons(query, limit=50)}
            else:
                results = {}

        # Display results
        total_results = sum(len(icons) for icons in results.values())
        if total_results == 0:
            self.results_label.setText(f"No icons found for '{query}'")
            return

        self.results_label.setText(f"Found {total_results} icons for '{query}'")

        row, col = 0, 0
        max_cols = 8

        for library_name, icons in results.items():
            for icon_meta in icons:
                btn = IconButton(icon_meta)
                btn.clicked.connect(
                    lambda checked, m=icon_meta, lib=library_name: self.on_icon_clicked(lib, m)
                )
                self.icon_grid.addWidget(btn, row, col)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def clear_grid(self) -> None:
        """Clear all icons from the grid."""
        while self.icon_grid.count():
            item = self.icon_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def on_icon_clicked(self, library_name: str, metadata: IconMetadata) -> None:
        """Handle icon selection.

        Args:
            library_name: Name of the library
            metadata: Icon metadata
        """
        # Highlight selection (for now, just store it)
        self.selected_icon = (library_name, metadata)
        self.select_btn.setEnabled(True)

        # If icon not cached, download it
        if not metadata.file_path.exists():
            self.download_and_accept(library_name, metadata)
        else:
            # Icon is already cached, can select immediately
            pass

    def download_and_accept(self, library_name: str, metadata: IconMetadata) -> None:
        """Download icon and accept dialog.

        Args:
            library_name: Library name
            metadata: Icon metadata
        """
        # Show progress dialog
        progress = QProgressDialog("Downloading icon...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        # Create worker thread
        self.download_worker = IconDownloadWorker(
            self.manager, library_name, metadata.name, size=128
        )

        def on_finished(path: Path) -> None:
            progress.close()
            self.selected_icon = (library_name, metadata)
            self.accept()

        def on_error(error_msg: str) -> None:
            progress.close()
            QMessageBox.warning(self, "Download Error", f"Failed to download icon:\n{error_msg}")

        self.download_worker.finished.connect(on_finished)
        self.download_worker.error.connect(on_error)
        self.download_worker.start()

    def get_selected_icon(self) -> Optional[tuple[str, IconMetadata]]:
        """Get the selected icon.

        Returns:
            Tuple of (library_name, metadata) or None
        """
        return self.selected_icon

    def accept(self) -> None:
        """Accept the dialog and emit signal."""
        if self.selected_icon:
            library_name, metadata = self.selected_icon
            if metadata.file_path.exists():
                self.icon_selected.emit(library_name, metadata.file_path)
        super().accept()
