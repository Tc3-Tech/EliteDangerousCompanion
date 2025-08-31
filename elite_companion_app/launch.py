#!/usr/bin/env python3
"""
Elite Dangerous Fidget Mode Launcher
Convenient launcher with system checks and error handling.
"""
import sys
import os
import subprocess
import platform

def check_system_requirements():
    """Check if system meets requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python 3.8+ required (found {python_version.major}.{python_version.minor})")
        return False
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check PyQt6
    try:
        import PyQt6
        print(f"✅ PyQt6 installed")
    except ImportError:
        print("❌ PyQt6 not found. Install with: pip install PyQt6")
        return False
    
    # Check display environment
    display_env = os.environ.get('DISPLAY')
    if platform.system() == "Linux" and not display_env:
        print("⚠️  No DISPLAY environment variable found")
        print("   Make sure X11 forwarding is enabled for WSL/SSH")
    
    return True

def check_assets():
    """Check if ship assets are available"""
    print("\n🖼️  Checking ship assets...")
    
    assets_dir = "/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets"
    
    if not os.path.exists(assets_dir):
        print(f"❌ Assets directory not found: {assets_dir}")
        return False
    
    # Count PNG files
    png_files = [f for f in os.listdir(assets_dir) if f.endswith('.png')]
    print(f"✅ Found {len(png_files)} ship images")
    
    if len(png_files) < 20:
        print("⚠️  Low number of ship images found")
    
    return True

def run_tests():
    """Run system tests"""
    print("\n🧪 Running system tests...")
    
    try:
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Import test module
        from tests.test_fidget_system import main as test_main
        
        # Capture test output
        original_stdout = sys.stdout
        from io import StringIO
        test_output = StringIO()
        sys.stdout = test_output
        
        try:
            result = test_main()
            sys.stdout = original_stdout
            
            if result == 0:
                print("✅ All system tests passed")
                return True
            else:
                print("❌ System tests failed")
                print("Test output:", test_output.getvalue())
                return False
                
        except Exception as e:
            sys.stdout = original_stdout
            print(f"❌ Test execution failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import test module: {e}")
        return False

def launch_fidget_mode():
    """Launch the fidget mode application"""
    print("\n🚀 Launching Elite Dangerous Fidget Mode...")
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fidget_mode_path = os.path.join(current_dir, "ui", "fidget_mode.py")
        
        if not os.path.exists(fidget_mode_path):
            print(f"❌ Fidget mode not found: {fidget_mode_path}")
            return False
        
        # Change to the app directory
        os.chdir(current_dir)
        
        # Launch application
        subprocess.run([sys.executable, fidget_mode_path])
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch fidget mode: {e}")
        return False

def print_banner():
    """Print application banner"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    ELITE DANGEROUS                           ║
║                    FIDGET MODE LAUNCHER                       ║
║                                                               ║
║  Interactive Ship Database & 3D Viewer                       ║
║  Optimized for 1024x768 Display                             ║
║  Hardware Integration Ready                                   ║
╚═══════════════════════════════════════════════════════════════╝
    """)

def print_controls_info():
    """Print control information"""
    print("""
🎮 CONTROLS:
   Mouse: Click & drag to rotate ships, scroll to zoom
   Gallery: Click thumbnails, use filters
   Hardware: 9-button navigation + potentiometer theme control
   Keyboard: Ctrl+S (screenshot), Ctrl+Q (exit)

🔧 FEATURES:
   • 38+ Elite Dangerous ships with full specifications
   • Real-time 3D viewer with technical overlays
   • Ship comparison system with performance charts
   • Dynamic theme system (6 Elite-style themes)
   • Memory-optimized image loading (50MB cache)
   • 60fps performance target
    """)

def main():
    """Main launcher function"""
    print_banner()
    
    # System checks
    if not check_system_requirements():
        print("\n❌ System requirements not met. Please fix issues above.")
        return 1
    
    if not check_assets():
        print("\n❌ Asset requirements not met. Please ensure ship images are available.")
        return 1
    
    # Quick system test
    print("\n🔧 Running quick system test...")
    try:
        # Just test imports without full GUI test
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from data.ship_database import get_ship_database
        db = get_ship_database()
        ship_count = db.get_ship_count()
        print(f"✅ Ship database loaded: {ship_count} ships")
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return 1
    
    print_controls_info()
    
    # Launch confirmation
    try:
        response = input("\n🚀 Launch Elite Dangerous Fidget Mode? [Y/n]: ").strip().lower()
        if response in ['', 'y', 'yes']:
            if launch_fidget_mode():
                print("\n✅ Application closed successfully")
                return 0
            else:
                print("\n❌ Application launch failed")
                return 1
        else:
            print("\n👋 Launch cancelled")
            return 0
    except KeyboardInterrupt:
        print("\n\n👋 Launch cancelled")
        return 0

if __name__ == "__main__":
    sys.exit(main())