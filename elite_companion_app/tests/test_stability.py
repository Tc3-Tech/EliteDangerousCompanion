#!/usr/bin/env python3
"""
Comprehensive Stability Test for Elite Fidget Mode
Tests crash prevention mechanisms and memory management.
"""
import sys
import os
import time
import gc
import subprocess
import signal
import threading
from typing import List, Dict, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test results tracking
test_results: List[Dict[str, Any]] = []
test_running = True


class StabilityTester:
    """Comprehensive stability testing framework"""
    
    def __init__(self):
        self.test_processes: List[subprocess.Popen] = []
        self.test_count = 0
        self.success_count = 0
        self.failure_count = 0
        
    def log_test_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'duration': duration,
            'details': details,
            'timestamp': time.time()
        }
        test_results.append(result)
        
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name} ({duration:.2f}s) - {details}")
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.test_count += 1
    
    def test_import_safety(self) -> bool:
        """Test if all imports work without segfault"""
        start_time = time.time()
        
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer
            from ui.fidget_mode import EliteFidgetMode
            from ui.widgets.ship_viewer import ShipViewer3D
            from data.ship_database import get_ship_database
            
            duration = time.time() - start_time
            self.log_test_result("Import Safety", True, duration, "All imports successful")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Import Safety", False, duration, f"Import error: {e}")
            return False
    
    def test_widget_creation_cleanup(self) -> bool:
        """Test widget creation and cleanup cycle"""
        start_time = time.time()
        
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.widgets.ship_viewer import ShipViewer3D, ShipViewerControls
            
            # Create minimal app if needed
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Test ShipViewer3D creation and cleanup
            viewer = ShipViewer3D()
            if hasattr(viewer, 'cleanup_resources'):
                viewer.cleanup_resources()
            del viewer
            
            # Test ShipViewerControls creation and cleanup  
            controls = ShipViewerControls()
            if hasattr(controls, 'cleanup_resources'):
                controls.cleanup_resources()
            del controls
            
            # Force garbage collection
            gc.collect()
            
            duration = time.time() - start_time
            self.log_test_result("Widget Creation/Cleanup", True, duration, "Widgets created and cleaned up successfully")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Widget Creation/Cleanup", False, duration, f"Widget error: {e}")
            return False
    
    def test_quick_startup_shutdown(self) -> bool:
        """Test quick startup and shutdown cycle"""
        start_time = time.time()
        
        try:
            # Launch the safe launcher with a quick exit
            process = subprocess.Popen(
                [sys.executable, "launch_fidget_safe.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Let it run for 5 seconds then terminate
            time.sleep(5)
            
            # Send interrupt signal
            process.send_signal(signal.SIGINT)
            
            # Wait for graceful shutdown
            try:
                stdout, stderr = process.communicate(timeout=10)
                exit_code = process.returncode
                
                duration = time.time() - start_time
                
                if exit_code == 0:
                    self.log_test_result("Quick Startup/Shutdown", True, duration, "Clean exit")
                    return True
                else:
                    self.log_test_result("Quick Startup/Shutdown", False, duration, f"Exit code: {exit_code}")
                    return False
                    
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't respond
                process.kill()
                duration = time.time() - start_time
                self.log_test_result("Quick Startup/Shutdown", False, duration, "Process hung, had to kill")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Quick Startup/Shutdown", False, duration, f"Process error: {e}")
            return False
    
    def test_memory_leak_detection(self) -> bool:
        """Test for memory leaks in widget creation cycle"""
        start_time = time.time()
        
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.widgets.ship_viewer import ShipViewer3D
            import resource
            
            # Create minimal app if needed
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Get initial memory usage
            initial_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            
            # Create and destroy widgets multiple times
            for i in range(20):
                viewer = ShipViewer3D()
                if hasattr(viewer, 'cleanup_resources'):
                    viewer.cleanup_resources()
                del viewer
                gc.collect()
                
                if i % 5 == 0:
                    app.processEvents()
            
            # Check final memory usage
            final_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            memory_increase = (final_memory - initial_memory) / 1024  # Convert to MB
            
            duration = time.time() - start_time
            
            if memory_increase < 50:  # Less than 50MB increase is acceptable
                self.log_test_result("Memory Leak Detection", True, duration, 
                                   f"Memory increase: {memory_increase:.1f}MB")
                return True
            else:
                self.log_test_result("Memory Leak Detection", False, duration, 
                                   f"Excessive memory increase: {memory_increase:.1f}MB")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Memory Leak Detection", False, duration, f"Memory test error: {e}")
            return False
    
    def test_theme_manager_safety(self) -> bool:
        """Test theme manager registration/unregistration safety"""
        start_time = time.time()
        
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.widgets.ship_viewer import ShipViewer3D
            from ui.elite_widgets import get_global_theme_manager
            
            # Create minimal app if needed
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Test theme manager operations
            theme_manager = get_global_theme_manager()
            
            # Create widget and register
            viewer = ShipViewer3D()
            theme_manager.register_widget(viewer)
            
            # Cleanup and unregister
            theme_manager.unregister_widget(viewer)
            viewer.cleanup_resources()
            del viewer
            
            duration = time.time() - start_time
            self.log_test_result("Theme Manager Safety", True, duration, "Theme manager operations safe")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Theme Manager Safety", False, duration, f"Theme manager error: {e}")
            return False
    
    def test_rapid_window_cycles(self) -> bool:
        """Test rapid window creation/destruction cycles"""
        start_time = time.time()
        
        cycles_completed = 0
        target_cycles = 10
        
        try:
            for cycle in range(target_cycles):
                # Launch process
                process = subprocess.Popen(
                    [sys.executable, "launch_fidget_safe.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Let it start up briefly
                time.sleep(2)
                
                # Terminate quickly
                process.send_signal(signal.SIGINT)
                
                # Wait for shutdown
                try:
                    stdout, stderr = process.communicate(timeout=8)
                    if process.returncode == 0:
                        cycles_completed += 1
                    else:
                        print(f"Cycle {cycle} failed with exit code {process.returncode}")
                        if stderr:
                            print(f"Stderr: {stderr[:200]}...")
                        
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"Cycle {cycle} hung and was killed")
                
                # Brief pause between cycles
                time.sleep(0.5)
            
            duration = time.time() - start_time
            
            if cycles_completed >= target_cycles * 0.8:  # 80% success rate acceptable
                self.log_test_result("Rapid Window Cycles", True, duration, 
                                   f"{cycles_completed}/{target_cycles} cycles successful")
                return True
            else:
                self.log_test_result("Rapid Window Cycles", False, duration, 
                                   f"Only {cycles_completed}/{target_cycles} cycles successful")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Rapid Window Cycles", False, duration, f"Cycle test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all stability tests"""
        print("=" * 60)
        print("Elite Fidget Mode - Comprehensive Stability Test Suite")
        print("=" * 60)
        
        tests = [
            self.test_import_safety,
            self.test_widget_creation_cleanup,
            self.test_theme_manager_safety,
            self.test_memory_leak_detection,
            self.test_quick_startup_shutdown,
            self.test_rapid_window_cycles,
        ]
        
        print(f"Running {len(tests)} stability tests...")
        print()
        
        for test in tests:
            try:
                test()
            except KeyboardInterrupt:
                print("\nTest suite interrupted by user")
                break
            except Exception as e:
                print(f"Test framework error: {e}")
                self.failure_count += 1
                self.test_count += 1
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print()
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests:    {self.test_count}")
        print(f"Passed:         {self.success_count}")
        print(f"Failed:         {self.failure_count}")
        print(f"Success Rate:   {(self.success_count/self.test_count*100):.1f}%")
        print()
        
        if self.failure_count == 0:
            print("✓ ALL TESTS PASSED - Application stability improvements successful!")
        elif self.success_count >= self.test_count * 0.8:
            print("⚠ Most tests passed - Application has good stability with minor issues")
        else:
            print("✗ Multiple test failures - Application still has significant stability issues")
        
        print()
        print("DETAILED RESULTS:")
        for result in test_results:
            status = "PASS" if result['success'] else "FAIL"
            print(f"  [{status}] {result['test_name']}: {result['details']}")


def main():
    """Run stability tests"""
    tester = StabilityTester()
    
    try:
        tester.run_all_tests()
        return 0 if tester.failure_count == 0 else 1
    except KeyboardInterrupt:
        print("\nStability test interrupted by user")
        return 1
    except Exception as e:
        print(f"Fatal error in stability test: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())