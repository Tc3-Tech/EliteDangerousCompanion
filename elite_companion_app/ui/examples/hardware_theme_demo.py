#!/usr/bin/env python3
"""
Hardware Theme Integration Demo

This example demonstrates the complete hardware-integrated theme system with:
- Real-time potentiometer control of theme colors
- Smooth HSV transitions
- Hardware calibration interface
- Theme persistence
- Multiple Elite UI examples that respond to theme changes

Usage:
    python hardware_theme_demo.py
"""

import sys
import os
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QPushButton, QTabWidget, QLabel, QSlider, 
                           QCheckBox, QComboBox, QSpinBox, QGroupBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.settings import AppSettings
from config.themes import (HardwareThemeManager, HardwareCalibration, ThemeTransition, 
                          PredefinedThemes, create_hardware_theme_manager)
from ui.elite_widgets import (ElitePanel, EliteButton, EliteHUD, EliteLabel, EliteProgressBar,
                            EliteMediaControl, EliteShipDisplay, EliteSystemMap,
                            setup_hardware_theme_integration, create_calibration_widget,
                            simulate_potentiometer_input, apply_elite_theme,
                            get_global_theme_manager)


class HardwareThemeDemo(QMainWindow):
    """Main demo window showcasing hardware theme integration"""
    
    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.theme_manager = None
        self.simulation_thread = None
        self.setup_ui()
        self.setup_theme_system()
        
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Elite Dangerous - Hardware Theme Integration Demo")
        self.setMinimumSize(1200, 800)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = EliteLabel("ELITE DANGEROUS HARDWARE THEME CONTROL", "header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_control_tab()
        self.create_ui_examples_tab()
        self.create_calibration_tab()
        self.create_settings_tab()
        
    def create_control_tab(self):
        """Create the main control tab"""
        control_widget = QWidget()
        layout = QVBoxLayout(control_widget)
        
        # Theme control panel
        theme_panel = ElitePanel("THEME CONTROL")
        theme_layout = QVBoxLayout()
        
        # Manual hue control
        hue_layout = QHBoxLayout()
        hue_layout.addWidget(EliteLabel("Manual Hue Control:", "small"))
        
        self.hue_slider = QSlider(Qt.Orientation.Horizontal)
        self.hue_slider.setRange(0, 360)
        self.hue_slider.setValue(180)  # Start with blue
        self.hue_slider.valueChanged.connect(self.on_manual_hue_changed)
        hue_layout.addWidget(self.hue_slider)
        
        self.hue_label = EliteLabel("180°", "value")
        hue_layout.addWidget(self.hue_label)
        
        theme_layout.addLayout(hue_layout)
        
        # Predefined themes
        predefined_layout = QHBoxLayout()
        predefined_layout.addWidget(EliteLabel("Predefined Themes:", "small"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "Matrix Green", "Ice Blue", "Deep Purple", 
            "Plasma Pink", "Arctic White", "Ember Red"
        ])
        self.theme_combo.setCurrentText("Ice Blue")
        self.theme_combo.currentTextChanged.connect(self.on_predefined_theme_changed)
        predefined_layout.addWidget(self.theme_combo)
        
        theme_layout.addLayout(predefined_layout)
        
        # Hardware simulation controls
        sim_layout = QVBoxLayout()
        sim_layout.addWidget(EliteLabel("HARDWARE SIMULATION", "header"))
        
        # Enable hardware checkbox
        self.hardware_enabled = QCheckBox("Enable Hardware Theme Control")
        self.hardware_enabled.toggled.connect(self.on_hardware_enabled_changed)
        sim_layout.addWidget(self.hardware_enabled)
        
        # Simulation controls
        sim_control_layout = QHBoxLayout()
        
        self.start_sim_btn = EliteButton("Start Color Sweep")
        self.start_sim_btn.clicked.connect(self.start_simulation)
        sim_control_layout.addWidget(self.start_sim_btn)
        
        self.stop_sim_btn = EliteButton("Stop Simulation")
        self.stop_sim_btn.clicked.connect(self.stop_simulation)
        self.stop_sim_btn.setEnabled(False)
        sim_control_layout.addWidget(self.stop_sim_btn)
        
        sim_layout.addLayout(sim_control_layout)
        
        # Simulation parameters
        param_layout = QHBoxLayout()
        param_layout.addWidget(EliteLabel("Duration (s):", "small"))
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 30)
        self.duration_spin.setValue(10)
        param_layout.addWidget(self.duration_spin)
        
        param_layout.addWidget(EliteLabel("Steps:", "small"))
        
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(10, 500)
        self.steps_spin.setValue(100)
        param_layout.addWidget(self.steps_spin)
        
        sim_layout.addLayout(param_layout)
        
        theme_layout.addLayout(sim_layout)
        theme_panel.content_layout.addLayout(theme_layout)
        layout.addWidget(theme_panel)
        
        # Hardware status panel
        status_panel = ElitePanel("HARDWARE STATUS")
        status_layout = QVBoxLayout()
        
        self.hardware_status = EliteLabel("Hardware: Disconnected", "small")
        status_layout.addWidget(self.hardware_status)
        
        self.raw_value_label = EliteLabel("Raw Value: 0.000", "small")
        status_layout.addWidget(self.raw_value_label)
        
        self.smoothed_value_label = EliteLabel("Smoothed Value: 0.000", "small")
        status_layout.addWidget(self.smoothed_value_label)
        
        self.current_hue_label = EliteLabel("Current Hue: 0.000", "small")
        status_layout.addWidget(self.current_hue_label)
        
        status_panel.content_layout.addLayout(status_layout)
        layout.addWidget(status_panel)
        
        self.tab_widget.addTab(control_widget, "Theme Control")
        
    def create_ui_examples_tab(self):
        """Create tab showing various UI examples"""
        examples_widget = QWidget()
        layout = QVBoxLayout(examples_widget)
        
        # Top row - HUD and Ship Display
        top_row = QHBoxLayout()
        
        # HUD Example
        self.hud = EliteHUD()
        self.hud.set_data({
            "Speed": "150 m/s",
            "Altitude": "2.3 km",
            "Target": "Thargoid Scout",
            "Hull": "98%",
            "Shields": "85%"
        })
        top_row.addWidget(self.hud)
        
        # Ship Display
        self.ship_display = EliteShipDisplay()
        self.ship_display.set_ship("Krait Phantom")
        top_row.addWidget(self.ship_display)
        
        layout.addLayout(top_row)
        
        # Middle row - System Map and Media Control
        middle_row = QHBoxLayout()
        
        # System Map
        self.system_map = EliteSystemMap()
        self.system_map.set_system("Sol", [
            "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn"
        ])
        middle_row.addWidget(self.system_map)
        
        # Media Control
        self.media_control = EliteMediaControl()
        self.media_control.update_track_info("Hyperspace", "Elite Dangerous")
        middle_row.addWidget(self.media_control)
        
        layout.addLayout(middle_row)
        
        # Bottom row - Control panels
        bottom_row = QHBoxLayout()
        
        # Sample controls panel
        controls_panel = ElitePanel("FLIGHT CONTROLS")
        controls_layout = QVBoxLayout()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(EliteButton("LANDING GEAR"))
        btn_layout.addWidget(EliteButton("CARGO SCOOP"))
        btn_layout.addWidget(EliteButton("HARDPOINTS"))
        controls_layout.addLayout(btn_layout)
        
        # Progress bars
        progress_layout = QVBoxLayout()
        
        hull_progress = EliteProgressBar()
        hull_progress.setValue(98)
        hull_progress.setFormat("Hull: %p%")
        progress_layout.addWidget(hull_progress)
        
        shield_progress = EliteProgressBar()
        shield_progress.setValue(85)
        shield_progress.setFormat("Shields: %p%")
        progress_layout.addWidget(shield_progress)
        
        fuel_progress = EliteProgressBar()
        fuel_progress.setValue(67)
        fuel_progress.setFormat("Fuel: %p%")
        progress_layout.addWidget(fuel_progress)
        
        controls_layout.addLayout(progress_layout)
        controls_panel.content_layout.addLayout(controls_layout)
        bottom_row.addWidget(controls_panel)
        
        # Status panel
        status_panel = ElitePanel("STATUS")
        status_layout = QVBoxLayout()
        
        status_layout.addWidget(EliteLabel("DOCKED: No", "small"))
        status_layout.addWidget(EliteLabel("LANDED: No", "small"))
        status_layout.addWidget(EliteLabel("GEAR: Up", "small"))
        status_layout.addWidget(EliteLabel("SCOOP: Retracted", "small"))
        status_layout.addWidget(EliteLabel("HARDPOINTS: Retracted", "small"))
        status_layout.addWidget(EliteLabel("FLIGHT ASSIST: On", "small"))
        
        status_panel.content_layout.addLayout(status_layout)
        bottom_row.addWidget(status_panel)
        
        layout.addLayout(bottom_row)
        
        self.tab_widget.addTab(examples_widget, "UI Examples")
        
    def create_calibration_tab(self):
        """Create hardware calibration tab"""
        calibration_widget = QWidget()
        layout = QVBoxLayout(calibration_widget)
        
        # This will be populated after theme_manager is created
        self.calibration_layout = layout
        
        self.tab_widget.addTab(calibration_widget, "Calibration")
        
    def create_settings_tab(self):
        """Create settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Theme settings panel
        theme_settings_panel = ElitePanel("THEME SETTINGS")
        theme_settings_layout = QVBoxLayout()
        
        # Transition settings
        transition_group = QGroupBox("Transition Settings")
        transition_layout = QVBoxLayout()
        
        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(EliteLabel("Duration (ms):", "small"))
        
        self.duration_spin_settings = QSpinBox()
        self.duration_spin_settings.setRange(0, 1000)
        self.duration_spin_settings.setValue(self.settings.theme.transition_duration_ms)
        self.duration_spin_settings.valueChanged.connect(self.on_transition_duration_changed)
        duration_layout.addWidget(self.duration_spin_settings)
        
        transition_layout.addLayout(duration_layout)
        
        # Easing
        easing_layout = QHBoxLayout()
        easing_layout.addWidget(EliteLabel("Easing:", "small"))
        
        self.easing_combo = QComboBox()
        self.easing_combo.addItems(["linear", "ease_in", "ease_out", "ease_in_out"])
        self.easing_combo.setCurrentText(self.settings.theme.transition_easing)
        self.easing_combo.currentTextChanged.connect(self.on_transition_easing_changed)
        easing_layout.addWidget(self.easing_combo)
        
        transition_layout.addLayout(easing_layout)
        
        # Debounce
        debounce_layout = QHBoxLayout()
        debounce_layout.addWidget(EliteLabel("Debounce (ms):", "small"))
        
        self.debounce_spin = QSpinBox()
        self.debounce_spin.setRange(0, 200)
        self.debounce_spin.setValue(self.settings.theme.debounce_ms)
        self.debounce_spin.valueChanged.connect(self.on_debounce_changed)
        debounce_layout.addWidget(self.debounce_spin)
        
        transition_layout.addLayout(debounce_layout)
        
        transition_group.setLayout(transition_layout)
        theme_settings_layout.addWidget(transition_group)
        
        theme_settings_panel.content_layout.addLayout(theme_settings_layout)
        layout.addWidget(theme_settings_panel)
        
        # Hardware settings panel  
        hardware_settings_panel = ElitePanel("HARDWARE SETTINGS")
        hardware_settings_layout = QVBoxLayout()
        
        # Enable hardware theme control
        self.enable_hardware_theme = QCheckBox("Enable Hardware Theme Control")
        self.enable_hardware_theme.setChecked(self.settings.hardware.enable_hardware_theme_control)
        self.enable_hardware_theme.toggled.connect(self.on_hardware_theme_enable_changed)
        hardware_settings_layout.addWidget(self.enable_hardware_theme)
        
        hardware_settings_panel.content_layout.addLayout(hardware_settings_layout)
        layout.addWidget(hardware_settings_panel)
        
        # Save/Reset buttons
        button_layout = QHBoxLayout()
        
        save_btn = EliteButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        reset_btn = EliteButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(settings_widget, "Settings")
        
    def setup_theme_system(self):
        """Setup the complete theme system"""
        # Create hardware theme manager
        self.theme_manager = create_hardware_theme_manager(
            ble_manager=None,  # No BLE for demo
            settings_manager=self.settings
        )
        
        # Setup global theme integration
        setup_hardware_theme_integration(
            app=QApplication.instance(),
            ble_manager=None,
            settings_manager=self.settings
        )
        
        # Connect to theme manager signals
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        self.theme_manager.hardware_value_changed.connect(self.on_hardware_value_changed)
        self.theme_manager.calibrated_value_changed.connect(self.on_calibrated_value_changed)
        
        # Add calibration widget to calibration tab
        calibration_widget = create_calibration_widget(
            parent=None, 
            theme_manager=self.theme_manager
        )
        self.calibration_layout.addWidget(calibration_widget)
        
        # Apply initial theme
        apply_elite_theme(QApplication.instance(), PredefinedThemes.ICE_BLUE)
        
    def on_manual_hue_changed(self, value):
        """Handle manual hue slider change"""
        if self.theme_manager and not self.hardware_enabled.isChecked():
            hue = value / 360.0  # Convert to 0-1 range
            self.hue_label.setText(f"{value}°")
            
            # Generate and apply custom theme
            theme = self.theme_manager.generate_custom_theme(hue, 0.8, 0.9)
            self.theme_manager.set_theme(theme, animate=True)
            
    def on_predefined_theme_changed(self, theme_name):
        """Handle predefined theme selection"""
        if self.theme_manager and not self.hardware_enabled.isChecked():
            self.theme_manager.set_predefined_theme(theme_name, animate=True)
            
    def on_hardware_enabled_changed(self, enabled):
        """Handle hardware enable/disable"""
        if self.theme_manager:
            self.theme_manager.enable_hardware_control(enabled)
            self.hardware_status.setText(
                f"Hardware: {'Enabled (Simulated)' if enabled else 'Disabled'}"
            )
            
            # Enable/disable manual controls
            self.hue_slider.setEnabled(not enabled)
            self.theme_combo.setEnabled(not enabled)
            self.start_sim_btn.setEnabled(enabled)
            
    def start_simulation(self):
        """Start hardware simulation"""
        if self.theme_manager and self.hardware_enabled.isChecked():
            duration = self.duration_spin.value() * 1000  # Convert to ms
            steps = self.steps_spin.value()
            
            self.simulation_thread = simulate_potentiometer_input(
                self.theme_manager, 
                start_value=0.0, 
                end_value=1.0, 
                duration_ms=duration, 
                steps=steps
            )
            
            self.start_sim_btn.setEnabled(False)
            self.stop_sim_btn.setEnabled(True)
            
            # Auto-disable after simulation completes
            QTimer.singleShot(duration + 1000, self.simulation_complete)
            
    def stop_simulation(self):
        """Stop hardware simulation"""
        self.start_sim_btn.setEnabled(True)
        self.stop_sim_btn.setEnabled(False)
        
    def simulation_complete(self):
        """Called when simulation completes"""
        self.start_sim_btn.setEnabled(True)
        self.stop_sim_btn.setEnabled(False)
        
    def on_theme_changed(self, theme):
        """Handle theme change from theme manager"""
        pass  # Theme is automatically applied to all widgets
        
    def on_hardware_value_changed(self, value):
        """Handle raw hardware value change"""
        self.raw_value_label.setText(f"Raw Value: {value:.3f}")
        
    def on_calibrated_value_changed(self, value):
        """Handle calibrated value change"""
        self.smoothed_value_label.setText(f"Smoothed Value: {value:.3f}")
        hue_degrees = value * 360
        self.current_hue_label.setText(f"Current Hue: {hue_degrees:.1f}°")
        
    def on_transition_duration_changed(self, value):
        """Handle transition duration change"""
        self.settings.theme.transition_duration_ms = value
        if self.theme_manager:
            config = self.settings.get_theme_transition_config()
            self.theme_manager.set_transition_config(config)
            
    def on_transition_easing_changed(self, value):
        """Handle transition easing change"""
        self.settings.theme.transition_easing = value
        if self.theme_manager:
            config = self.settings.get_theme_transition_config()
            self.theme_manager.set_transition_config(config)
            
    def on_debounce_changed(self, value):
        """Handle debounce change"""
        self.settings.theme.debounce_ms = value
        if self.theme_manager:
            config = self.settings.get_theme_transition_config()
            self.theme_manager.set_transition_config(config)
            
    def on_hardware_theme_enable_changed(self, enabled):
        """Handle hardware theme enable change"""
        self.settings.hardware.enable_hardware_theme_control = enabled
        
    def save_settings(self):
        """Save current settings"""
        self.settings.save()
        
        # Also save current calibration if hardware is enabled
        if self.theme_manager:
            self.settings.save_hardware_calibration(self.theme_manager.calibration)
            config = self.settings.get_theme_transition_config()
            self.settings.save_theme_transition_config(config)
        
        print("Settings saved successfully!")
        
    def reset_settings(self):
        """Reset settings to defaults"""
        self.settings.reset_to_defaults()
        
        # Update UI controls
        self.duration_spin_settings.setValue(self.settings.theme.transition_duration_ms)
        self.easing_combo.setCurrentText(self.settings.theme.transition_easing)
        self.debounce_spin.setValue(self.settings.theme.debounce_ms)
        self.enable_hardware_theme.setChecked(self.settings.hardware.enable_hardware_theme_control)
        
        # Reset theme manager if available
        if self.theme_manager:
            calibration = self.settings.get_hardware_calibration_config()
            self.theme_manager.set_calibration(calibration)
            
            config = self.settings.get_theme_transition_config()
            self.theme_manager.set_transition_config(config)
        
        print("Settings reset to defaults!")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Elite Dangerous Hardware Theme Demo")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Elite Companion")
    
    # Create and show main window
    window = HardwareThemeDemo()
    window.show()
    
    # Start event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())