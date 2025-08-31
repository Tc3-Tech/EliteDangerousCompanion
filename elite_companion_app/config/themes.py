"""
Theme system for customizable HUD colors and styling.
"""
from typing import Dict, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
import colorsys


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


class ThemeManager:
    """Manages theme application and custom color generation"""
    
    def __init__(self):
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
    
    def set_theme(self, theme: ThemeColors):
        """Set the current theme"""
        self.current_theme = theme
        self._notify_theme_change()
    
    def set_predefined_theme(self, theme_name: str):
        """Set a predefined theme by name"""
        if theme_name in self.predefined_themes:
            self.set_theme(self.predefined_themes[theme_name])
    
    def generate_custom_theme(self, hue: float, saturation: float = 0.8, 
                            brightness: float = 0.9) -> ThemeColors:
        """Generate a custom theme from HSV values"""
        # Convert HSV to RGB for primary color
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
        primary_hex = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        # Generate secondary (darker) and accent (lighter) colors
        secondary_r, secondary_g, secondary_b = colorsys.hsv_to_rgb(hue, saturation, brightness * 0.7)
        secondary_hex = f"#{int(secondary_r*255):02x}{int(secondary_g*255):02x}{int(secondary_b*255):02x}"
        
        accent_r, accent_g, accent_b = colorsys.hsv_to_rgb(hue, saturation * 0.6, brightness)
        accent_hex = f"#{int(accent_r*255):02x}{int(accent_g*255):02x}{int(accent_b*255):02x}"
        
        # Generate text color (high contrast)
        text_brightness = 0.95 if brightness < 0.5 else 0.1
        text_r, text_g, text_b = colorsys.hsv_to_rgb(hue, saturation * 0.2, text_brightness)
        text_hex = f"#{int(text_r*255):02x}{int(text_g*255):02x}{int(text_b*255):02x}"
        
        return ThemeColors(
            primary=primary_hex,
            secondary=secondary_hex,
            accent=accent_hex,
            background="#0A0A0A",
            surface="#1A1A1A",
            text=text_hex,
            text_secondary=secondary_hex,
            border=secondary_hex,
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
    
    def _notify_theme_change(self):
        """Notify all listeners of theme change"""
        for callback in self.theme_change_callbacks:
            callback(self.current_theme)