"""Tests for icon library management."""

from pathlib import Path
from unittest.mock import Mock, patch

from src.icon_library_manager import (
    IconifyLibrary,
    IconLibrary,
    IconLibraryManager,
    IconMetadata,
    SimpleIconsLibrary,
)


class TestIconMetadata:
    """Tests for IconMetadata dataclass."""

    def test_icon_metadata_creation(self, tmp_path):
        """Test creating icon metadata."""
        metadata = IconMetadata(
            name="test-icon",
            library="Test Library",
            keywords=["test", "icon"],
            file_path=tmp_path / "test.svg",
            url="https://example.com/icon.svg",
            license="MIT",
            size=(24, 24),
            format="svg",
        )

        assert metadata.name == "test-icon"
        assert metadata.library == "Test Library"
        assert len(metadata.keywords) == 2
        assert metadata.format == "svg"


class TestIconLibraryBase:
    """Tests for IconLibrary base class functionality."""

    def test_cache_initialization(self, tmp_path):
        """Test that cache directory is created."""
        cache_dir = tmp_path / "icon_cache"
        library = IconifyLibrary(cache_dir)

        assert cache_dir.exists()
        assert library.cache_dir == cache_dir

    def test_is_cached(self, tmp_path):
        """Test checking if icon is cached."""
        cache_dir = tmp_path / "icon_cache"
        library = IconifyLibrary(cache_dir)

        # Icon not in metadata
        assert not library.is_cached("nonexistent")

        # Add metadata but no file
        icon_path = cache_dir / "test.svg"
        library.metadata["test"] = IconMetadata(
            name="test",
            library="Test",
            keywords=[],
            file_path=icon_path,
            url="",
            license="MIT",
            size=(24, 24),
            format="svg",
        )
        assert not library.is_cached("test")

        # Create the file
        icon_path.write_text("<svg></svg>")
        assert library.is_cached("test")

    def test_get_cached_path(self, tmp_path):
        """Test getting cached icon path."""
        cache_dir = tmp_path / "icon_cache"
        library = IconifyLibrary(cache_dir)

        # Non-existent icon
        assert library.get_cached_path("nonexistent") is None

        # Create cached icon
        icon_path = cache_dir / "test.svg"
        icon_path.write_text("<svg></svg>")
        library.metadata["test"] = IconMetadata(
            name="test",
            library="Test",
            keywords=[],
            file_path=icon_path,
            url="",
            license="MIT",
            size=(24, 24),
            format="svg",
        )

        cached_path = library.get_cached_path("test")
        assert cached_path == icon_path

    def test_clear_cache(self, tmp_path):
        """Test clearing the cache."""
        cache_dir = tmp_path / "icon_cache"
        library = IconifyLibrary(cache_dir)

        # Create some cached files
        (cache_dir / "icon1.svg").write_text("<svg></svg>")
        (cache_dir / "icon2.svg").write_text("<svg></svg>")
        library.metadata["icon1"] = Mock()
        library.metadata["icon2"] = Mock()

        library.clear_cache()

        assert library.cache_dir.exists()
        assert len(list(library.cache_dir.glob("*.svg"))) == 0
        assert len(library.metadata) == 0


class TestIconifyLibrary:
    """Tests for Iconify library integration."""

    def test_library_name(self, tmp_path):
        """Test getting library name."""
        library = IconifyLibrary(tmp_path)
        assert library.get_library_name() == "Iconify"

    @patch("src.icon_library_manager.requests.get")
    def test_search_icons(self, mock_get, tmp_path):
        """Test searching for icons."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "icons": [
                {
                    "prefix": "mdi",
                    "icons": ["home", "user", "settings"],
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        library = IconifyLibrary(tmp_path)
        results = library.search_icons("home", limit=10)

        assert len(results) > 0
        assert all(isinstance(r, IconMetadata) for r in results)
        assert any("mdi" in r.name for r in results)

    @patch("src.icon_library_manager.requests.get")
    def test_download_icon(self, mock_get, tmp_path):
        """Test downloading an icon."""
        # Mock download response
        mock_response = Mock()
        mock_response.content = b"<svg>test icon</svg>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        library = IconifyLibrary(tmp_path)
        icon_path = library.download_icon("mdi:home")

        assert icon_path.exists()
        assert icon_path.read_text() == "<svg>test icon</svg>"
        assert library.is_cached("mdi:home")

    @patch("src.icon_library_manager.requests.get")
    def test_download_icon_cached(self, mock_get, tmp_path):
        """Test that cached icons are not re-downloaded."""
        # Setup cached icon
        library = IconifyLibrary(tmp_path)
        icon_path = tmp_path / "mdi_home.svg"
        icon_path.write_text("<svg>cached</svg>")
        library.metadata["mdi:home"] = IconMetadata(
            name="mdi:home",
            library="Iconify",
            keywords=[],
            file_path=icon_path,
            url="",
            license="MIT",
            size=(24, 24),
            format="svg",
        )

        # Request the icon
        result_path = library.download_icon("mdi:home")

        # Should return cached path without calling API
        assert result_path == icon_path
        mock_get.assert_not_called()


class TestSimpleIconsLibrary:
    """Tests for Simple Icons library."""

    def test_library_name(self, tmp_path):
        """Test getting library name."""
        library = SimpleIconsLibrary(tmp_path)
        assert library.get_library_name() == "Simple Icons"

    def test_search_icons(self, tmp_path):
        """Test searching for brand icons."""
        library = SimpleIconsLibrary(tmp_path)
        results = library.search_icons("github")

        assert len(results) > 0
        assert any("github" in r.name for r in results)
        assert all(r.library == "Simple Icons" for r in results)

    @patch("src.icon_library_manager.requests.get")
    def test_download_icon(self, mock_get, tmp_path):
        """Test downloading a brand icon."""
        mock_response = Mock()
        mock_response.content = b"<svg>github icon</svg>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        library = SimpleIconsLibrary(tmp_path)
        icon_path = library.download_icon("github")

        assert icon_path.exists()
        assert icon_path.read_text() == "<svg>github icon</svg>"


class TestIconLibraryManager:
    """Tests for IconLibraryManager."""

    def test_initialization(self, tmp_path):
        """Test manager initialization."""
        manager = IconLibraryManager(tmp_path)

        assert manager.base_cache_dir.exists()
        assert len(manager.libraries) >= 2
        assert "iconify" in manager.libraries
        assert "simple-icons" in manager.libraries

    def test_get_available_libraries(self, tmp_path):
        """Test getting available library names."""
        manager = IconLibraryManager(tmp_path)
        libraries = manager.get_available_libraries()

        assert "iconify" in libraries
        assert "simple-icons" in libraries

    @patch("src.icon_library_manager.requests.get")
    def test_search_all_libraries(self, mock_get, tmp_path):
        """Test searching across all libraries."""
        # Mock responses for different libraries
        mock_response = Mock()
        mock_response.json.return_value = {"icons": [{"prefix": "mdi", "icons": ["home"]}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        manager = IconLibraryManager(tmp_path)
        results = manager.search_all_libraries("home", limit_per_library=5)

        assert isinstance(results, dict)
        assert len(results) > 0

    @patch("src.icon_library_manager.requests.get")
    def test_download_icon_from_library(self, mock_get, tmp_path):
        """Test downloading from specific library."""
        mock_response = Mock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        manager = IconLibraryManager(tmp_path)
        icon_path = manager.download_icon_from_library("iconify", "mdi:home")

        assert icon_path is not None
        assert icon_path.exists()

    def test_download_from_unknown_library(self, tmp_path):
        """Test downloading from unknown library returns None."""
        manager = IconLibraryManager(tmp_path)
        result = manager.download_icon_from_library("unknown", "icon")

        assert result is None

    def test_clear_all_caches(self, tmp_path):
        """Test clearing all library caches."""
        manager = IconLibraryManager(tmp_path)

        # Create some cached files
        for lib_name, library in manager.libraries.items():
            test_file = library.cache_dir / "test.svg"
            test_file.write_text("<svg></svg>")

        manager.clear_all_caches()

        # Check all caches are cleared
        for library in manager.libraries.values():
            assert len(list(library.cache_dir.glob("*.svg"))) == 0
