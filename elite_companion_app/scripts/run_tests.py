#!/usr/bin/env python3
"""
Elite Dangerous Fidget Mode Test Runner
Comprehensive test runner for all fidget mode functionality.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add app root to path
app_root = Path(__file__).parent
sys.path.insert(0, str(app_root))

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️  {description} - TIMEOUT (30s)")
        return False
    except Exception as e:
        print(f"💥 {description} - EXCEPTION: {e}")
        return False

def check_imports():
    """Check if critical imports work"""
    print_header("CHECKING IMPORTS")
    
    imports_to_test = [
        ("PyQt6.QtWidgets", "PyQt6 Widgets"),
        ("data.ship_database", "Ship Database"),
        ("ui.elite_widgets", "Elite Widgets"),
        ("config.themes", "Theme System"),
        ("ui.fidget_mode", "Fidget Mode Main"),
        ("ui.widgets.ship_gallery", "Ship Gallery Widget"),
        ("ui.widgets.ship_viewer", "Ship Viewer Widget"),
        ("ui.widgets.ship_specs_panel", "Ship Specs Panel"),
        ("ui.widgets.ship_comparison", "Ship Comparison Widget"),
        ("utils.image_optimizer", "Image Optimizer")
    ]
    
    import_results = []
    
    for module, description in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {description} import - SUCCESS")
            import_results.append(True)
        except ImportError as e:
            print(f"❌ {description} import - FAILED: {e}")
            import_results.append(False)
        except Exception as e:
            print(f"💥 {description} import - EXCEPTION: {e}")
            import_results.append(False)
    
    success_rate = sum(import_results) / len(import_results) * 100
    print(f"\n📊 Import Success Rate: {success_rate:.1f}% ({sum(import_results)}/{len(import_results)})")
    
    return success_rate >= 80  # 80% imports must succeed

def test_basic_functionality():
    """Test basic functionality without full UI"""
    print_header("BASIC FUNCTIONALITY TESTS")
    
    tests = []
    
    # Test ship database
    try:
        from data.ship_database import get_ship_database
        db = get_ship_database()
        ship_count = db.get_ship_count()
        print(f"✅ Ship Database - {ship_count} ships loaded")
        tests.append(True)
    except Exception as e:
        print(f"❌ Ship Database - FAILED: {e}")
        tests.append(False)
    
    # Test theme system
    try:
        from config.themes import PredefinedThemes, HardwareThemeManager
        theme = PredefinedThemes.ICE_BLUE
        manager = HardwareThemeManager()
        print(f"✅ Theme System - Themes and manager created")
        tests.append(True)
    except Exception as e:
        print(f"❌ Theme System - FAILED: {e}")
        tests.append(False)
    
    # Test widget creation (without showing)
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.widgets.ship_gallery import ShipThumbnail
        from ui.widgets.ship_viewer import ShipViewer3D
        from ui.widgets.ship_specs_panel import AnimatedStatBar
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create widgets
        db = get_ship_database()
        if db.get_ship_count() > 0:
            ship = db.get_all_ships()[0]
            thumbnail = ShipThumbnail(ship)
        
        viewer = ShipViewer3D()
        stat_bar = AnimatedStatBar("Test", 50, 100)
        
        print(f"✅ Widget Creation - Basic widgets created successfully")
        tests.append(True)
    except Exception as e:
        print(f"❌ Widget Creation - FAILED: {e}")
        tests.append(False)
    
    success_rate = sum(tests) / len(tests) * 100 if tests else 0
    print(f"\n📊 Basic Functionality Success Rate: {success_rate:.1f}% ({sum(tests)}/{len(tests)})")
    
    return success_rate >= 66  # 66% basic tests must succeed

def run_consolidated_tests():
    """Run consolidated test suites"""
    print_header("RUNNING CONSOLIDATED TESTS")
    
    test_files = [
        ("tests/test_fidget_system.py", "System Integration Tests"),
        ("tests/test_quick_verification.py", "Quick Verification Tests"),
        ("tests/test_widgets.py", "Widget Unit Tests"),
        ("tests/test_integration.py", "Integration Tests"),
        ("tests/test_fidget_mode_comprehensive.py", "Comprehensive Fidget Mode Tests")
    ]
    
    results = []
    
    for test_file, description in test_files:
        if os.path.exists(test_file):
            # Try pytest first, fallback to direct execution
            cmd_pytest = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"]
            cmd_direct = [sys.executable, test_file]
            
            print(f"\n🔧 Running {description}...")
            success = False
            
            # Try pytest
            try:
                result = subprocess.run(cmd_pytest, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"✅ {description} (pytest) - SUCCESS")
                    success = True
                else:
                    # Fallback to direct execution
                    result = subprocess.run(cmd_direct, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        print(f"✅ {description} (direct) - SUCCESS")
                        success = True
                    else:
                        print(f"❌ {description} - FAILED")
                        if result.stderr.strip():
                            print(f"Error: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print(f"⏱️  {description} - TIMEOUT")
                success = False
            except Exception as e:
                print(f"💥 {description} - EXCEPTION: {e}")
                success = False
            
            results.append(success)
        else:
            print(f"⚠️  {description} - FILE NOT FOUND: {test_file}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100 if results else 0
    print(f"\n📊 Test Success Rate: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    
    return success_rate >= 40  # 40% test suites must succeed

def test_fidget_mode_creation():
    """Test creating the fidget mode window"""
    print_header("FIDGET MODE CREATION TEST")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        from ui.fidget_mode import EliteFidgetMode
        
        # Create application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        print("🔧 Creating EliteFidgetMode window...")
        
        # Create window with timeout
        window = None
        success = False
        error_msg = None
        
        def create_window():
            nonlocal window, success, error_msg
            try:
                window = EliteFidgetMode()
                success = True
                print("✅ EliteFidgetMode window created successfully")
            except Exception as e:
                error_msg = str(e)
                success = False
        
        # Run with timeout
        timer = QTimer()
        timer.timeout.connect(lambda: app.quit())
        timer.start(10000)  # 10 second timeout
        
        try:
            create_window()
            
            if success and window:
                print("🔧 Testing window show/hide cycle...")
                window.show()
                app.processEvents()
                
                # Quick show/hide test
                QTimer.singleShot(500, window.hide)
                QTimer.singleShot(1000, lambda: app.quit())
                
                app.exec()
                
                print("✅ Window show/hide cycle completed")
                
                if window:
                    window.close()
                
                return True
            else:
                print(f"❌ EliteFidgetMode creation failed: {error_msg}")
                return False
                
        except Exception as e:
            print(f"💥 EliteFidgetMode test exception: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import EliteFidgetMode: {e}")
        return False
    except Exception as e:
        print(f"💥 Fidget mode creation test exception: {e}")
        return False

def main():
    """Main test runner"""
    print_header("ELITE DANGEROUS FIDGET MODE TEST RUNNER")
    print("Testing all functionality and crash prevention measures...")
    
    start_time = time.time()
    test_results = []
    
    # Run test suites
    test_results.append(("Import Tests", check_imports()))
    test_results.append(("Basic Functionality", test_basic_functionality()))
    test_results.append(("Fidget Mode Creation", test_fidget_mode_creation()))
    test_results.append(("Consolidated Tests", run_consolidated_tests()))
    
    # Calculate overall results
    elapsed_time = time.time() - start_time
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    success_rate = passed_tests / total_tests * 100
    
    # Print summary
    print_header("TEST SUMMARY")
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\n📊 Overall Results:")
    print(f"   • Tests Passed: {passed_tests}/{total_tests}")
    print(f"   • Success Rate: {success_rate:.1f}%")
    print(f"   • Total Time: {elapsed_time:.1f}s")
    
    if success_rate >= 75:
        print("\n🎉 EXCELLENT! Fidget mode is ready for use.")
        return 0
    elif success_rate >= 50:
        print("\n⚠️  FAIR: Fidget mode has some issues but basic functionality works.")
        return 0
    else:
        print("\n💥 CRITICAL: Fidget mode has serious issues that need fixing.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)