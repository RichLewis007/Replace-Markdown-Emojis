"""Icon library management system for downloading and caching icons from various sources."""

import json
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from PIL import Image


@dataclass
class IconMetadata:
    """Metadata for an icon."""

    name: str
    library: str
    keywords: list[str]
    file_path: Path
    url: str
    license: str
    size: tuple[int, int]  # width, height
    format: str  # svg, png, jpg


class IconLibrary(ABC):
    """Abstract base class for icon libraries."""

    def __init__(self, cache_dir: Path):
        """Initialize the icon library.

        Args:
            cache_dir: Directory to cache downloaded icons
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata: dict[str, IconMetadata] = {}
        self._load_metadata()

    @abstractmethod
    def get_library_name(self) -> str:
        """Get the name of this icon library."""
        pass

    @abstractmethod
    def search_icons(self, query: str, limit: int = 50) -> list[IconMetadata]:
        """Search for icons matching the query.

        Args:
            query: Search query (keywords)
            limit: Maximum number of results

        Returns:
            List of icon metadata
        """
        pass

    @abstractmethod
    def download_icon(self, icon_name: str, size: Optional[int] = None) -> Path:
        """Download an icon and return its local path.

        Args:
            icon_name: Name of the icon to download
            size: Optional size in pixels (for raster images)

        Returns:
            Path to the downloaded icon file
        """
        pass

    def _load_metadata(self) -> None:
        """Load metadata from cache."""
        if self.metadata_file.exists():
            try:
                with self.metadata_file.open() as f:
                    data = json.load(f)
                    self.metadata = {
                        k: IconMetadata(**v) if isinstance(v, dict) else v for k, v in data.items()
                    }
            except (json.JSONDecodeError, TypeError):
                self.metadata = {}

    def _save_metadata(self) -> None:
        """Save metadata to cache."""
        data = {
            k: v.__dict__ if isinstance(v, IconMetadata) else v for k, v in self.metadata.items()
        }
        with self.metadata_file.open("w") as f:
            json.dump(data, f, indent=2, default=str)

    def is_cached(self, icon_name: str) -> bool:
        """Check if an icon is already cached.

        Args:
            icon_name: Name of the icon

        Returns:
            True if cached, False otherwise
        """
        if icon_name in self.metadata:
            icon_path = self.metadata[icon_name].file_path
            return Path(icon_path).exists()
        return False

    def get_cached_path(self, icon_name: str) -> Optional[Path]:
        """Get the cached path for an icon.

        Args:
            icon_name: Name of the icon

        Returns:
            Path if cached, None otherwise
        """
        if self.is_cached(icon_name):
            return Path(self.metadata[icon_name].file_path)
        return None

    def clear_cache(self) -> None:
        """Clear all cached icons."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = {}
        self._save_metadata()


class IconifyLibrary(IconLibrary):
    """Iconify icon library - provides access to 200,000+ icons from various collections.

    Iconify is an open-source project that provides a unified API for accessing
    icons from Font Awesome, Material Design Icons, Lucide, and many more.

    API Docs: https://iconify.design/docs/api/
    """

    BASE_URL = "https://api.iconify.design"

    def get_library_name(self) -> str:
        """Get the library name."""
        return "Iconify"

    def search_icons(self, query: str, limit: int = 50) -> list[IconMetadata]:
        """Search for icons using Iconify's search API.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of icon metadata
        """
        # Iconify's search endpoint
        url = f"{self.BASE_URL}/search"
        params = {"query": query, "limit": limit, "prefixes": ""}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for icon_set in data.get("icons", []):
                prefix = icon_set.get("prefix", "")
                for icon_name in icon_set.get("icons", [])[:limit]:
                    full_name = f"{prefix}:{icon_name}"
                    results.append(
                        IconMetadata(
                            name=full_name,
                            library="Iconify",
                            keywords=[query, prefix, icon_name],
                            file_path=self.cache_dir / f"{full_name.replace(':', '_')}.svg",
                            url=f"{self.BASE_URL}/{full_name}.svg",
                            license="Various (depends on icon set)",
                            size=(24, 24),
                            format="svg",
                        )
                    )
                    if len(results) >= limit:
                        break
                if len(results) >= limit:
                    break

            return results
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Error searching Iconify: {e}")
            return []

    def download_icon(self, icon_name: str, size: Optional[int] = None) -> Path:
        """Download an icon from Iconify.

        Args:
            icon_name: Icon name in format "prefix:name"
            size: Optional size (Iconify serves SVGs which are scalable)

        Returns:
            Path to downloaded icon

        Raises:
            RuntimeError: If download fails
        """
        # Check cache first
        if self.is_cached(icon_name):
            return self.get_cached_path(icon_name)

        # Download from Iconify
        url = f"{self.BASE_URL}/{icon_name}.svg"
        if size:
            url += f"?height={size}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Save to cache
            safe_name = icon_name.replace(":", "_")
            icon_path = self.cache_dir / f"{safe_name}.svg"
            icon_path.write_bytes(response.content)

            # Save metadata
            self.metadata[icon_name] = IconMetadata(
                name=icon_name,
                library="Iconify",
                keywords=icon_name.split(":"),
                file_path=icon_path,
                url=url,
                license="Various",
                size=(size or 24, size or 24),
                format="svg",
            )
            self._save_metadata()

            return icon_path

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download icon {icon_name}: {e}") from e


class SimpleIconsLibrary(IconLibrary):
    """Simple Icons library - 3000+ popular brand icons.

    Simple Icons provides SVG icons for popular brands.
    All icons are available under CC0 1.0 Universal license.

    Docs: https://github.com/simple-icons/simple-icons
    """

    CDN_URL = "https://cdn.simpleicons.org"

    def get_library_name(self) -> str:
        """Get the library name."""
        return "Simple Icons"

    def search_icons(self, query: str, limit: int = 50) -> list[IconMetadata]:
        """Search for brand icons.

        Args:
            query: Search query (brand name)
            limit: Maximum results

        Returns:
            List of icon metadata
        """
        # Simple Icons doesn't have a search API, so we'll use a known list
        # In a real implementation, you might fetch the icon list from GitHub
        # For now, return a placeholder result if the query matches common brands
        common_brands = [
            "github",
            "google",
            "facebook",
            "twitter",
            "youtube",
            "instagram",
            "linkedin",
            "amazon",
            "apple",
            "microsoft",
        ]

        results = []
        query_lower = query.lower()
        for brand in common_brands:
            if query_lower in brand or brand in query_lower:
                results.append(
                    IconMetadata(
                        name=brand,
                        library="Simple Icons",
                        keywords=[brand, "brand", "logo"],
                        file_path=self.cache_dir / f"{brand}.svg",
                        url=f"{self.CDN_URL}/{brand}",
                        license="CC0 1.0 Universal",
                        size=(24, 24),
                        format="svg",
                    )
                )
                if len(results) >= limit:
                    break

        return results

    def download_icon(self, icon_name: str, size: Optional[int] = None) -> Path:
        """Download a brand icon.

        Args:
            icon_name: Brand name (lowercase, no spaces)
            size: Size parameter (SVGs are scalable)

        Returns:
            Path to downloaded icon

        Raises:
            RuntimeError: If download fails
        """
        # Check cache
        if self.is_cached(icon_name):
            return self.get_cached_path(icon_name)

        # Download from CDN
        url = f"{self.CDN_URL}/{icon_name}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Save to cache
            icon_path = self.cache_dir / f"{icon_name}.svg"
            icon_path.write_bytes(response.content)

            # Save metadata
            self.metadata[icon_name] = IconMetadata(
                name=icon_name,
                library="Simple Icons",
                keywords=[icon_name, "brand", "logo"],
                file_path=icon_path,
                url=url,
                license="CC0 1.0 Universal",
                size=(24, 24),
                format="svg",
            )
            self._save_metadata()

            return icon_path

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download icon {icon_name}: {e}") from e


class IconLibraryManager:
    """Manager for multiple icon libraries."""

    def __init__(self, base_cache_dir: Path):
        """Initialize the icon library manager.

        Args:
            base_cache_dir: Base directory for caching icons
        """
        self.base_cache_dir = base_cache_dir
        self.base_cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize available libraries
        self.libraries: dict[str, IconLibrary] = {
            "iconify": IconifyLibrary(base_cache_dir / "iconify"),
            "simple-icons": SimpleIconsLibrary(base_cache_dir / "simple-icons"),
        }

    def search_all_libraries(
        self, query: str, limit_per_library: int = 20
    ) -> dict[str, list[IconMetadata]]:
        """Search across all icon libraries.

        Args:
            query: Search query
            limit_per_library: Maximum results per library

        Returns:
            Dictionary mapping library name to search results
        """
        results = {}
        for name, library in self.libraries.items():
            try:
                icons = library.search_icons(query, limit=limit_per_library)
                if icons:
                    results[name] = icons
            except Exception as e:
                print(f"Error searching {name}: {e}")
                results[name] = []

        return results

    def download_icon_from_library(
        self, library_name: str, icon_name: str, size: Optional[int] = None
    ) -> Optional[Path]:
        """Download an icon from a specific library.

        Args:
            library_name: Name of the library
            icon_name: Icon name
            size: Optional size

        Returns:
            Path to downloaded icon or None if failed
        """
        library = self.libraries.get(library_name)
        if not library:
            print(f"Unknown library: {library_name}")
            return None

        try:
            return library.download_icon(icon_name, size)
        except Exception as e:
            print(f"Error downloading icon: {e}")
            return None

    def get_available_libraries(self) -> list[str]:
        """Get list of available library names.

        Returns:
            List of library names
        """
        return list(self.libraries.keys())

    def clear_all_caches(self) -> None:
        """Clear all icon caches."""
        for library in self.libraries.values():
            library.clear_cache()
