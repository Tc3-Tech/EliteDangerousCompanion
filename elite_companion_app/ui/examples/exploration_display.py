"""
Elite Dangerous System Exploration Display
Interactive star system maps with planet information and discovery data.
"""
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QTabWidget, QListWidget,
                           QListWidgetItem, QSplitter, QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QBrush, QFont, QColor, QLinearGradient, QRadialGradient
import math
import random

# Add the parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from elite_widgets import (ElitePanel, EliteLabel, EliteButton, EliteProgressBar, 
                          EliteSystemMap, apply_elite_theme)
from config.themes import ThemeManager, PredefinedThemes


class PlanetaryBody:
    """Class representing a planetary body in the system"""
    
    def __init__(self, name, body_type, distance, mass=None, radius=None, 
                 temperature=None, discovered=False, mapped=False):
        self.name = name
        self.body_type = body_type  # "Star", "Planet", "Moon", "Station", "Belt"
        self.distance = distance  # Distance from system center in LS
        self.mass = mass
        self.radius = radius
        self.temperature = temperature
        self.discovered = discovered
        self.mapped = mapped
        self.orbital_angle = random.uniform(0, 2 * math.pi)
        self.orbital_speed = 1.0 / (distance + 1)  # Closer bodies orbit faster


class InteractiveSystemMap(QWidget):
    """Interactive system map with clickable bodies and detailed view"""
    
    body_selected = pyqtSignal(object)  # Signal when a body is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 400)
        self.system_name = "Sol"
        self.bodies = []
        self.selected_body = None
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.last_mouse_pos = QPoint()
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_orbits)
        self.animation_timer.start(50)  # 20 FPS
        
        self.animation_phase = 0.0
        self.setup_sol_system()
        
        # Enable mouse tracking
        self.setMouseTracking(True)
    
    def setup_sol_system(self):
        """Setup the Sol system with realistic data"""
        self.system_name = "Sol"
        self.bodies = [
            # Central star
            PlanetaryBody("Sol", "Star", 0, mass="1.989 × 10³⁰ kg", radius="695,700 km", 
                         temperature="5,778 K", discovered=True),
            
            # Planets
            PlanetaryBody("Mercury", "Planet", 0.39, mass="3.30 × 10²³ kg", radius="2,439 km", 
                         temperature="440 K", discovered=True, mapped=True),
            PlanetaryBody("Venus", "Planet", 0.72, mass="4.87 × 10²⁴ kg", radius="6,051 km", 
                         temperature="737 K", discovered=True, mapped=True),
            PlanetaryBody("Earth", "Planet", 1.00, mass="5.97 × 10²⁴ kg", radius="6,371 km", 
                         temperature="288 K", discovered=True, mapped=True),
            PlanetaryBody("Mars", "Planet", 1.52, mass="6.39 × 10²³ kg", radius="3,389 km", 
                         temperature="210 K", discovered=True, mapped=True),
            PlanetaryBody("Jupiter", "Gas Giant", 5.20, mass="1.90 × 10²⁷ kg", radius="69,911 km", 
                         temperature="165 K", discovered=True, mapped=True),
            PlanetaryBody("Saturn", "Gas Giant", 9.58, mass="5.68 × 10²⁶ kg", radius="58,232 km", 
                         temperature="134 K", discovered=True, mapped=True),
            PlanetaryBody("Uranus", "Ice Giant", 19.22, mass="8.68 × 10²⁵ kg", radius="25,362 km", 
                         temperature="76 K", discovered=True, mapped=False),
            PlanetaryBody("Neptune", "Ice Giant", 30.05, mass="1.02 × 10²⁶ kg", radius="24,622 km", 
                         temperature="72 K", discovered=True, mapped=False),
            
            # Notable moons
            PlanetaryBody("Luna", "Moon", 1.00, mass="7.35 × 10²² kg", radius="1,737 km", 
                         temperature="250 K", discovered=True, mapped=True),
            
            # Stations
            PlanetaryBody("Abraham Lincoln", "Station", 1.00, discovered=True),
            PlanetaryBody("Daedalus", "Station", 1.52, discovered=True)
        ]
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        zoom_factor = 1.2 if event.angleDelta().y() > 0 else 1.0 / 1.2
        self.zoom_level *= zoom_factor
        self.zoom_level = max(0.5, min(5.0, self.zoom_level))  # Limit zoom range
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse press for selecting bodies or starting pan"""
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_body = self.get_body_at_position(event.position().toPoint())
            if clicked_body:
                self.selected_body = clicked_body
                self.body_selected.emit(clicked_body)
                self.update()
            else:
                # Start panning
                self.last_mouse_pos = event.position().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            # Reset view
            self.zoom_level = 1.0
            self.pan_offset = QPoint(0, 0)
            self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement for panning"""
        if event.buttons() & Qt.MouseButton.LeftButton and not self.get_body_at_position(event.position().toPoint()):
            delta = event.position().toPoint() - self.last_mouse_pos
            self.pan_offset += delta
            self.last_mouse_pos = event.position().toPoint()
            self.update()
    
    def get_body_at_position(self, pos: QPoint):
        """Get the planetary body at the given screen position"""
        center_x = self.width() // 2 + self.pan_offset.x()
        center_y = self.height() // 2 + self.pan_offset.y()
        
        for body in self.bodies:
            if body.body_type == "Star":
                body_x = center_x
                body_y = center_y
                body_radius = 20 * self.zoom_level
            else:
                orbit_radius = body.distance * 50 * self.zoom_level
                body_x = center_x + orbit_radius * math.cos(body.orbital_angle)
                body_y = center_y + orbit_radius * math.sin(body.orbital_angle)
                body_radius = self.get_body_display_radius(body)
            
            # Check if click is within body radius
            distance = math.sqrt((pos.x() - body_x) ** 2 + (pos.y() - body_y) ** 2)
            if distance <= body_radius:
                return body
        
        return None
    
    def get_body_display_radius(self, body):
        """Get the display radius for a body based on its type"""
        base_radius = 5 * self.zoom_level
        
        if body.body_type == "Star":
            return 20 * self.zoom_level
        elif body.body_type == "Gas Giant":
            return 12 * self.zoom_level
        elif body.body_type == "Ice Giant":
            return 10 * self.zoom_level
        elif body.body_type == "Planet":
            return 8 * self.zoom_level
        elif body.body_type == "Moon":
            return 4 * self.zoom_level
        elif body.body_type == "Station":
            return 6 * self.zoom_level
        else:
            return base_radius
    
    def get_body_color(self, body):
        """Get the display color for a body based on its type"""
        if body.body_type == "Star":
            return QColor(255, 255, 100)
        elif body.body_type == "Gas Giant":
            return QColor(255, 200, 150)
        elif body.body_type == "Ice Giant":
            return QColor(150, 200, 255)
        elif body.body_type == "Planet":
            if "Earth" in body.name:
                return QColor(100, 150, 255)
            elif "Mars" in body.name:
                return QColor(255, 100, 100)
            elif "Venus" in body.name:
                return QColor(255, 200, 100)
            else:
                return QColor(200, 200, 200)
        elif body.body_type == "Moon":
            return QColor(180, 180, 180)
        elif body.body_type == "Station":
            return QColor(0, 255, 255)
        else:
            return QColor(255, 255, 255)
    
    def update_orbits(self):
        """Update orbital positions"""
        self.animation_phase = (self.animation_phase + 0.02) % (2 * math.pi)
        
        for body in self.bodies:
            if body.body_type != "Star":
                body.orbital_angle += body.orbital_speed * 0.02
        
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for interactive system map"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(5, 5, 15))
        
        # Draw star field
        self.draw_star_field(painter)
        
        center_x = self.width() // 2 + self.pan_offset.x()
        center_y = self.height() // 2 + self.pan_offset.y()
        
        # Draw orbital paths
        for body in self.bodies:
            if body.body_type != "Star":
                orbit_radius = body.distance * 50 * self.zoom_level
                
                # Draw orbit path
                pen = QPen(QColor(100, 100, 100, 80), 1, Qt.PenStyle.DotLine)
                painter.setPen(pen)
                painter.setBrush(QBrush())
                painter.drawEllipse(int(center_x - orbit_radius), int(center_y - orbit_radius),
                                  int(orbit_radius * 2), int(orbit_radius * 2))
        
        # Draw bodies
        for body in self.bodies:
            if body.body_type == "Star":
                body_x = center_x
                body_y = center_y
            else:
                orbit_radius = body.distance * 50 * self.zoom_level
                body_x = center_x + orbit_radius * math.cos(body.orbital_angle)
                body_y = center_y + orbit_radius * math.sin(body.orbital_angle)
            
            # Draw body
            body_radius = self.get_body_display_radius(body)
            body_color = self.get_body_color(body)
            
            # Selection highlight
            if body == self.selected_body:
                highlight_pen = QPen(QColor(0, 255, 255), 3)
                painter.setPen(highlight_pen)
                painter.setBrush(QBrush())
                painter.drawEllipse(int(body_x - body_radius - 5), int(body_y - body_radius - 5),
                                  int((body_radius + 5) * 2), int((body_radius + 5) * 2))
            
            # Draw body
            if body.body_type == "Star":
                # Radial gradient for star glow
                gradient = QRadialGradient(body_x, body_y, body_radius)
                gradient.setColorAt(0, QColor(255, 255, 200))
                gradient.setColorAt(0.7, QColor(255, 200, 100))
                gradient.setColorAt(1, QColor(255, 100, 0, 100))
                painter.setBrush(QBrush(gradient))
                painter.setPen(QPen(body_color, 2))
            else:
                painter.setBrush(QBrush(body_color))
                painter.setPen(QPen(body_color.lighter(), 1))
            
            painter.drawEllipse(int(body_x - body_radius), int(body_y - body_radius),
                              int(body_radius * 2), int(body_radius * 2))
            
            # Draw body name if zoomed in enough
            if self.zoom_level > 0.8:
                painter.setPen(QPen(Qt.GlobalColor.white, 1))
                font = QFont("Arial", max(8, int(8 * self.zoom_level)))
                painter.setFont(font)
                text_rect = QRect(int(body_x - 50), int(body_y + body_radius + 5), 100, 20)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, body.name)
            
            # Draw discovery/mapping status
            if body.discovered and self.zoom_level > 0.6:
                status_y = body_y + body_radius + 20
                if body.mapped:
                    painter.setPen(QPen(QColor(0, 255, 0), 1))
                    painter.drawText(int(body_x - 20), int(status_y), "MAPPED")
                else:
                    painter.setPen(QPen(QColor(255, 255, 0), 1))
                    painter.drawText(int(body_x - 25), int(status_y), "DISCOVERED")
        
        # Draw system name and info
        self.draw_system_info(painter)
    
    def draw_star_field(self, painter: QPainter):
        """Draw background stars"""
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        
        # Static star positions based on widget size
        for i in range(100):
            x = (i * 97) % self.width()
            y = (i * 73) % self.height()
            alpha = (i * 31) % 100 + 50  # Vary brightness
            
            star_color = QColor(255, 255, 255, alpha)
            painter.setPen(QPen(star_color, 1))
            painter.drawPoint(x, y)
    
    def draw_system_info(self, painter: QPainter):
        """Draw system information overlay"""
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        
        # System name
        painter.drawText(10, 25, f"SYSTEM: {self.system_name}")
        
        # Controls info
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        controls_text = [
            "LEFT CLICK: Select body",
            "MOUSE WHEEL: Zoom",
            "RIGHT CLICK: Reset view",
            "DRAG: Pan view"
        ]
        
        y_pos = self.height() - 80
        for text in controls_text:
            painter.drawText(10, y_pos, text)
            y_pos += 15
        
        # Zoom indicator
        painter.drawText(self.width() - 150, self.height() - 20, f"ZOOM: {self.zoom_level:.1f}x")


class BodyDetailsPanel(ElitePanel):
    """Panel showing detailed information about a selected body"""
    
    def __init__(self, parent=None):
        super().__init__("BODY DETAILS", parent)
        self.current_body = None
        self.setup_details_ui()
    
    def setup_details_ui(self):
        """Setup body details UI"""
        # Create scroll area for details
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.details_layout = QVBoxLayout(scroll_widget)
        
        # Initially show "No body selected" message
        self.no_selection_label = EliteLabel("NO BODY SELECTED", "header")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_layout.addWidget(self.no_selection_label)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.add_widget(scroll_area)
    
    def show_body_details(self, body):
        """Show details for the selected body"""
        self.current_body = body
        
        # Clear existing layout
        for i in reversed(range(self.details_layout.count())):
            self.details_layout.itemAt(i).widget().setParent(None)
        
        if not body:
            self.details_layout.addWidget(self.no_selection_label)
            return
        
        # Body name and type
        name_label = EliteLabel(body.name.upper(), "header")
        self.details_layout.addWidget(name_label)
        
        type_label = EliteLabel(f"TYPE: {body.body_type.upper()}", "value")
        self.details_layout.addWidget(type_label)
        
        # Distance
        if body.body_type != "Star":
            distance_label = EliteLabel(f"DISTANCE: {body.distance:.2f} AU", "value")
            self.details_layout.addWidget(distance_label)
        
        # Physical properties
        if body.mass:
            mass_label = EliteLabel(f"MASS: {body.mass}", "value")
            self.details_layout.addWidget(mass_label)
        
        if body.radius:
            radius_label = EliteLabel(f"RADIUS: {body.radius}", "value")
            self.details_layout.addWidget(radius_label)
        
        if body.temperature:
            temp_label = EliteLabel(f"SURFACE TEMP: {body.temperature}", "value")
            self.details_layout.addWidget(temp_label)
        
        # Discovery status
        discovery_label = EliteLabel("DISCOVERY STATUS:", "small")
        self.details_layout.addWidget(discovery_label)
        
        if body.discovered:
            discovered_label = EliteLabel("✓ DISCOVERED", "value")
            discovered_label.setStyleSheet("color: #00FF00;")
            self.details_layout.addWidget(discovered_label)
            
            if body.mapped:
                mapped_label = EliteLabel("✓ DETAILED SURFACE SCAN", "value")
                mapped_label.setStyleSheet("color: #00FF00;")
                self.details_layout.addWidget(mapped_label)
            else:
                unmapped_label = EliteLabel("✗ NOT MAPPED", "value")
                unmapped_label.setStyleSheet("color: #FFFF00;")
                self.details_layout.addWidget(unmapped_label)
        else:
            undiscovered_label = EliteLabel("✗ NOT DISCOVERED", "value")
            undiscovered_label.setStyleSheet("color: #FF4444;")
            self.details_layout.addWidget(undiscovered_label)
        
        # Add scan button for undiscovered/unmapped bodies
        if not body.discovered or not body.mapped:
            if body.body_type != "Station":
                scan_btn = EliteButton("INITIATE SCAN" if not body.discovered else "DETAILED SURFACE SCAN")
                scan_btn.clicked.connect(lambda: self.initiate_scan(body))
                self.details_layout.addWidget(scan_btn)
        
        # Spacer
        self.details_layout.addStretch()
    
    def initiate_scan(self, body):
        """Simulate scanning a body"""
        if not body.discovered:
            body.discovered = True
        elif not body.mapped and body.body_type in ["Planet", "Moon"]:
            body.mapped = True
        
        # Refresh display
        self.show_body_details(body)


class ExplorationDataPanel(ElitePanel):
    """Panel showing exploration statistics and discoveries"""
    
    def __init__(self, parent=None):
        super().__init__("EXPLORATION DATA", parent)
        self.setup_exploration_ui()
        
        # Update timer for statistics
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)
        self.stats_timer.start(5000)  # Update every 5 seconds
    
    def setup_exploration_ui(self):
        """Setup exploration statistics UI"""
        # Statistics
        stats_grid = QGridLayout()
        
        # Credits earned
        stats_grid.addWidget(EliteLabel("CREDITS EARNED:", "small"), 0, 0)
        self.credits_label = EliteLabel("2,450,750 CR", "value")
        stats_grid.addWidget(self.credits_label, 0, 1)
        
        # Systems visited
        stats_grid.addWidget(EliteLabel("SYSTEMS VISITED:", "small"), 1, 0)
        self.systems_label = EliteLabel("127", "value")
        stats_grid.addWidget(self.systems_label, 1, 1)
        
        # Bodies discovered
        stats_grid.addWidget(EliteLabel("BODIES DISCOVERED:", "small"), 2, 0)
        self.bodies_label = EliteLabel("423", "value")
        stats_grid.addWidget(self.bodies_label, 2, 1)
        
        # Bodies mapped
        stats_grid.addWidget(EliteLabel("BODIES MAPPED:", "small"), 3, 0)
        self.mapped_label = EliteLabel("156", "value")
        stats_grid.addWidget(self.mapped_label, 3, 1)
        
        # Distance traveled
        stats_grid.addWidget(EliteLabel("DISTANCE TRAVELED:", "small"), 4, 0)
        self.distance_label = EliteLabel("15,234 ly", "value")
        stats_grid.addWidget(self.distance_label, 4, 1)
        
        # Efficiency rating
        stats_grid.addWidget(EliteLabel("EFFICIENCY RATING:", "small"), 5, 0)
        efficiency_bar = EliteProgressBar()
        efficiency_bar.setValue(78)
        stats_grid.addWidget(efficiency_bar, 5, 1)
        
        self.add_layout(stats_grid)
        
        # Recent discoveries list
        self.add_widget(EliteLabel("RECENT DISCOVERIES:", "small"))
        
        self.discoveries_list = QListWidget()
        self.discoveries_list.setMaximumHeight(150)
        
        discoveries = [
            "High Metal Content World - Sol 3 (Earth)",
            "Icy Body - Sol 6a (Europa)",
            "Rocky Body - Proxima Centauri b",
            "Gas Giant - Kepler-442 b",
            "Water World - Gliese 667 Cc"
        ]
        
        for discovery in discoveries:
            item = QListWidgetItem(discovery)
            self.discoveries_list.addItem(item)
        
        self.add_widget(self.discoveries_list)
    
    def update_statistics(self):
        """Update exploration statistics (simulated)"""
        # Simulate gradual progress
        current_credits = int(self.credits_label.text().replace(",", "").replace(" CR", ""))
        current_systems = int(self.systems_label.text())
        current_bodies = int(self.bodies_label.text())
        current_mapped = int(self.mapped_label.text())
        current_distance = float(self.distance_label.text().replace(" ly", "").replace(",", ""))
        
        # Small random increases
        self.credits_label.setText(f"{current_credits + random.randint(0, 50000):,} CR")
        
        if random.random() < 0.3:  # 30% chance to discover new system
            self.systems_label.setText(str(current_systems + 1))
        
        if random.random() < 0.5:  # 50% chance to discover new body
            self.bodies_label.setText(str(current_bodies + 1))
        
        if random.random() < 0.2:  # 20% chance to map a body
            self.mapped_label.setText(str(current_mapped + 1))
        
        self.distance_label.setText(f"{current_distance + random.uniform(0, 5):.1f} ly")


class ExplorationWindow(QMainWindow):
    """Main Exploration Display Window"""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.setup_window()
        self.setup_ui()
        
        # Apply initial theme
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
    
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("Elite Dangerous - System Exploration")
        self.setGeometry(100, 100, 1024, 768)
        self.setMinimumSize(800, 600)
    
    def setup_ui(self):
        """Setup the exploration display UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Left side - Interactive system map
        map_panel = ElitePanel("SYSTEM MAP")
        self.system_map = InteractiveSystemMap()
        self.system_map.body_selected.connect(self.on_body_selected)
        map_panel.add_widget(self.system_map)
        
        main_layout.addWidget(map_panel, 3)
        
        # Right side - Body details and exploration data
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Body details panel
        self.body_details = BodyDetailsPanel()
        right_splitter.addWidget(self.body_details)
        
        # Exploration data panel
        self.exploration_data = ExplorationDataPanel()
        right_splitter.addWidget(self.exploration_data)
        
        # Set splitter proportions
        right_splitter.setSizes([400, 300])
        
        main_layout.addWidget(right_splitter, 2)
        
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
        
        # Add to main layout
        main_layout_with_themes = QVBoxLayout()
        main_layout_with_themes.addLayout(main_layout)
        main_layout_with_themes.addWidget(theme_widget)
        
        container = QWidget()
        container.setLayout(main_layout_with_themes)
        self.setCentralWidget(container)
    
    def on_body_selected(self, body):
        """Handle body selection from the system map"""
        self.body_details.show_body_details(body)
    
    def change_theme(self, theme_name: str):
        """Change the application theme"""
        self.theme_manager.set_predefined_theme(theme_name)
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
        
        # Force refresh
        self.update()
        for widget in self.findChildren(QWidget):
            widget.update()


def main():
    """Main function to run the Exploration Display example"""
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show exploration window
    window = ExplorationWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())