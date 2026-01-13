"""Pytest configuration and fixtures."""

import gc
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


@pytest.fixture(scope="session")
def qt_app():
    """Create a QApplication for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Cleanup is handled by pytest-qt


@pytest.fixture
def sample_markdown_text():
    """Sample markdown text with emojis for testing."""
    return """# Test Document 🚀

This is a test document with various emojis:
- Happy face 😊
- Thumbs up 👍
- Heart ❤️
- Star ⭐

## Another Section 📝

More emojis here:
- Fire 🔥
- Lightning ⚡
- Check mark ✅
"""


@pytest.fixture
def temp_markdown_file(tmp_path, sample_markdown_text):
    """Create a temporary markdown file for testing."""
    test_file = tmp_path / "test.md"
    test_file.write_text(sample_markdown_text)
    return test_file


@pytest.fixture
def mock_database():
    """Create a mock database for testing."""
    mock_db = Mock()
    mock_db.get_emoji_mappings.return_value = {
        "🚀": ["rocket", "launch", "space"],
        "😊": ["happy", "smile", "joy"],
        "👍": ["thumbs", "up", "good"],
        "❤️": ["heart", "love", "red"],
        "⭐": ["star", "favorite", "rating"],
    }
    return mock_db


@pytest.fixture(autouse=True)
def cleanup_databases():
    """Automatically close database connections after each test."""
    yield
    # Force garbage collection to close any remaining database connections
    gc.collect()


@pytest.fixture
def main_window(qt_app):  # noqa: ARG001
    """Create a MainWindow instance that's properly cleaned up.

    Args:
        qt_app: QApplication fixture (required for MainWindow initialization)
    """
    window = MainWindow()
    yield window
    # Ensure database is closed when test finishes
    if window.db:
        window.db.close()
