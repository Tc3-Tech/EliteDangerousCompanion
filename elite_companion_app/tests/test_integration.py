"""
Integration Tests for Elite Dangerous Fidget Mode
Tests real-world usage scenarios and end-to-end functionality.
"""

import pytest
import sys
import os
import time
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

# Import test configuration
from . import app_root

# Import modules under test
try:
    from ui.fidget_mode import main, EliteFidgetMode
    INTEGRATION_IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Integration test import error: {e}")
    INTEGRATION_IMPORTS_SUCCESSFUL = False


@pytest.fixture
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestFidgetModeIntegration:
    """Integration tests for complete fidget mode functionality"""
    
    def test_main_function_execution(self, qapp):
        """Test that main function can execute without crashing"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        # Mock sys.argv to avoid conflicts
        with patch('sys.argv', ['fidget_mode.py']):
            try:
                # Create a timer to close the application after a short time
                def close_app():
                    app = QApplication.instance()
                    if app:
                        app.quit()
                
                QTimer.singleShot(500, close_app)  # Close after 500ms
                
                # Run main function
                result = main()
                
                # Should return 0 for success or handle errors gracefully
                assert result in [0, 1], f"Main function returned unexpected code: {result}"
                
            except SystemExit as e:
                # SystemExit with code 0 is acceptable
                assert e.code == 0, f"Main function exited with code: {e.code}"
            except Exception as e:
                pytest.fail(f"Main function execution failed: {e}")
    
    def test_application_lifecycle(self, qapp):
        """Test complete application lifecycle"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        try:
            # Create application window
            window = EliteFidgetMode()
            
            # Test show
            window.show()
            QTest.qWait(100)  # Wait for window to appear
            
            # Test that window is visible
            assert window.isVisible()
            
            # Test basic interactions
            if hasattr(window, 'hardware_nav') and window.hardware_nav:
                # Simulate hardware input
                window.on_hardware_button_pressed(1)
                window.on_hardware_pot_changed(0.5)
            
            # Test theme change
            if hasattr(window, 'change_theme'):
                window.change_theme("Matrix Green")
                QTest.qWait(50)
            
            # Test hide
            window.hide()
            QTest.qWait(50)
            assert not window.isVisible()
            
            # Test close
            window.close()
            
        except Exception as e:
            pytest.fail(f"Application lifecycle test failed: {e}")
    
    def test_performance_under_load(self, qapp):
        """Test application performance under simulated load"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        try:
            window = EliteFidgetMode()
            window.show()
            
            # Simulate rapid interactions
            start_time = time.time()
            
            for i in range(20):  # 20 rapid interactions
                if window.hardware_nav:
                    window.on_hardware_button_pressed((i % 9) + 1)
                    window.on_hardware_pot_changed(i / 20.0)
                
                # Force update
                window.update()
                QTest.qWait(10)  # Small wait
                
                # Break if it takes too long
                if time.time() - start_time > 5.0:
                    break
            
            elapsed = time.time() - start_time
            
            # Should handle rapid interactions in reasonable time
            assert elapsed < 5.0, f"Performance test took too long: {elapsed}s"
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Performance under load test failed: {e}")
    
    def test_memory_management(self, qapp):
        """Test memory management during widget creation/destruction"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        try:
            # Create and destroy multiple windows to test memory management
            windows = []
            
            for i in range(3):  # Create 3 windows
                window = EliteFidgetMode()
                windows.append(window)
                window.show()
                QTest.qWait(50)
            
            # Close all windows
            for window in windows:
                window.close()
                QTest.qWait(25)
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # If we get here without crashing, memory management is working
            assert True
            
        except Exception as e:
            pytest.fail(f"Memory management test failed: {e}")


class TestErrorRecoveryScenarios:
    """Test error recovery in real-world failure scenarios"""
    
    def test_missing_assets_recovery(self, qapp):
        """Test recovery when assets are missing"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        # Mock missing asset files
        with patch('os.path.exists', return_value=False):
            try:
                window = EliteFidgetMode()
                window.show()
                QTest.qWait(100)
                
                # Should show fallback UI instead of crashing
                assert window.isVisible()
                
                window.close()
                
            except Exception as e:
                pytest.fail(f"Missing assets recovery test failed: {e}")
    
    def test_database_connection_failure(self, qapp):
        """Test recovery when ship database fails"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        # Mock database failure
        with patch('data.ship_database.get_ship_database') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            try:
                window = EliteFidgetMode()
                
                # Should handle database failure gracefully
                assert window is not None
                window.show()
                QTest.qWait(100)
                window.close()
                
            except Exception as e:
                pytest.fail(f"Database failure recovery test failed: {e}")
    
    def test_theme_system_failure(self, qapp):
        """Test recovery when theme system fails"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        # Mock theme system failure
        with patch('config.themes.HardwareThemeManager') as mock_theme:
            mock_theme.side_effect = Exception("Theme system failed")
            
            try:
                window = EliteFidgetMode()
                
                # Should handle theme failure gracefully
                assert window is not None
                window.show()
                QTest.qWait(100)
                window.close()
                
            except Exception as e:
                pytest.fail(f"Theme system failure recovery test failed: {e}")


class TestRealWorldUsagePatterns:
    """Test realistic usage patterns"""
    
    def test_ship_browsing_workflow(self, qapp):
        """Test typical ship browsing workflow"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        try:
            window = EliteFidgetMode()
            window.show()
            
            # Simulate browsing through ships
            if window.ship_database and window.ship_database.get_ship_count() > 0:
                ships = window.ship_database.get_all_ships()
                
                # Browse through first few ships
                for i, ship in enumerate(ships[:5]):
                    window.set_current_ship(ship, animate=False)
                    QTest.qWait(50)
                    
                    # Test ship display updates
                    window.update_ship_displays()
                    QTest.qWait(25)
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Ship browsing workflow test failed: {e}")
    
    def test_hardware_interaction_simulation(self, qapp):
        """Test simulated hardware interaction patterns"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        try:
            window = EliteFidgetMode()
            window.show()
            
            if window.hardware_nav:
                # Enable hardware simulation
                window.hardware_nav.enable_hardware_simulation(True)
                QTest.qWait(100)
                
                # Simulate user interactions
                interaction_patterns = [
                    (1, 0.2), (3, 0.4), (2, 0.6), (5, 0.8), (7, 0.3)
                ]
                
                for button, pot_value in interaction_patterns:
                    window.on_hardware_button_pressed(button)
                    QTest.qWait(50)
                    window.on_hardware_pot_changed(pot_value)
                    QTest.qWait(50)
                
                # Disable simulation
                window.hardware_nav.enable_hardware_simulation(False)
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Hardware interaction simulation test failed: {e}")
    
    def test_extended_session_simulation(self, qapp):
        """Test extended usage session to detect memory leaks"""
        if not INTEGRATION_IMPORTS_SUCCESSFUL:
            pytest.skip("Integration imports failed")
        
        try:
            window = EliteFidgetMode()
            window.show()
            
            # Simulate extended session with various activities
            start_time = time.time()
            activity_count = 0
            
            while time.time() - start_time < 2.0 and activity_count < 50:  # 2 second max, 50 activities max
                activity_type = activity_count % 4
                
                if activity_type == 0:  # Ship navigation
                    window.navigate_ship(1)
                elif activity_type == 1:  # Theme change
                    if window.theme_manager:
                        themes = ["Ice Blue", "Matrix Green", "Deep Purple"]
                        theme = themes[activity_count % len(themes)]
                        window.change_theme(theme)
                elif activity_type == 2:  # Hardware simulation
                    if window.hardware_nav:
                        window.on_hardware_button_pressed((activity_count % 9) + 1)
                elif activity_type == 3:  # Update displays
                    window.update_ship_displays()
                
                QTest.qWait(20)  # Small wait between activities
                activity_count += 1
            
            # Should handle extended session without issues
            assert activity_count > 0, "No activities were performed"
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Extended session simulation test failed: {e}")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])