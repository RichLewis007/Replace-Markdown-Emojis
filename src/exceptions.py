"""Custom exceptions for the replace-markdown-emojis application.

Author: Rich Lewis
"""


class EmojiReplacerError(Exception):
    """Base exception for all application-specific errors."""

    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.details = details


class DatabaseError(EmojiReplacerError):
    """Database-related errors."""

    def __init__(self, message: str, details: str | None = None):
        super().__init__(f"Database error: {message}", details)


class DatabaseConnectionError(DatabaseError):
    """Database connection errors."""

    def __init__(self, message: str, details: str | None = None):
        super().__init__(f"Database connection failed: {message}", details)


class DatabaseQueryError(DatabaseError):
    """Database query errors."""

    def __init__(self, message: str, query: str | None = None, details: str | None = None):
        super().__init__(f"Database query failed: {message}", details)
        self.query = query


class FileOperationError(EmojiReplacerError):
    """File operation errors."""

    def __init__(self, message: str, file_path: str | None = None, details: str | None = None):
        super().__init__(f"File operation failed: {message}", details)
        self.file_path = file_path


class FileReadError(FileOperationError):
    """File reading errors."""

    def __init__(self, message: str, file_path: str | None = None, details: str | None = None):
        super().__init__(f"Failed to read file: {message}", file_path, details)


class FileWriteError(FileOperationError):
    """File writing errors."""

    def __init__(self, message: str, file_path: str | None = None, details: str | None = None):
        super().__init__(f"Failed to write file: {message}", file_path, details)


class FileBackupError(FileOperationError):
    """File backup errors."""

    def __init__(self, message: str, file_path: str | None = None, details: str | None = None):
        super().__init__(f"Failed to backup file: {message}", file_path, details)


class IconLibraryError(EmojiReplacerError):
    """Icon library-related errors."""

    def __init__(self, message: str, library: str | None = None, details: str | None = None):
        super().__init__(f"Icon library error: {message}", details)
        self.library = library


class IconDownloadError(IconLibraryError):
    """Icon download errors."""

    def __init__(
        self,
        message: str,
        icon_name: str | None = None,
        library: str | None = None,
        details: str | None = None,
    ):
        super().__init__(f"Failed to download icon: {message}", library, details)
        self.icon_name = icon_name


class IconSearchError(IconLibraryError):
    """Icon search errors."""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        library: str | None = None,
        details: str | None = None,
    ):
        super().__init__(f"Failed to search icons: {message}", library, details)
        self.query = query


class EmojiDetectionError(EmojiReplacerError):
    """Emoji detection errors."""

    def __init__(self, message: str, content: str | None = None, details: str | None = None):
        super().__init__(f"Emoji detection failed: {message}", details)
        self.content = content


class EmojiMatchingError(EmojiReplacerError):
    """Emoji matching errors."""

    def __init__(
        self,
        message: str,
        emoji: str | None = None,
        keywords: list[str] | None = None,
        details: str | None = None,
    ):
        super().__init__(f"Emoji matching failed: {message}", details)
        self.emoji = emoji
        self.keywords = keywords


class ConfigurationError(EmojiReplacerError):
    """Configuration-related errors."""

    def __init__(self, message: str, config_key: str | None = None, details: str | None = None):
        super().__init__(f"Configuration error: {message}", details)
        self.config_key = config_key


class ValidationError(EmojiReplacerError):
    """Data validation errors."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: str | None = None,
        details: str | None = None,
    ):
        super().__init__(f"Validation error: {message}", details)
        self.field = field
        self.value = value


class CacheError(EmojiReplacerError):
    """Cache-related errors."""

    def __init__(self, message: str, cache_path: str | None = None, details: str | None = None):
        super().__init__(f"Cache error: {message}", details)
        self.cache_path = cache_path


class NetworkError(EmojiReplacerError):
    """Network-related errors."""

    def __init__(self, message: str, url: str | None = None, details: str | None = None):
        super().__init__(f"Network error: {message}", details)
        self.url = url


class TimeoutError(NetworkError):
    """Network timeout errors."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        timeout: int | None = None,
        details: str | None = None,
    ):
        super().__init__(f"Request timeout: {message}", url, details)
        self.timeout = timeout


class APIError(NetworkError):
    """API-related errors."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        status_code: int | None = None,
        details: str | None = None,
    ):
        super().__init__(f"API error: {message}", url, details)
        self.status_code = status_code
