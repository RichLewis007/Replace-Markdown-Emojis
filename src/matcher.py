"""Emoji-to-icon matching algorithm with fuzzy matching and duplicate detection."""

# Standard library
from dataclasses import dataclass

# Third-party
from fuzzywuzzy import fuzz

# Local imports
from database import EmojiDatabase
from emoji_detector import EmojiDetector, EmojiOccurrence


@dataclass
class IconSuggestion:
    """Represents a suggested icon replacement for an emoji."""

    icon_name: str
    emoji_unicode: str
    match_score: int
    source: str  # "database", "learned", "popular"
    keywords_matched: list[str]


@dataclass
class DuplicateWarning:
    """Warning about duplicate icon usage with different contexts."""

    icon_name: str
    current_context: str
    current_line: int
    existing_context: str
    existing_line: int
    similarity_score: int
    is_critical: bool  # True if contexts are very different


class EmojiMatcher:
    """Matches emojis to icons based on keywords and context."""

    def __init__(self, db: EmojiDatabase):
        """Initialize the matcher.

        Args:
            db: EmojiDatabase instance
        """
        self.db = db
        self.detector = EmojiDetector()
        self.similarity_threshold = 50  # Configurable threshold for duplicate detection

    def find_icon_suggestions(
        self, occurrence: EmojiOccurrence, library_name: str = None, limit: int = 10
    ) -> list[IconSuggestion]:
        """Find icon suggestions for an emoji occurrence.

        Args:
            occurrence: EmojiOccurrence object
            library_name: Optional icon library name for learning
            limit: Maximum number of suggestions

        Returns:
            List of IconSuggestion objects sorted by relevance
        """
        suggestions = []

        # Extract keywords from context
        context_keywords = self.detector.extract_keywords_from_context(occurrence)

        # Get emoji from database
        emojis = self.db.search_emojis_by_keywords(
            context_keywords + [occurrence.emoji], limit=limit * 2
        )

        for emoji_data in emojis:
            # Calculate match score
            keywords_matched = []
            score = 0

            for keyword in emoji_data["keywords"]:
                for context_kw in context_keywords:
                    if (
                        context_kw.lower() in keyword.lower()
                        or keyword.lower() in context_kw.lower()
                    ):
                        keywords_matched.append(keyword)
                        score += 1

            # Add score for exact emoji match
            if emoji_data["unicode"] == occurrence.emoji:
                score += 10

            # Add score for usage count (popular emojis)
            score += min(emoji_data["usage_count"] // 10, 5)

            if score > 0:
                # Use common name as icon name (in real app, would fetch from icon library)
                suggestion = IconSuggestion(
                    icon_name=emoji_data["common_name"],
                    emoji_unicode=emoji_data["unicode"],
                    match_score=score,
                    source="database",
                    keywords_matched=keywords_matched,
                )
                suggestions.append(suggestion)

        # Check for learned preferences
        if library_name:
            popular_icon = self.db.get_popular_icon_for_emoji(occurrence.emoji, library_name)
            if popular_icon:
                # Boost learned icon to top of list
                learned_suggestion = IconSuggestion(
                    icon_name=popular_icon,
                    emoji_unicode=occurrence.emoji,
                    match_score=1000,  # Very high score
                    source="learned",
                    keywords_matched=["user_preference"],
                )
                suggestions.insert(0, learned_suggestion)

        # Sort by score and remove duplicates
        suggestions.sort(key=lambda x: x.match_score, reverse=True)

        # Remove duplicate icon names, keep highest scored
        seen_icons = set()
        unique_suggestions = []
        for sugg in suggestions:
            if sugg.icon_name not in seen_icons:
                unique_suggestions.append(sugg)
                seen_icons.add(sugg.icon_name)

        return unique_suggestions[:limit]

    def check_duplicate_usage(
        self, session_id: int, icon_name: str, occurrence: EmojiOccurrence
    ) -> DuplicateWarning | None:
        """Check if icon is already used in session with different context.

        Args:
            session_id: Document session ID
            icon_name: Name of the icon being considered
            occurrence: Current EmojiOccurrence

        Returns:
            DuplicateWarning if duplicate detected, None otherwise
        """
        # Get all usages of this icon in session
        existing_usages = self.db.get_session_icon_usages(session_id, icon_name)

        if not existing_usages:
            return None

        # Get context for current occurrence
        current_context = self.detector.get_context_summary(occurrence)
        normalized_current = self.detector.normalize_context_for_comparison(current_context)

        # Check each existing usage
        for usage in existing_usages:
            existing_context = usage["context_text"]
            normalized_existing = self.detector.normalize_context_for_comparison(existing_context)

            # Calculate similarity using fuzzy matching
            similarity = fuzz.ratio(normalized_current, normalized_existing)

            # If contexts are different enough, warn user
            if similarity < self.similarity_threshold:
                is_critical = similarity < 30  # Very different contexts

                return DuplicateWarning(
                    icon_name=icon_name,
                    current_context=current_context,
                    current_line=occurrence.line_number,
                    existing_context=existing_context,
                    existing_line=usage["line_number"],
                    similarity_score=similarity,
                    is_critical=is_critical,
                )

        return None

    def set_similarity_threshold(self, threshold: int):
        """Set the similarity threshold for duplicate detection.

        Args:
            threshold: Percentage threshold (0-100)
        """
        self.similarity_threshold = max(0, min(100, threshold))

    def get_match_explanation(self, suggestion: IconSuggestion) -> str:
        """Get human-readable explanation for why icon was suggested.

        Args:
            suggestion: IconSuggestion object

        Returns:
            Explanation string
        """
        if suggestion.source == "learned":
            return "Your previous choice for this emoji"
        elif suggestion.source == "popular":
            return f"Popular choice (used {suggestion.match_score} times)"
        elif suggestion.keywords_matched:
            keywords = ", ".join(suggestion.keywords_matched[:3])
            return f"Matches: {keywords}"
        else:
            return "Suggested by emoji match"


class DuplicateDetectionManager:
    """Manages duplicate detection across document session."""

    def __init__(self, db: EmojiDatabase, matcher: EmojiMatcher):
        """Initialize duplicate detection manager.

        Args:
            db: EmojiDatabase instance
            matcher: EmojiMatcher instance
        """
        self.db = db
        self.matcher = matcher
        self.current_session_id = None

    def start_session(self, document_path: str) -> int:
        """Start a new document session.

        Args:
            document_path: Path to the document

        Returns:
            Session ID
        """
        self.current_session_id = self.db.start_document_session(document_path)
        return self.current_session_id

    def end_session(self):
        """End the current document session."""
        if self.current_session_id:
            self.db.end_document_session(self.current_session_id)
            self.current_session_id = None

    def record_replacement(self, emoji_unicode: str, icon_name: str, occurrence: EmojiOccurrence):
        """Record an icon replacement in the current session.

        Args:
            emoji_unicode: Unicode of the emoji being replaced
            icon_name: Name of the selected icon
            occurrence: EmojiOccurrence object
        """
        if not self.current_session_id:
            raise ValueError("No active session")

        context = self.matcher.detector.get_context_summary(occurrence)
        self.db.record_icon_usage(
            self.current_session_id,
            emoji_unicode,
            icon_name,
            context,
            occurrence.line_number,
        )

    def check_for_duplicates(
        self, icon_name: str, occurrence: EmojiOccurrence
    ) -> DuplicateWarning | None:
        """Check for duplicate icon usage.

        Args:
            icon_name: Name of the icon being considered
            occurrence: EmojiOccurrence object

        Returns:
            DuplicateWarning if duplicate detected, None otherwise
        """
        if not self.current_session_id:
            return None

        return self.matcher.check_duplicate_usage(self.current_session_id, icon_name, occurrence)

    def get_all_replacements(self) -> list[dict]:
        """Get all replacements made in current session.

        Returns:
            List of replacement dictionaries
        """
        if not self.current_session_id:
            return []

        return self.db.get_session_icon_usages(self.current_session_id)
