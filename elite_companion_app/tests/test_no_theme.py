#!/usr/bin/env python3
"""
Test fidget mode without theme system to isolate issues
"""

import sys
import os

# Add app root to path
app_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_root)

def test_minimal_creation():
    """Test creating fidget mode with minimal theme system"""
    print("Testing minimal fidget mode creation...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        
        # Create app
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Import and patch theme functions to do nothing
        from ui import elite_widgets
        
        # Temporarily disable theme functionality
        original_apply_theme = elite_widgets.apply_elite_theme
        def dummy_apply_theme(*args, **kwargs):
            print("Theme application skipped")
            pass
        
        elite_widgets.apply_elite_theme = dummy_apply_theme
        
        # Now try to create fidget mode
        from ui.fidget_mode import EliteFidgetMode
        
        print("Creating EliteFidgetMode window...")
        window = EliteFidgetMode()
        print("✅ Window created successfully!")
        
        print("Testing window show...")
        window.show()
        print("✅ Window shown successfully!")
        
        # Process events briefly
        app.processEvents()
        
        # Close window
        window.close()
        print("✅ Window closed successfully!")
        
        # Restore original function
        elite_widgets.apply_elite_theme = original_apply_theme
        
        print("🎉 Minimal test passed! The core application works without theme recursion.")
        return True
        
    except Exception as e:
        print(f"❌ Minimal test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 Testing Elite Fidget Mode Without Theme System")
    print("=" * 50)
    
    if test_minimal_creation():
        print("\n✅ Core application functionality works!")
        print("The issue is specifically in the theme system recursion.")
        return 0
    else:
        print("\n❌ Core application has issues beyond themes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())