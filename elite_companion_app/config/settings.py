"""
Application settings management with persistent storage.
"""
import configparser
import os
from pathlib import Path
from typing import Any, Optional, Dict
from dataclasses import dataclass, asdict
import yaml
from pathlib import Path


@dataclass
class DisplaySettings:
    """Display-related settings"""
    use_secondary_display: bool = True
    fullscreen: bool = False
    width: int = 1024
    height: int = 768
    framerate_limit: int = 60


@dataclass
class ThemeSettings:
    """Theme and color settings"""
    current_theme: str = "Ice Blue"
    custom_hue: float = 0.5
    custom_saturation: float = 0.8
    custom_brightness: float = 0.9
    use_custom_theme: bool = False
    
    # Hardware integration settings
    hardware_control_enabled: bool = False
    
    # Theme transition settings
    transition_duration_ms: int = 150
    transition_easing: str = "ease_out"  # "linear", "ease_in", "ease_out", "ease_in_out"
    interpolation_steps: int = 30
    debounce_ms: int = 50


@dataclass
class HardwareSettings:
    """Hardware input settings"""
    ble_device_name: str = "EDMC_Controller"
    enable_ble: bool = True
    button_debounce_ms: int = 50
    pot_smoothing: float = 0.85  # Changed from 0.1 to 0.85 for better smoothing
    invert_pot: bool = False
    
    # Potentiometer calibration settings
    pot_min_value: float = 0.0
    pot_max_value: float = 1.0
    pot_dead_zone: float = 0.02
    sensitivity_curve: str = "linear"  # "linear", "exponential", "logarithmic"
    
    # Hue range mapping for theme control
    hue_range_start: float = 0.0  # Starting hue (0-1)
    hue_range_end: float = 1.0    # Ending hue (0-1)
    
    # Hardware theme control
    enable_hardware_theme_control: bool = False
    theme_update_rate_ms: int = 100  # Rate limit for theme updates


@dataclass
class IntegrationSettings:
    """External service integration settings"""
    edmc_enabled: bool = True
    edmc_plugin_path: str = ""
    spotify_enabled: bool = False
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    auto_detect_elite: bool = True
    
    # WSL-Windows Integration Settings
    enable_wsl_integration: bool = True
    enable_journal_monitoring: bool = True
    journal_poll_interval: float = 0.5
    enable_process_monitoring: bool = True
    process_poll_interval: float = 2.0
    enable_audio_integration: bool = True
    enable_media_monitoring: bool = True
    audio_profile_on_game_start: bool = True
    enable_ble_integration: bool = True
    ble_device_name: str = "EDMC_Controller"
    ble_auto_connect: bool = True


@dataclass
class UISettings:
    """User interface settings"""
    show_button_hints: bool = True
    animation_speed: float = 1.0
    sound_enabled: bool = True
    screensaver_timeout: int = 300  # seconds


class AppSettings:
    """Main settings manager with file persistence"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".config" / "elite_companion"
        
        self.config_dir = config_dir
        self.config_file = config_dir / "settings.yaml"
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize settings with defaults
        self.display = DisplaySettings()
        self.theme = ThemeSettings()
        self.hardware = HardwareSettings()
        self.integration = IntegrationSettings()
        self.ui = UISettings()
        
        # Load existing settings
        self.load()
    
    def load(self):
        """Load settings from file"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Update settings from file
            if 'display' in data:
                self._update_dataclass(self.display, data['display'])
            if 'theme' in data:
                self._update_dataclass(self.theme, data['theme'])
            if 'hardware' in data:
                self._update_dataclass(self.hardware, data['hardware'])
            if 'integration' in data:
                self._update_dataclass(self.integration, data['integration'])
            if 'ui' in data:
                self._update_dataclass(self.ui, data['ui'])
                
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save(self):
        """Save settings to file"""
        try:
            data = {
                'display': asdict(self.display),
                'theme': asdict(self.theme),
                'hardware': asdict(self.hardware),
                'integration': asdict(self.integration),
                'ui': asdict(self.ui),
            }
            
            with open(self.config_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _update_dataclass(self, instance, data: Dict[str, Any]):
        """Update a dataclass instance with dictionary data"""
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get a setting value with fallback (for compatibility)"""
        section_obj = getattr(self, section, None)
        if section_obj is None:
            return fallback
        
        return getattr(section_obj, key, fallback)
    
    def set(self, section: str, key: str, value: Any):
        """Set a setting value"""
        section_obj = getattr(self, section, None)
        if section_obj is not None:
            setattr(section_obj, key, value)
            self.save()  # Auto-save on change
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.display = DisplaySettings()
        self.theme = ThemeSettings()
        self.hardware = HardwareSettings()
        self.integration = IntegrationSettings()
        self.ui = UISettings()
        self.save()
    
    def get_hardware_calibration_config(self):
        """Get hardware calibration configuration for theme manager"""
        from .themes import HardwareCalibration
        
        return HardwareCalibration(
            min_value=self.hardware.pot_min_value,
            max_value=self.hardware.pot_max_value,
            dead_zone=self.hardware.pot_dead_zone,
            smoothing_factor=self.hardware.pot_smoothing,
            invert=self.hardware.invert_pot,
            hue_range_start=self.hardware.hue_range_start,
            hue_range_end=self.hardware.hue_range_end,
            sensitivity_curve=self.hardware.sensitivity_curve
        )
    
    def get_theme_transition_config(self):
        """Get theme transition configuration for theme manager"""
        from .themes import ThemeTransition
        
        return ThemeTransition(
            duration_ms=self.theme.transition_duration_ms,
            easing=self.theme.transition_easing,
            interpolation_steps=self.theme.interpolation_steps,
            debounce_ms=self.theme.debounce_ms
        )
    
    def is_hardware_theme_control_enabled(self) -> bool:
        """Check if hardware theme control is enabled"""
        return (
            self.hardware.enable_hardware_theme_control and 
            self.theme.hardware_control_enabled and 
            self.hardware.enable_ble
        )
    
    def save_hardware_calibration(self, calibration):
        """Save hardware calibration settings"""
        self.hardware.pot_min_value = calibration.min_value
        self.hardware.pot_max_value = calibration.max_value
        self.hardware.pot_dead_zone = calibration.dead_zone
        self.hardware.pot_smoothing = calibration.smoothing_factor
        self.hardware.invert_pot = calibration.invert
        self.hardware.hue_range_start = calibration.hue_range_start
        self.hardware.hue_range_end = calibration.hue_range_end
        self.hardware.sensitivity_curve = calibration.sensitivity_curve
        self.save()
    
    def save_theme_transition_config(self, config):
        """Save theme transition configuration"""
        self.theme.transition_duration_ms = config.duration_ms
        self.theme.transition_easing = config.easing
        self.theme.interpolation_steps = config.interpolation_steps
        self.theme.debounce_ms = config.debounce_ms
        self.save()