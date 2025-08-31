"""
Elite Dangerous Main Dashboard Example
Demonstrates the main status display for the companion app with real-time data visualization.
"""
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QLabel, QSplitter)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

# Add the parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from elite_widgets import (ElitePanel, EliteLabel, EliteButton, EliteProgressBar, 
                          EliteHUD, EliteShipDisplay, apply_elite_theme)
from config.themes import ThemeManager, PredefinedThemes


class CommanderStatus(ElitePanel):
    """Panel showing commander information and status"""
    
    def __init__(self, parent=None):
        super().__init__("COMMANDER STATUS", parent)
        self.setup_commander_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second
    
    def setup_commander_ui(self):
        """Setup commander status UI elements"""
        # Commander info grid
        info_grid = QGridLayout()
        
        # Commander name
        info_grid.addWidget(EliteLabel("CMDR:", "small"), 0, 0)
        self.cmdr_name = EliteLabel("JOHN SHEPARD", "value")
        info_grid.addWidget(self.cmdr_name, 0, 1)
        
        # Credits
        info_grid.addWidget(EliteLabel("CREDITS:", "small"), 1, 0)
        self.credits = EliteLabel("1,234,567,890 CR", "value")
        info_grid.addWidget(self.credits, 1, 1)
        
        # Rank
        info_grid.addWidget(EliteLabel("COMBAT RANK:", "small"), 2, 0)
        self.combat_rank = EliteLabel("ELITE", "value")
        info_grid.addWidget(self.combat_rank, 2, 1)
        
        # Trade rank
        info_grid.addWidget(EliteLabel("TRADE RANK:", "small"), 3, 0)
        self.trade_rank = EliteLabel("MERCHANT", "value")
        info_grid.addWidget(self.trade_rank, 3, 1)
        
        # Exploration rank
        info_grid.addWidget(EliteLabel("EXPLORATION:", "small"), 4, 0)
        self.exploration_rank = EliteLabel("PATHFINDER", "value")
        info_grid.addWidget(self.exploration_rank, 4, 1)
        
        self.add_layout(info_grid)
    
    def update_status(self):
        """Update commander status (simulated)"""
        import random
        
        # Simulate credit changes
        current_credits = int(self.credits.text().replace(",", "").replace(" CR", ""))
        change = random.randint(-1000, 5000)
        new_credits = max(0, current_credits + change)
        self.credits.setText(f"{new_credits:,} CR")


class ShipStatus(ElitePanel):
    """Panel showing current ship status and health"""
    
    def __init__(self, parent=None):
        super().__init__("SHIP STATUS", parent)
        self.setup_ship_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ship_status)
        self.update_timer.start(2000)  # Update every 2 seconds
        
        # Ship health values
        self.hull_integrity = 100
        self.power_plant = 100
        self.thrusters = 100
        self.life_support = 100
        self.fsd = 100
    
    def setup_ship_ui(self):
        """Setup ship status UI"""
        # Ship name and type
        ship_info = QHBoxLayout()
        ship_info.addWidget(EliteLabel("CURRENT SHIP:", "small"))
        self.ship_name = EliteLabel("ASP EXPLORER", "value")
        ship_info.addWidget(self.ship_name)
        ship_info.addStretch()
        self.add_layout(ship_info)
        
        # Health bars
        self.hull_bar = EliteProgressBar()
        self.hull_bar.setValue(self.hull_integrity)
        self.add_widget(EliteLabel("Hull Integrity:", "small"))
        self.add_widget(self.hull_bar)
        
        self.power_bar = EliteProgressBar()
        self.power_bar.setValue(self.power_plant)
        self.add_widget(EliteLabel("Power Plant:", "small"))
        self.add_widget(self.power_bar)
        
        self.thruster_bar = EliteProgressBar()
        self.thruster_bar.setValue(self.thrusters)
        self.add_widget(EliteLabel("Thrusters:", "small"))
        self.add_widget(self.thruster_bar)
        
        self.fsd_bar = EliteProgressBar()
        self.fsd_bar.setValue(self.fsd)
        self.add_widget(EliteLabel("Frame Shift Drive:", "small"))
        self.add_widget(self.fsd_bar)
    
    def update_ship_status(self):
        """Update ship status (simulated wear and repair)"""
        import random
        
        # Simulate gradual wear
        systems = [
            (self.hull_bar, 'hull_integrity'),
            (self.power_bar, 'power_plant'),
            (self.thruster_bar, 'thrusters'),
            (self.fsd_bar, 'fsd')
        ]
        
        for bar, attr_name in systems:
            current_val = getattr(self, attr_name)
            # Small chance of damage, higher chance of repair
            change = random.choice([-2, -1, 0, 0, 0, 1, 2, 3])
            new_val = max(0, min(100, current_val + change))
            setattr(self, attr_name, new_val)
            bar.setValue(new_val)


class SystemInfo(ElitePanel):
    """Panel showing current system information"""
    
    def __init__(self, parent=None):
        super().__init__("SYSTEM INFORMATION", parent)
        self.setup_system_ui()
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self.update_system_info)
        self.system_timer.start(10000)  # Update every 10 seconds
    
    def setup_system_ui(self):
        """Setup system information UI"""
        # System details grid
        system_grid = QGridLayout()
        
        # Current system
        system_grid.addWidget(EliteLabel("SYSTEM:", "small"), 0, 0)
        self.current_system = EliteLabel("SOL", "value")
        system_grid.addWidget(self.current_system, 0, 1)
        
        # Station
        system_grid.addWidget(EliteLabel("STATION:", "small"), 1, 0)
        self.current_station = EliteLabel("ABRAHAM LINCOLN", "value")
        system_grid.addWidget(self.current_station, 1, 1)
        
        # Security level
        system_grid.addWidget(EliteLabel("SECURITY:", "small"), 2, 0)
        self.security_level = EliteLabel("HIGH", "value")
        system_grid.addWidget(self.security_level, 2, 1)
        
        # Government
        system_grid.addWidget(EliteLabel("GOVERNMENT:", "small"), 3, 0)
        self.government = EliteLabel("FEDERATION", "value")
        system_grid.addWidget(self.government, 3, 1)
        
        # Economy
        system_grid.addWidget(EliteLabel("ECONOMY:", "small"), 4, 0)
        self.economy = EliteLabel("SERVICE", "value")
        system_grid.addWidget(self.economy, 4, 1)
        
        # Population
        system_grid.addWidget(EliteLabel("POPULATION:", "small"), 5, 0)
        self.population = EliteLabel("22,780,000,000", "value")
        system_grid.addWidget(self.population, 5, 1)
        
        self.add_layout(system_grid)
    
    def update_system_info(self):
        """Update system information (simulate system changes)"""
        systems = [
            ("DECIAT", "JAMESON MEMORIAL", "LOW", "INDEPENDENT", "INDUSTRIAL"),
            ("SHINRARTA DEZHRA", "JAMESON MEMORIAL", "PERMIT", "PILOTS FED", "SERVICE"),
            ("LTT 15574", "CELSIUS STATION", "MEDIUM", "FEDERATION", "EXTRACTION"),
            ("MAIA", "OBSIDIAN ORBITAL", "ANARCHY", "INDEPENDENT", "TOURISM"),
            ("COLONIA", "JAQUES STATION", "MEDIUM", "INDEPENDENT", "REFINERY")
        ]
        
        import random
        system_data = random.choice(systems)
        
        self.current_system.setText(system_data[0])
        self.current_station.setText(system_data[1])
        self.security_level.setText(system_data[2])
        self.government.setText(system_data[3])
        self.economy.setText(system_data[4])


class MissionTracker(ElitePanel):
    """Panel showing active missions and objectives"""
    
    def __init__(self, parent=None):
        super().__init__("ACTIVE MISSIONS", parent)
        self.setup_mission_ui()
    
    def setup_mission_ui(self):
        """Setup mission tracking UI"""
        # Mission list
        missions = [
            ("DATA COURIER", "DELIVER TO SHINRARTA DEZHRA", "2,340,000 CR"),
            ("MASSACRE", "ELIMINATE 12 PIRATES", "8,750,000 CR"),
            ("EXPLORATION", "SCAN 5 SYSTEMS", "1,200,000 CR")
        ]
        
        for i, (mission_type, description, reward) in enumerate(missions):
            mission_layout = QVBoxLayout()
            
            # Mission type header
            type_label = EliteLabel(mission_type, "header")
            mission_layout.addWidget(type_label)
            
            # Description
            desc_label = EliteLabel(description, "small")
            mission_layout.addWidget(desc_label)
            
            # Reward
            reward_label = EliteLabel(f"REWARD: {reward}", "value")
            mission_layout.addWidget(reward_label)
            
            # Progress bar (simulate mission progress)
            progress = EliteProgressBar()
            progress.setValue((i + 1) * 25)  # Different progress for each mission
            mission_layout.addWidget(progress)
            
            self.add_layout(mission_layout)
            
            if i < len(missions) - 1:  # Add separator except for last mission
                separator = QLabel("─" * 40)
                separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.add_widget(separator)


class EliteDashboard(QMainWindow):
    """Main Elite Dangerous Dashboard Window"""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.setup_ui()
        self.setup_window()
        
        # Apply initial theme
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
    
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("Elite Dangerous - Main Dashboard")
        self.setGeometry(100, 100, 1024, 768)  # Target resolution
        self.setMinimumSize(800, 600)
        
        # Set window flags for secondary display
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
    
    def setup_ui(self):
        """Setup the main dashboard UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - split between HUD and status panels
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Left side - HUD display
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # HUD display
        self.hud = EliteHUD()
        self.hud.set_data({
            "SPEED": "245 m/s",
            "ALTITUDE": "2.3 km",
            "HEADING": "092°",
            "FUEL": "87%",
            "CARGO": "12/64t"
        })
        left_layout.addWidget(self.hud, 2)  # Give HUD more space
        
        # Ship display
        self.ship_display = EliteShipDisplay()
        self.ship_display.set_ship("Asp Explorer")
        left_layout.addWidget(self.ship_display, 1)
        
        main_layout.addWidget(left_panel, 3)  # Left side takes 3/5 of space
        
        # Right side - Status panels
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Commander status
        self.commander_status = CommanderStatus()
        right_splitter.addWidget(self.commander_status)
        
        # Ship status
        self.ship_status = ShipStatus()
        right_splitter.addWidget(self.ship_status)
        
        # System info
        self.system_info = SystemInfo()
        right_splitter.addWidget(self.system_info)
        
        # Mission tracker
        self.mission_tracker = MissionTracker()
        right_splitter.addWidget(self.mission_tracker)
        
        # Set splitter proportions
        right_splitter.setSizes([200, 200, 150, 200])
        
        main_layout.addWidget(right_splitter, 2)  # Right side takes 2/5 of space
        
        # Theme switching buttons at the bottom
        theme_layout = QHBoxLayout()
        
        theme_btn_ice = EliteButton("ICE BLUE")
        theme_btn_ice.clicked.connect(lambda: self.change_theme("Ice Blue"))
        theme_layout.addWidget(theme_btn_ice)
        
        theme_btn_green = EliteButton("MATRIX GREEN")
        theme_btn_green.clicked.connect(lambda: self.change_theme("Matrix Green"))
        theme_layout.addWidget(theme_btn_green)
        
        theme_btn_purple = EliteButton("DEEP PURPLE")
        theme_btn_purple.clicked.connect(lambda: self.change_theme("Deep Purple"))
        theme_layout.addWidget(theme_btn_purple)
        
        theme_btn_pink = EliteButton("PLASMA PINK")
        theme_btn_pink.clicked.connect(lambda: self.change_theme("Plasma Pink"))
        theme_layout.addWidget(theme_btn_pink)
        
        theme_layout.addStretch()
        
        # Add theme buttons to the right panel at bottom
        theme_widget = QWidget()
        theme_widget.setLayout(theme_layout)
        theme_widget.setMaximumHeight(50)
        right_splitter.addWidget(theme_widget)
    
    def change_theme(self, theme_name: str):
        """Change the application theme"""
        self.theme_manager.set_predefined_theme(theme_name)
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
        
        # Force refresh of all widgets
        self.update()
        for widget in self.findChildren(QWidget):
            widget.update()


def main():
    """Main function to run the Elite Dashboard example"""
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show dashboard
    dashboard = EliteDashboard()
    dashboard.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())