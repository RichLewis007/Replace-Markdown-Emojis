"""Tests for GUI components using pytest-qt."""

import pytest

from src.gui.main_window import EmojiCard, MainWindow


@pytest.mark.gui
class TestEmojiCard:
    """Test cases for EmojiCard widget."""

    def test_emoji_card_creation(self, qt_app):
        """Test creating an EmojiCard widget."""
        card = EmojiCard("😊", "Hello world", 1)

        assert card.emoji == "😊"
        assert card.context == "Hello world"
        assert card.line_number == 1
        assert card.selected_icon is None

    def test_emoji_card_ui_elements(self, qt_app):
        """Test that UI elements are properly created."""
        card = EmojiCard("🚀", "Launch sequence", 5)

        # Check that the card is properly initialized
        assert card.isVisible() is False  # Not shown until parent is set
        assert card.emoji == "🚀"
        assert card.context == "Launch sequence"
        assert card.line_number == 5


@pytest.mark.gui
class TestMainWindow:
    """Test cases for MainWindow."""

    def test_main_window_creation(self, qt_app):
        """Test creating the main window."""
        window = MainWindow()

        assert window is not None
        assert window.windowTitle() == "Replace Markdown Emojis"

    def test_main_window_initialization(self, qt_app):
        """Test that the main window initializes properly."""
        window = MainWindow()

        # Check that the window has the expected properties
        assert window.isVisible() is False  # Not shown by default
        assert window.windowTitle() == "Replace Markdown Emojis"

    def test_file_dialog_integration(self, qt_app):
        """Test file dialog functionality."""
        window = MainWindow()

        # This would normally open a file dialog, but we can test the method exists
        assert hasattr(window, "open_file_dialog")
        assert callable(window.open_file_dialog)


@pytest.mark.gui
@pytest.mark.slow
class TestGUIIntegration:
    """Integration tests for GUI components."""

    def test_emoji_card_in_main_window(self, qt_app):
        """Test that EmojiCard works within MainWindow."""
        window = MainWindow()
        card = EmojiCard("🎉", "Celebration", 10, window)

        assert card.parent() == window
        assert card.emoji == "🎉"
        assert card.context == "Celebration"
        assert card.line_number == 10
