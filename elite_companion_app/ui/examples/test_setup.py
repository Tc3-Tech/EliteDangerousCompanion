#!/usr/bin/env python3
"""
Test script to verify Elite Dangerous UI Examples setup
"""
import sys
import os

def test_python_version():
    """Test Python version compatibility"""
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def test_pyqt6():
    """Test PyQt6 availability"""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPainter
        print("✓ PyQt6 is available")
        return True
    except ImportError as e:
        print(f"✗ PyQt6 not available: {e}")
        print("  Install with: pip install PyQt6")
        return False

def test_elite_modules():
    """Test Elite UI modules"""
    # Add paths for imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_dir = os.path.dirname(current_dir)
    app_dir = os.path.dirname(ui_dir)
    
    sys.path.insert(0, ui_dir)
    sys.path.insert(0, app_dir)
    
    try:
        from elite_widgets import ElitePanel, EliteLabel, EliteButton
        print("✓ Elite widgets module available")
        
        from config.themes import ThemeManager
        print("✓ Theme system available")
        
        # Test theme manager
        theme_manager = ThemeManager()
        themes = list(theme_manager.predefined_themes.keys())
        print(f"✓ {len(themes)} predefined themes available: {', '.join(themes)}")
        
        return True
    except ImportError as e:
        print(f"✗ Elite modules not available: {e}")
        return False

def test_assets():
    """Test asset availability"""
    assets_path = "/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets"
    if not os.path.exists(assets_path):
        print(f"✗ Assets directory not found: {assets_path}")
        return False
    
    ship_assets = [f for f in os.listdir(assets_path) if f.endswith('.png') and 'ship' not in f.lower() or 'asp-explorer' in f.lower()]
    if len(ship_assets) > 0:
        print(f"✓ {len([f for f in os.listdir(assets_path) if f.endswith('.png')])} ship assets available")
    else:
        print("! Ship assets directory exists but may be empty")
    
    return True

def main():
    """Run all setup tests"""
    print("Elite Dangerous UI Examples - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("PyQt6 Installation", test_pyqt6),
        ("Elite UI Modules", test_elite_modules),
        ("Asset Files", test_assets)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Setup Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! You're ready to run the Elite UI examples.")
        print("\nTo get started:")
        print("  python example_launcher.py")
        print("\nOr run individual examples:")
        print("  python elite_dashboard.py")
        print("  python ship_details.py")
        print("  python exploration_display.py")
        print("  python media_control.py")
        print("  python settings_panel.py")
    else:
        print(f"\n❌ {total - passed} tests failed. Please fix the issues above.")
        if not test_pyqt6():
            print("\nTo install PyQt6:")
            print("  pip install -r requirements.txt")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)