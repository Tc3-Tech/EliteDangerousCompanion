"""
Elite Dangerous Professional Ship Viewer
Clean, static ship presentation with professional technical overlays and HUD elements.
Optimized for 1024x768 display and smooth performance.
"""
import sys
import os
import math
import time
import random
from typing import Optional, Dict, List, Tuple, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import (Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, 
                        QRect, QSize, QPoint, QParallelAnimationGroup, QRectF, QPointF)
from PyQt6.QtGui import (QPainter, QPen, QBrush, QLinearGradient, QPixmap, QTransform, 
                       QFont, QFontMetrics, QColor, QPainterPath, QRadialGradient,
                       QPaintEvent, QResizeEvent, QWheelEvent, QMouseEvent)

# Add app root to path for imports
from pathlib import Path
app_root = Path(__file__).parent.parent.parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

from data.ship_database import ShipSpecification, get_ship_database
from ui.elite_widgets import ThemeAwareWidget, get_global_theme_manager
from config.themes import ThemeColors
from utils.image_optimizer import get_smart_image_manager


class ShipViewer3D(QWidget, ThemeAwareWidget):
    """Professional static ship viewer with clean presentation and technical overlays"""
    
    ship_clicked = pyqtSignal(str)  # Emits ship key when clicked
    zoom_changed = pyqtSignal(float)  # Emits current zoom level
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        # Core data - safe initialization
        self.ship_spec = None
        self.ship_image = None
        self.original_ship_image = None
        self._current_theme = None
        
        # Cleanup tracking
        self._is_destroyed = False
        self._cleanup_performed = False
        
        # Clean presentation parameters (no fake 3D)
        self.hover_phase = 0.0
        self.zoom_level = 1.0
        self.position_x = 0.0
        self.position_y = 0.0
        
        # Animation state (professional minimal effects only)
        self.hover_animate = True
        self.scan_animate = True
        self.pulse_animate = True
        
        # Scanning effects
        self.scan_line_position = 0.0
        self.scan_direction = 1.0
        self.scan_active = True
        
        # Technical overlay data
        self.technical_readouts = []
        self.scan_points = []
        self.target_reticles = []
        
        # Performance optimization
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 60.0
        self.target_fps = 60.0
        
        # Mouse interaction (zoom only)
        self.mouse_dragging = False
        self.last_mouse_pos = QPoint()
        
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        self.setup_animations()
        self.generate_scan_points()
        
        # Register with theme manager safely
        try:
            get_global_theme_manager().register_widget(self)
        except Exception as e:
            print(f"Warning: Could not register with theme manager: {e}")
    
    def setup_animations(self):
        """Setup animation timers for smooth 60fps performance"""
        # Main animation timer - 60 FPS target with parent for proper cleanup
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.safe_update_animations)
        self.animation_timer.start(16)  # ~60 FPS
        
        # Scanning animation timer - 30 FPS for efficiency with parent
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.safe_update_scan_effects)
        self.scan_timer.start(33)  # ~30 FPS
        
        # Performance monitoring timer with parent
        self.fps_timer = QTimer(self)
        self.fps_timer.timeout.connect(self.safe_update_fps)
        self.fps_timer.start(1000)  # 1 second intervals
    
    def set_ship(self, ship_spec: ShipSpecification):
        """Set the ship to display"""
        self.ship_spec = ship_spec
        self.load_ship_image()
        self.generate_technical_readouts()
        self.generate_target_reticles()
        self.update()
    
    def load_ship_image(self):
        """Load and prepare ship image for 3D effects using optimized loading"""
        if not self.ship_spec:
            return
        
        try:
            # Use smart image manager for optimized loading
            image_manager = get_smart_image_manager()
            self.ship_image = image_manager.get_optimized_image(self.ship_spec.name, "viewer")
        except Exception as e:
            print(f"Warning: Smart image manager failed: {e}")
            self.ship_image = None
        
        # Fallback to direct loading if optimized version fails
        if not self.ship_image:
            try:
                image_path = self.ship_spec.get_image_path()
                if os.path.exists(image_path):
                    self.original_ship_image = QPixmap(image_path)
                    if not self.original_ship_image.isNull():
                        # Pre-scale for optimal performance at 1024x768
                        optimal_size = min(400, self.width() - 100 if self.width() > 100 else 300)
                        self.ship_image = self.original_ship_image.scaled(
                            optimal_size, optimal_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                else:
                    print(f"Warning: Ship image not found: {image_path}")
            except Exception as e:
                print(f"Warning: Direct image loading failed: {e}")
                self.ship_image = None
    
    def generate_technical_readouts(self):
        """Generate technical readout positions and data"""
        if not self.ship_spec:
            return
        
        self.technical_readouts = [
            {"text": f"MASS: {self.ship_spec.performance.hull_mass:.1f}t", "pos": (50, 80), "type": "mass"},
            {"text": f"LENGTH: {self.ship_spec.dimensions.length:.1f}m", "pos": (50, 100), "type": "dimension"},
            {"text": f"MAX SPEED: {self.ship_spec.performance.max_speed} m/s", "pos": (50, 120), "type": "performance"},
            {"text": f"JUMP RANGE: {self.ship_spec.performance.base_jump_range:.2f} ly", "pos": (50, 140), "type": "performance"},
            {"text": f"SHIELDS: {self.ship_spec.performance.base_shield_strength} MJ", "pos": (50, 160), "type": "defensive"},
            {"text": f"HARDPOINTS: {self.ship_spec.hardpoints.total_hardpoints}", "pos": (50, 180), "type": "offensive"},
            {"text": f"INTEGRITY: 100%", "pos": (50, 200), "type": "status"},
            {"text": f"FUEL: {self.ship_spec.performance.fuel_capacity}t", "pos": (50, 220), "type": "fuel"},
        ]
    
    def generate_scan_points(self):
        """Generate scanning target points"""
        self.scan_points = []
        for _ in range(8):
            x = random.uniform(0.2, 0.8)
            y = random.uniform(0.2, 0.8)
            phase = random.uniform(0, 2 * math.pi)
            intensity = random.uniform(0.3, 1.0)
            self.scan_points.append({"x": x, "y": y, "phase": phase, "intensity": intensity})
    
    def generate_target_reticles(self):
        """Generate targeting reticle positions"""
        if not self.ship_spec:
            return
        
        self.target_reticles = []
        # Generate reticles based on ship hardpoints
        hardpoint_count = self.ship_spec.hardpoints.total_hardpoints
        for i in range(min(hardpoint_count, 6)):  # Limit for performance
            angle = (i / max(1, hardpoint_count - 1)) * math.pi * 2
            distance = 0.3 + (i % 2) * 0.2
            x = 0.5 + distance * math.cos(angle)
            y = 0.5 + distance * math.sin(angle)
            self.target_reticles.append({"x": x, "y": y, "size": 20 + (i % 3) * 10, "active": i < 3})
    
    def safe_update_animations(self):
        """Safely update animations with destruction check"""
        if self._is_destroyed or self._cleanup_performed:
            return
        try:
            self.update_animations()
        except Exception as e:
            print(f"Animation update error: {e}")
            self.cleanup_resources()
    
    def update_animations(self):
        """Update all animations - called at 60 FPS"""
        if self._is_destroyed:
            return
            
        current_time = time.time()
        
        # Gentle hover bobbing effect
        if self.hover_animate:
            self.hover_phase = (self.hover_phase + 0.03) % (2 * math.pi)  # Slower, more subtle
        
        # Pulse effects for technical elements
        if self.pulse_animate and self.scan_points:
            # Update scan point phases
            for point in self.scan_points:
                point["phase"] = (point["phase"] + 0.1) % (2 * math.pi)
        
        # Performance tracking
        self.frame_count += 1
        
        # Trigger repaint only if not destroyed
        if not self._is_destroyed:
            self.update()
    
    def safe_update_scan_effects(self):
        """Safely update scan effects with destruction check"""
        if self._is_destroyed or self._cleanup_performed:
            return
        try:
            self.update_scan_effects()
        except Exception as e:
            print(f"Scan effects update error: {e}")
            self.cleanup_resources()
    
    def update_scan_effects(self):
        """Update scanning effects - called at 30 FPS for efficiency"""
        if self._is_destroyed:
            return
            
        if self.scan_animate:
            # Scanning line movement
            self.scan_line_position += 0.02 * self.scan_direction
            if self.scan_line_position >= 1.0 or self.scan_line_position <= 0.0:
                self.scan_direction *= -1
                self.scan_line_position = max(0.0, min(1.0, self.scan_line_position))
    
    def safe_update_fps(self):
        """Safely update FPS with destruction check"""
        if self._is_destroyed or self._cleanup_performed:
            return
        try:
            self.update_fps()
        except Exception as e:
            print(f"FPS update error: {e}")
            self.cleanup_resources()
    
    def update_fps(self):
        """Update FPS counter"""
        if self._is_destroyed or not hasattr(self, 'animation_timer'):
            return
            
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        if elapsed > 0:
            self.current_fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
            
            # Adaptive quality based on FPS
            try:
                if self.current_fps < 45:
                    # Reduce animation frequency if FPS drops
                    self.animation_timer.setInterval(20)  # 50 FPS
                elif self.current_fps > 65:
                    # Restore full frequency if FPS is good
                    self.animation_timer.setInterval(16)  # 60 FPS
            except Exception:
                # Timer might be destroyed, ignore
                pass
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme colors to viewer"""
        self._current_theme = theme
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press - simplified for professional presentation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_dragging = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move - no rotation in professional mode"""
        # Professional mode - no fake rotation effects
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle wheel event for zooming"""
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        
        new_zoom = self.zoom_level * zoom_factor
        self.zoom_level = max(0.3, min(3.0, new_zoom))  # Clamp zoom range
        
        self.zoom_changed.emit(self.zoom_level)
        self.update()
    
    def paintEvent(self, event: QPaintEvent):
        """Main paint method with optimized rendering and safety checks"""
        if self._is_destroyed or self._cleanup_performed:
            return
            
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._safe_paint_content(painter)
        except Exception as e:
            print(f"Paint error in ship viewer: {e}")
            # Continue painting basic background to prevent visual corruption
            try:
                painter.fillRect(self.rect(), self.palette().window())
            except:
                pass
        finally:
            painter.end()
    
    def _safe_paint_content(self, painter: QPainter):
        """Paint content with error handling"""
        
        # Get theme colors
        if self._current_theme:
            primary_color = QColor(self._current_theme.primary)
            accent_color = QColor(self._current_theme.accent)
            text_color = QColor(self._current_theme.text)
            background_color = QColor(self._current_theme.background)
            surface_color = QColor(self._current_theme.surface)
        else:
            palette = self.palette()
            primary_color = palette.highlight().color()
            accent_color = palette.highlightedText().color()
            text_color = palette.text().color()
            background_color = palette.window().color()
            surface_color = palette.base().color()
        
        # Background with space-like gradient
        self.draw_space_background(painter, background_color, surface_color)
        
        # Technical grid overlay
        self.draw_technical_grid(painter, primary_color)
        
        # Ship with clean static presentation
        self.draw_ship_static(painter)
        
        # Scanning effects
        if self.scan_active:
            self.draw_scanning_effects(painter, accent_color)
        
        # Technical readouts with safety
        try:
            self.draw_technical_readouts(painter, text_color, accent_color)
        except Exception as e:
            print(f"Error drawing technical readouts: {e}")
        
        # Targeting reticles with safety
        try:
            self.draw_targeting_reticles(painter, primary_color, accent_color)
        except Exception as e:
            print(f"Error drawing targeting reticles: {e}")
        
        # HUD elements with safety
        try:
            self.draw_hud_elements(painter, primary_color, text_color)
        except Exception as e:
            print(f"Error drawing HUD elements: {e}")
        
        # Performance overlay (debug) with safety
        try:
            if self.current_fps < 50:  # Show FPS when performance is low
                self.draw_performance_info(painter, text_color)
        except Exception as e:
            print(f"Error drawing performance info: {e}")
    
    def draw_space_background(self, painter: QPainter, bg_color: QColor, surface_color: QColor):
        """Draw space-like background with subtle gradient"""
        gradient = QRadialGradient(self.width() / 2, self.height() / 2, max(self.width(), self.height()) / 2)
        gradient.setColorAt(0.0, surface_color)
        gradient.setColorAt(1.0, bg_color)
        
        painter.fillRect(self.rect(), gradient)
        
        # Add subtle star field effect
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        for i in range(20):  # Limited for performance
            x = (i * 47) % self.width()  # Pseudo-random but deterministic
            y = (i * 73) % self.height()
            painter.drawPoint(x, y)
    
    def draw_technical_grid(self, painter: QPainter, grid_color: QColor):
        """Draw technical grid overlay"""
        grid_pen = QPen(QColor(grid_color.red(), grid_color.green(), grid_color.blue(), 20), 1)
        painter.setPen(grid_pen)
        
        # Vertical lines
        for x in range(0, self.width(), 50):
            painter.drawLine(x, 0, x, self.height())
        
        # Horizontal lines
        for y in range(0, self.height(), 50):
            painter.drawLine(0, y, self.width(), y)
    
    def draw_ship_static(self, painter: QPainter):
        """Draw ship with clean, professional static presentation"""
        if not self.ship_image:
            return
        
        center_x = self.width() / 2 + self.position_x
        center_y = self.height() / 2 + self.position_y
        
        # Apply subtle hover bobbing (professional floating effect)
        hover_offset = math.sin(self.hover_phase) * 3  # Reduced from 5 to 3 for subtlety
        center_y += hover_offset
        
        # Create clean transformation matrix (no fake 3D effects)
        transform = QTransform()
        
        # Center the ship
        transform.translate(center_x, center_y)
        
        # Apply zoom only (no scaling distortions)
        transform.scale(self.zoom_level, self.zoom_level)
        
        # Center image for drawing
        img_width = self.ship_image.width()
        img_height = self.ship_image.height()
        transform.translate(-img_width / 2, -img_height / 2)
        
        painter.setTransform(transform)
        
        # Clean, professional glow effect (no fake lighting)
        if self._current_theme:
            glow_color = QColor(self._current_theme.accent)
            glow_color.setAlpha(30)  # Consistent subtle glow
            
            # Single clean glow layer
            for offset in range(1, 3):  # Minimal glow layers
                glow_transform = QTransform(transform)
                glow_transform.translate(-offset, -offset)
                painter.setTransform(glow_transform)
                
                glow_image = QPixmap(self.ship_image.size())
                glow_image.fill(glow_color)
                glow_image.setMask(self.ship_image.mask())
                painter.drawPixmap(0, 0, glow_image)
        
        # Draw main ship image (clean, undistorted)
        painter.setTransform(transform)
        painter.drawPixmap(0, 0, self.ship_image)
        
        painter.resetTransform()
    
    def draw_scanning_effects(self, painter: QPainter, scan_color: QColor):
        """Draw scanning line and pulse effects"""
        # Scanning line
        scan_y = int(self.scan_line_position * self.height())
        scan_pen = QPen(scan_color, 2)
        scan_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(scan_pen)
        painter.drawLine(0, scan_y, self.width(), scan_y)
        
        # Scanning points
        for point in self.scan_points:
            x = int(point["x"] * self.width())
            y = int(point["y"] * self.height())
            
            # Pulsing effect
            pulse = (math.sin(point["phase"]) + 1) / 2  # Normalize to 0-1
            alpha = int(50 + pulse * 100 * point["intensity"])
            
            point_color = QColor(scan_color)
            point_color.setAlpha(alpha)
            
            painter.setPen(QPen(point_color, 2))
            painter.setBrush(QBrush(point_color))
            
            radius = int(3 + pulse * 5)
            painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
    
    def draw_technical_readouts(self, painter: QPainter, text_color: QColor, accent_color: QColor):
        """Draw technical readout overlays"""
        font = QFont("Courier New", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        for i, readout in enumerate(self.technical_readouts):
            x, y = readout["pos"]
            
            # Typing effect (reveal text gradually)
            reveal_progress = min(1.0, (time.time() * 10 - i) % 20 / 2)  # Cycle every 2 seconds
            if reveal_progress < 0:
                continue
            
            text = readout["text"]
            reveal_length = int(len(text) * reveal_progress)
            displayed_text = text[:reveal_length]
            
            # Color coding by type
            if readout["type"] == "performance":
                painter.setPen(QPen(accent_color, 1))
            elif readout["type"] == "offensive":
                painter.setPen(QPen(QColor(255, 100, 100), 1))
            elif readout["type"] == "defensive":
                painter.setPen(QPen(QColor(100, 255, 100), 1))
            else:
                painter.setPen(QPen(text_color, 1))
            
            painter.drawText(x, y, displayed_text)
            
            # Cursor blink effect at end of text
            if reveal_progress < 1.0 and int(time.time() * 3) % 2:
                cursor_x = x + painter.fontMetrics().horizontalAdvance(displayed_text)
                painter.drawText(cursor_x, y, "_")
    
    def draw_targeting_reticles(self, painter: QPainter, primary_color: QColor, accent_color: QColor):
        """Draw targeting reticles around ship elements"""
        for i, reticle in enumerate(self.target_reticles):
            x = int(reticle["x"] * self.width())
            y = int(reticle["y"] * self.height())
            size = reticle["size"]
            
            color = accent_color if reticle["active"] else primary_color
            color.setAlpha(150 if reticle["active"] else 80)
            
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush())
            
            # Draw crosshair reticle
            half_size = size // 2
            
            # Outer circle
            painter.drawEllipse(x - half_size, y - half_size, size, size)
            
            # Cross lines
            painter.drawLine(x - half_size, y, x - half_size + 8, y)
            painter.drawLine(x + half_size - 8, y, x + half_size, y)
            painter.drawLine(x, y - half_size, x, y - half_size + 8)
            painter.drawLine(x, y + half_size - 8, x, y + half_size)
            
            # Center dot
            if reticle["active"]:
                painter.setBrush(QBrush(color))
                painter.drawEllipse(x - 2, y - 2, 4, 4)
    
    def draw_hud_elements(self, painter: QPainter, primary_color: QColor, text_color: QColor):
        """Draw HUD corner brackets and status indicators"""
        bracket_size = 20
        bracket_pen = QPen(primary_color, 2)
        painter.setPen(bracket_pen)
        
        # Corner brackets
        corners = [
            (10, 10, 1, 1),                                     # Top-left
            (self.width() - 30, 10, -1, 1),                    # Top-right
            (10, self.height() - 30, 1, -1),                   # Bottom-left
            (self.width() - 30, self.height() - 30, -1, -1)    # Bottom-right
        ]
        
        for x, y, h_dir, v_dir in corners:
            painter.drawLine(x, y, x + bracket_size * h_dir, y)
            painter.drawLine(x, y, x, y + bracket_size * v_dir)
        
        # Status indicators
        painter.setPen(QPen(text_color, 1))
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Ship name in top center
        if self.ship_spec:
            ship_name = self.ship_spec.display_name.upper()
            text_rect = painter.fontMetrics().boundingRect(ship_name)
            name_x = (self.width() - text_rect.width()) // 2
            painter.drawText(name_x, 25, ship_name)
        
        # Zoom level indicator
        zoom_text = f"ZOOM: {self.zoom_level:.1f}x"
        painter.drawText(self.width() - 120, self.height() - 15, zoom_text)
        
        # Status indicator (no fake rotation)
        status_text = "STATUS: READY"
        painter.drawText(15, self.height() - 15, status_text)
    
    def draw_performance_info(self, painter: QPainter, text_color: QColor):
        """Draw performance information overlay"""
        painter.setPen(QPen(text_color, 1))
        font = QFont("Courier New", 8)
        painter.setFont(font)
        
        fps_text = f"FPS: {self.current_fps:.1f}"
        painter.drawText(15, 40, fps_text)
    
    # Public control methods
    
    def set_zoom(self, zoom: float):
        """Set zoom level manually"""
        self.zoom_level = max(0.3, min(3.0, zoom))
        self.zoom_changed.emit(self.zoom_level)
    
    def toggle_scanning(self):
        """Toggle scanning effects"""
        self.scan_active = not self.scan_active
    
    def reset_view(self):
        """Reset view to default state"""
        self.zoom_level = 1.0
        self.position_x = 0.0
        self.position_y = 0.0
        self.zoom_changed.emit(self.zoom_level)
    
    def take_screenshot(self) -> QPixmap:
        """Take a screenshot of the current view"""
        return self.grab()
    
    def resizeEvent(self, event: QResizeEvent):
        """Handle resize event"""
        super().resizeEvent(event)
        
        # Reload ship image for new size
        if self.ship_spec and self.original_ship_image:
            optimal_size = min(400, self.width() - 100)
            self.ship_image = self.original_ship_image.scaled(
                optimal_size, optimal_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        
        # Regenerate scan points for new dimensions
        self.generate_scan_points()
    
    def cleanup_resources(self):
        """Critical cleanup method to prevent segfaults"""
        if self._cleanup_performed:
            return
            
        print("ShipViewer3D: Performing cleanup...")
        self._cleanup_performed = True
        self._is_destroyed = True
        
        try:
            # Stop and cleanup timers
            if hasattr(self, 'animation_timer') and self.animation_timer:
                self.animation_timer.stop()
                self.animation_timer.timeout.disconnect()
                self.animation_timer.deleteLater()
                self.animation_timer = None
                
            if hasattr(self, 'scan_timer') and self.scan_timer:
                self.scan_timer.stop()
                self.scan_timer.timeout.disconnect()
                self.scan_timer.deleteLater()
                self.scan_timer = None
                
            if hasattr(self, 'fps_timer') and self.fps_timer:
                self.fps_timer.stop()
                self.fps_timer.timeout.disconnect()
                self.fps_timer.deleteLater()
                self.fps_timer = None
            
            # Cleanup image resources
            if hasattr(self, 'ship_image'):
                self.ship_image = None
            if hasattr(self, 'original_ship_image'):
                self.original_ship_image = None
                
            # Clear data structures
            if hasattr(self, 'scan_points'):
                self.scan_points.clear()
            if hasattr(self, 'technical_readouts'):
                self.technical_readouts.clear()
            if hasattr(self, 'target_reticles'):
                self.target_reticles.clear()
                
            # Unregister from theme manager
            try:
                get_global_theme_manager().unregister_widget(self)
            except Exception as e:
                print(f"Warning: Could not unregister from theme manager: {e}")
                
        except Exception as e:
            print(f"Error during ShipViewer3D cleanup: {e}")
    
    def closeEvent(self, event):
        """Handle close event"""
        self.cleanup_resources()
        super().closeEvent(event)
    
    def __del__(self):
        """Destructor with cleanup"""
        try:
            self.cleanup_resources()
        except Exception:
            pass


class ShipViewerControls(QWidget, ThemeAwareWidget):
    """Professional control panel for ship viewer"""
    
    zoom_changed = pyqtSignal(float)
    scanning_toggled = pyqtSignal()
    view_reset = pyqtSignal()
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        # Cleanup tracking
        self._is_destroyed = False
        self._cleanup_performed = False
        
        self.setup_ui()
        
        # Register with theme manager safely
        try:
            get_global_theme_manager().register_widget(self)
        except Exception as e:
            print(f"Warning: Could not register ShipViewerControls with theme manager: {e}")
    
    def setup_ui(self):
        """Setup control UI - professional layout focused on essential controls"""
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Zoom controls
        zoom_label = QLabel("ZOOM:")
        zoom_label.setStyleSheet("color: #88ccff; font-size: 10px; font-weight: bold;")
        layout.addWidget(zoom_label)
        
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setFixedSize(25, 25)
        self.zoom_out_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 212, 255, 0.2);
                border: 1px solid #00d4ff;
                border-radius: 3px;
                color: #00d4ff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 212, 255, 0.4);
            }
        """)
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_changed.emit(0.8))
        layout.addWidget(self.zoom_out_btn)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(25, 25)
        self.zoom_in_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 212, 255, 0.2);
                border: 1px solid #00d4ff;
                border-radius: 3px;
                color: #00d4ff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 212, 255, 0.4);
            }
        """)
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_changed.emit(1.2))
        layout.addWidget(self.zoom_in_btn)
        
        
        # Professional toggle buttons
        self.scan_label = QLabel("ANALYSIS:")
        self.scan_label.setStyleSheet("color: #88ccff; font-size: 10px; font-weight: bold;")
        layout.addWidget(self.scan_label)
        
        self.scanning_btn = QPushButton("SCAN")
        self.scanning_btn.setCheckable(True)
        self.scanning_btn.setChecked(True)
        self.scanning_btn.setFixedSize(50, 25)
        self.scanning_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 150, 0.2);
                border: 1px solid #00ff96;
                border-radius: 3px;
                color: #00ff96;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: rgba(0, 255, 150, 0.5);
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 150, 0.4);
            }
        """)
        self.scanning_btn.clicked.connect(self.scanning_toggled.emit)
        layout.addWidget(self.scanning_btn)
        
        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: #444; margin: 0 5px;")
        layout.addWidget(separator)
        
        self.reset_btn = QPushButton("RESET VIEW")
        self.reset_btn.setFixedSize(70, 25)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 150, 255, 0.2);
                border: 1px solid #6496ff;
                border-radius: 3px;
                color: #6496ff;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(100, 150, 255, 0.4);
            }
        """)
        self.reset_btn.clicked.connect(self.view_reset.emit)
        layout.addWidget(self.reset_btn)
        
        layout.addStretch()
    
    def cleanup_resources(self):
        """Cleanup resources to prevent segfaults"""
        if self._cleanup_performed:
            return
            
        print("ShipViewerControls: Performing cleanup...")
        self._cleanup_performed = True
        self._is_destroyed = True
        
        try:
            # Unregister from theme manager
            get_global_theme_manager().unregister_widget(self)
        except Exception as e:
            print(f"Warning: Could not unregister ShipViewerControls from theme manager: {e}")
    
    def closeEvent(self, event):
        """Handle close event"""
        self.cleanup_resources()
        super().closeEvent(event)
    
    def __del__(self):
        """Destructor with cleanup"""
        try:
            self.cleanup_resources()
        except Exception:
            pass


# Export main classes
__all__ = ['ShipViewer3D', 'ShipViewerControls']