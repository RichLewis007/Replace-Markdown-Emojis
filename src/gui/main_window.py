"""Main application window."""

# Standard library
import contextlib
import sys
from pathlib import Path

# Third-party
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Local imports
from src.constants import (
    CONTEXT_PREVIEW_LENGTH,
    DEFAULT_ICON_SUGGESTIONS_LIMIT,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    EMOJI_FONT_SIZE,
    FRAME_LINE_WIDTH,
)
from src.database import EmojiDatabase
from src.emoji_detector import EmojiDetector, EmojiOccurrence
from src.exceptions import DatabaseError, FileOperationError
from src.file_operations import IconFileManager, MarkdownFileHandler
from src.initialize_emoji_db import initialize_database
from src.matcher import DuplicateDetectionManager, EmojiMatcher


class EmojiCard(QFrame):
    """Widget representing a detected emoji with its context."""

    def __init__(
        self, emoji: str, context: str, line_number: int, parent: QWidget | None = None
    ) -> None:
        """Initialize the emoji card widget.

        Args:
            emoji: The emoji character to display
            context: Context text around the emoji
            line_number: Line number where emoji was found
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.emoji = emoji
        self.context = context
        self.line_number = line_number
        self.selected_icon: str | None = None

        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the UI for the emoji card."""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(FRAME_LINE_WIDTH)

        layout = QVBoxLayout()

        # Emoji display (large)
        emoji_label = QLabel(self.emoji)
        emoji_font = QFont()
        emoji_font.setPointSize(EMOJI_FONT_SIZE)
        emoji_label.setFont(emoji_font)
        emoji_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(emoji_label)

        # Context
        context_label = QLabel(f"Context: {self.context[:CONTEXT_PREVIEW_LENGTH]}...")
        context_label.setWordWrap(True)
        context_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(context_label)

        # Line number
        line_label = QLabel(f"Line: {self.line_number}")
        line_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(line_label)

        # Selected icon display
        self.icon_label = QLabel("No icon selected")
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        # Select button
        self.select_btn = QPushButton("Select Icon")
        self.select_btn.clicked.connect(self.on_select_clicked)
        layout.addWidget(self.select_btn)

        self.setLayout(layout)

    def on_select_clicked(self) -> None:
        """Handle select button click."""
        # Emit signal or call parent method
        if self.parent():
            parent = self.parent()
            while parent and not isinstance(parent, MainWindow):
                parent = parent.parent()
            if parent and isinstance(parent, MainWindow):
                parent.show_icon_selector(self)

    def set_selected_icon(self, icon_name: str) -> None:
        """Set the selected icon for this emoji.

        Args:
            icon_name: Name of the selected icon
        """
        self.selected_icon = icon_name
        self.icon_label.setText(f"Selected: {icon_name}")
        self.select_btn.setText("Change Icon")


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        """Initialize the main application window.

        Sets up the UI, initializes database connection, and prepares
        the application for use.
        """
        super().__init__()
        self.setWindowTitle("Replace Markdown Emojis")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        # Initialize components
        self.db: EmojiDatabase | None = None
        self.detector = EmojiDetector()
        self.matcher: EmojiMatcher | None = None
        self.duplicate_manager: DuplicateDetectionManager | None = None
        self.file_handler = MarkdownFileHandler()
        self.icon_manager = IconFileManager()

        # Current state
        self.current_file: str | None = None
        self.emoji_occurrences: list[EmojiOccurrence] = []
        self.emoji_cards: dict[str, EmojiCard] = {}

        # Initialize database
        self.initialize_database()

        # Set up UI
        self.setup_ui()
        self.create_menus()

    def initialize_database(self) -> None:
        """Initialize the emoji database."""
        self.db = None
        try:
            from src.constants import CACHE_DIR_NAME, DB_FILENAME  # noqa: PLC0415

            # Use local cache directory (fallback to current directory for compatibility)
            cache_dir = Path(CACHE_DIR_NAME)
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(cache_dir / DB_FILENAME)
            db_file = Path(db_path)

            # Initialize database if it doesn't exist
            if not db_file.exists():
                QMessageBox.information(
                    self,
                    "First Run",
                    "Initializing emoji database with 200+ entries. This may take a moment...",
                )
                initialize_database(db_path)

            # Connect to database
            self.db = EmojiDatabase(db_path)
            self.matcher = EmojiMatcher(self.db)
            self.duplicate_manager = DuplicateDetectionManager(self.db, self.matcher)

        except DatabaseError as e:
            if self.db:
                self.db.close()
                self.db = None
            QMessageBox.critical(
                self,
                "Database Error",
                f"Database initialization failed: {e}\n\nDetails: {e.details or 'No additional details available'}",
            )
            sys.exit(1)
        except Exception as e:
            if self.db:
                self.db.close()
                self.db = None
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"Unexpected error during initialization: {e}",
            )
            sys.exit(1)

    def setup_ui(self) -> None:
        """Set up the main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        self.open_btn = QPushButton("📂 Open Markdown File")
        self.open_btn.clicked.connect(self.open_file)
        toolbar_layout.addWidget(self.open_btn)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)
        toolbar_layout.addWidget(self.save_btn)

        self.replace_all_btn = QPushButton("🔄 Replace All")
        self.replace_all_btn.clicked.connect(self.replace_all)
        self.replace_all_btn.setEnabled(False)
        toolbar_layout.addWidget(self.replace_all_btn)

        toolbar_layout.addStretch()

        self.file_label = QLabel("No file loaded")
        toolbar_layout.addWidget(self.file_label)

        main_layout.addLayout(toolbar_layout)

        # Emoji panel (top)
        emoji_group = QGroupBox("Detected Emojis")
        emoji_layout = QVBoxLayout()

        # Scroll area for emoji cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(250)

        self.emoji_container = QWidget()
        self.emoji_grid = QGridLayout(self.emoji_container)
        scroll.setWidget(self.emoji_container)

        emoji_layout.addWidget(scroll)
        emoji_group.setLayout(emoji_layout)
        main_layout.addWidget(emoji_group)

        # Document preview
        preview_group = QGroupBox("Document Preview")
        preview_layout = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)

        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # Status bar
        self.statusBar().showMessage("Ready")

    def create_menus(self) -> None:
        """Create application menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        db_editor_action = QAction("Manage Emoji &Database", self)
        db_editor_action.triggered.connect(self.show_database_editor)
        tools_menu.addAction(db_editor_action)

        clear_cache_action = QAction("&Clear Cache", self)
        clear_cache_action.triggered.connect(self.clear_cache)
        tools_menu.addAction(clear_cache_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def open_file(self) -> None:
        """Open a markdown file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Markdown File", "", "Markdown Files (*.md);;All Files (*)"
        )

        if file_path:
            try:
                # Load file
                content = self.file_handler.load_file(file_path)
                self.current_file = file_path

                # Update UI
                self.file_label.setText(Path(file_path).name)
                self.preview_text.setPlainText(content)
                self.save_btn.setEnabled(False)
                self.replace_all_btn.setEnabled(False)

                # Detect emojis
                self.detect_emojis(content)

                # Start duplicate detection session
                if self.duplicate_manager:
                    self.duplicate_manager.start_session(file_path)

                self.statusBar().showMessage(f"Loaded: {file_path}")

            except FileOperationError as e:
                QMessageBox.critical(
                    self,
                    "File Error",
                    f"Failed to open file: {e}\n\nFile: {e.file_path or 'Unknown'}\nDetails: {e.details or 'No additional details'}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Unexpected Error",
                    f"Unexpected error opening file: {e}",
                )

    def detect_emojis(self, content: str) -> None:
        """Detect emojis in the content and display them.

        Args:
            content: Markdown content
        """
        # Clear existing emoji cards
        for i in reversed(range(self.emoji_grid.count())):
            item = self.emoji_grid.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        self.emoji_cards.clear()

        # Detect emojis
        self.emoji_occurrences = self.detector.detect_emojis_in_text(content)

        if not self.emoji_occurrences:
            label = QLabel("No emojis detected in this document.")
            label.setAlignment(Qt.AlignCenter)
            self.emoji_grid.addWidget(label, 0, 0)
            return

        # Create emoji cards
        unique_emojis = self.detector.get_unique_emojis(self.emoji_occurrences)

        for idx, emoji_char in enumerate(unique_emojis):
            # Get first occurrence for context
            occurrences = [occ for occ in self.emoji_occurrences if occ.emoji == emoji_char]
            first_occ = occurrences[0]

            # Create card
            context = self.detector.get_context_summary(first_occ)
            card = EmojiCard(emoji_char, context, first_occ.line_number, self.emoji_container)

            row = idx // 4
            col = idx % 4
            self.emoji_grid.addWidget(card, row, col)

            self.emoji_cards[emoji_char] = card

        self.statusBar().showMessage(
            f"Detected {len(unique_emojis)} unique emojis in {len(self.emoji_occurrences)} locations"
        )

    def show_icon_selector(self, emoji_card: EmojiCard) -> None:
        """Show icon selector for an emoji card.

        Args:
            emoji_card: The EmojiCard that was clicked
        """
        # For now, use a simple input dialog
        # In full implementation, this would show a grid of icon suggestions
        from PySide6.QtWidgets import QInputDialog  # noqa: PLC0415

        # Get suggestions from matcher
        occurrences = [occ for occ in self.emoji_occurrences if occ.emoji == emoji_card.emoji]
        if not occurrences:
            return

        first_occ = occurrences[0]
        if self.matcher is None:
            return
        suggestions = self.matcher.find_icon_suggestions(
            first_occ, limit=DEFAULT_ICON_SUGGESTIONS_LIMIT
        )

        if not suggestions:
            QMessageBox.information(
                self, "No Suggestions", "No icon suggestions found for this emoji."
            )
            return

        # Create list of icon names
        icon_names = [s.icon_name for s in suggestions]

        # Show selection dialog
        icon_name, ok = QInputDialog.getItem(
            self,
            "Select Icon",
            f"Choose an icon to replace {emoji_card.emoji}:",
            icon_names,
            0,
            False,
        )

        if ok and icon_name:
            # Check for duplicates
            if self.duplicate_manager:
                warning = self.duplicate_manager.check_for_duplicates(icon_name, first_occ)
                if warning:
                    msg = f"Warning: This icon is already used at line {warning.existing_line}.\n\n"
                    msg += f"Existing context: {warning.existing_context}\n"
                    msg += f"Current context: {warning.current_context}\n\n"
                    msg += f"Similarity: {warning.similarity_score}%\n\n"
                    msg += "Do you want to use it anyway?"

                    reply = QMessageBox.question(
                        self, "Duplicate Icon Usage", msg, QMessageBox.Yes | QMessageBox.No
                    )

                    if reply == QMessageBox.No:
                        return

            # Set selected icon
            emoji_card.set_selected_icon(icon_name)
            self.replace_all_btn.setEnabled(True)
            self.statusBar().showMessage(f"Selected '{icon_name}' for {emoji_card.emoji}")

    def replace_all(self) -> None:
        """Replace all emojis with selected icons."""
        if not self.current_file:
            return

        # Check if all emojis have icons selected
        unselected = [emoji for emoji, card in self.emoji_cards.items() if not card.selected_icon]

        if unselected:
            msg = f"{len(unselected)} emoji(s) don't have icons selected. Replace anyway?"
            reply = QMessageBox.question(
                self, "Incomplete Selection", msg, QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # Perform replacements
        count = 0
        for emoji_char, card in self.emoji_cards.items():
            if card.selected_icon:
                # Get relative icon path
                icon_path = self.icon_manager.get_relative_icon_path(
                    card.selected_icon, self.current_file
                )

                # Replace in file handler
                replaced = self.file_handler.replace_emoji_with_icon(
                    emoji_char, icon_path, card.selected_icon
                )
                count += replaced

                # Record in database
                if self.duplicate_manager:
                    occurrences = [occ for occ in self.emoji_occurrences if occ.emoji == emoji_char]
                    for occ in occurrences:
                        self.duplicate_manager.record_replacement(
                            emoji_char, card.selected_icon, occ
                        )

                # Record selection for learning
                if self.db:
                    self.db.record_icon_selection(emoji_char, "default", card.selected_icon)
                    self.db.increment_emoji_usage(emoji_char)

        # Update preview
        self.preview_text.setPlainText(self.file_handler.get_current_content())
        self.save_btn.setEnabled(True)

        QMessageBox.information(self, "Success", f"Replaced {count} emoji occurrences with icons!")
        self.statusBar().showMessage(f"Replaced {count} emojis")

    def save_file(self) -> None:
        """Save the modified file."""
        if not self.current_file:
            return

        try:
            self.file_handler.save_file(create_backup=True)
            self.save_btn.setEnabled(False)
            QMessageBox.information(
                self,
                "Success",
                f"File saved successfully!\nBackup created: {self.current_file}.bak",
            )
            self.statusBar().showMessage("File saved with backup")
        except FileOperationError as e:
            QMessageBox.critical(
                self,
                "File Error",
                f"Failed to save file: {e}\n\nFile: {e.file_path or 'Unknown'}\nDetails: {e.details or 'No additional details'}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"Unexpected error saving file: {e}",
            )

    def show_database_editor(self) -> None:
        """Show the database editor dialog."""
        from gui.database_editor import DatabaseEditorDialog  # noqa: PLC0415

        dialog = DatabaseEditorDialog(self.db, self)
        dialog.exec()

    def clear_cache(self) -> None:
        """Clear the icon cache."""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "This will clear all cached icon data. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Clear old sessions
            if self.db:
                self.db.clear_old_sessions(days=0)
            QMessageBox.information(self, "Success", "Cache cleared successfully!")

    def show_about(self) -> None:
        """Show the about dialog with application information.

        Displays version, features, and credits in a formatted message box.
        """
        from src import __version__  # noqa: PLC0415

        about_text = f"""
        <h2>Replace Markdown Emojis</h2>
        <p>Version {__version__}</p>
        <p>A tool to replace Unicode emojis in markdown files with professional icons.</p>
        <p><b>Features:</b></p>
        <ul>
            <li>2000+ pre-populated emoji-keyword mappings</li>
            <li>Smart emoji-to-icon matching</li>
            <li>Duplicate detection</li>
            <li>Learning system</li>
            <li>Database editor</li>
        </ul>
        <p>Built with Python and PySide6</p>
        """
        QMessageBox.about(self, "About", about_text)

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        """Handle window close event.

        Args:
            event: Close event from Qt
        """
        if self.file_handler.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )

            if reply == QMessageBox.Save:
                self.save_file()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

        # Cleanup
        if self.duplicate_manager and self.duplicate_manager.current_session_id:
            self.duplicate_manager.end_session()

        if self.db:
            self.db.close()

    def __del__(self) -> None:
        """Cleanup when object is destroyed."""
        # Ensure database is closed even if closeEvent wasn't called
        if hasattr(self, "db") and self.db:
            with contextlib.suppress(Exception):
                self.db.close()
