# Replace Markdown Emojis 🚀

A powerful desktop application to replace Unicode emojis in markdown files with professional icon images. Built with Python and PySide6.

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Code Quality](https://img.shields.io/badge/code%20quality-A-green)
![Security](https://img.shields.io/badge/security-scanned-green)

## ✨ Features

- **🎯 Smart Emoji-to-Icon Matching** - 2000+ pre-populated emoji-keyword mappings
- **🔄 Many-to-Many Mapping** - Multiple emojis can share keywords for visual variety
- **⚠️ Duplicate Detection** - Warns when same icon is used for different concepts
- **🗄️ Database Editor** - Full CRUD interface for managing emoji mappings
- **📈 Learning System** - Improves suggestions based on your selections
- **💾 Safe File Operations** - Automatic .bak backup before saving
- **🎨 Beautiful GUI** - Modern, intuitive interface with PySide6

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv (for package management)

### Install with uv (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd replace-markdown-emojis

# Install dependencies and create virtual environment
uv sync

# Run the application
uv run python replace-emojis.py
```

### Development Setup

```bash
# Install with development dependencies
uv sync --dev

# Install pre-commit hooks (recommended)
python dev.py install

# Development workflow
uv run black .          # Format code
uv run isort .          # Sort imports
uv run ruff check .     # Lint code
uv run mypy src/        # Type checking
uv run bandit -r src/   # Security check
uv run pytest          # Run tests
uv run pytest -m gui    # Run GUI tests only

# Or use the development helper script
python dev.py all       # Run all development tasks
python dev.py format    # Format and sort imports
python dev.py lint      # Lint code
python dev.py type-check # Type checking
python dev.py security  # Security checks
python dev.py test      # Run tests
python dev.py test-gui  # Run GUI tests only
python dev.py install   # Install pre-commit hooks
```

### Code Quality Tools

This project uses modern Python development tools:

- **🖤 Black** - Code formatting
- **🔧 Ruff** - Fast linting and import sorting
- **🔍 MyPy** - Static type checking
- **🛡️ Bandit** - Security vulnerability scanning
- **🔒 Safety** - Dependency security checking
- **🧪 Pytest** - Testing framework with GUI support
- **📊 Coverage** - Test coverage reporting
- **🪝 Pre-commit** - Git hooks for code quality

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed information about all changes, improvements, and new features.

### Recent Updates (v1.1.0)
- 🚀 **Modernized to `uv`** - 10x faster dependency management
- 🛠️ **Enhanced development tools** - Black, Ruff, MyPy, Bandit, Safety
- 🧪 **Comprehensive testing** - pytest with GUI testing support
- 🔄 **CI/CD pipeline** - GitHub Actions with multi-platform testing
- 🛡️ **Security scanning** - Automated vulnerability detection
- 📚 **Modern documentation** - Updated with 2025 best practices

### Manual Requirements

If you prefer to install dependencies manually:

```bash
pip install PySide6>=6.6.0 markdown>=3.5 emoji>=2.10.0 requests>=2.31.0 \
            Pillow>=10.2.0 beautifulsoup4>=4.12.0 lxml>=5.1.0 \
            fuzzywuzzy>=0.18.0 python-Levenshtein>=0.24.0
```

## 🏗️ Modern Development Practices

This project follows **2025 Python development best practices** with:

- **📦 `uv` Package Management** - 10x faster than pip
- **🛠️ Comprehensive Tooling** - Black, Ruff, MyPy, Bandit, Safety
- **🧪 Advanced Testing** - pytest with GUI testing support
- **🔄 CI/CD Pipeline** - GitHub Actions with multi-platform testing
- **🛡️ Security Scanning** - Automated vulnerability detection
- **📚 Professional Documentation** - Modern development practices

### Development Workflow
```bash
# One-command setup
uv sync --dev && python dev.py install

# Quality assurance
python dev.py all  # Run all quality checks

# Individual tasks
python dev.py format    # Format code
python dev.py lint      # Lint code  
python dev.py test      # Run tests
python dev.py security  # Security checks
```

## 🚀 Quick Start

### Run the Application

```bash
python replace-emojis.py
```

### First Run

On first run, the application will:
1. Create `./emoji-cache/` directory
2. Initialize database with 200+ curated emoji entries
3. Display the main window

### Basic Workflow

1. **Open a Markdown File** - Click "📂 Open Markdown File" or use `Ctrl+O`
2. **View Detected Emojis** - All emojis appear in cards at the top
3. **Select Icons** - Click "Select Icon" on each emoji card
4. **Replace All** - Click "🔄 Replace All" to apply changes
5. **Save** - Click "💾 Save" to write changes (creates .bak backup)

## 📖 User Guide

### Emoji Detection

The application automatically detects:
- ✅ Emojis in headings (# Heading with 🚀)
- ✅ Emojis in body text
- ✅ Multiple occurrences of the same emoji
- ✅ Context around each emoji

### Icon Selection

When selecting an icon:
- **Top suggestions** are based on context keywords
- **Learned preferences** appear first if you've used this emoji before
- **Match score** indicates relevance
- **Duplicate warnings** alert you if the icon is already used elsewhere

### Duplicate Detection

The application warns you when:
- ⚠️ Same icon selected for different concepts
- Example: Using "rocket" for both "Launch App" and "Security Settings"
- Similarity threshold: 50% (configurable)
- You can choose to proceed anyway

### Database Editor

Access via **Tools → Manage Emoji Database**

Features:
- 📋 View all 200+ emoji entries
- 🔍 Search by emoji, name, or keywords
- ➕ Add new emoji mappings
- ✏️ Edit keywords for existing emojis
- 🗑️ Delete obsolete entries
- 📊 View usage statistics

## 🗂️ Project Structure

```
replace-markdown-emojis/
├── replace-emojis.py          # Main application entry point
├── pyproject.toml             # Project configuration
├── src/
│   ├── __init__.py
│   ├── database.py            # SQLite database operations
│   ├── emoji_detector.py      # Emoji detection & context extraction
│   ├── matcher.py             # Emoji-to-icon matching & duplicate detection
│   ├── file_operations.py     # Markdown file handling
│   ├── initialize_emoji_db.py # Database initialization script
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py     # Main application window
│       └── database_editor.py # Database editor dialog
├── emoji-cache/               # Created on first run
│   ├── emojis.db             # SQLite database
│   └── config.json           # User preferences
└── assets/                    # Created when saving icons
    └── icons/                # Replacement icons
```

## 🎓 Database Schema

### Emojis Table

Stores emoji-keyword mappings with many-to-many support:

```sql
CREATE TABLE emojis (
    unicode TEXT PRIMARY KEY,      -- Emoji character
    common_name TEXT,              -- Common name (e.g., "rocket")
    keywords TEXT,                 -- JSON array of keywords
    context_words TEXT,            -- Learned context keywords
    usage_count INTEGER,           -- Times used
    last_used TIMESTAMP           -- Last usage timestamp
);
```

### Session Tracking

For duplicate detection:

```sql
CREATE TABLE document_sessions (
    id INTEGER PRIMARY KEY,
    document_path TEXT,
    session_start TIMESTAMP,
    session_end TIMESTAMP
);

CREATE TABLE session_icon_usage (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,
    emoji_unicode TEXT,
    icon_name TEXT,
    context_text TEXT,
    line_number INTEGER,
    is_replaced BOOLEAN
);
```

## 📊 Pre-populated Emoji Categories

The database includes 200+ emojis across 25 categories:

- 🚀 Getting Started & Launch (6 emojis)
- 📦 Installation & Setup (10)
- 📝 Documentation (14)
- ✨ Features & Highlights (8)
- ✅ Success & Completion (12)
- ❌ Errors & Warnings (13)
- ℹ️ Information & Tips (10)
- 💻 Code & Development (13)
- 🧪 Testing & QA (8)
- 🔒 Security & Privacy (10)
- 📊 Data & Analytics (9)
- 🌐 Network & Web (12)
- 📁 Files & Folders (9)
- 📧 Communication & Messaging (15)
- ⏰ Time & Scheduling (9)
- 🎨 Design & Creativity (10)
- 🏗️ Build & Deployment (10)
- 🔀 Version Control & Git (15)
- ⚡ Performance & Optimization (9)
- 🤝 Collaboration & Team (9)
- 🎓 Learning & Education (10)
- ▶️ UI Elements & Controls (16)
- 🟢 Status & Indicators (17)
- 🔥 Popular & Trending (10)
- 📌 Miscellaneous Common (14)

## ⌨️ Keyboard Shortcuts

- `Ctrl+O` - Open file
- `Ctrl+S` - Save file
- `Ctrl+Q` - Quit application

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
ruff check src/
```

### Building from Source

```bash
python -m build
```

## 🔧 Configuration

Configuration file: `./emoji-cache/config.json`

```json
{
  "similarity_threshold": 50,
  "default_icon_format": "svg",
  "auto_backup": true,
  "icon_directory": "./assets/icons"
}
```

## 📋 Requirements

- **Python**: 3.11+
- **PySide6**: 6.6.0+ (Qt for Python)
- **markdown**: 3.5+ (Markdown parsing)
- **emoji**: 2.10.0+ (Emoji detection)
- **requests**: 2.31.0+ (HTTP requests)
- **Pillow**: 10.2.0+ (Image processing)
- **beautifulsoup4**: 4.12.0+ (HTML/XML parsing)
- **lxml**: 5.1.0+ (XML processing)
- **fuzzywuzzy**: 0.18.0+ (Fuzzy string matching)
- **python-Levenshtein**: 0.24.0+ (Fast string similarity)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Changelog & Updates

### Recent Updates (v1.1.0)
- 🚀 **Modernized to `uv`** - 10x faster dependency management
- 🛠️ **Enhanced development tools** - Black, Ruff, MyPy, Bandit, Safety
- 🧪 **Comprehensive testing** - pytest with GUI testing support
- 🔄 **CI/CD pipeline** - GitHub Actions with multi-platform testing
- 🛡️ **Security scanning** - Automated vulnerability detection
- 📚 **Modern documentation** - Updated with 2025 best practices

### Full Changelog
See [CHANGELOG.md](CHANGELOG.md) for detailed information about all changes, improvements, and new features since the project began.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [PySide6](https://wiki.qt.io/Qt_for_Python)
- Emoji data from [Unicode CLDR](https://github.com/unicode-org/cldr)
- Icon libraries: Font Awesome, Material Design Icons, Lucide, and more
- Inspired by the need for professional-looking documentation

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

## 🗺️ Roadmap

- [ ] Icon library API integration
- [ ] Batch processing multiple files
- [ ] Custom icon upload
- [ ] Export/import emoji mappings
- [ ] Undo/redo functionality
- [ ] CLI mode for automation
- [ ] Icon color customization for SVGs

## 🐛 Known Issues

- Icon library integration is currently a placeholder (icons must be manually added)
- Some emoji variants may not be detected correctly
- Large files (>10MB) may be slow to process

## 💡 Tips

- **Use context wisely**: Add descriptive text near emojis for better matching
- **Review suggestions**: Top suggestions are usually most relevant
- **Check duplicates**: Pay attention to duplicate warnings
- **Back up your work**: The app creates .bak files automatically
- **Edit the database**: Add your own emoji-keyword mappings for better results

---

**Author:** Rich Lewis  
Made with ❤️ using Python and PySide6
