"""File operations for reading, writing, and modifying markdown files."""

import shutil
from pathlib import Path

from src.exceptions import FileBackupError, FileOperationError, FileReadError, FileWriteError


class MarkdownFileHandler:
    """Handles markdown file operations including backup and replacement."""

    def __init__(self):
        """Initialize the file handler."""
        self.current_file = None
        self.original_content = None
        self.modified_content = None

    def load_file(self, file_path: str) -> str:
        """Load a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()

            self.current_file = str(path.absolute())
            self.original_content = content
            self.modified_content = content
            return content
        except FileNotFoundError as e:
            raise FileReadError(
                f"File not found: {file_path}",
                file_path=str(file_path),
                details=str(e),
            ) from e
        except PermissionError as e:
            raise FileReadError(
                f"Permission denied reading file: {file_path}",
                file_path=str(file_path),
                details=str(e),
            ) from e
        except UnicodeDecodeError as e:
            raise FileReadError(
                f"Unable to decode file as UTF-8: {file_path}",
                file_path=str(file_path),
                details=str(e),
            ) from e
        except Exception as e:
            raise FileReadError(
                f"Unexpected error reading file: {e}",
                file_path=str(file_path),
                details=str(e),
            ) from e

    def replace_emoji_with_icon(self, emoji: str, icon_path: str, alt_text: str = None) -> int:
        """Replace all occurrences of an emoji with markdown image syntax.

        Args:
            emoji: Emoji character to replace
            icon_path: Path to the icon file (relative or absolute)
            alt_text: Alt text for the image (defaults to icon filename)

        Returns:
            Number of replacements made
        """
        if not self.modified_content:
            return 0

        if alt_text is None:
            alt_text = Path(icon_path).stem

        # Create markdown image syntax
        icon_markdown = f"![{alt_text}]({icon_path})"

        # Count occurrences before replacement
        count = self.modified_content.count(emoji)

        # Replace all occurrences
        self.modified_content = self.modified_content.replace(emoji, icon_markdown)

        return count

    def replace_emoji_at_position(
        self, line_number: int, char_position: int, emoji: str, icon_path: str, alt_text: str = None
    ) -> bool:
        """Replace a specific emoji occurrence at given position.

        Args:
            line_number: Line number (1-based)
            char_position: Character position in line (0-based)
            emoji: Emoji character to replace
            icon_path: Path to the icon file
            alt_text: Alt text for the image

        Returns:
            True if replacement successful, False otherwise
        """
        if not self.modified_content:
            return False

        if alt_text is None:
            alt_text = Path(icon_path).stem

        lines = self.modified_content.split("\n")
        if line_number < 1 or line_number > len(lines):
            return False

        line = lines[line_number - 1]
        if char_position < 0 or char_position >= len(line):
            return False

        # Check if emoji is at the position
        if not line[char_position : char_position + len(emoji)] == emoji:
            return False

        # Create markdown image syntax
        icon_markdown = f"![{alt_text}]({icon_path})"

        # Replace at specific position
        new_line = line[:char_position] + icon_markdown + line[char_position + len(emoji) :]
        lines[line_number - 1] = new_line

        self.modified_content = "\n".join(lines)
        return True

    def save_file(self, file_path: str = None, create_backup: bool = True) -> bool:
        """Save the modified content to file.

        Args:
            file_path: Path to save to (defaults to current file)
            create_backup: Whether to create a .bak backup

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If no file is loaded
            IOError: If file can't be written
        """
        if file_path is None:
            if not self.current_file:
                raise ValueError("No file loaded")
            file_path = self.current_file

        path = Path(file_path)

        try:
            # Create backup if requested and file exists
            if create_backup and path.exists():
                backup_path = path.with_suffix(path.suffix + ".bak")
                shutil.copy2(path, backup_path)

            # Write modified content
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.modified_content)

            return True
        except PermissionError as e:
            raise FileWriteError(
                f"Permission denied writing file: {file_path}",
                file_path=str(file_path),
                details=str(e),
            ) from e
        except OSError as e:
            raise FileWriteError(
                f"OS error writing file: {e}",
                file_path=str(file_path),
                details=str(e),
            ) from e
        except Exception as e:
            raise FileWriteError(
                f"Unexpected error writing file: {e}",
                file_path=str(file_path),
                details=str(e),
            ) from e

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes.

        Returns:
            True if content has been modified, False otherwise
        """
        return self.original_content != self.modified_content

    def get_current_content(self) -> str:
        """Get the current (possibly modified) content.

        Returns:
            Current content as string
        """
        return self.modified_content or ""

    def get_original_content(self) -> str:
        """Get the original (unmodified) content.

        Returns:
            Original content as string
        """
        return self.original_content or ""

    def reset_changes(self):
        """Reset modified content to original."""
        self.modified_content = self.original_content

    def get_current_file_path(self) -> str:
        """Get the path of the currently loaded file.

        Returns:
            File path or empty string if no file loaded
        """
        return self.current_file or ""


class IconFileManager:
    """Manages icon files and directories."""

    def __init__(self, base_path: str = "./assets/icons"):
        """Initialize icon file manager.

        Args:
            base_path: Base directory for storing icons
        """
        self.base_path = Path(base_path)

    def ensure_directory_exists(self):
        """Create the icon directory if it doesn't exist."""
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_icon_path(self, icon_name: str, extension: str = "svg") -> str:
        """Get the full path for an icon file.

        Args:
            icon_name: Name of the icon (without extension)
            extension: File extension (default: svg)

        Returns:
            Full path to icon file
        """
        self.ensure_directory_exists()
        filename = f"{icon_name}.{extension}"
        return str(self.base_path / filename)

    def get_relative_icon_path(
        self, icon_name: str, markdown_file_path: str, extension: str = "svg"
    ) -> str:
        """Get relative path from markdown file to icon.

        Args:
            icon_name: Name of the icon
            markdown_file_path: Path to the markdown file
            extension: File extension

        Returns:
            Relative path suitable for markdown
        """
        self.ensure_directory_exists()
        icon_path = Path(self.get_icon_path(icon_name, extension))
        md_path = Path(markdown_file_path).parent

        try:
            relative_path = icon_path.relative_to(md_path)
            return str(relative_path)
        except ValueError:
            # If relative path can't be computed, return absolute
            return str(icon_path.absolute())

    def copy_icon_to_directory(self, source_path: str, icon_name: str) -> str:
        """Copy an icon file to the managed directory.

        Args:
            source_path: Source icon file path
            icon_name: Name to save icon as

        Returns:
            Path to the copied icon

        Raises:
            FileNotFoundError: If source doesn't exist
            IOError: If copy fails
        """
        self.ensure_directory_exists()
        source = Path(source_path)

        if not source.exists():
            raise FileNotFoundError(f"Source icon not found: {source_path}")

        dest = self.base_path / f"{icon_name}{source.suffix}"

        try:
            shutil.copy2(source, dest)
            return str(dest)
        except FileNotFoundError as e:
            raise FileBackupError(
                f"Source file not found: {source}",
                file_path=str(source),
                details=str(e),
            ) from e
        except PermissionError as e:
            raise FileBackupError(
                f"Permission denied copying file: {source}",
                file_path=str(source),
                details=str(e),
            ) from e
        except OSError as e:
            raise FileBackupError(
                f"OS error copying file: {e}",
                file_path=str(source),
                details=str(e),
            ) from e
        except Exception as e:
            raise FileBackupError(
                f"Unexpected error copying file: {e}",
                file_path=str(source),
                details=str(e),
            ) from e

    def list_icons(self) -> list[str]:
        """List all icons in the managed directory.

        Returns:
            List of icon filenames
        """
        if not self.base_path.exists():
            return []

        icons = []
        for ext in ["*.svg", "*.png", "*.jpg", "*.jpeg"]:
            icons.extend([f.name for f in self.base_path.glob(ext)])

        return sorted(icons)

    def delete_icon(self, icon_name: str, extension: str = None) -> bool:
        """Delete an icon file.

        Args:
            icon_name: Name of the icon
            extension: File extension (if None, tries common extensions)

        Returns:
            True if deleted, False if not found
        """
        if extension:
            icon_path = Path(self.get_icon_path(icon_name, extension))
            if icon_path.exists():
                icon_path.unlink()
                return True
            return False
        else:
            # Try common extensions
            deleted = False
            for ext in ["svg", "png", "jpg", "jpeg"]:
                icon_path = Path(self.get_icon_path(icon_name, ext))
                if icon_path.exists():
                    icon_path.unlink()
                    deleted = True
            return deleted

    def get_base_path(self) -> str:
        """Get the base path for icons.

        Returns:
            Base path as string
        """
        return str(self.base_path.absolute())
