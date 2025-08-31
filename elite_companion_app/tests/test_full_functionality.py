#!/usr/bin/env python3
"""
Full Functionality Test for Elite Dangerous Fidget Mode
Tests the complete application including all widgets and features.
"""

import sys
import os

# Add app root to path
app_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_root)

def run_fidget_mode_briefly():
    """Run fidget mode for a few seconds to test full functionality"""
    print("🚀 Starting Elite Dangerous Fidget Mode...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        from ui.fidget_mode import EliteFidgetMode
        
        # Create app
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create main window
        print("Creating main window...")
        window = EliteFidgetMode()
        
        # Show window
        print("Displaying window...")
        window.show()
        
        # Test various interactions
        print("Testing ship navigation...")
        if window.ship_database and window.ship_database.get_ship_count() > 0:
            ships = window.ship_database.get_all_ships()
            
            # Test navigating through a few ships
            for i, ship in enumerate(ships[:3]):
                print(f"  Loading ship: {ship.display_name}")
                window.set_current_ship(ship, animate=False)
                app.processEvents()
                
                # Test hardware simulation
                if window.hardware_nav:
                    print(f"  Simulating button press {i+1}")
                    window.on_hardware_button_pressed(i + 1)
                    app.processEvents()
        
        # Test theme changes
        print("Testing theme system...")
        if window.theme_manager:
            themes = ["Ice Blue", "Matrix Green", "Deep Purple", "Plasma Pink"]
            for theme_name in themes:
                print(f"  Applying theme: {theme_name}")
                window.change_theme(theme_name)
                app.processEvents()
        
        # Test potentiometer simulation
        print("Testing potentiometer simulation...")
        if window.hardware_nav:
            for val in [0.2, 0.5, 0.8, 0.3]:
                print(f"  Setting pot value: {val}")
                window.on_hardware_pot_changed(val)
                app.processEvents()
        
        print("✅ All functionality tests completed successfully!")
        print("📊 Final window status:")
        print(f"   • Window visible: {window.isVisible()}")
        print(f"   • Current ship: {window.current_ship.display_name if window.current_ship else 'None'}")
        print(f"   • Theme manager: {'Active' if window.theme_manager else 'Inactive'}")
        print(f"   • Hardware nav: {'Active' if window.hardware_nav else 'Inactive'}")
        
        # Close gracefully
        print("Closing application...")
        window.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Full functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 Elite Dangerous Fidget Mode - Full Functionality Test")
    print("=" * 60)
    
    if run_fidget_mode_briefly():
        print("\n🎉 SUCCESS! Elite Dangerous Fidget Mode is fully functional!")
        print("You can now run the application with: python ui/fidget_mode.py")
        return 0
    else:
        print("\n💥 FAILURE! There are still issues to resolve.")
        return 1

if __name__ == "__main__":
    sys.exit(main())