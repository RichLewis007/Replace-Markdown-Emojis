#!/usr/bin/env python3
"""
Replace Markdown Emojis - Main application entry point.

A desktop application to replace Unicode emojis in markdown files with professional icons.

Author: Rich Lewis
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication  # noqa: E402

from gui.main_window import MainWindow  # noqa: E402


def main() -> None:
    """Main entry point for the application."""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Replace Markdown Emojis")
    app.setOrganizationName("RichDev")

    # Note: High DPI scaling is now handled automatically by Qt6
    # The deprecated attributes are no longer needed

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
