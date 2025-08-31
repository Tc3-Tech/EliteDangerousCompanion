"""
Elite Dangerous Ship Comparison System
Advanced side-by-side ship analysis with visual charts and performance metrics.
"""
import sys
import os
import math
from typing import List, Dict, Optional, Tuple, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                           QScrollArea, QFrame, QLabel, QPushButton, QComboBox,
                           QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                           QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QPointF
from PyQt6.QtGui import (QPainter, QPen, QBrush, QFont, QColor, QPainterPath, 
                       QLinearGradient, QPolygonF)

# Add app root to path for imports
from pathlib import Path
app_root = Path(__file__).parent.parent.parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

from data.ship_database import get_ship_database, ShipSpecification
from ui.elite_widgets import (ElitePanel, EliteLabel, EliteButton, ThemeAwareWidget, 
                          get_global_theme_manager)
from config.themes import ThemeColors


class RadarChart(QWidget, ThemeAwareWidget):
    """Radar/spider chart for comparing ship capabilities"""
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.ships = []
        self.metrics = []
        self.max_values = {}
        self._current_theme = None
        
        self.setMinimumSize(300, 300)
        
        # Standard ship comparison metrics
        self.default_metrics = [
            ("Combat", "firepower_rating", 20),
            ("Speed", "max_speed", 400),
            ("Jump Range", "max_jump_range", 80),
            ("Cargo", "max_cargo_capacity", 800),
            ("Shields", "base_shield_strength", 600),
            ("Hull", "hull_integrity", 1500),
            ("Agility", "calculated_agility", 100),  # Calculated metric
            ("Cost Efficiency", "cost_efficiency", 100)  # Calculated metric
        ]
        
        self.set_default_metrics()
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def set_default_metrics(self):
        """Set default comparison metrics"""
        self.metrics = []
        self.max_values = {}
        
        for name, key, max_val in self.default_metrics:
            self.metrics.append({"name": name, "key": key})
            self.max_values[key] = max_val
    
    def set_ships(self, ships: List[ShipSpecification]):
        """Set ships to compare"""
        self.ships = ships[:4]  # Limit to 4 ships for readability
        self.update()
    
    def get_ship_metric_value(self, ship: ShipSpecification, metric_key: str) -> float:
        """Get metric value for a ship"""
        if metric_key == "firepower_rating":
            return ship.firepower_rating
        elif metric_key == "max_speed":
            return ship.performance.max_speed
        elif metric_key == "max_jump_range":
            return ship.performance.max_jump_range
        elif metric_key == "max_cargo_capacity":
            return ship.internal_slots.max_cargo_capacity
        elif metric_key == "base_shield_strength":
            return ship.performance.base_shield_strength
        elif metric_key == "hull_integrity":
            return ship.performance.hull_integrity
        elif metric_key == "calculated_agility":
            # Calculate agility based on mass and speed
            if ship.performance.hull_mass > 0:
                return min(100, (ship.performance.boost_speed / ship.performance.hull_mass) * 10)
            return 0
        elif metric_key == "cost_efficiency":
            # Calculate cost efficiency (lower cost per ton is better)
            if ship.cost_per_ton > 0:
                return max(0, 100 - (ship.cost_per_ton / 1000))
            return 0
        
        return 0
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme colors"""
        self._current_theme = theme
        self.update()
    
    def paintEvent(self, event):
        """Paint radar chart"""
        if not self.ships or not self.metrics:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get theme colors
        if self._current_theme:
            primary_color = QColor(self._current_theme.primary)
            accent_color = QColor(self._current_theme.accent)
            text_color = QColor(self._current_theme.text)
            surface_color = QColor(self._current_theme.surface)
            border_color = QColor(self._current_theme.border)
        else:
            palette = self.palette()
            primary_color = palette.highlight().color()
            accent_color = palette.highlightedText().color()
            text_color = palette.text().color()
            surface_color = palette.base().color()
            border_color = palette.mid().color()
        
        # Calculate chart dimensions
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) / 2 - 60
        
        # Draw grid circles
        painter.setPen(QPen(border_color, 1))
        for i in range(1, 6):
            grid_radius = (radius * i) / 5
            painter.drawEllipse(center, grid_radius, grid_radius)
        
        # Draw metric axes and labels
        angle_step = 2 * math.pi / len(self.metrics)
        
        painter.setPen(QPen(border_color, 1))
        font = QFont("Arial", 8)
        painter.setFont(font)
        
        for i, metric in enumerate(self.metrics):
            angle = i * angle_step - math.pi / 2  # Start from top
            
            # Draw axis line
            end_point = QPointF(
                center.x() + radius * math.cos(angle),
                center.y() + radius * math.sin(angle)
            )
            painter.drawLine(center, end_point)
            
            # Draw metric label
            label_distance = radius + 25
            label_point = QPointF(
                center.x() + label_distance * math.cos(angle),
                center.y() + label_distance * math.sin(angle)
            )
            
            painter.setPen(QPen(text_color, 1))
            text_rect = painter.fontMetrics().boundingRect(metric["name"])
            painter.drawText(
                int(label_point.x() - text_rect.width() / 2),
                int(label_point.y() + text_rect.height() / 2),
                metric["name"]
            )
        
        # Draw ship data polygons
        ship_colors = [
            QColor(255, 100, 100, 100),  # Red
            QColor(100, 255, 100, 100),  # Green
            QColor(100, 100, 255, 100),  # Blue
            QColor(255, 255, 100, 100)   # Yellow
        ]
        
        ship_line_colors = [
            QColor(255, 100, 100),
            QColor(100, 255, 100),
            QColor(100, 100, 255),
            QColor(255, 255, 100)
        ]
        
        for ship_idx, ship in enumerate(self.ships):
            if ship_idx >= len(ship_colors):
                break
            
            # Calculate ship data points
            points = []
            for i, metric in enumerate(self.metrics):
                angle = i * angle_step - math.pi / 2
                
                value = self.get_ship_metric_value(ship, metric["key"])
                max_value = self.max_values.get(metric["key"], 1)
                normalized_value = min(1.0, value / max_value) if max_value > 0 else 0
                
                point_distance = radius * normalized_value
                point = QPointF(
                    center.x() + point_distance * math.cos(angle),
                    center.y() + point_distance * math.sin(angle)
                )
                points.append(point)
            
            # Draw filled polygon
            if points:
                polygon = QPolygonF(points)
                painter.setPen(QPen(ship_line_colors[ship_idx], 2))
                painter.setBrush(QBrush(ship_colors[ship_idx]))
                painter.drawPolygon(polygon)
                
                # Draw data points
                for point in points:
                    painter.setBrush(QBrush(ship_line_colors[ship_idx]))
                    painter.drawEllipse(point, 3, 3)
        
        # Draw legend
        self.draw_legend(painter, text_color, ship_line_colors)
    
    def draw_legend(self, painter: QPainter, text_color: QColor, ship_colors: List[QColor]):
        """Draw chart legend"""
        if not self.ships:
            return
        
        painter.setPen(QPen(text_color, 1))
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        
        legend_x = 10
        legend_y = 20
        
        for i, ship in enumerate(self.ships):
            if i >= len(ship_colors):
                break
            
            # Color indicator
            painter.setBrush(QBrush(ship_colors[i]))
            painter.drawRect(legend_x, legend_y + (i * 20), 15, 10)
            
            # Ship name
            painter.drawText(legend_x + 20, legend_y + (i * 20) + 8, ship.display_name)


class ComparisonTable(QTableWidget, ThemeAwareWidget):
    """Detailed comparison table for ship specifications"""
    
    def __init__(self, parent=None):
        QTableWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.ships = []
        self._current_theme = None
        
        self.setup_table()
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def setup_table(self):
        """Setup table structure"""
        # Table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(True)
        
        # Comparison categories
        self.categories = [
            ("Basic Information", [
                ("Name", lambda s: s.display_name),
                ("Manufacturer", lambda s: s.manufacturer.value),
                ("Class", lambda s: s.ship_class.value),
                ("Role", lambda s: s.primary_role.value),
                ("Crew", lambda s: str(s.crew_seats)),
                ("Base Cost", lambda s: f"{s.base_cost:,} CR"),
            ]),
            ("Physical", [
                ("Length", lambda s: f"{s.dimensions.length:.1f} m"),
                ("Width", lambda s: f"{s.dimensions.width:.1f} m"),
                ("Height", lambda s: f"{s.dimensions.height:.1f} m"),
                ("Mass", lambda s: f"{s.performance.hull_mass:.0f} t"),
            ]),
            ("Performance", [
                ("Max Speed", lambda s: f"{s.performance.max_speed} m/s"),
                ("Boost Speed", lambda s: f"{s.performance.boost_speed} m/s"),
                ("Base Jump Range", lambda s: f"{s.performance.base_jump_range:.2f} ly"),
                ("Max Jump Range", lambda s: f"{s.performance.max_jump_range:.2f} ly"),
                ("Power Plant", lambda s: f"{s.performance.power_plant_capacity} MW"),
                ("Fuel Capacity", lambda s: f"{s.performance.fuel_capacity} t"),
            ]),
            ("Combat", [
                ("Base Shields", lambda s: f"{s.performance.base_shield_strength} MJ"),
                ("Hull Integrity", lambda s: str(s.performance.hull_integrity)),
                ("Large Hardpoints", lambda s: str(s.hardpoints.large)),
                ("Medium Hardpoints", lambda s: str(s.hardpoints.medium)),
                ("Small Hardpoints", lambda s: str(s.hardpoints.small)),
                ("Utility Mounts", lambda s: str(s.hardpoints.utility)),
                ("Firepower Rating", lambda s: str(s.firepower_rating)),
            ]),
            ("Internal", [
                ("Max Cargo", lambda s: f"{s.internal_slots.max_cargo_capacity} t"),
                ("Total Slots", lambda s: str(s.internal_slots.total_slots)),
                ("Class 8 Slots", lambda s: str(s.internal_slots.class_8)),
                ("Class 7 Slots", lambda s: str(s.internal_slots.class_7)),
                ("Class 6 Slots", lambda s: str(s.internal_slots.class_6)),
                ("Class 5 Slots", lambda s: str(s.internal_slots.class_5)),
            ]),
            ("Ratings", [
                ("Cargo Rating", lambda s: s.cargo_rating),
                ("Exploration Rating", lambda s: s.exploration_rating),
                ("Cost per Ton", lambda s: f"{s.cost_per_ton:,.0f} CR/t"),
            ])
        ]
    
    def set_ships(self, ships: List[ShipSpecification]):
        """Set ships to compare"""
        self.ships = ships
        self.populate_table()
    
    def populate_table(self):
        """Populate table with ship data"""
        if not self.ships:
            return
        
        # Calculate total rows
        total_rows = sum(len(category[1]) for category in self.categories) + len(self.categories)
        
        # Setup table dimensions
        self.setRowCount(total_rows)
        self.setColumnCount(len(self.ships) + 1)  # +1 for specification column
        
        # Setup headers
        headers = ["Specification"] + [ship.display_name for ship in self.ships]
        self.setHorizontalHeaderLabels(headers)
        
        # Populate data
        current_row = 0
        
        for category_name, specs in self.categories:
            # Category header
            category_item = QTableWidgetItem(category_name)
            category_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.setItem(current_row, 0, category_item)
            
            # Empty cells for category row
            for col in range(1, len(self.ships) + 1):
                self.setItem(current_row, col, QTableWidgetItem(""))
            
            current_row += 1
            
            # Specification rows
            for spec_name, spec_func in specs:
                # Specification name
                spec_item = QTableWidgetItem(f"  {spec_name}")
                self.setItem(current_row, 0, spec_item)
                
                # Ship values
                for col, ship in enumerate(self.ships):
                    try:
                        value = spec_func(ship)
                        value_item = QTableWidgetItem(str(value))
                        value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.setItem(current_row, col + 1, value_item)
                    except:
                        self.setItem(current_row, col + 1, QTableWidgetItem("N/A"))
                
                current_row += 1
        
        # Resize columns
        self.resizeColumnsToContents()
        
        # Highlight best/worst values
        self.highlight_comparative_values()
    
    def highlight_comparative_values(self):
        """Highlight best and worst values for numeric comparisons"""
        if not self.ships:
            return
        
        # Define numeric comparisons (higher is better)
        numeric_better_higher = [
            "Max Speed", "Boost Speed", "Base Jump Range", "Max Jump Range",
            "Base Shields", "Hull Integrity", "Max Cargo", "Total Slots",
            "Firepower Rating", "Power Plant", "Fuel Capacity"
        ]
        
        # Define numeric comparisons (lower is better)
        numeric_better_lower = [
            "Base Cost", "Mass", "Cost per Ton"
        ]
        
        for row in range(self.rowCount()):
            spec_item = self.item(row, 0)
            if not spec_item:
                continue
            
            spec_name = spec_item.text().strip()
            
            # Check if this is a numeric comparison
            is_higher_better = any(name in spec_name for name in numeric_better_higher)
            is_lower_better = any(name in spec_name for name in numeric_better_lower)
            
            if not (is_higher_better or is_lower_better):
                continue
            
            # Extract numeric values
            values = []
            items = []
            
            for col in range(1, self.columnCount()):
                item = self.item(row, col)
                if item:
                    try:
                        # Extract numeric value from text
                        text = item.text().replace(",", "").replace("CR", "").replace("t", "").replace("m/s", "").replace("ly", "").replace("MJ", "").replace("MW", "").replace("m", "").strip()
                        
                        # Handle ranges (take first number)
                        if " - " in text:
                            text = text.split(" - ")[0]
                        
                        value = float(text)
                        values.append((value, item))
                        items.append(item)
                    except:
                        continue
            
            if len(values) < 2:
                continue
            
            # Find best and worst
            if is_higher_better:
                best_value = max(values, key=lambda x: x[0])
                worst_value = min(values, key=lambda x: x[0])
            else:
                best_value = min(values, key=lambda x: x[0])
                worst_value = max(values, key=lambda x: x[0])
            
            # Apply highlighting
            if self._current_theme:
                best_color = QColor(self._current_theme.accent)
                worst_color = QColor(self._current_theme.error)
            else:
                best_color = QColor(100, 255, 100)
                worst_color = QColor(255, 100, 100)
            
            best_value[1].setBackground(best_color)
            worst_value[1].setBackground(worst_color)
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme to table"""
        self._current_theme = theme
        
        colors = theme.to_dict()
        table_stylesheet = f"""
        QTableWidget {{
            background-color: {colors['surface']};
            alternate-background-color: {colors['background']};
            color: {colors['text']};
            gridline-color: {colors['border']};
            selection-background-color: {colors['primary']};
        }}
        QHeaderView::section {{
            background-color: {colors['primary']};
            color: {colors['background']};
            padding: 5px;
            border: 1px solid {colors['border']};
            font-weight: bold;
        }}
        """
        self.setStyleSheet(table_stylesheet)


class ShipComparisonDialog(QDialog, ThemeAwareWidget):
    """Dialog for ship-to-ship comparison"""
    
    def __init__(self, initial_ships: List[ShipSpecification] = None, parent=None):
        QDialog.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.ship_database = get_ship_database()
        self.selected_ships = initial_ships[:4] if initial_ships else []
        self._current_theme = None
        
        self.setup_ui()
        self.populate_ship_selectors()
        
        if self.selected_ships:
            self.update_comparison()
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def setup_ui(self):
        """Setup comparison dialog UI"""
        self.setWindowTitle("Ship Comparison Analysis")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        # Ship selection panel
        selection_panel = ElitePanel("SELECT SHIPS TO COMPARE")
        selection_layout = QHBoxLayout()
        
        self.ship_selectors = []
        for i in range(4):
            selector_layout = QVBoxLayout()
            
            label = EliteLabel(f"Ship {i+1}:", "small")
            selector_layout.addWidget(label)
            
            selector = QComboBox()
            selector.currentTextChanged.connect(self.on_ship_selection_changed)
            self.ship_selectors.append(selector)
            selector_layout.addWidget(selector)
            
            selection_layout.addLayout(selector_layout)
        
        # Clear and compare buttons
        button_layout = QVBoxLayout()
        
        clear_btn = EliteButton("CLEAR ALL")
        clear_btn.clicked.connect(self.clear_selection)
        button_layout.addWidget(clear_btn)
        
        compare_btn = EliteButton("COMPARE")
        compare_btn.clicked.connect(self.update_comparison)
        button_layout.addWidget(compare_btn)
        
        button_layout.addStretch()
        
        selection_layout.addLayout(button_layout)
        selection_panel.add_layout(selection_layout)
        layout.addWidget(selection_panel)
        
        # Comparison tabs
        self.tabs = QTabWidget()
        
        # Radar chart tab
        radar_widget = QWidget()
        radar_layout = QVBoxLayout(radar_widget)
        
        self.radar_chart = RadarChart()
        radar_layout.addWidget(self.radar_chart)
        
        self.tabs.addTab(radar_widget, "PERFORMANCE RADAR")
        
        # Table comparison tab
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        self.comparison_table = ComparisonTable()
        table_layout.addWidget(self.comparison_table)
        
        self.tabs.addTab(table_widget, "DETAILED COMPARISON")
        
        layout.addWidget(self.tabs)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def populate_ship_selectors(self):
        """Populate ship selection dropdowns"""
        ships = self.ship_database.get_all_ships()
        
        for selector in self.ship_selectors:
            selector.clear()
            selector.addItem("-- Select Ship --")
            
            for ship in ships:
                selector.addItem(ship.display_name, ship.name)
        
        # Set initial selections if provided
        for i, ship in enumerate(self.selected_ships):
            if i < len(self.ship_selectors):
                index = self.ship_selectors[i].findData(ship.name)
                if index >= 0:
                    self.ship_selectors[i].setCurrentIndex(index)
    
    def on_ship_selection_changed(self):
        """Handle ship selection change"""
        self.selected_ships = []
        
        for selector in self.ship_selectors:
            ship_key = selector.currentData()
            if ship_key:
                ship = self.ship_database.get_ship(ship_key)
                if ship:
                    self.selected_ships.append(ship)
    
    def clear_selection(self):
        """Clear all ship selections"""
        for selector in self.ship_selectors:
            selector.setCurrentIndex(0)
        
        self.selected_ships = []
        self.radar_chart.set_ships([])
        self.comparison_table.set_ships([])
    
    def update_comparison(self):
        """Update comparison displays"""
        self.on_ship_selection_changed()
        
        if self.selected_ships:
            self.radar_chart.set_ships(self.selected_ships)
            self.comparison_table.set_ships(self.selected_ships)
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme to dialog"""
        self._current_theme = theme
        
        # Apply theme to tabs
        colors = theme.to_dict()
        tab_stylesheet = f"""
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['surface']};
        }}
        QTabBar::tab {{
            background-color: {colors['background']};
            color: {colors['text']};
            padding: 8px 16px;
            margin: 2px;
            border: 1px solid {colors['border']};
        }}
        QTabBar::tab:selected {{
            background-color: {colors['primary']};
            color: {colors['background']};
            border-color: {colors['primary']};
        }}
        QTabBar::tab:hover {{
            background-color: {colors['accent']};
            color: {colors['background']};
        }}
        """
        self.tabs.setStyleSheet(tab_stylesheet)


def show_ship_comparison(ships: List[ShipSpecification] = None, parent=None) -> ShipComparisonDialog:
    """Show ship comparison dialog"""
    dialog = ShipComparisonDialog(ships, parent)
    dialog.exec()
    return dialog


# Export main classes
__all__ = ['RadarChart', 'ComparisonTable', 'ShipComparisonDialog', 'show_ship_comparison']