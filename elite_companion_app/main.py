#!/usr/bin/env python3
"""
Elite Dangerous Companion App
Main entry point for the application.
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set WSL display mode if needed
if 'WSL' in os.environ.get('WSL_DISTRO_NAME', '') or os.path.exists('/proc/version'):
    try:
        with open('/proc/version', 'r') as f:
            if 'microsoft' in f.read().lower():
                os.environ['QT_QPA_PLATFORM'] = 'xcb'
    except:
        pass

from PyQt6.QtWidgets import QApplication
from ui.fidget_mode import EliteFidgetMode


def main():
    """Main application entry point"""
    print("🚀 Starting Elite Dangerous Companion App...")
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Elite Dangerous Companion")
        app.setApplicationVersion("1.0.0")
        
        # Create main window
        window = EliteFidgetMode()
        window.show()
        
        print("✅ Application started successfully!")
        
        # Start application event loop
        return app.exec()
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())