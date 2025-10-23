"""Tests for the EmojiDetector class."""

from src.emoji_detector import EmojiDetector, EmojiOccurrence


class TestEmojiDetector:
    """Test cases for EmojiDetector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = EmojiDetector()

    def test_detect_emojis_basic(self):
        """Test basic emoji detection."""
        text = "Hello 😊 world!"
        results = self.detector.detect_emojis_in_text(text)

        assert len(results) == 1
        assert results[0].emoji == "😊"
        assert results[0].line_number == 1
        assert results[0].char_position == 6

    def test_detect_emojis_multiple(self):
        """Test detection of multiple emojis."""
        text = "🚀 Launch 🎉 Party 🎊"
        results = self.detector.detect_emojis_in_text(text)

        assert len(results) == 3
        assert results[0].emoji == "🚀"
        assert results[1].emoji == "🎉"
        assert results[2].emoji == "🎊"

    def test_detect_emojis_in_heading(self):
        """Test emoji detection in markdown headings."""
        text = "# Main Title 🚀\n## Subtitle 📝"
        results = self.detector.detect_emojis_in_text(text)

        assert len(results) == 2
        assert results[0].is_in_heading is True
        assert results[0].heading_level == 1
        assert results[1].is_in_heading is True
        assert results[1].heading_level == 2

    def test_context_extraction(self):
        """Test context extraction around emojis."""
        text = "Before 😊 after"
        results = self.detector.detect_emojis_in_text(text)

        assert len(results) == 1
        assert "Before" in results[0].context_before
        assert "after" in results[0].context_after

    def test_no_emojis(self):
        """Test text with no emojis."""
        text = "No emojis here"
        results = self.detector.detect_emojis_in_text(text)

        assert len(results) == 0

    def test_empty_text(self):
        """Test empty text."""
        results = self.detector.detect_emojis_in_text("")
        assert len(results) == 0

    def test_emoji_occurrence_dataclass(self):
        """Test EmojiOccurrence dataclass."""
        occurrence = EmojiOccurrence(
            emoji="😊",
            line_number=1,
            char_position=5,
            context_before="Hello",
            context_after="world",
            full_line="Hello 😊 world",
            is_in_heading=False,
        )

        assert occurrence.emoji == "😊"
        assert occurrence.line_number == 1
        assert occurrence.char_position == 5
        assert occurrence.is_in_heading is False
