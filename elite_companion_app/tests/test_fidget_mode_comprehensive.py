"""
Comprehensive Test Suite for Elite Dangerous Fidget Mode
Tests all functionality including widget creation, theme management, and crash prevention.
"""

import pytest
import sys
import os
import time
from unittest.mock import MagicMock, patch, Mock
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

# Import test configuration
from . import app_root

# Import modules under test
try:
    from ui.fidget_mode import EliteFidgetMode, AnimatedTransition, HardwareNavigationManager
    from data.ship_database import get_ship_database
    from config.themes import HardwareThemeManager
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Import error in tests: {e}")
    IMPORTS_SUCCESSFUL = False


class TestFidgetModeImports:
    """Test that all imports work correctly"""
    
    def test_imports_successful(self):
        """Test that all required imports are available"""
        assert IMPORTS_SUCCESSFUL, "Critical imports failed"
    
    def test_ship_database_available(self):
        """Test that ship database can be imported and initialized"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        database = get_ship_database()
        assert database is not None
        assert database.get_ship_count() > 0


@pytest.fixture
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Clean up is handled by pytest-qt


class TestAnimatedTransition:
    """Test the animated transition system"""
    
    def test_animated_transition_creation(self, qapp):
        """Test that AnimatedTransition can be created without crashing"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        parent = QMainWindow()
        transition = AnimatedTransition(parent)
        
        assert transition is not None
        assert not transition.is_transitioning
        assert transition.transition_duration == 500


class TestHardwareNavigationManager:
    """Test hardware navigation system"""
    
    def test_hardware_nav_creation(self, qapp):
        """Test that HardwareNavigationManager can be created"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        nav_manager = HardwareNavigationManager()
        
        assert nav_manager is not None
        assert len(nav_manager.button_mappings) == 9
        assert nav_manager.pot_mode == "theme"
    
    def test_hardware_simulation(self, qapp):
        """Test hardware simulation functionality"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        nav_manager = HardwareNavigationManager()
        
        # Test enabling simulation
        nav_manager.enable_hardware_simulation(True)
        assert nav_manager.enable_simulation == True
        
        # Test disabling simulation
        nav_manager.enable_hardware_simulation(False)
        assert nav_manager.enable_simulation == False


class TestEliteFidgetModeInitialization:
    """Test Elite Fidget Mode initialization and crash prevention"""
    
    def test_fidget_mode_creation_safe(self, qapp):
        """Test that EliteFidgetMode can be created without segmentation fault"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        # Test creation in a try-catch to detect crashes
        try:
            window = EliteFidgetMode()
            assert window is not None
            assert window.ship_database is not None
            
            # Test that the window has basic properties
            assert window.windowTitle() == "Elite Dangerous - Ship Database Fidget Mode"
            assert window.minimumWidth() >= 800
            assert window.minimumHeight() >= 600
            
            # Clean up
            window.close()
            
        except Exception as e:
            pytest.fail(f"EliteFidgetMode creation crashed: {e}")
    
    def test_window_components_initialized(self, qapp):
        """Test that all window components are properly initialized"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        try:
            window = EliteFidgetMode()
            
            # Test that core components exist (even if they failed to initialize)
            assert hasattr(window, 'ship_database')
            assert hasattr(window, 'theme_manager')
            assert hasattr(window, 'hardware_nav')
            assert hasattr(window, 'transition_manager')
            
            # Test UI components exist
            assert hasattr(window, 'gallery_widget')
            assert hasattr(window, 'ship_viewer')
            assert hasattr(window, 'specs_panel')
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Component initialization failed: {e}")
    
    def test_error_handling_graceful(self, qapp):
        """Test that errors in initialization don't crash the application"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        # Mock a component to fail and ensure graceful handling
        with patch('ui.fidget_mode.get_ship_database') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            try:
                window = EliteFidgetMode()
                # Should not crash, should have fallbacks
                assert window is not None
                window.close()
            except Exception as e:
                # If it crashes, the error handling isn't working
                pytest.fail(f"Application crashed instead of handling error gracefully: {e}")


class TestFidgetModeThemeManagement:
    """Test theme management functionality"""
    
    def test_theme_manager_initialization(self, qapp):
        """Test that theme manager initializes correctly"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        try:
            window = EliteFidgetMode()
            
            # Theme manager should exist (or be None with graceful fallback)
            assert hasattr(window, 'theme_manager')
            
            # If theme manager exists, test basic functionality
            if window.theme_manager is not None:
                assert hasattr(window.theme_manager, 'current_theme')
                assert hasattr(window.theme_manager, 'set_predefined_theme')
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Theme manager test failed: {e}")


class TestFidgetModePerformance:
    """Test performance aspects and crash prevention"""
    
    def test_fps_counter_functionality(self, qapp):
        """Test that FPS counter works without crashing"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        try:
            window = EliteFidgetMode()
            
            # Test FPS counter attributes
            assert hasattr(window, 'fps_counter')
            assert hasattr(window, 'last_fps_time')
            assert hasattr(window, 'fps_timer')
            
            # Test that FPS update doesn't crash
            window.update_performance_metrics()
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"FPS counter test failed: {e}")
    
    def test_paint_event_safe(self, qapp):
        """Test that paint events don't cause crashes"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        try:
            window = EliteFidgetMode()
            window.show()
            
            # Force a paint event
            window.update()
            QTest.qWait(100)  # Wait for paint
            
            # Test manual paint event
            from PyQt6.QtGui import QPaintEvent
            from PyQt6.QtCore import QRect
            
            paint_event = QPaintEvent(QRect(0, 0, window.width(), window.height()))
            window.paintEvent(paint_event)
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Paint event test failed: {e}")


class TestFidgetModeShipLoading:
    """Test ship loading and display functionality"""
    
    def test_ship_loading_safe(self, qapp):
        """Test that ship loading doesn't crash"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        try:
            window = EliteFidgetMode()
            
            # Test loading default ship
            window.load_default_ship()
            
            # Should have a current ship or gracefully handle absence
            assert hasattr(window, 'current_ship')
            
            # If ship database is available, test ship selection
            if window.ship_database and window.ship_database.get_ship_count() > 0:
                ships = window.ship_database.get_all_ships()
                if ships:
                    # Test setting a ship
                    window.set_current_ship(ships[0], animate=False)
                    assert window.current_ship is not None
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Ship loading test failed: {e}")


class TestFidgetModeIntegration:
    """Integration tests for complete workflow"""
    
    def test_complete_initialization_workflow(self, qapp):
        """Test the complete initialization workflow"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        try:
            # Test step-by-step initialization
            window = EliteFidgetMode()
            
            # Verify each initialization step completed
            assert window.ship_database is not None
            
            # Test show and hide
            window.show()
            QTest.qWait(100)
            
            window.hide()
            QTest.qWait(50)
            
            # Test close
            window.close()
            
        except Exception as e:
            pytest.fail(f"Complete workflow test failed: {e}")
    
    def test_hardware_integration_safe(self, qapp):
        """Test hardware integration doesn't crash"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        try:
            window = EliteFidgetMode()
            
            if window.hardware_nav is not None:
                # Test hardware button press simulation
                window.on_hardware_button_pressed(1)
                window.on_hardware_button_pressed(5)
                window.on_hardware_button_pressed(9)
                
                # Test potentiometer simulation
                window.on_hardware_pot_changed(0.5)
                window.on_hardware_pot_changed(0.8)
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Hardware integration test failed: {e}")


class TestFidgetModeErrorRecovery:
    """Test error recovery and resilience"""
    
    def test_missing_assets_handling(self, qapp):
        """Test handling of missing assets"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        try:
            window = EliteFidgetMode()
            
            # Should handle missing assets gracefully
            # Test by trying to load a non-existent ship image
            if window.ship_viewer:
                # This should not crash even with missing assets
                window.update_ship_displays()
            
            window.close()
            
        except Exception as e:
            pytest.fail(f"Missing assets test failed: {e}")
    
    def test_widget_failure_resilience(self, qapp):
        """Test resilience to widget creation failures"""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip("Imports failed")
        
        # Test with mocked widget failures
        with patch('ui.widgets.ship_gallery.ShipGalleryWidget') as mock_gallery:
            mock_gallery.side_effect = Exception("Widget creation failed")
            
            try:
                window = EliteFidgetMode()
                # Should create fallback UI instead of crashing
                assert window is not None
                window.close()
            except Exception as e:
                pytest.fail(f"Widget failure resilience test failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])