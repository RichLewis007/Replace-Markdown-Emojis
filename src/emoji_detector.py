"""Emoji detection and context extraction module."""

# Standard library
import re
from dataclasses import dataclass

# Third-party
import emoji as emoji_lib

# Local imports
from src.constants import (
    CONTEXT_AFTER_MAX_CHARS,
    CONTEXT_AFTER_PREVIEW_LENGTH,
    CONTEXT_BEFORE_MAX_CHARS,
    CONTEXT_BEFORE_PREVIEW_LENGTH,
    MIN_KEYWORD_LENGTH,
)


@dataclass
class EmojiOccurrence:
    """Represents an emoji found in a document."""

    emoji: str
    line_number: int
    char_position: int
    context_before: str
    context_after: str
    full_line: str
    is_in_heading: bool
    heading_level: int = 0


class EmojiDetector:
    """Detects and extracts emojis from markdown documents with context."""

    def __init__(self) -> None:
        """Initialize the emoji detector."""
        self.heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)

    def detect_emojis_in_text(self, text: str) -> list[EmojiOccurrence]:
        """Detect all emojis in text with their context.

        Args:
            text: The markdown text to search

        Returns:
            List of EmojiOccurrence objects
        """
        occurrences = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, start=1):
            # Check if line is a heading
            heading_match = self.heading_pattern.match(line)
            is_heading = heading_match is not None
            heading_level = len(heading_match.group(1)) if heading_match is not None else 0

            # Find all emojis in the line
            for match in emoji_lib.emoji_list(line):
                emoji_char = match["emoji"]
                char_pos = match["match_start"]

                # Extract context (word boundaries preferred, fallback to character limits)
                context_before = self._extract_context_before(line, char_pos)
                context_after = self._extract_context_after(line, char_pos + len(emoji_char))

                occurrence = EmojiOccurrence(
                    emoji=emoji_char,
                    line_number=line_num,
                    char_position=char_pos,
                    context_before=context_before,
                    context_after=context_after,
                    full_line=line,
                    is_in_heading=is_heading,
                    heading_level=heading_level,
                )
                occurrences.append(occurrence)

        return occurrences

    def _extract_context_before(
        self, line: str, position: int, max_chars: int = CONTEXT_BEFORE_MAX_CHARS
    ) -> str:
        """Extract context before an emoji.

        Args:
            line: The full line text
            position: Position of the emoji
            max_chars: Maximum characters to extract

        Returns:
            Context string before the emoji
        """
        start = max(0, position - max_chars)
        context = line[start:position].strip()
        return context

    def _extract_context_after(
        self, line: str, position: int, max_chars: int = CONTEXT_AFTER_MAX_CHARS
    ) -> str:
        """Extract context after an emoji.

        Args:
            line: The full line text
            position: Position after the emoji
            max_chars: Maximum characters to extract

        Returns:
            Context string after the emoji
        """
        end = min(len(line), position + max_chars)
        context = line[position:end].strip()
        return context

    def extract_keywords_from_context(self, occurrence: EmojiOccurrence) -> list[str]:
        """Extract keywords from emoji context for matching.

        Args:
            occurrence: EmojiOccurrence object

        Returns:
            List of keywords extracted from context
        """
        keywords = []

        # If in heading, use the heading text (without heading markers and emoji)
        if occurrence.is_in_heading:
            # Remove heading markers and emojis
            heading_text = occurrence.full_line
            heading_text = re.sub(r"^#{1,6}\s+", "", heading_text)
            heading_text = self._remove_emojis(heading_text)
            heading_text = heading_text.strip()

            # Extract words from heading
            words = re.findall(r"\b\w+\b", heading_text.lower())
            keywords.extend(words)
        else:
            # Use context before and after
            context = occurrence.context_before + " " + occurrence.context_after
            context = self._remove_emojis(context)
            words = re.findall(r"\b\w+\b", context.lower())
            keywords.extend(words)

        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "be",
            "this",
            "that",
        }
        keywords = [k for k in keywords if k not in stop_words and len(k) > MIN_KEYWORD_LENGTH]

        return keywords

    def _remove_emojis(self, text: str) -> str:
        """Remove all emojis from text.

        Args:
            text: Text to clean

        Returns:
            Text with emojis removed
        """
        result = emoji_lib.replace_emoji(text, "")
        return str(result)

    def get_unique_emojis(self, occurrences: list[EmojiOccurrence]) -> list[str]:
        """Get list of unique emojis from occurrences.

        Args:
            occurrences: List of EmojiOccurrence objects

        Returns:
            List of unique emoji characters
        """
        unique = []
        seen = set()
        for occ in occurrences:
            if occ.emoji not in seen:
                unique.append(occ.emoji)
                seen.add(occ.emoji)
        return unique

    def group_occurrences_by_emoji(
        self, occurrences: list[EmojiOccurrence]
    ) -> dict[str, list[EmojiOccurrence]]:
        """Group occurrences by emoji character.

        Args:
            occurrences: List of EmojiOccurrence objects

        Returns:
            Dictionary mapping emoji to list of occurrences
        """
        grouped: dict[str, list[EmojiOccurrence]] = {}
        for occ in occurrences:
            if occ.emoji not in grouped:
                grouped[occ.emoji] = []
            grouped[occ.emoji].append(occ)
        return grouped

    def get_context_summary(self, occurrence: EmojiOccurrence) -> str:
        """Get a human-readable context summary for display.

        Args:
            occurrence: EmojiOccurrence object

        Returns:
            Context summary string
        """
        if occurrence.is_in_heading:
            # Extract heading text without markers
            heading_text = re.sub(r"^#{1,6}\s+", "", occurrence.full_line)
            return f"Heading: {heading_text.strip()}"
        else:
            # Show surrounding context
            before = (
                occurrence.context_before[-CONTEXT_BEFORE_PREVIEW_LENGTH:]
                if occurrence.context_before
                else ""
            )
            after = (
                occurrence.context_after[:CONTEXT_AFTER_PREVIEW_LENGTH]
                if occurrence.context_after
                else ""
            )
            return f"{before} {occurrence.emoji} {after}".strip()

    def normalize_context_for_comparison(self, context: str) -> str:
        """Normalize context text for duplicate detection comparison.

        Args:
            context: Context text to normalize

        Returns:
            Normalized context text
        """
        # Remove emojis
        context = self._remove_emojis(context)
        # Remove markdown formatting
        context = re.sub(r"[*_`~#\[\]()]", "", context)
        # Convert to lowercase
        context = context.lower()
        # Remove extra whitespace
        context = " ".join(context.split())
        # Remove punctuation
        context = re.sub(r"[^\w\s]", "", context)
        return context.strip()
