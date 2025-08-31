#!/usr/bin/env python3
"""
Simple PyQt6 test to verify Elite Dangerous theming works in WSL
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor

class SimpleEliteWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elite Dangerous UI Test")
        self.setFixedSize(800, 600)
        
        # Set Elite color scheme (Ice Blue theme)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0A0F1A;
                color: #E0F8FF;
            }
            QLabel {
                color: #00D4FF;
                font-size: 18px;
                font-weight: bold;
                margin: 10px;
            }
            QPushButton {
                background-color: #00D4FF;
                color: #0A0F1A;
                border: 2px solid #0099CC;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #40E0FF;
            }
            QPushButton:pressed {
                background-color: #0099CC;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Add content
        title = QLabel("ELITE DANGEROUS COMPANION")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        status = QLabel("System Status: OPERATIONAL")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status)
        
        # Theme buttons
        themes = [
            ("Ice Blue", "#00D4FF"),
            ("Matrix Green", "#00FF41"), 
            ("Deep Purple", "#9D4EDD"),
            ("Plasma Pink", "#FF006E")
        ]
        
        for theme_name, color in themes:
            btn = QPushButton(f"Switch to {theme_name}")
            btn.clicked.connect(lambda checked, c=color, n=theme_name: self.change_theme(c, n))
            layout.addWidget(btn)
        
        layout.addStretch()
        
    def change_theme(self, primary_color, theme_name):
        """Change the theme colors"""
        # Calculate derived colors
        if primary_color == "#00D4FF":  # Ice Blue
            bg_color = "#0A0F1A"
            secondary_color = "#0099CC"
        elif primary_color == "#00FF41":  # Matrix Green
            bg_color = "#0A0A0A"
            secondary_color = "#00CC33"
        elif primary_color == "#9D4EDD":  # Deep Purple
            bg_color = "#1A0A2E"
            secondary_color = "#7B2CBF"
        else:  # Plasma Pink
            bg_color = "#1A0A14"
            secondary_color = "#CC0055"
        
        # Apply new theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg_color};
                color: #E0F8FF;
            }}
            QLabel {{
                color: {primary_color};
                font-size: 18px;
                font-weight: bold;
                margin: 10px;
            }}
            QPushButton {{
                background-color: {primary_color};
                color: {bg_color};
                border: 2px solid {secondary_color};
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {secondary_color};
            }}
            QPushButton:pressed {{
                background-color: {secondary_color};
                border-color: {primary_color};
            }}
        """)
        
        # Update window title
        self.setWindowTitle(f"Elite Dangerous UI Test - {theme_name}")


def main():
    # Set up Qt for WSL
    import os
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    app = QApplication(sys.argv)
    app.setApplicationName("Elite Dangerous UI Test")
    
    window = SimpleEliteWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())