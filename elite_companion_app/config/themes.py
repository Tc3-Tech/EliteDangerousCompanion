"""
Theme system for customizable HUD colors and styling.
"""
from typing import Dict, Tuple, NamedTuple, Optional, Callable, Any, List
from dataclasses import dataclass, field
from enum import Enum
import colorsys
import time
import threading
import math
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QColor


class ColorRole(Enum):
    """Different UI elements that can be themed"""
    PRIMARY = "primary"          # Main UI elements
    SECONDARY = "secondary"      # Secondary elements
    ACCENT = "accent"           # Highlights and focus
    BACKGROUND = "background"    # Window background
    SURFACE = "surface"         # Panel backgrounds
    TEXT = "text"               # Text color
    TEXT_SECONDARY = "text_secondary"  # Dimmed text
    BORDER = "border"           # Borders and dividers
    SUCCESS = "success"         # Success states
    WARNING = "warning"         # Warning states
    ERROR = "error"            # Error states


@dataclass
class ThemeColors:
    """Color palette for a theme"""
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    text_secondary: str
    border: str
    success: str
    warning: str
    error: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for easy access"""
        return {
            ColorRole.PRIMARY.value: self.primary,
            ColorRole.SECONDARY.value: self.secondary,
            ColorRole.ACCENT.value: self.accent,
            ColorRole.BACKGROUND.value: self.background,
            ColorRole.SURFACE.value: self.surface,
            ColorRole.TEXT.value: self.text,
            ColorRole.TEXT_SECONDARY.value: self.text_secondary,
            ColorRole.BORDER.value: self.border,
            ColorRole.SUCCESS.value: self.success,
            ColorRole.WARNING.value: self.warning,
            ColorRole.ERROR.value: self.error,
        }


class PredefinedThemes:
    """Collection of predefined color themes"""
    
    MATRIX_GREEN = ThemeColors(
        primary="#00FF41",
        secondary="#00CC33",
        accent="#00FF80",
        background="#0A0A0A",
        surface="#1A1A1A",
        text="#00FF41",
        text_secondary="#00AA2A",
        border="#00CC33",
        success="#00FF41",
        warning="#FFFF00",
        error="#FF4444"
    )
    
    ICE_BLUE = ThemeColors(
        primary="#00D4FF",
        secondary="#0099CC",
        accent="#40E0FF",
        background="#0A0F1A",
        surface="#152030",
        text="#E0F8FF",
        text_secondary="#B0D4E8",
        border="#0099CC",
        success="#00FF88",
        warning="#FFD700",
        error="#FF4444"
    )
    
    DEEP_PURPLE = ThemeColors(
        primary="#9D4EDD",
        secondary="#7B2CBF",
        accent="#C77DFF",
        background="#1A0A2E",
        surface="#2D1B40",
        text="#F0E6FF",
        text_secondary="#D4C2E8",
        border="#7B2CBF",
        success="#00FF88",
        warning="#FFD700",
        error="#FF4444"
    )
    
    PLASMA_PINK = ThemeColors(
        primary="#FF006E",
        secondary="#CC0055",
        accent="#FF4088",
        background="#1A0A14",
        surface="#2D1520",
        text="#FFE0F0",
        text_secondary="#E8B8D0",
        border="#CC0055",
        success="#00FF88",
        warning="#FFD700",
        error="#FF4444"
    )
    
    ARCTIC_WHITE = ThemeColors(
        primary="#F8F8FF",
        secondary="#E0E0E8",
        accent="#C0C8FF",
        background="#F0F0F5",
        surface="#FFFFFF",
        text="#2A2A2A",
        text_secondary="#666666",
        border="#D0D0D8",
        success="#00AA44",
        warning="#DD8800",
        error="#CC3333"
    )
    
    EMBER_RED = ThemeColors(
        primary="#FF4B4B",
        secondary="#CC3333",
        accent="#FF6666",
        background="#1A0A0A",
        surface="#2D1515",
        text="#FFE0E0",
        text_secondary="#E8B8B8",
        border="#CC3333",
        success="#00FF88",
        warning="#FFD700",
        error="#FF4B4B"
    )


@dataclass
class HardwareCalibration:
    """Hardware calibration settings for potentiometer input"""
    min_value: float = 0.0          # Minimum potentiometer reading
    max_value: float = 1.0          # Maximum potentiometer reading
    dead_zone: float = 0.02         # Dead zone around center
    smoothing_factor: float = 0.85   # Exponential smoothing factor (0-1)
    invert: bool = False            # Invert the potentiometer range
    hue_range_start: float = 0.0    # Starting hue (0-1)
    hue_range_end: float = 1.0      # Ending hue (0-1)
    sensitivity_curve: str = "linear" # "linear", "exponential", "logarithmic"


@dataclass
class ThemeTransition:
    """Theme transition configuration"""
    duration_ms: int = 150          # Transition duration in milliseconds
    easing: str = "ease_out"        # Easing function type
    interpolation_steps: int = 30   # Number of interpolation steps
    debounce_ms: int = 50          # Debounce time for rapid changes


class HardwareThemeManager(QObject):
    """Enhanced theme manager with hardware potentiometer integration"""
    
    # Signals for real-time theme updates
    theme_changed = pyqtSignal(object)  # ThemeColors object
    hardware_value_changed = pyqtSignal(float)  # Raw hardware value
    calibrated_value_changed = pyqtSignal(float)  # Calibrated value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = PredefinedThemes.ICE_BLUE
        self.predefined_themes = {
            "Matrix Green": PredefinedThemes.MATRIX_GREEN,
            "Ice Blue": PredefinedThemes.ICE_BLUE,
            "Deep Purple": PredefinedThemes.DEEP_PURPLE,
            "Plasma Pink": PredefinedThemes.PLASMA_PINK,
            "Arctic White": PredefinedThemes.ARCTIC_WHITE,
            "Ember Red": PredefinedThemes.EMBER_RED,
        }
        self.theme_change_callbacks = []
        
        # Hardware integration
        self.hardware_enabled = False
        self.calibration = HardwareCalibration()
        self.transition_config = ThemeTransition()
        
        # Smoothing and debouncing
        self._last_raw_value = 0.5
        self._smoothed_value = 0.5
        self._last_update_time = 0.0
        self._update_lock = threading.Lock()
        
        # Theme interpolation
        self._transition_timer = QTimer()
        self._transition_timer.timeout.connect(self._update_transition)
        self._transition_start_time = 0.0
        self._transition_start_theme = None
        self._transition_target_theme = None
        self._is_transitioning = False
        
        # Context-sensitive theming
        self._element_contexts = {
            'primary': {'hue_offset': 0.0, 'saturation_multiplier': 1.0, 'brightness_multiplier': 1.0},
            'secondary': {'hue_offset': 0.0, 'saturation_multiplier': 0.8, 'brightness_multiplier': 0.7},
            'accent': {'hue_offset': 0.05, 'saturation_multiplier': 0.6, 'brightness_multiplier': 1.0},
            'background': {'hue_offset': 0.0, 'saturation_multiplier': 0.1, 'brightness_multiplier': 0.1},
            'surface': {'hue_offset': 0.0, 'saturation_multiplier': 0.2, 'brightness_multiplier': 0.2}
        }
    
    def set_theme(self, theme: ThemeColors, animate: bool = True):
        """Set the current theme with optional animation"""
        if animate and self.transition_config.duration_ms > 0:
            self._start_theme_transition(theme)
        else:
            self.current_theme = theme
            self._notify_theme_change()
            self.theme_changed.emit(theme)
    
    def set_predefined_theme(self, theme_name: str, animate: bool = True):
        """Set a predefined theme by name"""
        if theme_name in self.predefined_themes:
            self.set_theme(self.predefined_themes[theme_name], animate)
    
    def generate_custom_theme(self, hue: float, saturation: float = 0.8, 
                            brightness: float = 0.9, context: str = "default") -> ThemeColors:
        """Generate a custom theme from HSV values with context-sensitive adjustments"""
        
        # Apply context-specific adjustments
        context_adjustments = self._element_contexts.get('primary', {})
        
        adjusted_hue = (hue + context_adjustments.get('hue_offset', 0.0)) % 1.0
        adjusted_saturation = min(1.0, saturation * context_adjustments.get('saturation_multiplier', 1.0))
        adjusted_brightness = min(1.0, brightness * context_adjustments.get('brightness_multiplier', 1.0))
        
        # Generate primary color
        primary_color = self._hsv_to_hex(adjusted_hue, adjusted_saturation, adjusted_brightness)
        
        # Generate secondary color (darker)
        secondary_color = self._hsv_to_hex(
            adjusted_hue, 
            adjusted_saturation, 
            adjusted_brightness * 0.7
        )
        
        # Generate accent color (lighter, slightly shifted hue)
        accent_color = self._hsv_to_hex(
            (adjusted_hue + 0.05) % 1.0, 
            adjusted_saturation * 0.6, 
            min(1.0, adjusted_brightness * 1.2)
        )
        
        # Generate surface and background colors
        surface_color = self._hsv_to_hex(adjusted_hue, adjusted_saturation * 0.2, 0.15)
        background_color = self._hsv_to_hex(adjusted_hue, adjusted_saturation * 0.1, 0.08)
        
        # Generate text colors with high contrast
        text_brightness = 0.95 if adjusted_brightness < 0.5 else 0.05
        text_color = self._hsv_to_hex(adjusted_hue, adjusted_saturation * 0.2, text_brightness)
        text_secondary = self._hsv_to_hex(adjusted_hue, adjusted_saturation * 0.3, text_brightness * 0.8)
        
        # Border color matches secondary
        border_color = secondary_color
        
        return ThemeColors(
            primary=primary_color,
            secondary=secondary_color,
            accent=accent_color,
            background=background_color,
            surface=surface_color,
            text=text_color,
            text_secondary=text_secondary,
            border=border_color,
            success="#00FF88",
            warning="#FFD700",
            error="#FF4444"
        )
    
    def get_qt_stylesheet(self) -> str:
        """Generate Qt stylesheet for current theme"""
        colors = self.current_theme.to_dict()
        
        return f"""
        QMainWindow {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        
        QWidget {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
        }}
        
        QPushButton {{
            background-color: {colors['primary']};
            color: {colors['background']};
            border: 2px solid {colors['primary']};
            padding: 8px 16px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {colors['accent']};
            border-color: {colors['accent']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['secondary']};
            border-color: {colors['secondary']};
        }}
        
        QLabel {{
            color: {colors['text']};
            background: transparent;
            border: none;
        }}
        
        QFrame {{
            background-color: {colors['surface']};
            border: 1px solid {colors['border']};
        }}
        """
    
    def add_theme_change_callback(self, callback):
        """Add callback for theme changes"""
        self.theme_change_callbacks.append(callback)
    
    def enable_hardware_control(self, enabled: bool = True):
        """Enable or disable hardware potentiometer control"""
        self.hardware_enabled = enabled
        if enabled:
            # Initialize with current smoothed value
            self.update_from_hardware(self._smoothed_value)
    
    def set_calibration(self, calibration: HardwareCalibration):
        """Update hardware calibration settings"""
        self.calibration = calibration
    
    def set_transition_config(self, config: ThemeTransition):
        """Update theme transition configuration"""
        self.transition_config = config
    
    def update_from_hardware(self, raw_value: float):
        """Update theme from hardware potentiometer input"""
        if not self.hardware_enabled:
            return
        
        with self._update_lock:
            current_time = time.time()
            
            # Apply debouncing
            if (current_time - self._last_update_time) < (self.transition_config.debounce_ms / 1000.0):
                return
            
            self._last_update_time = current_time
            
            # Store raw value for debugging
            self._last_raw_value = raw_value
            self.hardware_value_changed.emit(raw_value)
            
            # Apply hardware calibration
            calibrated_value = self._calibrate_hardware_value(raw_value)
            
            # Apply smoothing
            self._smoothed_value = self._apply_smoothing(calibrated_value)
            self.calibrated_value_changed.emit(self._smoothed_value)
            
            # Generate and apply new theme
            hue = self._map_to_hue_range(self._smoothed_value)
            new_theme = self.generate_custom_theme(hue, 0.8, 0.9)
            
            # Apply theme with smooth transition
            self.set_theme(new_theme, animate=True)
    
    def _calibrate_hardware_value(self, raw_value: float) -> float:
        """Apply hardware calibration to raw input value"""
        # Apply inversion if enabled
        if self.calibration.invert:
            raw_value = 1.0 - raw_value
        
        # Map from hardware range to 0-1
        normalized = (raw_value - self.calibration.min_value) / (self.calibration.max_value - self.calibration.min_value)
        normalized = max(0.0, min(1.0, normalized))  # Clamp to [0, 1]
        
        # Apply dead zone
        if abs(normalized - 0.5) < self.calibration.dead_zone:
            normalized = 0.5
        
        # Apply sensitivity curve
        if self.calibration.sensitivity_curve == "exponential":
            normalized = normalized ** 2
        elif self.calibration.sensitivity_curve == "logarithmic":
            normalized = math.sqrt(normalized)
        # "linear" requires no transformation
        
        return normalized
    
    def _apply_smoothing(self, new_value: float) -> float:
        """Apply exponential smoothing to reduce jitter"""
        alpha = 1.0 - self.calibration.smoothing_factor
        return (alpha * new_value) + (self.calibration.smoothing_factor * self._smoothed_value)
    
    def _map_to_hue_range(self, normalized_value: float) -> float:
        """Map normalized value to configured hue range"""
        hue_range = self.calibration.hue_range_end - self.calibration.hue_range_start
        return self.calibration.hue_range_start + (normalized_value * hue_range)
    
    def _hsv_to_hex(self, h: float, s: float, v: float) -> str:
        """Convert HSV values to hex color string"""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def _start_theme_transition(self, target_theme: ThemeColors):
        """Start animated transition to new theme"""
        if self._is_transitioning:
            # Update target for current transition
            self._transition_target_theme = target_theme
        else:
            self._transition_start_time = time.time()
            self._transition_start_theme = self.current_theme
            self._transition_target_theme = target_theme
            self._is_transitioning = True
            
            # Start transition timer
            interval_ms = max(16, self.transition_config.duration_ms // self.transition_config.interpolation_steps)
            self._transition_timer.start(interval_ms)
    
    def _update_transition(self):
        """Update theme transition animation"""
        if not self._is_transitioning:
            self._transition_timer.stop()
            return
        
        current_time = time.time()
        elapsed_ms = (current_time - self._transition_start_time) * 1000
        
        if elapsed_ms >= self.transition_config.duration_ms:
            # Transition complete
            self.current_theme = self._transition_target_theme
            self._is_transitioning = False
            self._transition_timer.stop()
        else:
            # Calculate interpolation progress
            progress = elapsed_ms / self.transition_config.duration_ms
            
            # Apply easing
            if self.transition_config.easing == "ease_out":
                progress = 1 - (1 - progress) ** 3
            elif self.transition_config.easing == "ease_in":
                progress = progress ** 3
            elif self.transition_config.easing == "ease_in_out":
                progress = 3 * progress ** 2 - 2 * progress ** 3
            # "linear" requires no transformation
            
            # Interpolate between start and target themes
            self.current_theme = self._interpolate_themes(
                self._transition_start_theme,
                self._transition_target_theme,
                progress
            )
        
        # Notify of theme update
        self._notify_theme_change()
        self.theme_changed.emit(self.current_theme)
    
    def _interpolate_themes(self, start_theme: ThemeColors, end_theme: ThemeColors, progress: float) -> ThemeColors:
        """Interpolate between two themes"""
        def interpolate_color(start_hex: str, end_hex: str, t: float) -> str:
            # Convert hex to RGB
            start_rgb = [int(start_hex[i:i+2], 16) for i in (1, 3, 5)]
            end_rgb = [int(end_hex[i:i+2], 16) for i in (1, 3, 5)]
            
            # Interpolate in RGB space
            interpolated_rgb = [
                int(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * t)
                for i in range(3)
            ]
            
            return f"#{interpolated_rgb[0]:02x}{interpolated_rgb[1]:02x}{interpolated_rgb[2]:02x}"
        
        return ThemeColors(
            primary=interpolate_color(start_theme.primary, end_theme.primary, progress),
            secondary=interpolate_color(start_theme.secondary, end_theme.secondary, progress),
            accent=interpolate_color(start_theme.accent, end_theme.accent, progress),
            background=interpolate_color(start_theme.background, end_theme.background, progress),
            surface=interpolate_color(start_theme.surface, end_theme.surface, progress),
            text=interpolate_color(start_theme.text, end_theme.text, progress),
            text_secondary=interpolate_color(start_theme.text_secondary, end_theme.text_secondary, progress),
            border=interpolate_color(start_theme.border, end_theme.border, progress),
            success=end_theme.success,  # Keep utility colors constant
            warning=end_theme.warning,
            error=end_theme.error
        )
    
    def get_current_hardware_value(self) -> Tuple[float, float]:
        """Get current raw and smoothed hardware values"""
        return self._last_raw_value, self._smoothed_value
    
    def _notify_theme_change(self):
        """Notify all listeners of theme change"""
        for callback in self.theme_change_callbacks:
            callback(self.current_theme)


class ThemeManager(HardwareThemeManager):
    """Legacy theme manager for backward compatibility"""
    
    def __init__(self):
        super().__init__()
        # Disable hardware by default for legacy compatibility
        self.hardware_enabled = False


# Convenience functions for theme persistence and loading
class ThemePersistence:
    """Handles theme saving and loading from persistent storage"""
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
    
    def save_theme(self, theme: ThemeColors, name: str = "custom"):
        """Save a theme to persistent storage"""
        if not self.settings_manager:
            return False
        
        try:
            theme_data = {
                'name': name,
                'colors': theme.to_dict(),
                'timestamp': time.time()
            }
            
            # Save to settings
            self.settings_manager.set('theme', f'saved_theme_{name}', theme_data)
            return True
        except Exception as e:
            print(f"Error saving theme: {e}")
            return False
    
    def load_theme(self, name: str = "custom") -> Optional[ThemeColors]:
        """Load a theme from persistent storage"""
        if not self.settings_manager:
            return None
        
        try:
            theme_data = self.settings_manager.get('theme', f'saved_theme_{name}')
            if not theme_data or 'colors' not in theme_data:
                return None
            
            colors = theme_data['colors']
            return ThemeColors(
                primary=colors.get('primary', '#00D4FF'),
                secondary=colors.get('secondary', '#0099CC'),
                accent=colors.get('accent', '#40E0FF'),
                background=colors.get('background', '#0A0F1A'),
                surface=colors.get('surface', '#152030'),
                text=colors.get('text', '#E0F8FF'),
                text_secondary=colors.get('text_secondary', '#B0D4E8'),
                border=colors.get('border', '#0099CC'),
                success=colors.get('success', '#00FF88'),
                warning=colors.get('warning', '#FFD700'),
                error=colors.get('error', '#FF4444')
            )
        except Exception as e:
            print(f"Error loading theme: {e}")
            return None
    
    def list_saved_themes(self) -> List[str]:
        """List all saved theme names"""
        if not self.settings_manager:
            return []
        
        try:
            # This would need to be implemented based on the settings manager structure
            # For now, return empty list
            return []
        except Exception:
            return []


# Hardware integration helper functions
def create_hardware_theme_manager(ble_manager=None, settings_manager=None) -> HardwareThemeManager:
    """Create a hardware-integrated theme manager"""
    theme_manager = HardwareThemeManager()
    
    # Set up hardware calibration from settings
    if settings_manager:
        calibration = HardwareCalibration(
            min_value=settings_manager.get('hardware', 'pot_min_value', 0.0),
            max_value=settings_manager.get('hardware', 'pot_max_value', 1.0),
            dead_zone=settings_manager.get('hardware', 'pot_dead_zone', 0.02),
            smoothing_factor=settings_manager.get('hardware', 'pot_smoothing', 0.85),
            invert=settings_manager.get('hardware', 'invert_pot', False),
            hue_range_start=settings_manager.get('hardware', 'hue_range_start', 0.0),
            hue_range_end=settings_manager.get('hardware', 'hue_range_end', 1.0),
            sensitivity_curve=settings_manager.get('hardware', 'sensitivity_curve', 'linear')
        )
        theme_manager.set_calibration(calibration)
        
        transition_config = ThemeTransition(
            duration_ms=settings_manager.get('theme', 'transition_duration_ms', 150),
            easing=settings_manager.get('theme', 'transition_easing', 'ease_out'),
            interpolation_steps=settings_manager.get('theme', 'interpolation_steps', 30),
            debounce_ms=settings_manager.get('theme', 'debounce_ms', 50)
        )
        theme_manager.set_transition_config(transition_config)
    
    # Connect to BLE manager if provided
    if ble_manager:
        # This would need to be implemented to connect to potentiometer input
        # For now, we'll add a placeholder
        def handle_potentiometer_input(value):
            theme_manager.update_from_hardware(value)
        
        # Connect BLE potentiometer callback (implementation depends on BLE manager structure)
        # ble_manager.add_callback('potentiometer_changed', handle_potentiometer_input)
    
    return theme_manager


def apply_theme_to_palette(app, theme: ThemeColors):
    """Apply theme colors to application palette"""
    from PyQt6.QtGui import QPalette, QColor
    
    palette = app.palette()
    
    # Set palette colors
    palette.setColor(QPalette.ColorRole.Window, QColor(theme.background))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.text))
    palette.setColor(QPalette.ColorRole.Base, QColor(theme.surface))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.background))
    palette.setColor(QPalette.ColorRole.Text, QColor(theme.text))
    palette.setColor(QPalette.ColorRole.Button, QColor(theme.primary))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.background))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(theme.accent))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme.background))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(theme.accent))
    palette.setColor(QPalette.ColorRole.Mid, QColor(theme.border))
    palette.setColor(QPalette.ColorRole.Dark, QColor(theme.secondary))
    
    app.setPalette(palette)


# Export main classes and functions
__all__ = [
    'ColorRole',
    'ThemeColors', 
    'PredefinedThemes',
    'ThemeManager',
    'HardwareThemeManager',
    'HardwareCalibration',
    'ThemeTransition',
    'ThemePersistence',
    'create_hardware_theme_manager',
    'apply_theme_to_palette'
]