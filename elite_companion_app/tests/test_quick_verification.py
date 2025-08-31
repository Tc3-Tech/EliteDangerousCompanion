#!/usr/bin/env python3
"""
Quick test to verify fidget mode fixes
"""

import sys
import os

# Add app root to path
app_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_root)

def test_imports():
    """Test critical imports"""
    print("Testing imports...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 imported")
    except ImportError as e:
        print(f"❌ PyQt6 failed: {e}")
        return False
    
    try:
        from ui.fidget_mode import EliteFidgetMode
        print("✅ EliteFidgetMode imported")
    except ImportError as e:
        print(f"❌ EliteFidgetMode failed: {e}")
        return False
    
    try:
        from data.ship_database import get_ship_database
        db = get_ship_database()
        print(f"✅ Ship database: {db.get_ship_count()} ships")
    except Exception as e:
        print(f"❌ Ship database failed: {e}")
        return False
    
    return True

def test_fidget_creation():
    """Test creating fidget mode window"""
    print("\nTesting fidget mode creation...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        from ui.fidget_mode import EliteFidgetMode
        
        # Create app if needed
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create window
        print("Creating EliteFidgetMode window...")
        window = EliteFidgetMode()
        print("✅ Window created successfully!")
        
        # Test basic properties
        if hasattr(window, 'ship_database') and window.ship_database:
            print(f"✅ Ship database loaded: {window.ship_database.get_ship_count()} ships")
        
        if hasattr(window, 'theme_manager') and window.theme_manager:
            print("✅ Theme manager initialized")
        
        # Quick show test
        print("Testing window show...")
        window.show()
        print("✅ Window shown successfully!")
        
        # Process events briefly
        app.processEvents()
        
        # Close window
        window.close()
        print("✅ Window closed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Fidget mode creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 Testing Elite Dangerous Fidget Mode Fixes")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n💥 Critical import failures - cannot continue")
        return 1
    
    # Test window creation
    if not test_fidget_creation():
        print("\n💥 Window creation failed")
        return 1
    
    print("\n🎉 All tests passed! Fidget mode should work now.")
    print("Try running: python ui/fidget_mode.py")
    return 0

if __name__ == "__main__":
    sys.exit(main())