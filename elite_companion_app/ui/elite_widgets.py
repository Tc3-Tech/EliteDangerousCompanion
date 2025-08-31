"""
Elite Dangerous themed UI widgets for PyQt6.
Provides a consistent aesthetic across all UI components.
"""
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QFrame, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QProgressBar, QSlider,
                           QListWidget, QTextEdit, QGroupBox, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QObject
from PyQt6.QtGui import QPainter, QPen, QBrush, QLinearGradient, QFont, QFontMetrics, QPixmap, QIcon, QPalette, QColor
import math
import os
from typing import Optional, List, Callable
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.themes import ThemeColors, HardwareThemeManager


class ThemeAwareWidget:
    """Mixin class for widgets that respond to theme changes"""
    
    def __init__(self):
        self._theme_manager = None
        self._custom_theme_callback = None
    
    def connect_theme_manager(self, theme_manager: HardwareThemeManager):
        """Connect widget to theme manager for real-time updates"""
        self._theme_manager = theme_manager
        theme_manager.theme_changed.connect(self._on_theme_changed)
        # Apply current theme immediately
        self._on_theme_changed(theme_manager.current_theme)
    
    def set_theme_callback(self, callback: Callable):
        """Set custom callback for theme changes"""
        self._custom_theme_callback = callback
    
    def _on_theme_changed(self, theme: ThemeColors):
        """Handle theme change - override in subclasses"""
        if hasattr(self, 'apply_theme'):
            self.apply_theme(theme)
        if self._custom_theme_callback:
            self._custom_theme_callback(theme)
        if hasattr(self, 'update'):
            self.update()


class ElitePanel(QFrame, ThemeAwareWidget):
    """Base panel with Elite Dangerous styling - geometric with beveled edges"""
    
    def __init__(self, title: str = "", parent=None):
        QFrame.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        self.title = title
        self.setMinimumSize(200, 150)
        self.setup_ui()
        
        # Register with global theme manager
        _global_theme_manager.register_widget(self)
        
    def setup_ui(self):
        """Initialize the panel styling"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        if self.title:
            title_label = EliteLabel(self.title, style="header")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)
            
            # Add separator line
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFixedHeight(2)
            layout.addWidget(separator)
        
        # Content area
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
    
    def add_widget(self, widget):
        """Add widget to the panel content area"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to the panel content area"""
        self.content_layout.addLayout(layout)


class EliteLabel(QLabel):
    """Elite-styled label with glow effect and technical font"""
    
    def __init__(self, text: str = "", style: str = "normal", parent=None):
        super().__init__(text, parent)
        self.label_style = style
        self.setup_styling()
    
    def setup_styling(self):
        """Apply Elite-specific styling"""
        if self.label_style == "header":
            self.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
                text-transform: uppercase;
            """)
        elif self.label_style == "value":
            self.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            """)
        elif self.label_style == "small":
            self.setStyleSheet("""
                font-size: 10px;
                opacity: 0.8;
            """)


class EliteButton(QPushButton):
    """Elite-styled button with hover animations and technical appearance"""
    
    def __init__(self, text: str = "", icon_path: str = "", parent=None):
        super().__init__(text, parent)
        self.icon_path = icon_path
        self.setup_styling()
        
        # Animation for hover effects
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def setup_styling(self):
        """Apply Elite button styling"""
        self.setMinimumSize(120, 35)
        
        if self.icon_path and os.path.exists(self.icon_path):
            self.setIcon(QIcon(self.icon_path))
        
        self.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
                border: 2px solid;
                padding: 8px 16px;
            }
            QPushButton:hover {
                /* transform not supported in Qt stylesheets */
            }
            QPushButton:pressed {
                /* transform not supported in Qt stylesheets */
            }
        """)


class EliteProgressBar(QProgressBar):
    """Elite-styled progress bar with gradient fill and technical readout"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(25)
        self.setTextVisible(True)
        self.setup_styling()
    
    def setup_styling(self):
        """Apply Elite progress bar styling"""
        self.setStyleSheet("""
            QProgressBar {
                text-align: center;
                font-weight: bold;
                border: 2px solid;
                background-color: transparent;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 255, 255, 0.8),
                    stop: 0.5 rgba(0, 200, 255, 0.9),
                    stop: 1 rgba(0, 150, 255, 1.0));
            }
        """)


class EliteHUD(QWidget, ThemeAwareWidget):
    """Heads-up display style widget with real-time data visualization"""
    
    data_updated = pyqtSignal(dict)  # Signal for data updates
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        self.setMinimumSize(400, 300)
        self.data = {}
        self.crosshair_enabled = True
        self._current_theme = None
        
        # Update timer for animations
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(50)  # 20 FPS for smooth animations
        
        self.animation_phase = 0.0
        
        # Register with global theme manager
        _global_theme_manager.register_widget(self)
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme to HUD elements"""
        self._current_theme = theme
        self.update()
    
    def set_data(self, data: dict):
        """Update HUD data"""
        self.data = data
        self.data_updated.emit(data)
        self.update()
    
    def update_display(self):
        """Update animation phase and refresh display"""
        self.animation_phase = (self.animation_phase + 0.1) % (2 * math.pi)
        if self.crosshair_enabled:
            self.update()
    
    def paintEvent(self, event):
        """Custom paint for HUD elements"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get current theme colors from theme manager or palette
        if self._current_theme:
            primary_color = QColor(self._current_theme.primary)
            text_color = QColor(self._current_theme.text)
        else:
            primary_color = self.palette().highlight().color()
            text_color = self.palette().text().color()
        
        # Draw crosshair if enabled
        if self.crosshair_enabled:
            self.draw_crosshair(painter, primary_color)
        
        # Draw data readouts
        self.draw_data_readouts(painter, text_color)
        
        # Draw scanning animation
        self.draw_scan_lines(painter, primary_color)
    
    def draw_crosshair(self, painter: QPainter, color):
        """Draw HUD crosshair"""
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        pen = QPen(color, 2)
        painter.setPen(pen)
        
        # Main crosshair
        painter.drawLine(center_x - 20, center_y, center_x + 20, center_y)
        painter.drawLine(center_x, center_y - 20, center_x, center_y + 20)
        
        # Corner brackets
        bracket_size = 10
        corners = [
            (center_x - 50, center_y - 50),  # Top-left
            (center_x + 50, center_y - 50),  # Top-right
            (center_x - 50, center_y + 50),  # Bottom-left
            (center_x + 50, center_y + 50)   # Bottom-right
        ]
        
        for x, y in corners:
            # L-shaped brackets
            painter.drawLine(x, y, x + bracket_size, y)
            painter.drawLine(x, y, x, y + bracket_size)
    
    def draw_data_readouts(self, painter: QPainter, color):
        """Draw data readouts around the edges"""
        painter.setPen(QPen(color, 1))
        font = QFont("Courier New", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Left side data
        y_pos = 30
        for key, value in self.data.items():
            text = f"{key}: {value}"
            painter.drawText(10, y_pos, text)
            y_pos += 20
    
    def draw_scan_lines(self, painter: QPainter, color):
        """Draw animated scanning lines"""
        pen = QPen(color, 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        # Rotating scan line
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(self.width(), self.height()) // 3
        
        end_x = center_x + radius * math.cos(self.animation_phase)
        end_y = center_y + radius * math.sin(self.animation_phase)
        
        painter.drawLine(center_x, center_y, int(end_x), int(end_y))


class EliteShipDisplay(QWidget):
    """Widget for displaying ship information with 3D-style visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ship_name = "Sidewinder"
        self.ship_image = None
        self.setMinimumSize(300, 200)
        
    def set_ship(self, ship_name: str, image_path: str = ""):
        """Set the current ship"""
        self.ship_name = ship_name
        
        if image_path and os.path.exists(image_path):
            self.ship_image = QPixmap(image_path)
        else:
            # Try to find ship image in assets
            asset_path = f"/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets/{ship_name.lower().replace(' ', '-')}.png"
            if os.path.exists(asset_path):
                self.ship_image = QPixmap(asset_path)
        
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for ship display"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.ship_image:
            # Scale and center the ship image
            scaled_pixmap = self.ship_image.scaled(
                self.size() * 0.8, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        
        # Draw ship name
        painter.setPen(QPen(self.palette().text().color(), 2))
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        
        text_rect = QRect(0, self.height() - 30, self.width(), 30)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.ship_name.upper())


class EliteSystemMap(QWidget):
    """Widget for displaying system maps and exploration data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.system_name = "Sol"
        self.bodies = []
        self.setMinimumSize(400, 300)
        
        # Animation timer
        self.orbit_timer = QTimer()
        self.orbit_timer.timeout.connect(self.update_orbits)
        self.orbit_timer.start(100)  # 10 FPS for orbital motion
        
        self.orbit_phase = 0.0
    
    def set_system(self, system_name: str, bodies: list):
        """Set system data"""
        self.system_name = system_name
        self.bodies = bodies
        self.update()
    
    def update_orbits(self):
        """Update orbital animation"""
        self.orbit_phase = (self.orbit_phase + 0.05) % (2 * math.pi)
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for system map"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Draw star at center
        star_color = self.palette().highlight().color()
        painter.setBrush(QBrush(star_color))
        painter.setPen(QPen(star_color, 2))
        painter.drawEllipse(center_x - 15, center_y - 15, 30, 30)
        
        # Draw orbiting bodies
        for i, body in enumerate(self.bodies[:6]):  # Limit to 6 bodies for display
            orbit_radius = 50 + (i * 40)
            angle = self.orbit_phase + (i * math.pi / 3)
            
            body_x = center_x + orbit_radius * math.cos(angle)
            body_y = center_y + orbit_radius * math.sin(angle)
            
            # Draw orbit path
            painter.setPen(QPen(self.palette().mid().color(), 1, Qt.PenStyle.DotLine))
            painter.setBrush(QBrush())
            painter.drawEllipse(center_x - orbit_radius, center_y - orbit_radius, 
                              orbit_radius * 2, orbit_radius * 2)
            
            # Draw body
            body_color = self.palette().text().color()
            painter.setBrush(QBrush(body_color))
            painter.setPen(QPen(body_color, 1))
            painter.drawEllipse(int(body_x - 5), int(body_y - 5), 10, 10)
        
        # Draw system name
        painter.setPen(QPen(self.palette().text().color(), 2))
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        
        text_rect = QRect(0, 0, self.width(), 30)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.system_name.upper())


class EliteMediaControl(QWidget, ThemeAwareWidget):
    """Media control widget with Elite styling"""
    
    play_pause_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    previous_clicked = pyqtSignal()
    volume_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        self.is_playing = False
        self.current_track = "No Track"
        self.current_artist = "Unknown Artist"
        self.progress = 0
        self.volume = 50
        self.setup_ui()
        
        # Register with global theme manager
        _global_theme_manager.register_widget(self)
    
    def setup_ui(self):
        """Setup media control UI"""
        layout = QVBoxLayout(self)
        
        # Track info
        info_panel = ElitePanel("NOW PLAYING")
        
        self.track_label = EliteLabel(self.current_track, "value")
        self.artist_label = EliteLabel(self.current_artist, "small")
        
        info_panel.add_widget(self.track_label)
        info_panel.add_widget(self.artist_label)
        
        # Progress bar
        self.progress_bar = EliteProgressBar()
        self.progress_bar.setValue(self.progress)
        info_panel.add_widget(self.progress_bar)
        
        layout.addWidget(info_panel)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.prev_btn = EliteButton("⏮")
        self.play_btn = EliteButton("▶" if not self.is_playing else "⏸")
        self.next_btn = EliteButton("⏭")
        
        self.prev_btn.clicked.connect(self.previous_clicked.emit)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        self.next_btn.clicked.connect(self.next_clicked.emit)
        
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.next_btn)
        
        layout.addLayout(controls_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(EliteLabel("VOLUME:", "small"))
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.volume)
        self.volume_slider.valueChanged.connect(self.volume_changed.emit)
        volume_layout.addWidget(self.volume_slider)
        
        layout.addLayout(volume_layout)
    
    def toggle_play_pause(self):
        """Toggle play/pause state"""
        self.is_playing = not self.is_playing
        self.play_btn.setText("⏸" if self.is_playing else "▶")
        self.play_pause_clicked.emit()
    
    def update_track_info(self, track: str, artist: str):
        """Update current track information"""
        self.current_track = track
        self.current_artist = artist
        self.track_label.setText(track)
        self.artist_label.setText(artist)
    
    def update_progress(self, progress: int):
        """Update playback progress"""
        self.progress = progress
        self.progress_bar.setValue(progress)




class RealTimeThemeManager(QObject):
    """Manages real-time theme application across all widgets"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._registered_widgets = []
        self._current_theme = None
        self._app = None
    
    def register_widget(self, widget):
        """Register a widget for theme updates"""
        if hasattr(widget, '_on_theme_changed'):
            self._registered_widgets.append(widget)
            # Apply current theme if available
            if self._current_theme:
                widget._on_theme_changed(self._current_theme)
    
    def unregister_widget(self, widget):
        """Unregister a widget from theme updates"""
        if widget in self._registered_widgets:
            self._registered_widgets.remove(widget)
    
    def set_application(self, app):
        """Set the QApplication instance for global styling"""
        self._app = app
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme to all registered widgets and application"""
        self._current_theme = theme
        
        # Apply to application if available
        if self._app:
            apply_elite_theme(self._app, theme)
        
        # Apply to all registered widgets
        for widget in self._registered_widgets:
            if hasattr(widget, '_on_theme_changed'):
                widget._on_theme_changed(theme)
    
    def get_registered_widget_count(self) -> int:
        """Get count of registered widgets"""
        return len(self._registered_widgets)


# Global theme manager instance
_global_theme_manager = RealTimeThemeManager()


def get_global_theme_manager() -> RealTimeThemeManager:
    """Get the global theme manager instance"""
    return _global_theme_manager


# Theme application function with enhanced real-time support
def apply_elite_theme(app, theme_colors: ThemeColors, force_update: bool = False):
    """Apply Elite theme to the entire application with real-time support"""
    colors = theme_colors.to_dict()
    
    # Enhanced stylesheet compatible with Qt QSS
    stylesheet = f"""
    /* Global Application Style */
    * {{
        /* transition not supported in Qt stylesheets - handled by Qt animations instead */
    }}
    
    QMainWindow {{
        background-color: {colors['background']};
        color: {colors['text']};
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    
    /* Elite Panel Styling */
    QFrame {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 {colors['surface']},
            stop: 1 rgba(0, 0, 0, 0.3));
        border: 2px solid {colors['border']};
        border-radius: 4px;
        color: {colors['text']};
    }}
    
    /* Elite Button Styling */
    QPushButton {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 {colors['primary']},
            stop: 1 {colors['secondary']});
        color: {colors['background']};
        border: 2px solid {colors['primary']};
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        min-height: 25px;
    }}
    
    QPushButton:hover {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 {colors['accent']},
            stop: 1 {colors['primary']});
        border-color: {colors['accent']};
        color: {colors['background']};
    }}
    
    QPushButton:pressed {{
        background: {colors['secondary']};
        border-color: {colors['secondary']};
    }}
    
    QPushButton:disabled {{
        background: {colors['surface']};
        color: {colors['text_secondary']};
        border-color: {colors['text_secondary']};
    }}
    
    /* Elite Label Styling */
    QLabel {{
        color: {colors['text']};
        background: transparent;
        border: none;
        font-weight: normal;
    }}
    
    /* Elite Progress Bar */
    QProgressBar {{
        background-color: {colors['background']};
        border: 2px solid {colors['border']};
        border-radius: 4px;
        text-align: center;
        color: {colors['text']};
        font-weight: bold;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 {colors['primary']},
            stop: 0.5 {colors['accent']},
            stop: 1 {colors['primary']});
        border-radius: 2px;
    }}
    
    /* Elite Slider */
    QSlider::groove:horizontal {{
        border: 1px solid {colors['border']};
        height: 8px;
        background: {colors['background']};
        margin: 2px 0;
        border-radius: 4px;
    }}
    
    QSlider::handle:horizontal {{
        background: {colors['primary']};
        border: 1px solid {colors['border']};
        width: 18px;
        margin: -2px 0;
        border-radius: 9px;
    }}
    
    QSlider::handle:hover {{
        background: {colors['accent']};
    }}
    
    QSlider::sub-page:horizontal {{
        background: {colors['primary']};
        border-radius: 4px;
    }}
    
    /* Elite List Widget */
    QListWidget {{
        background-color: {colors['surface']};
        border: 1px solid {colors['border']};
        color: {colors['text']};
        selection-background-color: {colors['primary']};
        selection-color: {colors['background']};
    }}
    
    QListWidget::item {{
        padding: 5px;
        border-bottom: 1px solid {colors['border']};
    }}
    
    QListWidget::item:hover {{
        background-color: {colors['accent']};
        color: {colors['background']};
    }}
    
    /* Elite Text Edit */
    QTextEdit {{
        background-color: {colors['surface']};
        border: 1px solid {colors['border']};
        color: {colors['text']};
        selection-background-color: {colors['primary']};
    }}
    
    /* Elite Group Box */
    QGroupBox {{
        color: {colors['text']};
        border: 2px solid {colors['border']};
        border-radius: 5px;
        margin-top: 1ex;
        font-weight: bold;
        text-transform: uppercase;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
        color: {colors['primary']};
    }}
    """
    
    app.setStyleSheet(stylesheet)
    
    # Also update palette for better integration
    from config.themes import apply_theme_to_palette
    apply_theme_to_palette(app, theme_colors)
    
    # Notify global theme manager
    _global_theme_manager.apply_theme(theme_colors)


# Hardware integration helper functions
def setup_hardware_theme_integration(app, ble_manager=None, settings_manager=None):
    """Setup complete hardware theme integration"""
    from config.themes import create_hardware_theme_manager
    
    # Create hardware theme manager
    theme_manager = create_hardware_theme_manager(ble_manager, settings_manager)
    
    # Set up global theme manager
    _global_theme_manager.set_application(app)
    
    # Connect hardware theme manager to global theme manager
    theme_manager.theme_changed.connect(_global_theme_manager.apply_theme)
    
    # Enable hardware control if configured
    if settings_manager and settings_manager.is_hardware_theme_control_enabled():
        theme_manager.enable_hardware_control(True)
        
        # Set up BLE integration if available
        if ble_manager:
            def handle_potentiometer_change(value):
                theme_manager.update_from_hardware(value)
            
            # This would need to be connected to actual BLE potentiometer events
            # ble_manager.add_callback('potentiometer_changed', handle_potentiometer_change)
    
    return theme_manager


def create_calibration_widget(parent=None, theme_manager=None):
    """Create a widget for hardware calibration"""
    from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QDoubleSpinBox, QCheckBox, QComboBox
    
    calibration_panel = ElitePanel("HARDWARE CALIBRATION", parent)
    
    if theme_manager:
        calibration = theme_manager.calibration
        
        # Min/Max value controls
        min_layout = QHBoxLayout()
        min_layout.addWidget(EliteLabel("Min Value:", "small"))
        min_spinbox = QDoubleSpinBox()
        min_spinbox.setRange(0.0, 1.0)
        min_spinbox.setSingleStep(0.01)
        min_spinbox.setValue(calibration.min_value)
        min_spinbox.valueChanged.connect(
            lambda v: setattr(calibration, 'min_value', v) or theme_manager.set_calibration(calibration)
        )
        min_layout.addWidget(min_spinbox)
        calibration_panel.add_layout(min_layout)
        
        max_layout = QHBoxLayout()
        max_layout.addWidget(EliteLabel("Max Value:", "small"))
        max_spinbox = QDoubleSpinBox()
        max_spinbox.setRange(0.0, 1.0)
        max_spinbox.setSingleStep(0.01)
        max_spinbox.setValue(calibration.max_value)
        max_spinbox.valueChanged.connect(
            lambda v: setattr(calibration, 'max_value', v) or theme_manager.set_calibration(calibration)
        )
        max_layout.addWidget(max_spinbox)
        calibration_panel.add_layout(max_layout)
        
        # Dead zone control
        dead_layout = QHBoxLayout()
        dead_layout.addWidget(EliteLabel("Dead Zone:", "small"))
        dead_spinbox = QDoubleSpinBox()
        dead_spinbox.setRange(0.0, 0.1)
        dead_spinbox.setSingleStep(0.001)
        dead_spinbox.setValue(calibration.dead_zone)
        dead_spinbox.valueChanged.connect(
            lambda v: setattr(calibration, 'dead_zone', v) or theme_manager.set_calibration(calibration)
        )
        dead_layout.addWidget(dead_spinbox)
        calibration_panel.add_layout(dead_layout)
        
        # Smoothing control
        smooth_layout = QHBoxLayout()
        smooth_layout.addWidget(EliteLabel("Smoothing:", "small"))
        smooth_spinbox = QDoubleSpinBox()
        smooth_spinbox.setRange(0.0, 1.0)
        smooth_spinbox.setSingleStep(0.01)
        smooth_spinbox.setValue(calibration.smoothing_factor)
        smooth_spinbox.valueChanged.connect(
            lambda v: setattr(calibration, 'smoothing_factor', v) or theme_manager.set_calibration(calibration)
        )
        smooth_layout.addWidget(smooth_spinbox)
        calibration_panel.add_layout(smooth_layout)
        
        # Invert checkbox
        invert_checkbox = QCheckBox("Invert Potentiometer")
        invert_checkbox.setChecked(calibration.invert)
        invert_checkbox.toggled.connect(
            lambda v: setattr(calibration, 'invert', v) or theme_manager.set_calibration(calibration)
        )
        calibration_panel.add_widget(invert_checkbox)
        
        # Sensitivity curve
        curve_layout = QHBoxLayout()
        curve_layout.addWidget(EliteLabel("Curve:", "small"))
        curve_combo = QComboBox()
        curve_combo.addItems(["linear", "exponential", "logarithmic"])
        curve_combo.setCurrentText(calibration.sensitivity_curve)
        curve_combo.currentTextChanged.connect(
            lambda v: setattr(calibration, 'sensitivity_curve', v) or theme_manager.set_calibration(calibration)
        )
        curve_layout.addWidget(curve_combo)
        calibration_panel.add_layout(curve_layout)
        
        # Hue range controls
        hue_start_layout = QHBoxLayout()
        hue_start_layout.addWidget(EliteLabel("Hue Start:", "small"))
        hue_start_spinbox = QDoubleSpinBox()
        hue_start_spinbox.setRange(0.0, 1.0)
        hue_start_spinbox.setSingleStep(0.01)
        hue_start_spinbox.setValue(calibration.hue_range_start)
        hue_start_spinbox.valueChanged.connect(
            lambda v: setattr(calibration, 'hue_range_start', v) or theme_manager.set_calibration(calibration)
        )
        hue_start_layout.addWidget(hue_start_spinbox)
        calibration_panel.add_layout(hue_start_layout)
        
        hue_end_layout = QHBoxLayout()
        hue_end_layout.addWidget(EliteLabel("Hue End:", "small"))
        hue_end_spinbox = QDoubleSpinBox()
        hue_end_spinbox.setRange(0.0, 1.0)
        hue_end_spinbox.setSingleStep(0.01)
        hue_end_spinbox.setValue(calibration.hue_range_end)
        hue_end_spinbox.valueChanged.connect(
            lambda v: setattr(calibration, 'hue_range_end', v) or theme_manager.set_calibration(calibration)
        )
        hue_end_layout.addWidget(hue_end_spinbox)
        calibration_panel.add_layout(hue_end_layout)
    
    return calibration_panel


def simulate_potentiometer_input(theme_manager, start_value=0.0, end_value=1.0, duration_ms=5000, steps=100):
    """Simulate potentiometer input for testing - sweeps from start to end value"""
    import threading
    import time
    
    def simulate():
        step_duration = duration_ms / 1000.0 / steps
        value_step = (end_value - start_value) / steps
        
        for i in range(steps + 1):
            value = start_value + (i * value_step)
            theme_manager.update_from_hardware(value)
            time.sleep(step_duration)
    
    simulation_thread = threading.Thread(target=simulate, daemon=True)
    simulation_thread.start()
    
    return simulation_thread


# Export enhanced widget classes and functions
__all__ = [
    'ElitePanel', 'EliteLabel', 'EliteButton', 'EliteProgressBar',
    'EliteHUD', 'EliteShipDisplay', 'EliteSystemMap', 'EliteMediaControl',
    'ThemeAwareWidget', 'RealTimeThemeManager',
    'apply_elite_theme', 'get_global_theme_manager',
    'setup_hardware_theme_integration', 'create_calibration_widget',
    'simulate_potentiometer_input'
]