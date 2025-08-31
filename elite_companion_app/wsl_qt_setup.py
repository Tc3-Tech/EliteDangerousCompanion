#!/usr/bin/env python3
"""
WSL Qt/PyQt6 Setup Helper
Configure proper display and platform for PyQt6 applications in WSL2 environment.
"""
import os
import sys
import subprocess
from typing import Optional

def detect_wsl_environment() -> bool:
    """Detect if running in WSL environment"""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
    except:
        return False

def detect_x11_server() -> Optional[str]:
    """Detect available X11 server"""
    # Check common X11 display variables
    display_vars = [
        os.environ.get('DISPLAY'),
        ':0',
        ':0.0',
        'localhost:0.0'
    ]
    
    for display in display_vars:
        if display:
            # Test if X11 server is accessible
            try:
                result = subprocess.run(
                    ['xset', '-display', display, 'q'], 
                    capture_output=True, 
                    timeout=2
                )
                if result.returncode == 0:
                    return display
            except:
                continue
    
    return None

def setup_wsl_qt_environment():
    """Setup Qt environment variables for WSL"""
    is_wsl = detect_wsl_environment()
    if not is_wsl:
        print("Not running in WSL - no special setup needed")
        return True
    
    print("WSL environment detected - configuring Qt settings...")
    
    # Force X11/XCB platform (avoid Wayland issues in WSL)
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    print("Set QT_QPA_PLATFORM=xcb")
    
    # Detect and configure display
    display = detect_x11_server()
    if display:
        os.environ['DISPLAY'] = display
        print(f"Set DISPLAY={display}")
    else:
        # Try common WSL display configurations
        wsl_displays = [':0', 'localhost:10.0', 'localhost:0.0']
        for wsl_display in wsl_displays:
            os.environ['DISPLAY'] = wsl_display
            print(f"Trying DISPLAY={wsl_display}")
            break
    
    # Disable problematic Qt features that may cause issues in WSL
    os.environ['QT_X11_NO_MITSHM'] = '1'  # Disable MIT-SHM extension
    os.environ['QT_QUICK_BACKEND'] = 'software'  # Use software rendering
    print("Set Qt compatibility flags for WSL")
    
    # Test Qt functionality
    try:
        print("Testing PyQt6 functionality...")
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QCoreApplication
        
        # Create minimal app to test
        if not QCoreApplication.instance():
            app = QApplication(sys.argv)
            print(f"✓ PyQt6 QApplication created successfully")
            print(f"✓ Platform: {app.platformName()}")
            return True
        else:
            print("✓ PyQt6 QApplication already exists")
            return True
            
    except Exception as e:
        print(f"✗ PyQt6 test failed: {e}")
        print("This may indicate missing X11 server or PyQt6 installation issues")
        return False

def print_wsl_setup_instructions():
    """Print setup instructions for WSL GUI applications"""
    print("\n" + "="*60)
    print("WSL GUI SETUP INSTRUCTIONS")
    print("="*60)
    print()
    print("For WSL2 with GUI applications, you need an X11 server:")
    print()
    print("Option 1: Use WSLg (Windows 11 22H2+):")
    print("  - WSLg is built-in, no additional setup needed")
    print("  - Should work automatically with DISPLAY=:0")
    print()
    print("Option 2: Use VcXsrv/Xming (Windows 10/11):")
    print("  1. Install VcXsrv: https://sourceforge.net/projects/vcxsrv/")
    print("  2. Run XLaunch with these settings:")
    print("     - Display number: 0")
    print("     - Start no client: checked")
    print("     - Clipboard: checked") 
    print("     - Primary selection: checked")
    print("     - Native opengl: checked")
    print("     - Disable access control: checked")
    print("  3. Set DISPLAY=<WINDOWS_IP>:0.0 in WSL")
    print()
    print("Option 3: Use Windows Terminal with WSLg:")
    print("  - Use Windows Terminal or VS Code with WSL extension")
    print("  - GUI apps should launch automatically")
    print()
    print("Verify setup by running:")
    print("  export QT_QPA_PLATFORM=xcb")
    print("  python3 -c \"from PyQt6.QtWidgets import QApplication, QLabel; app=QApplication([]); print('Success')\"")
    print()

def main():
    """Main setup function"""
    print("WSL Qt/PyQt6 Setup Helper")
    print("="*40)
    
    # Setup environment
    success = setup_wsl_qt_environment()
    
    if success:
        print("\n✓ WSL Qt environment configured successfully!")
        print("You can now run PyQt6 applications.")
    else:
        print("\n✗ WSL Qt setup encountered issues.")
        print_wsl_setup_instructions()
    
    return success

if __name__ == '__main__':
    main()