"""Pytest configuration and fixtures."""

from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication


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
