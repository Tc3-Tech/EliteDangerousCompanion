#!/usr/bin/env python3
"""
Simple Hardware Theme Integration Example

This shows how to integrate the hardware theme system into an existing application
with minimal code changes.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import QTimer

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.settings import AppSettings
from ui.elite_widgets import (ElitePanel, EliteButton, EliteHUD, EliteProgressBar,
                            setup_hardware_theme_integration, simulate_potentiometer_input)


class SimpleEliteApp(QMainWindow):
    """Simple Elite-themed application with hardware theme integration"""
    
    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.theme_manager = None
        self.setup_ui()
        self.setup_theme_integration()
        
    def setup_ui(self):
        """Setup basic UI"""
        self.setWindowTitle("Elite App with Hardware Themes")
        self.setMinimumSize(600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Main panel
        panel = ElitePanel("FLIGHT STATUS")
        
        # HUD display
        self.hud = EliteHUD()
        self.hud.set_data({
            "Speed": "245 m/s",
            "Altitude": "1.2 km", 
            "Target": "None",
            "Hull": "100%"
        })
        panel.add_widget(self.hud)
        
        # Progress bars
        self.hull_bar = EliteProgressBar()
        self.hull_bar.setValue(100)
        self.hull_bar.setFormat("Hull Integrity: %p%")
        panel.add_widget(self.hull_bar)
        
        self.shield_bar = EliteProgressBar()
        self.shield_bar.setValue(85)
        self.shield_bar.setFormat("Shield Strength: %p%")
        panel.add_widget(self.shield_bar)
        
        # Control buttons
        btn_demo = EliteButton("Start Theme Demo")
        btn_demo.clicked.connect(self.start_theme_demo)
        panel.add_widget(btn_demo)
        
        layout.addWidget(panel)
        
    def setup_theme_integration(self):
        """Setup hardware theme integration - this is all you need!"""
        # This single function call sets up the entire hardware theme system
        self.theme_manager = setup_hardware_theme_integration(
            app=QApplication.instance(),
            ble_manager=None,  # Your BLE manager would go here
            settings_manager=self.settings
        )
        
        # Optionally enable hardware control
        if self.settings.is_hardware_theme_control_enabled():
            self.theme_manager.enable_hardware_control(True)
            
    def start_theme_demo(self):
        """Demonstrate theme changes with simulated hardware input"""
        if self.theme_manager:
            # Enable hardware mode temporarily
            self.theme_manager.enable_hardware_control(True)
            
            # Start a color sweep simulation
            simulate_potentiometer_input(
                self.theme_manager,
                start_value=0.0,
                end_value=1.0,
                duration_ms=8000,
                steps=80
            )
            
            # Update HUD data during demo
            QTimer.singleShot(2000, lambda: self.hud.set_data({
                "Speed": "312 m/s", "Altitude": "0.8 km", "Target": "Anaconda", "Hull": "95%"
            }))
            
            QTimer.singleShot(4000, lambda: (
                self.hull_bar.setValue(95),
                self.shield_bar.setValue(72)
            ))
            
            QTimer.singleShot(6000, lambda: self.hud.set_data({
                "Speed": "156 m/s", "Altitude": "2.1 km", "Target": "Station", "Hull": "95%"  
            }))


def main():
    """Run the simple example"""
    app = QApplication(sys.argv)
    
    window = SimpleEliteApp()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())