"""
Elite Dangerous Ship Information Panel
Detailed technical specifications and 3D visualization of the current ship.
"""
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QTabWidget, QScrollArea, 
                           QSplitter, QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QLinearGradient, QPixmap, QTransform
import math

# Add the parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from elite_widgets import (ElitePanel, EliteLabel, EliteButton, EliteProgressBar, 
                          EliteShipDisplay, apply_elite_theme)
from config.themes import ThemeManager, PredefinedThemes


class ShipSpecsPanel(ElitePanel):
    """Panel showing detailed ship specifications"""
    
    def __init__(self, parent=None):
        super().__init__("SHIP SPECIFICATIONS", parent)
        self.current_ship_data = self.get_asp_explorer_data()
        self.setup_specs_ui()
    
    def get_asp_explorer_data(self):
        """Get Asp Explorer ship data"""
        return {
            "name": "Asp Explorer",
            "manufacturer": "Lakon Spaceways",
            "class": "Medium",
            "cost": "6,661,154 CR",
            "mass": "280 t",
            "max_cargo": "120 t",
            "jump_range": "35.36 ly",
            "max_speed": "254 m/s",
            "boost_speed": "340 m/s",
            "shields": "105 MJ",
            "armour": "315",
            "hardpoints": {
                "large": 2,
                "medium": 2,
                "small": 2,
                "utility": 4
            },
            "internal_slots": {
                "class_6": 1,
                "class_5": 2,
                "class_4": 2,
                "class_3": 3,
                "class_2": 4,
                "class_1": 2
            },
            "crew": "2"
        }
    
    def setup_specs_ui(self):
        """Setup ship specifications UI"""
        # Create tabs for different spec categories
        tabs = QTabWidget()
        
        # Basic Info Tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        basic_grid = QGridLayout()
        specs = [
            ("MANUFACTURER:", self.current_ship_data["manufacturer"]),
            ("SHIP CLASS:", self.current_ship_data["class"]),
            ("PURCHASE COST:", self.current_ship_data["cost"]),
            ("MASS (EMPTY):", self.current_ship_data["mass"]),
            ("MAX CARGO:", self.current_ship_data["max_cargo"]),
            ("CREW SEATS:", self.current_ship_data["crew"])
        ]
        
        for i, (label, value) in enumerate(specs):
            basic_grid.addWidget(EliteLabel(label, "small"), i, 0)
            basic_grid.addWidget(EliteLabel(value, "value"), i, 1)
        
        basic_layout.addLayout(basic_grid)
        basic_layout.addStretch()
        tabs.addTab(basic_tab, "BASIC INFO")
        
        # Performance Tab
        perf_tab = QWidget()
        perf_layout = QVBoxLayout(perf_tab)
        
        perf_grid = QGridLayout()
        performance = [
            ("MAX SPEED:", self.current_ship_data["max_speed"]),
            ("BOOST SPEED:", self.current_ship_data["boost_speed"]),
            ("JUMP RANGE:", self.current_ship_data["jump_range"]),
            ("SHIELD STRENGTH:", self.current_ship_data["shields"]),
            ("HULL ARMOUR:", self.current_ship_data["armour"])
        ]
        
        for i, (label, value) in enumerate(performance):
            perf_grid.addWidget(EliteLabel(label, "small"), i, 0)
            perf_grid.addWidget(EliteLabel(value, "value"), i, 1)
        
        perf_layout.addLayout(perf_grid)
        perf_layout.addStretch()
        tabs.addTab(perf_tab, "PERFORMANCE")
        
        # Hardpoints Tab
        hardpoint_tab = QWidget()
        hardpoint_layout = QVBoxLayout(hardpoint_tab)
        
        hardpoint_grid = QGridLayout()
        hardpoints = [
            ("LARGE HARDPOINTS:", str(self.current_ship_data["hardpoints"]["large"])),
            ("MEDIUM HARDPOINTS:", str(self.current_ship_data["hardpoints"]["medium"])),
            ("SMALL HARDPOINTS:", str(self.current_ship_data["hardpoints"]["small"])),
            ("UTILITY MOUNTS:", str(self.current_ship_data["hardpoints"]["utility"]))
        ]
        
        for i, (label, value) in enumerate(hardpoints):
            hardpoint_grid.addWidget(EliteLabel(label, "small"), i, 0)
            hardpoint_grid.addWidget(EliteLabel(value, "value"), i, 1)
        
        hardpoint_layout.addLayout(hardpoint_grid)
        hardpoint_layout.addStretch()
        tabs.addTab(hardpoint_tab, "HARDPOINTS")
        
        # Internal Slots Tab
        slots_tab = QWidget()
        slots_layout = QVBoxLayout(slots_tab)
        
        slots_grid = QGridLayout()
        slots = [
            ("CLASS 6 SLOTS:", str(self.current_ship_data["internal_slots"]["class_6"])),
            ("CLASS 5 SLOTS:", str(self.current_ship_data["internal_slots"]["class_5"])),
            ("CLASS 4 SLOTS:", str(self.current_ship_data["internal_slots"]["class_4"])),
            ("CLASS 3 SLOTS:", str(self.current_ship_data["internal_slots"]["class_3"])),
            ("CLASS 2 SLOTS:", str(self.current_ship_data["internal_slots"]["class_2"])),
            ("CLASS 1 SLOTS:", str(self.current_ship_data["internal_slots"]["class_1"]))
        ]
        
        for i, (label, value) in enumerate(slots):
            slots_grid.addWidget(EliteLabel(label, "small"), i, 0)
            slots_grid.addWidget(EliteLabel(value, "value"), i, 1)
        
        slots_layout.addLayout(slots_grid)
        slots_layout.addStretch()
        tabs.addTab(slots_tab, "INTERNALS")
        
        self.add_widget(tabs)


class ShipLoadoutPanel(ElitePanel):
    """Panel showing current ship loadout and modules"""
    
    def __init__(self, parent=None):
        super().__init__("CURRENT LOADOUT", parent)
        self.setup_loadout_ui()
    
    def setup_loadout_ui(self):
        """Setup loadout tree view"""
        self.loadout_tree = QTreeWidget()
        self.loadout_tree.setHeaderLabels(["MODULE", "RATING", "CLASS", "STATUS"])
        
        # Core Modules
        core_item = QTreeWidgetItem(["CORE MODULES", "", "", ""])
        core_modules = [
            ("Power Plant", "A", "4", "100%"),
            ("Thrusters", "A", "5", "100%"),
            ("Frame Shift Drive", "A", "5", "100%"),
            ("Life Support", "A", "4", "100%"),
            ("Power Distributor", "A", "5", "100%"),
            ("Sensors", "A", "4", "100%"),
            ("Fuel Tank", "C", "5", "100%")
        ]
        
        for name, rating, class_num, status in core_modules:
            module_item = QTreeWidgetItem([name, rating, class_num, status])
            core_item.addChild(module_item)
        
        self.loadout_tree.addTopLevelItem(core_item)
        
        # Hardpoints
        hardpoint_item = QTreeWidgetItem(["HARDPOINTS", "", "", ""])
        hardpoints = [
            ("Large Hardpoint 1", "Pulse Laser", "2A/F", "100%"),
            ("Large Hardpoint 2", "Pulse Laser", "2A/F", "100%"),
            ("Medium Hardpoint 1", "Multi-cannon", "2A/F", "100%"),
            ("Medium Hardpoint 2", "Multi-cannon", "2A/F", "100%"),
            ("Small Hardpoint 1", "Empty", "", ""),
            ("Small Hardpoint 2", "Empty", "", "")
        ]
        
        for name, weapon, rating, status in hardpoints:
            hardpoint_item_child = QTreeWidgetItem([name, weapon, rating, status])
            hardpoint_item.addChild(hardpoint_item_child)
        
        self.loadout_tree.addTopLevelItem(hardpoint_item)
        
        # Internal Modules
        internal_item = QTreeWidgetItem(["INTERNAL MODULES", "", "", ""])
        internals = [
            ("Slot 6", "Fuel Scoop", "6A", "100%"),
            ("Slot 5-1", "Cargo Rack", "5E", "100%"),
            ("Slot 5-2", "Cargo Rack", "5E", "100%"),
            ("Slot 4-1", "Shield Generator", "4A", "100%"),
            ("Slot 4-2", "Auto Field-Main Unit", "4A", "100%"),
            ("Slot 3-1", "Detailed Surface Scanner", "3C", "100%"),
            ("Slot 3-2", "Advanced Discovery Scanner", "3E", "100%"),
            ("Slot 3-3", "Supercruise Assist", "3E", "100%")
        ]
        
        for name, module, rating, status in internals:
            internal_item_child = QTreeWidgetItem([name, module, rating, status])
            internal_item.addChild(internal_item_child)
        
        self.loadout_tree.addTopLevelItem(internal_item)
        
        # Expand all items
        self.loadout_tree.expandAll()
        
        self.add_widget(self.loadout_tree)


class Ship3DViewer(QWidget):
    """3D-style ship viewer with rotation and technical overlay"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ship_image = None
        self.rotation_angle = 0.0
        self.hover_effect = 0.0
        self.setMinimumSize(400, 300)
        
        # Animation timers
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.rotate_ship)
        self.rotation_timer.start(50)  # 20 FPS
        
        self.hover_timer = QTimer()
        self.hover_timer.timeout.connect(self.update_hover)
        self.hover_timer.start(100)  # 10 FPS
        
        # Load ship image
        self.load_ship_image("asp-explorer")
    
    def load_ship_image(self, ship_name: str):
        """Load ship image from assets"""
        image_path = f"/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets/{ship_name}.png"
        if os.path.exists(image_path):
            self.ship_image = QPixmap(image_path)
        self.update()
    
    def rotate_ship(self):
        """Rotate ship slowly"""
        self.rotation_angle = (self.rotation_angle + 1.0) % 360.0
        self.update()
    
    def update_hover(self):
        """Update hover bobbing effect"""
        self.hover_effect = (self.hover_effect + 0.2) % (2 * math.pi)
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for 3D ship viewer"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.ship_image:
            # Calculate hover offset
            hover_offset = int(math.sin(self.hover_effect) * 10)
            
            # Create transform for rotation
            transform = QTransform()
            transform.translate(self.width() / 2, self.height() / 2)
            transform.rotate(self.rotation_angle)
            transform.scale(0.8, 0.8)  # Scale down slightly
            transform.translate(-self.ship_image.width() / 2, -self.ship_image.height() / 2)
            
            painter.setTransform(transform)
            
            # Draw ship with hover offset
            painter.drawPixmap(0, hover_offset, self.ship_image)
            
            painter.resetTransform()
        
        # Draw technical overlay
        self.draw_technical_overlay(painter)
    
    def draw_technical_overlay(self, painter: QPainter):
        """Draw technical readouts and scan lines"""
        painter.setPen(QPen(self.palette().text().color(), 1))
        font = QFont("Courier New", 8, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Corner brackets
        bracket_size = 15
        corners = [
            (10, 10),                                    # Top-left
            (self.width() - 10 - bracket_size, 10),     # Top-right
            (10, self.height() - 10 - bracket_size),    # Bottom-left
            (self.width() - 10 - bracket_size, self.height() - 10 - bracket_size)  # Bottom-right
        ]
        
        for x, y in corners:
            painter.drawLine(x, y, x + bracket_size, y)
            painter.drawLine(x, y, x, y + bracket_size)
        
        # Technical readouts
        readouts = [
            "MASS: 280.00t",
            "LENGTH: 56.0m",
            "WIDTH: 51.3m",
            "HEIGHT: 11.0m",
            "INTEGRITY: 100%"
        ]
        
        y_pos = 30
        for readout in readouts:
            painter.drawText(15, y_pos, readout)
            y_pos += 15
        
        # Scan lines (animated)
        pen = QPen(self.palette().highlight().color(), 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        scan_y = int((self.hover_effect * self.height() / (2 * math.pi)) % self.height())
        painter.drawLine(0, scan_y, self.width(), scan_y)


class PowerManagementPanel(ElitePanel):
    """Panel for power distribution and management"""
    
    power_changed = pyqtSignal(str, int)  # Signal for power changes
    
    def __init__(self, parent=None):
        super().__init__("POWER MANAGEMENT", parent)
        self.sys_power = 2
        self.eng_power = 2
        self.wep_power = 2
        self.total_power = 8  # Standard 4 pips per system, 2 default each
        self.setup_power_ui()
    
    def setup_power_ui(self):
        """Setup power management UI"""
        # Power bars for SYS/ENG/WEP
        systems = [
            ("SYSTEMS", "sys_power", "SYS"),
            ("ENGINES", "eng_power", "ENG"),
            ("WEAPONS", "wep_power", "WEP")
        ]
        
        self.power_bars = {}
        
        for name, attr, short_name in systems:
            # System name
            self.add_widget(EliteLabel(f"{name}:", "small"))
            
            # Power bar (shows pips)
            power_layout = QHBoxLayout()
            
            # Decrease button
            decrease_btn = EliteButton("−")
            decrease_btn.setMaximumSize(30, 30)
            decrease_btn.clicked.connect(lambda checked, s=short_name: self.decrease_power(s))
            power_layout.addWidget(decrease_btn)
            
            # Power display (pip representation)
            power_bar = EliteProgressBar()
            power_bar.setRange(0, 4)  # 0 to 4 pips
            power_bar.setValue(getattr(self, attr))
            self.power_bars[short_name] = power_bar
            power_layout.addWidget(power_bar)
            
            # Increase button
            increase_btn = EliteButton("+")
            increase_btn.setMaximumSize(30, 30)
            increase_btn.clicked.connect(lambda checked, s=short_name: self.increase_power(s))
            power_layout.addWidget(increase_btn)
            
            self.add_layout(power_layout)
        
        # Total power indicator
        self.add_widget(EliteLabel("", "small"))  # Spacer
        total_label = EliteLabel(f"TOTAL POWER: {self.total_power}/8", "value")
        self.add_widget(total_label)
        self.total_power_label = total_label
    
    def increase_power(self, system: str):
        """Increase power to a system"""
        current = self.get_power(system)
        if current < 4 and self.total_power < 8:
            self.set_power(system, current + 1)
            self.total_power += 1
            self.update_display()
            self.power_changed.emit(system, current + 1)
    
    def decrease_power(self, system: str):
        """Decrease power to a system"""
        current = self.get_power(system)
        if current > 0:
            self.set_power(system, current - 1)
            self.total_power -= 1
            self.update_display()
            self.power_changed.emit(system, current - 1)
    
    def get_power(self, system: str) -> int:
        """Get current power level for system"""
        mapping = {"SYS": "sys_power", "ENG": "eng_power", "WEP": "wep_power"}
        return getattr(self, mapping[system])
    
    def set_power(self, system: str, value: int):
        """Set power level for system"""
        mapping = {"SYS": "sys_power", "ENG": "eng_power", "WEP": "wep_power"}
        setattr(self, mapping[system], value)
    
    def update_display(self):
        """Update power display bars"""
        for system, bar in self.power_bars.items():
            bar.setValue(self.get_power(system))
        
        self.total_power_label.setText(f"TOTAL POWER: {self.total_power}/8")


class ShipDetailsWindow(QMainWindow):
    """Ship Details Main Window"""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.setup_window()
        self.setup_ui()
        
        # Apply initial theme
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
    
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("Elite Dangerous - Ship Details")
        self.setGeometry(100, 100, 1024, 768)
        self.setMinimumSize(800, 600)
    
    def setup_ui(self):
        """Setup the ship details UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Left side - 3D viewer and power management
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 3D ship viewer
        viewer_panel = ElitePanel("3D SHIP VIEWER")
        self.ship_viewer = Ship3DViewer()
        viewer_panel.add_widget(self.ship_viewer)
        left_layout.addWidget(viewer_panel, 2)
        
        # Power management
        self.power_panel = PowerManagementPanel()
        left_layout.addWidget(self.power_panel, 1)
        
        main_layout.addWidget(left_panel, 2)
        
        # Right side - Ship specs and loadout
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Ship specifications
        self.ship_specs = ShipSpecsPanel()
        right_splitter.addWidget(self.ship_specs)
        
        # Ship loadout
        self.ship_loadout = ShipLoadoutPanel()
        right_splitter.addWidget(self.ship_loadout)
        
        # Set splitter proportions
        right_splitter.setSizes([300, 400])
        
        main_layout.addWidget(right_splitter, 3)
        
        # Theme controls at bottom
        theme_layout = QHBoxLayout()
        
        themes = [
            ("ICE BLUE", "Ice Blue"),
            ("MATRIX GREEN", "Matrix Green"),
            ("DEEP PURPLE", "Deep Purple"),
            ("PLASMA PINK", "Plasma Pink")
        ]
        
        for btn_text, theme_name in themes:
            theme_btn = EliteButton(btn_text)
            theme_btn.clicked.connect(lambda checked, t=theme_name: self.change_theme(t))
            theme_layout.addWidget(theme_btn)
        
        theme_layout.addStretch()
        
        theme_widget = QWidget()
        theme_widget.setLayout(theme_layout)
        theme_widget.setMaximumHeight(50)
        
        # Add to main layout at bottom
        main_layout_with_themes = QVBoxLayout()
        main_layout_with_themes.addLayout(main_layout)
        main_layout_with_themes.addWidget(theme_widget)
        
        container = QWidget()
        container.setLayout(main_layout_with_themes)
        self.setCentralWidget(container)
    
    def change_theme(self, theme_name: str):
        """Change the application theme"""
        self.theme_manager.set_predefined_theme(theme_name)
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
        
        # Force refresh
        self.update()
        for widget in self.findChildren(QWidget):
            widget.update()


def main():
    """Main function to run the Ship Details example"""
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show ship details window
    window = ShipDetailsWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())