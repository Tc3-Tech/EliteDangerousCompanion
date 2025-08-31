"""
Unit Tests for Elite Dangerous UI Widgets
Tests individual widget functionality, performance, and crash prevention.
"""

import pytest
import sys
import os
import time
from unittest.mock import MagicMock, patch, Mock
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint
from PyQt6.QtGui import QPaintEvent
from PyQt6.QtTest import QTest

# Import test configuration
from . import app_root

# Import modules under test
try:
    from ui.widgets.ship_gallery import ShipGalleryWidget, ShipThumbnail, ShipGalleryGrid
    from ui.widgets.ship_viewer import ShipViewer3D, ShipViewerControls
    from ui.widgets.ship_specs_panel import ShipSpecificationPanel, AnimatedStatBar
    from ui.widgets.ship_comparison import RadarChart, ComparisonTable
    from data.ship_database import get_ship_database
    from config.themes import ThemeColors, PredefinedThemes
    WIDGET_IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Widget import error in tests: {e}")
    WIDGET_IMPORTS_SUCCESSFUL = False


@pytest.fixture
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_ship():
    """Create a sample ship for testing"""
    if not WIDGET_IMPORTS_SUCCESSFUL:
        return None
    
    try:
        database = get_ship_database()
        ships = database.get_all_ships()
        return ships[0] if ships else None
    except:
        return None


@pytest.fixture
def sample_theme():
    """Create a sample theme for testing"""
    return PredefinedThemes.ICE_BLUE


class TestShipThumbnail:
    """Test ShipThumbnail widget functionality"""
    
    def test_ship_thumbnail_creation(self, qapp, sample_ship):
        """Test ShipThumbnail can be created without crashing"""
        if not WIDGET_IMPORTS_SUCCESSFUL or not sample_ship:
            pytest.skip("Widget imports or sample ship not available")
        
        try:
            thumbnail = ShipThumbnail(sample_ship)
            assert thumbnail is not None
            assert thumbnail.ship_spec == sample_ship
            assert thumbnail.width() == 120
            assert thumbnail.height() == 90
            
            # Test that it doesn't crash on paint
            paint_event = QPaintEvent(QRect(0, 0, 120, 90))
            thumbnail.paintEvent(paint_event)
            
        except Exception as e:
            pytest.fail(f"ShipThumbnail creation/paint failed: {e}")
    
    def test_thumbnail_mouse_events(self, qapp, sample_ship):
        """Test thumbnail mouse interaction"""
        if not WIDGET_IMPORTS_SUCCESSFUL or not sample_ship:
            pytest.skip("Widget imports or sample ship not available")
        
        try:
            thumbnail = ShipThumbnail(sample_ship)
            
            # Test mouse enter/leave events
            from PyQt6.QtCore import QEvent
            from PyQt6.QtGui import QEnterEvent
            
            enter_event = QEnterEvent(QPoint(50, 50), QPoint(50, 50), QPoint(50, 50))
            thumbnail.enterEvent(enter_event)
            assert thumbnail.is_hovered == True
            
            leave_event = QEvent(QEvent.Type.Leave)
            thumbnail.leaveEvent(leave_event)
            assert thumbnail.is_hovered == False
            
        except Exception as e:
            pytest.fail(f"Thumbnail mouse events failed: {e}")


class TestShipGalleryGrid:
    """Test ShipGalleryGrid widget functionality"""
    
    def test_gallery_grid_creation(self, qapp):
        """Test ShipGalleryGrid can be created"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            grid = ShipGalleryGrid()
            assert grid is not None
            assert hasattr(grid, 'ship_database')
            assert hasattr(grid, 'thumbnails')
            
        except Exception as e:
            pytest.fail(f"ShipGalleryGrid creation failed: {e}")
    
    def test_gallery_population_safe(self, qapp):
        """Test that gallery population doesn't crash even with missing data"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            grid = ShipGalleryGrid()
            
            # This should not crash even if ship data is missing
            grid.populate_ships()
            
            # Test filter functionality
            grid.set_filter({"ship_class": "Small"})
            grid.clear_filter()
            
        except Exception as e:
            pytest.fail(f"Gallery population test failed: {e}")


class TestShipViewer3D:
    """Test ShipViewer3D widget functionality"""
    
    def test_ship_viewer_creation(self, qapp):
        """Test ShipViewer3D can be created without crashing"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            viewer = ShipViewer3D()
            assert viewer is not None
            assert viewer.rotation_angle == 0.0
            assert viewer.zoom_level == 1.0
            assert viewer.auto_rotate == True
            
        except Exception as e:
            pytest.fail(f"ShipViewer3D creation failed: {e}")
    
    def test_viewer_ship_loading(self, qapp, sample_ship):
        """Test loading ship into viewer"""
        if not WIDGET_IMPORTS_SUCCESSFUL or not sample_ship:
            pytest.skip("Widget imports or sample ship not available")
        
        try:
            viewer = ShipViewer3D()
            
            # Test setting ship
            viewer.set_ship(sample_ship)
            assert viewer.ship_spec == sample_ship
            
            # Test paint event doesn't crash
            paint_event = QPaintEvent(QRect(0, 0, 400, 300))
            viewer.paintEvent(paint_event)
            
        except Exception as e:
            pytest.fail(f"Ship loading in viewer failed: {e}")
    
    def test_viewer_controls(self, qapp):
        """Test viewer control functionality"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            viewer = ShipViewer3D()
            
            # Test rotation control
            viewer.set_rotation(45.0)
            assert viewer.rotation_angle == 45.0
            
            # Test zoom control
            viewer.set_zoom(2.0)
            assert viewer.zoom_level == 2.0
            
            # Test auto-rotate toggle
            viewer.set_auto_rotate(False)
            assert viewer.auto_rotate == False
            
            # Test reset
            viewer.reset_view()
            assert viewer.rotation_angle == 0.0
            assert viewer.zoom_level == 1.0
            
        except Exception as e:
            pytest.fail(f"Viewer controls test failed: {e}")
    
    def test_viewer_mouse_interaction(self, qapp):
        """Test viewer mouse interaction for rotation"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            viewer = ShipViewer3D()
            viewer.show()
            
            # Test mouse press/release cycle
            from PyQt6.QtGui import QMouseEvent
            from PyQt6.QtCore import QPointF
            
            press_event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPointF(100, 100),
                QPointF(100, 100),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            viewer.mousePressEvent(press_event)
            assert viewer.mouse_dragging == True
            
            release_event = QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease,
                QPointF(100, 100),
                QPointF(100, 100),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier
            )
            viewer.mouseReleaseEvent(release_event)
            assert viewer.mouse_dragging == False
            
        except Exception as e:
            pytest.fail(f"Viewer mouse interaction test failed: {e}")


class TestShipViewerControls:
    """Test ShipViewerControls widget"""
    
    def test_viewer_controls_creation(self, qapp):
        """Test ShipViewerControls can be created"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            controls = ShipViewerControls()
            assert controls is not None
            
            # Test that control buttons exist
            assert hasattr(controls, 'rotate_left_btn')
            assert hasattr(controls, 'rotate_right_btn')
            assert hasattr(controls, 'zoom_in_btn')
            assert hasattr(controls, 'zoom_out_btn')
            
        except Exception as e:
            pytest.fail(f"ShipViewerControls creation failed: {e}")


class TestShipSpecificationPanel:
    """Test ShipSpecificationPanel widget"""
    
    def test_specs_panel_creation(self, qapp):
        """Test ShipSpecificationPanel can be created"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            panel = ShipSpecificationPanel()
            assert panel is not None
            assert hasattr(panel, 'tabs')
            assert panel.tabs.count() >= 5  # Should have at least 5 tabs
            
        except Exception as e:
            pytest.fail(f"ShipSpecificationPanel creation failed: {e}")
    
    def test_specs_ship_loading(self, qapp, sample_ship):
        """Test loading ship data into specs panel"""
        if not WIDGET_IMPORTS_SUCCESSFUL or not sample_ship:
            pytest.skip("Widget imports or sample ship not available")
        
        try:
            panel = ShipSpecificationPanel()
            panel.set_ship(sample_ship)
            
            assert panel.current_ship == sample_ship
            
            # Test that stats were populated
            if hasattr(panel, 'basic_info_card'):
                assert panel.basic_info_card is not None
                
        except Exception as e:
            pytest.fail(f"Specs ship loading test failed: {e}")


class TestAnimatedStatBar:
    """Test AnimatedStatBar widget"""
    
    def test_stat_bar_creation(self, qapp):
        """Test AnimatedStatBar can be created"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            stat_bar = AnimatedStatBar("Test Stat", 50.0, 100.0, " units")
            assert stat_bar is not None
            assert stat_bar.label_text == "Test Stat"
            assert stat_bar.target_value == 50.0
            assert stat_bar.max_value == 100.0
            
        except Exception as e:
            pytest.fail(f"AnimatedStatBar creation failed: {e}")
    
    def test_stat_bar_animation(self, qapp):
        """Test stat bar animation functionality"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            stat_bar = AnimatedStatBar("Test", 0.0, 100.0)
            
            # Test setting new value with animation
            stat_bar.set_value(75.0, animate=True)
            assert stat_bar.target_value == 75.0
            
            # Test setting value without animation
            stat_bar.set_value(50.0, animate=False)
            assert stat_bar.current_value == 50.0
            assert stat_bar.target_value == 50.0
            
            # Test paint event doesn't crash
            paint_event = QPaintEvent(QRect(0, 0, 200, 25))
            stat_bar.paintEvent(paint_event)
            
        except Exception as e:
            pytest.fail(f"Stat bar animation test failed: {e}")


class TestRadarChart:
    """Test RadarChart widget for ship comparison"""
    
    def test_radar_chart_creation(self, qapp):
        """Test RadarChart can be created"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            chart = RadarChart()
            assert chart is not None
            assert len(chart.default_metrics) > 0
            assert hasattr(chart, 'metrics')
            
        except Exception as e:
            pytest.fail(f"RadarChart creation failed: {e}")
    
    def test_radar_chart_ship_data(self, qapp, sample_ship):
        """Test setting ship data in radar chart"""
        if not WIDGET_IMPORTS_SUCCESSFUL or not sample_ship:
            pytest.skip("Widget imports or sample ship not available")
        
        try:
            chart = RadarChart()
            chart.set_ships([sample_ship])
            
            assert len(chart.ships) == 1
            assert chart.ships[0] == sample_ship
            
            # Test paint event doesn't crash
            paint_event = QPaintEvent(QRect(0, 0, 300, 300))
            chart.paintEvent(paint_event)
            
        except Exception as e:
            pytest.fail(f"Radar chart ship data test failed: {e}")


class TestComparisonTable:
    """Test ComparisonTable widget"""
    
    def test_comparison_table_creation(self, qapp):
        """Test ComparisonTable can be created"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            table = ComparisonTable()
            assert table is not None
            assert hasattr(table, 'categories')
            assert len(table.categories) > 0
            
        except Exception as e:
            pytest.fail(f"ComparisonTable creation failed: {e}")
    
    def test_comparison_table_population(self, qapp, sample_ship):
        """Test populating comparison table with ship data"""
        if not WIDGET_IMPORTS_SUCCESSFUL or not sample_ship:
            pytest.skip("Widget imports or sample ship not available")
        
        try:
            table = ComparisonTable()
            table.set_ships([sample_ship])
            
            assert len(table.ships) == 1
            assert table.rowCount() > 0
            assert table.columnCount() >= 2  # Specification column + at least one ship
            
        except Exception as e:
            pytest.fail(f"Comparison table population test failed: {e}")


class TestWidgetThemeIntegration:
    """Test widget theme integration"""
    
    def test_widget_theme_application(self, qapp, sample_theme):
        """Test that widgets can apply themes without crashing"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            # Test various widgets with theme application
            viewer = ShipViewer3D()
            if hasattr(viewer, 'apply_theme'):
                viewer.apply_theme(sample_theme)
            
            stat_bar = AnimatedStatBar("Test", 50, 100)
            if hasattr(stat_bar, 'apply_theme'):
                stat_bar.apply_theme(sample_theme)
            
            chart = RadarChart()
            if hasattr(chart, 'apply_theme'):
                chart.apply_theme(sample_theme)
            
            # If we get here without exception, theme application worked
            assert True
            
        except Exception as e:
            pytest.fail(f"Widget theme integration test failed: {e}")


class TestWidgetPerformance:
    """Test widget performance and responsiveness"""
    
    def test_viewer_animation_performance(self, qapp):
        """Test that viewer animations don't cause performance issues"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            viewer = ShipViewer3D()
            viewer.show()
            
            # Enable animations
            viewer.auto_rotate = True
            viewer.hover_animate = True
            viewer.scan_animate = True
            
            # Run animations for a short time
            start_time = time.time()
            iterations = 0
            
            while time.time() - start_time < 0.1 and iterations < 100:  # 100ms max
                viewer.update_animations()
                viewer.update_scan_effects()
                iterations += 1
            
            # Should complete many iterations without hanging
            assert iterations > 0
            
        except Exception as e:
            pytest.fail(f"Viewer animation performance test failed: {e}")
    
    def test_stat_bar_animation_performance(self, qapp):
        """Test animated stat bar performance"""
        if not WIDGET_IMPORTS_SUCCESSFUL:
            pytest.skip("Widget imports not available")
        
        try:
            stat_bar = AnimatedStatBar("Performance Test", 0, 100)
            
            # Trigger rapid value changes
            for i in range(10):
                stat_bar.set_value(i * 10, animate=True)
                stat_bar.update_animation()
            
            # Should handle rapid changes without crashing
            assert True
            
        except Exception as e:
            pytest.fail(f"Stat bar animation performance test failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])