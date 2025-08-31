#!/usr/bin/env python3
"""
Elite Dangerous Companion App
Main entry point for the application.
"""
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.app import CompanionApp
from config.settings import AppSettings


def setup_application():
    """Initialize the Qt application with Elite Dangerous styling"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Elite Dangerous Companion")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Commander Dashboard")
    
    # Load custom fonts
    font_path = project_root / "assets" / "fonts" / "EUROCAPS.TTF"
    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                app.setFont(QFont(font_families[0], 10))
    
    # Enable high DPI support
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    return app


def main():
    """Main application entry point"""
    # Initialize Qt application
    qt_app = setup_application()
    
    # Load settings
    settings = AppSettings()
    
    # Create and configure main application
    companion_app = CompanionApp(settings)
    
    # Set window properties for secondary display
    companion_app.setFixedSize(1024, 768)
    companion_app.setWindowTitle("Elite Dangerous Companion")
    
    # Show application
    companion_app.show()
    
    # Move to secondary display if configured
    if settings.get('display', 'use_secondary_display', fallback=True):
        screens = qt_app.screens()
        if len(screens) > 1:
            # Move to second screen
            secondary_screen = screens[1]
            companion_app.move(secondary_screen.geometry().x(), secondary_screen.geometry().y())
    
    # Start the application event loop
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()