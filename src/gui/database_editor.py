"""Database editor dialog for managing emoji mappings."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QLabel,
    QMessageBox,
    QInputDialog,
    QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import json

from database import EmojiDatabase


class DatabaseEditorDialog(QDialog):
    """Dialog for viewing and editing the emoji database."""

    def __init__(self, db: EmojiDatabase, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Manage Emoji Database")
        self.resize(1000, 600)

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search emojis, names, or keywords...")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ Add New")
        self.add_btn.clicked.connect(self.add_emoji)
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_emoji)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_emoji)
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_data)
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addLayout(toolbar_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Emoji", "Unicode", "Common Name", "Keywords", "Usage Count"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Info label
        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        # Button box
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def load_data(self):
        """Load data from database and populate table."""
        emojis = self.db.get_all_emojis()

        self.table.setRowCount(len(emojis))

        for row, emoji_data in enumerate(emojis):
            # Emoji (with larger font)
            emoji_item = QTableWidgetItem(emoji_data["unicode"])
            emoji_font = QFont()
            emoji_font.setPointSize(20)
            emoji_item.setFont(emoji_font)
            emoji_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, emoji_item)

            # Unicode code point
            unicode_val = emoji_data["unicode"].encode("unicode-escape").decode("ascii")
            self.table.setItem(row, 1, QTableWidgetItem(unicode_val))

            # Common name
            self.table.setItem(row, 2, QTableWidgetItem(emoji_data["common_name"]))

            # Keywords (truncated)
            keywords = ", ".join(emoji_data["keywords"][:5])
            if len(emoji_data["keywords"]) > 5:
                keywords += "..."
            self.table.setItem(row, 3, QTableWidgetItem(keywords))

            # Usage count
            usage_item = QTableWidgetItem(str(emoji_data["usage_count"]))
            usage_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, usage_item)

        self.info_label.setText(f"Total: {len(emojis)} emojis")

    def filter_table(self):
        """Filter table based on search input."""
        search_text = self.search_input.text().lower()

        for row in range(self.table.rowCount()):
            match = False

            # Check each column for match
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break

            self.table.setRowHidden(row, not match)

    def add_emoji(self):
        """Add a new emoji to the database."""
        # Get emoji
        emoji, ok = QInputDialog.getText(self, "Add Emoji", "Enter emoji character:")
        if not ok or not emoji:
            return

        # Get common name
        name, ok = QInputDialog.getText(self, "Add Emoji", "Enter common name:")
        if not ok or not name:
            return

        # Get keywords
        keywords_text, ok = QInputDialog.getText(
            self, "Add Emoji", "Enter keywords (comma-separated):"
        )
        if not ok or not keywords_text:
            return

        keywords = [k.strip() for k in keywords_text.split(",")]

        # Add to database
        if self.db.add_emoji(emoji, name, keywords):
            QMessageBox.information(self, "Success", "Emoji added successfully!")
            self.load_data()
        else:
            QMessageBox.critical(self, "Error", "Failed to add emoji.")

    def edit_emoji(self):
        """Edit selected emoji."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an emoji to edit.")
            return

        # Get current data
        emoji = self.table.item(current_row, 0).text()
        current_name = self.table.item(current_row, 2).text()

        # Get all emoji data
        emojis = self.db.get_all_emojis()
        emoji_data = next((e for e in emojis if e["unicode"] == emoji), None)

        if not emoji_data:
            return

        # Edit keywords
        current_keywords = ", ".join(emoji_data["keywords"])
        keywords_text, ok = QInputDialog.getText(
            self,
            "Edit Keywords",
            f"Edit keywords for {emoji} ({current_name}):",
            text=current_keywords,
        )

        if ok and keywords_text:
            keywords = [k.strip() for k in keywords_text.split(",")]
            if self.db.update_emoji_keywords(emoji, keywords):
                QMessageBox.information(self, "Success", "Keywords updated successfully!")
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", "Failed to update keywords.")

    def delete_emoji(self):
        """Delete selected emoji."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an emoji to delete.")
            return

        emoji = self.table.item(current_row, 0).text()
        name = self.table.item(current_row, 2).text()

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {emoji} ({name})?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.db.delete_emoji(emoji):
                QMessageBox.information(self, "Success", "Emoji deleted successfully!")
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete emoji.")

