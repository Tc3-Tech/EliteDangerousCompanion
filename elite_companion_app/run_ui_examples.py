#!/usr/bin/env python3
"""
UI Examples Runner with WSL Support
Properly configure environment and launch Elite Dangerous UI examples.
"""
import os
import sys
import traceback
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configure WSL Qt environment before importing PyQt6
from wsl_qt_setup import setup_wsl_qt_environment

def main():
    """Main function to run UI examples with proper WSL setup"""
    
    print("Elite Dangerous UI Examples - WSL Ready")
    print("=" * 50)
    
    # Setup WSL Qt environment first
    if not setup_wsl_qt_environment():
        print("❌ Failed to setup WSL Qt environment")
        print("Please check the setup instructions and try again.")
        return 1
    
    try:
        # Import PyQt6 after environment setup
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        import sys
        
        # Import the example launcher
        from ui.examples.example_launcher import main as launcher_main
        
        print("✓ All imports successful - launching UI examples...")
        print()
        
        # Run the launcher
        return launcher_main()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print()
        print("Please ensure PyQt6 is installed:")
        print("  pip install PyQt6")
        print()
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print()
        print("Full traceback:")
        traceback.print_exc()
        print()
        print("This may indicate a problem with the X11 server or display configuration.")
        print("Try running the wsl_qt_setup.py script for more detailed diagnostics.")
        return 1

if __name__ == '__main__':
    sys.exit(main())