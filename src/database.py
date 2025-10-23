"""Database module for managing emoji-to-keyword mappings and session tracking."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


class EmojiDatabase:
    """Manages the SQLite database for emoji mappings and session tracking."""

    def __init__(self, db_path: str = "./emoji-cache/emojis.db"):
        """Initialize database connection and create tables if needed.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create all necessary database tables."""
        cursor = self.conn.cursor()

        # Emoji knowledge base
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS emojis (
                unicode TEXT PRIMARY KEY,
                common_name TEXT,
                keywords TEXT,
                context_words TEXT,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP
            )
        """
        )

        # Icon library metadata
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS icon_libraries (
                id INTEGER PRIMARY KEY,
                name TEXT,
                total_icons INTEGER,
                free_icons INTEGER,
                license TEXT,
                api_endpoint TEXT,
                last_updated TIMESTAMP
            )
        """
        )

        # User icon selections (learning)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS icon_mappings (
                id INTEGER PRIMARY KEY,
                emoji_unicode TEXT,
                library_name TEXT,
                icon_name TEXT,
                selection_count INTEGER DEFAULT 1,
                last_selected TIMESTAMP,
                FOREIGN KEY (emoji_unicode) REFERENCES emojis(unicode)
            )
        """
        )

        # Document session tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_sessions (
                id INTEGER PRIMARY KEY,
                document_path TEXT,
                session_start TIMESTAMP,
                session_end TIMESTAMP
            )
        """
        )

        # Icon usage within current document session
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_icon_usage (
                id INTEGER PRIMARY KEY,
                session_id INTEGER,
                emoji_unicode TEXT,
                icon_name TEXT,
                context_text TEXT,
                line_number INTEGER,
                is_replaced BOOLEAN DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES document_sessions(id)
            )
        """
        )

        self.conn.commit()

    def add_emoji(
        self, unicode: str, common_name: str, keywords: list[str], context_words: list[str] = None
    ) -> bool:
        """Add a new emoji to the database.

        Args:
            unicode: Unicode representation of emoji
            common_name: Common name for the emoji
            keywords: List of keywords associated with emoji
            context_words: Optional list of context words

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO emojis 
                (unicode, common_name, keywords, context_words, usage_count, last_used)
                VALUES (?, ?, ?, ?, 0, NULL)
            """,
                (
                    unicode,
                    common_name,
                    json.dumps(keywords),
                    json.dumps(context_words or []),
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding emoji: {e}")
            return False

    def search_emojis_by_keywords(self, search_terms: list[str], limit: int = 10) -> list[dict]:
        """Search for emojis matching any of the search terms.

        Args:
            search_terms: List of keywords to search for
            limit: Maximum number of results to return

        Returns:
            List of emoji dictionaries with match scores
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM emojis")
        rows = cursor.fetchall()

        results = []
        for row in rows:
            keywords = json.loads(row["keywords"])
            context_words = json.loads(row["context_words"] or "[]")
            all_terms = keywords + context_words

            # Calculate match score
            score = sum(
                1
                for term in search_terms
                for keyword in all_terms
                if term.lower() in keyword.lower()
            )

            if score > 0:
                results.append(
                    {
                        "unicode": row["unicode"],
                        "common_name": row["common_name"],
                        "keywords": keywords,
                        "context_words": context_words,
                        "usage_count": row["usage_count"],
                        "score": score,
                    }
                )

        # Sort by score (descending) and usage count
        results.sort(key=lambda x: (x["score"], x["usage_count"]), reverse=True)
        return results[:limit]

    def get_all_emojis(self) -> list[dict]:
        """Get all emojis from the database.

        Returns:
            List of all emoji dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM emojis ORDER BY usage_count DESC")
        rows = cursor.fetchall()

        return [
            {
                "unicode": row["unicode"],
                "common_name": row["common_name"],
                "keywords": json.loads(row["keywords"]),
                "context_words": json.loads(row["context_words"] or "[]"),
                "usage_count": row["usage_count"],
                "last_used": row["last_used"],
            }
            for row in rows
        ]

    def update_emoji_keywords(self, unicode: str, keywords: list[str]) -> bool:
        """Update keywords for an emoji.

        Args:
            unicode: Unicode representation of emoji
            keywords: New list of keywords

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE emojis SET keywords = ? WHERE unicode = ?", (json.dumps(keywords), unicode)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating emoji keywords: {e}")
            return False

    def delete_emoji(self, unicode: str) -> bool:
        """Delete an emoji from the database.

        Args:
            unicode: Unicode representation of emoji

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM emojis WHERE unicode = ?", (unicode,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting emoji: {e}")
            return False

    def increment_emoji_usage(self, unicode: str):
        """Increment usage count for an emoji.

        Args:
            unicode: Unicode representation of emoji
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE emojis 
            SET usage_count = usage_count + 1, last_used = ?
            WHERE unicode = ?
        """,
            (datetime.now().isoformat(), unicode),
        )
        self.conn.commit()

    def start_document_session(self, document_path: str) -> int:
        """Start a new document session for duplicate tracking.

        Args:
            document_path: Path to the document being edited

        Returns:
            Session ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO document_sessions (document_path, session_start)
            VALUES (?, ?)
        """,
            (document_path, datetime.now().isoformat()),
        )
        self.conn.commit()
        return cursor.lastrowid

    def end_document_session(self, session_id: int):
        """End a document session.

        Args:
            session_id: ID of the session to end
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE document_sessions 
            SET session_end = ?
            WHERE id = ?
        """,
            (datetime.now().isoformat(), session_id),
        )
        self.conn.commit()

    def record_icon_usage(
        self,
        session_id: int,
        emoji_unicode: str,
        icon_name: str,
        context_text: str,
        line_number: int,
    ):
        """Record icon usage in current session for duplicate detection.

        Args:
            session_id: Current document session ID
            emoji_unicode: Unicode of the emoji being replaced
            icon_name: Name of the icon selected
            context_text: Context text around the emoji
            line_number: Line number in document
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO session_icon_usage 
            (session_id, emoji_unicode, icon_name, context_text, line_number, is_replaced)
            VALUES (?, ?, ?, ?, ?, 1)
        """,
            (session_id, emoji_unicode, icon_name, context_text, line_number),
        )
        self.conn.commit()

    def get_session_icon_usages(self, session_id: int, icon_name: str = None) -> list[dict]:
        """Get all icon usages for a session, optionally filtered by icon name.

        Args:
            session_id: Document session ID
            icon_name: Optional icon name to filter by

        Returns:
            List of icon usage dictionaries
        """
        cursor = self.conn.cursor()
        if icon_name:
            cursor.execute(
                """
                SELECT * FROM session_icon_usage 
                WHERE session_id = ? AND icon_name = ?
            """,
                (session_id, icon_name),
            )
        else:
            cursor.execute("SELECT * FROM session_icon_usage WHERE session_id = ?", (session_id,))

        rows = cursor.fetchall()
        return [
            {
                "emoji_unicode": row["emoji_unicode"],
                "icon_name": row["icon_name"],
                "context_text": row["context_text"],
                "line_number": row["line_number"],
                "is_replaced": row["is_replaced"],
            }
            for row in rows
        ]

    def record_icon_selection(self, emoji_unicode: str, library_name: str, icon_name: str):
        """Record user's icon selection for learning.

        Args:
            emoji_unicode: Unicode of the emoji
            library_name: Name of icon library
            icon_name: Name of selected icon
        """
        cursor = self.conn.cursor()

        # Check if mapping already exists
        cursor.execute(
            """
            SELECT id, selection_count FROM icon_mappings
            WHERE emoji_unicode = ? AND library_name = ? AND icon_name = ?
        """,
            (emoji_unicode, library_name, icon_name),
        )
        row = cursor.fetchone()

        if row:
            # Increment count
            cursor.execute(
                """
                UPDATE icon_mappings
                SET selection_count = ?, last_selected = ?
                WHERE id = ?
            """,
                (row["selection_count"] + 1, datetime.now().isoformat(), row["id"]),
            )
        else:
            # Create new mapping
            cursor.execute(
                """
                INSERT INTO icon_mappings
                (emoji_unicode, library_name, icon_name, selection_count, last_selected)
                VALUES (?, ?, ?, 1, ?)
            """,
                (emoji_unicode, library_name, icon_name, datetime.now().isoformat()),
            )

        self.conn.commit()

    def get_popular_icon_for_emoji(self, emoji_unicode: str, library_name: str) -> str | None:
        """Get the most popular icon selection for an emoji in a library.

        Args:
            emoji_unicode: Unicode of the emoji
            library_name: Name of icon library

        Returns:
            Icon name or None if no history
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT icon_name FROM icon_mappings
            WHERE emoji_unicode = ? AND library_name = ?
            ORDER BY selection_count DESC, last_selected DESC
            LIMIT 1
        """,
            (emoji_unicode, library_name),
        )
        row = cursor.fetchone()
        return row["icon_name"] if row else None

    def clear_old_sessions(self, days: int = 30):
        """Clear document sessions older than specified days.

        Args:
            days: Number of days to keep
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

        cursor.execute(
            """
            DELETE FROM session_icon_usage 
            WHERE session_id IN (
                SELECT id FROM document_sessions 
                WHERE session_start < ?
            )
        """,
            (datetime.fromtimestamp(cutoff_date).isoformat(),),
        )

        cursor.execute(
            "DELETE FROM document_sessions WHERE session_start < ?",
            (datetime.fromtimestamp(cutoff_date).isoformat(),),
        )

        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
