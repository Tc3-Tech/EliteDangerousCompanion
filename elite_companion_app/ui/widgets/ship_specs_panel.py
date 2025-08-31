"""
Elite Dangerous Ship Specifications Panel
Comprehensive technical readout display with Elite aesthetic and advanced data visualization.
"""
import sys
import os
import math
import time
from typing import Optional, Dict, List, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                           QTabWidget, QScrollArea, QFrame, QLabel, QPushButton,
                           QProgressBar, QSizePolicy, QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import (QPainter, QPen, QBrush, QLinearGradient, QFont, 
                       QFontMetrics, QColor, QPainterPath, QRadialGradient)

# Add app root to path for imports
from pathlib import Path
app_root = Path(__file__).parent.parent.parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

from data.ship_database import ShipSpecification, ShipClass, ShipRole, Manufacturer
from ui.elite_widgets import (ElitePanel, EliteLabel, EliteButton, EliteProgressBar,
                          ThemeAwareWidget, get_global_theme_manager)
from config.themes import ThemeColors


class AnimatedStatBar(QWidget, ThemeAwareWidget):
    """Animated statistics bar with comparison capability"""
    
    def __init__(self, label: str, value: float, max_value: float = 100.0, 
                 unit: str = "", format_str: str = "{:.1f}", parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.label_text = label
        self.current_value = 0.0
        self.target_value = value
        self.max_value = max_value
        self.unit = unit
        self.format_str = format_str
        self._current_theme = None
        
        self.setFixedHeight(25)
        self.setMinimumWidth(200)
        
        # Animation properties
        self.animation_progress = 0.0
        self.animation_speed = 0.05
        
        # Start animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(16)  # 60 FPS
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def set_value(self, value: float, animate: bool = True):
        """Set new target value with optional animation"""
        if animate:
            self.target_value = value
            self.animation_progress = 0.0
            if not self.animation_timer.isActive():
                self.animation_timer.start(16)
        else:
            self.current_value = value
            self.target_value = value
            self.animation_timer.stop()
        
        self.update()
    
    def update_animation(self):
        """Update animation progress"""
        if self.current_value != self.target_value:
            diff = self.target_value - self.current_value
            self.current_value += diff * self.animation_speed
            
            if abs(diff) < 0.01:
                self.current_value = self.target_value
                self.animation_timer.stop()
            
            self.update()
        else:
            self.animation_timer.stop()
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme colors"""
        self._current_theme = theme
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for animated stat bar"""
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
        
        # Bar background
        bar_rect = QRect(80, 2, self.width() - 160, 16)
        painter.fillRect(bar_rect, surface_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRect(bar_rect)
        
        # Animated fill
        fill_ratio = min(1.0, self.current_value / self.max_value) if self.max_value > 0 else 0
        fill_width = int(bar_rect.width() * fill_ratio)
        
        if fill_width > 0:
            fill_rect = QRect(bar_rect.x(), bar_rect.y(), fill_width, bar_rect.height())
            
            # Gradient fill
            gradient = QLinearGradient(float(fill_rect.left()), float(fill_rect.top()), 
                                     float(fill_rect.right()), float(fill_rect.top()))
            gradient.setColorAt(0.0, primary_color)
            gradient.setColorAt(1.0, accent_color)
            
            painter.fillRect(fill_rect, gradient)
        
        # Label
        painter.setPen(QPen(text_color, 1))
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(5, 14, self.label_text)
        
        # Value
        value_text = self.format_str.format(self.current_value) + self.unit
        value_x = self.width() - 80
        painter.drawText(value_x, 14, value_text)
        
        # Max indicator line
        if self.max_value > 0:
            max_x = bar_rect.x() + bar_rect.width()
            painter.setPen(QPen(accent_color, 2))
            painter.drawLine(max_x, bar_rect.y() - 2, max_x, bar_rect.bottom() + 2)


class ShipStatsCard(ElitePanel):
    """Card displaying ship statistics with visual indicators"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.stats = {}
        self.stat_bars = {}
        self.setup_stats_ui()
    
    def setup_stats_ui(self):
        """Setup statistics display UI"""
        self.stats_layout = QVBoxLayout()
        self.add_layout(self.stats_layout)
    
    def add_stat(self, key: str, label: str, value: float, max_value: float = 100.0, 
                unit: str = "", format_str: str = "{:.1f}"):
        """Add a statistic with animated bar"""
        stat_bar = AnimatedStatBar(label, value, max_value, unit, format_str)
        self.stat_bars[key] = stat_bar
        self.stats[key] = value
        self.stats_layout.addWidget(stat_bar)
    
    def update_stat(self, key: str, value: float, animate: bool = True):
        """Update a statistic value"""
        if key in self.stat_bars:
            self.stat_bars[key].set_value(value, animate)
            self.stats[key] = value
    
    def get_stat(self, key: str) -> float:
        """Get current statistic value"""
        return self.stats.get(key, 0.0)
    
    def clear_stats(self):
        """Clear all statistics"""
        for bar in self.stat_bars.values():
            bar.deleteLater()
        self.stat_bars.clear()
        self.stats.clear()


class HardpointDisplay(QWidget, ThemeAwareWidget):
    """Visual display of ship hardpoints"""
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.hardpoints = None
        self._current_theme = None
        self.setFixedHeight(120)
        self.setMinimumWidth(300)
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def set_hardpoints(self, hardpoints):
        """Set hardpoint data"""
        self.hardpoints = hardpoints
        self.update()
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme colors"""
        self._current_theme = theme
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for hardpoint display"""
        if not self.hardpoints:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get theme colors
        if self._current_theme:
            primary_color = QColor(self._current_theme.primary)
            accent_color = QColor(self._current_theme.accent)
            text_color = QColor(self._current_theme.text)
            surface_color = QColor(self._current_theme.surface)
        else:
            palette = self.palette()
            primary_color = palette.highlight().color()
            accent_color = palette.highlightedText().color()
            text_color = palette.text().color()
            surface_color = palette.base().color()
        
        # Ship outline (simplified)
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        painter.setPen(QPen(surface_color, 2))
        painter.drawEllipse(center_x - 40, center_y - 20, 80, 40)
        
        # Draw hardpoints
        hardpoint_positions = []
        
        # Large hardpoints (red)
        for i in range(self.hardpoints.large):
            angle = i * math.pi / max(1, self.hardpoints.large - 1) - math.pi / 2
            x = center_x + 50 * math.cos(angle)
            y = center_y + 25 * math.sin(angle)
            
            painter.setPen(QPen(QColor(255, 100, 100), 3))
            painter.setBrush(QBrush(QColor(255, 100, 100, 100)))
            painter.drawEllipse(int(x - 8), int(y - 8), 16, 16)
            
            painter.setPen(QPen(text_color, 1))
            font = QFont("Arial", 8, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(int(x - 5), int(y + 3), "L")
        
        # Medium hardpoints (yellow)
        for i in range(self.hardpoints.medium):
            angle = i * math.pi / max(1, self.hardpoints.medium - 1) + math.pi / 4
            x = center_x + 35 * math.cos(angle)
            y = center_y + 35 * math.sin(angle)
            
            painter.setPen(QPen(QColor(255, 255, 100), 2))
            painter.setBrush(QBrush(QColor(255, 255, 100, 100)))
            painter.drawEllipse(int(x - 6), int(y - 6), 12, 12)
            
            painter.setPen(QPen(text_color, 1))
            font = QFont("Arial", 7, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(int(x - 3), int(y + 2), "M")
        
        # Small hardpoints (cyan)
        for i in range(self.hardpoints.small):
            angle = i * math.pi / max(1, self.hardpoints.small - 1) + 3 * math.pi / 4
            x = center_x + 30 * math.cos(angle)
            y = center_y + 30 * math.sin(angle)
            
            painter.setPen(QPen(primary_color, 2))
            painter.setBrush(QBrush(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 100)))
            painter.drawEllipse(int(x - 4), int(y - 4), 8, 8)
            
            painter.setPen(QPen(text_color, 1))
            font = QFont("Arial", 6, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(int(x - 2), int(y + 2), "S")
        
        # Legend
        legend_y = 10
        
        # Large hardpoints legend
        painter.setPen(QPen(QColor(255, 100, 100), 2))
        painter.setBrush(QBrush(QColor(255, 100, 100)))
        painter.drawEllipse(10, legend_y, 8, 8)
        painter.setPen(QPen(text_color, 1))
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.drawText(25, legend_y + 6, f"Large: {self.hardpoints.large}")
        
        # Medium hardpoints legend
        painter.setPen(QPen(QColor(255, 255, 100), 2))
        painter.setBrush(QBrush(QColor(255, 255, 100)))
        painter.drawEllipse(10, legend_y + 20, 6, 6)
        painter.setPen(QPen(text_color, 1))
        painter.drawText(25, legend_y + 26, f"Medium: {self.hardpoints.medium}")
        
        # Small hardpoints legend
        painter.setPen(QPen(primary_color, 2))
        painter.setBrush(QBrush(primary_color))
        painter.drawEllipse(10, legend_y + 40, 4, 4)
        painter.setPen(QPen(text_color, 1))
        painter.drawText(25, legend_y + 46, f"Small: {self.hardpoints.small}")
        
        # Utility mounts
        painter.setPen(QPen(accent_color, 1))
        painter.drawText(25, legend_y + 66, f"Utility: {self.hardpoints.utility}")


class InternalSlotsDisplay(QWidget, ThemeAwareWidget):
    """Visual display of internal compartments"""
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.internal_slots = None
        self._current_theme = None
        self.setFixedHeight(150)
        self.setMinimumWidth(300)
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def set_internal_slots(self, internal_slots):
        """Set internal slots data"""
        self.internal_slots = internal_slots
        self.update()
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme colors"""
        self._current_theme = theme
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for internal slots display"""
        if not self.internal_slots:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get theme colors
        if self._current_theme:
            primary_color = QColor(self._current_theme.primary)
            accent_color = QColor(self._current_theme.accent)
            text_color = QColor(self._current_theme.text)
            surface_color = QColor(self._current_theme.surface)
        else:
            palette = self.palette()
            primary_color = palette.highlight().color()
            accent_color = palette.highlightedText().color()
            text_color = palette.text().color()
            surface_color = palette.base().color()
        
        # Draw slot grid
        slot_size = 20
        start_x = 20
        start_y = 20
        
        slots_data = [
            ("8", self.internal_slots.class_8, QColor(255, 0, 0)),      # Red for Class 8
            ("7", self.internal_slots.class_7, QColor(255, 100, 0)),   # Orange for Class 7
            ("6", self.internal_slots.class_6, QColor(255, 200, 0)),   # Yellow for Class 6
            ("5", self.internal_slots.class_5, QColor(100, 255, 0)),   # Light Green for Class 5
            ("4", self.internal_slots.class_4, QColor(0, 255, 100)),   # Green for Class 4
            ("3", self.internal_slots.class_3, QColor(0, 200, 255)),   # Light Blue for Class 3
            ("2", self.internal_slots.class_2, QColor(0, 100, 255)),   # Blue for Class 2
            ("1", self.internal_slots.class_1, QColor(100, 0, 255)),   # Purple for Class 1
        ]
        
        current_x = start_x
        current_y = start_y
        
        for class_name, count, color in slots_data:
            if count > 0:
                # Draw class label
                painter.setPen(QPen(text_color, 1))
                font = QFont("Arial", 10, QFont.Weight.Bold)
                painter.setFont(font)
                painter.drawText(current_x, current_y - 5, f"Class {class_name}:")
                
                # Draw slots
                for i in range(count):
                    slot_x = current_x + (i * (slot_size + 5))
                    slot_y = current_y
                    
                    # Slot rectangle
                    painter.setPen(QPen(color, 2))
                    painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 50)))
                    painter.drawRect(slot_x, slot_y, slot_size, slot_size)
                    
                    # Class number in slot
                    painter.setPen(QPen(text_color, 1))
                    font = QFont("Arial", 8, QFont.Weight.Bold)
                    painter.setFont(font)
                    text_rect = QRect(slot_x, slot_y, slot_size, slot_size)
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, class_name)
                
                current_y += 30
                
                # Wrap to new column if needed
                if current_y > self.height() - 40:
                    current_x += 150
                    current_y = start_y
        
        # Total slots indicator
        total_slots = self.internal_slots.total_slots
        painter.setPen(QPen(accent_color, 1))
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.width() - 150, self.height() - 20, f"Total Slots: {total_slots}")


class ShipSpecificationPanel(QWidget, ThemeAwareWidget):
    """Main ship specifications panel with tabbed interface"""
    
    comparison_requested = pyqtSignal(str)  # Request ship comparison
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.current_ship = None
        self._current_theme = None
        
        self.setup_ui()
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def setup_ui(self):
        """Setup main specification UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with ship name and controls
        self.setup_header(layout)
        
        # Tabbed interface
        self.tabs = QTabWidget()
        
        # Overview tab
        self.overview_tab = self.create_overview_tab()
        self.tabs.addTab(self.overview_tab, "OVERVIEW")
        
        # Performance tab
        self.performance_tab = self.create_performance_tab()
        self.tabs.addTab(self.performance_tab, "PERFORMANCE")
        
        # Combat tab
        self.combat_tab = self.create_combat_tab()
        self.tabs.addTab(self.combat_tab, "COMBAT")
        
        # Internals tab
        self.internals_tab = self.create_internals_tab()
        self.tabs.addTab(self.internals_tab, "INTERNALS")
        
        # Economics tab
        self.economics_tab = self.create_economics_tab()
        self.tabs.addTab(self.economics_tab, "ECONOMICS")
        
        layout.addWidget(self.tabs)
    
    def setup_header(self, parent_layout):
        """Setup header section"""
        header_layout = QHBoxLayout()
        
        # Ship name and basic info
        self.ship_name_label = EliteLabel("No Ship Selected", "header")
        header_layout.addWidget(self.ship_name_label)
        
        header_layout.addStretch()
        
        # Compare button
        self.compare_btn = EliteButton("COMPARE")
        self.compare_btn.clicked.connect(self.request_comparison)
        self.compare_btn.setEnabled(False)
        header_layout.addWidget(self.compare_btn)
        
        parent_layout.addLayout(header_layout)
    
    def create_overview_tab(self) -> QWidget:
        """Create overview tab with basic ship information"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Basic info card
        self.basic_info_card = ShipStatsCard("BASIC INFORMATION")
        layout.addWidget(self.basic_info_card)
        
        # Physical dimensions
        self.dimensions_card = ShipStatsCard("PHYSICAL DIMENSIONS")
        layout.addWidget(self.dimensions_card)
        
        # Ship description
        self.description_panel = ElitePanel("DESCRIPTION")
        self.description_label = EliteLabel("", "small")
        self.description_label.setWordWrap(True)
        self.description_panel.add_widget(self.description_label)
        layout.addWidget(self.description_panel)
        
        layout.addStretch()
        return tab
    
    def create_performance_tab(self) -> QWidget:
        """Create performance tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Speed and maneuverability
        self.speed_card = ShipStatsCard("SPEED & MANEUVERABILITY")
        layout.addWidget(self.speed_card)
        
        # Jump capabilities
        self.jump_card = ShipStatsCard("JUMP CAPABILITIES")
        layout.addWidget(self.jump_card)
        
        # Power and fuel
        self.power_card = ShipStatsCard("POWER & FUEL")
        layout.addWidget(self.power_card)
        
        layout.addStretch()
        return tab
    
    def create_combat_tab(self) -> QWidget:
        """Create combat capabilities tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Combat stats
        self.combat_stats_card = ShipStatsCard("COMBAT STATISTICS")
        layout.addWidget(self.combat_stats_card)
        
        # Hardpoints visualization
        hardpoints_panel = ElitePanel("HARDPOINT LAYOUT")
        self.hardpoints_display = HardpointDisplay()
        hardpoints_panel.add_widget(self.hardpoints_display)
        layout.addWidget(hardpoints_panel)
        
        layout.addStretch()
        return tab
    
    def create_internals_tab(self) -> QWidget:
        """Create internal compartments tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Cargo and storage
        self.storage_card = ShipStatsCard("CARGO & STORAGE")
        layout.addWidget(self.storage_card)
        
        # Internal slots visualization
        slots_panel = ElitePanel("INTERNAL COMPARTMENTS")
        self.slots_display = InternalSlotsDisplay()
        slots_panel.add_widget(self.slots_display)
        layout.addWidget(slots_panel)
        
        layout.addStretch()
        return tab
    
    def create_economics_tab(self) -> QWidget:
        """Create economics and value tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Cost analysis
        self.cost_card = ShipStatsCard("COST ANALYSIS")
        layout.addWidget(self.cost_card)
        
        # Value metrics
        self.value_card = ShipStatsCard("VALUE METRICS")
        layout.addWidget(self.value_card)
        
        layout.addStretch()
        return tab
    
    def set_ship(self, ship_spec: ShipSpecification):
        """Set ship to display"""
        self.current_ship = ship_spec
        self.update_all_displays()
        self.compare_btn.setEnabled(True)
    
    def update_all_displays(self):
        """Update all display panels with current ship data"""
        if not self.current_ship:
            return
        
        ship = self.current_ship
        
        # Update header
        self.ship_name_label.setText(ship.display_name.upper())
        
        # Update basic info
        self.basic_info_card.clear_stats()
        self.basic_info_card.add_stat("manufacturer", "MANUFACTURER", 0, 1, "", "{}")
        self.basic_info_card.add_stat("class", "CLASS", 0, 1, "", "{}")
        self.basic_info_card.add_stat("role", "PRIMARY ROLE", 0, 1, "", "{}")
        self.basic_info_card.add_stat("crew", "CREW CAPACITY", ship.crew_seats, 10, " seats")
        
        # Since these are text fields, we'll handle them specially
        self.basic_info_card.stat_bars["manufacturer"].label_text = f"MANUFACTURER: {ship.manufacturer.value}"
        self.basic_info_card.stat_bars["class"].label_text = f"CLASS: {ship.ship_class.value}"
        self.basic_info_card.stat_bars["role"].label_text = f"PRIMARY ROLE: {ship.primary_role.value}"
        
        # Update dimensions
        self.dimensions_card.clear_stats()
        self.dimensions_card.add_stat("length", "LENGTH", ship.dimensions.length, 200, " m")
        self.dimensions_card.add_stat("width", "WIDTH", ship.dimensions.width, 200, " m")
        self.dimensions_card.add_stat("height", "HEIGHT", ship.dimensions.height, 50, " m")
        self.dimensions_card.add_stat("mass", "HULL MASS", ship.performance.hull_mass, 1200, " t")
        
        # Update description
        description = ship.description or "No description available."
        manufacturer_desc = ship.manufacturer_description or ""
        full_description = f"{description}\n\n{manufacturer_desc}".strip()
        self.description_label.setText(full_description)
        
        # Update performance
        self.speed_card.clear_stats()
        self.speed_card.add_stat("max_speed", "MAX SPEED", ship.performance.max_speed, 400, " m/s")
        self.speed_card.add_stat("boost_speed", "BOOST SPEED", ship.performance.boost_speed, 500, " m/s")
        
        self.jump_card.clear_stats()
        self.jump_card.add_stat("base_jump", "BASE JUMP RANGE", ship.performance.base_jump_range, 15, " ly", "{:.2f}")
        self.jump_card.add_stat("max_jump", "MAX JUMP RANGE", ship.performance.max_jump_range, 80, " ly", "{:.2f}")
        
        self.power_card.clear_stats()
        self.power_card.add_stat("power", "POWER PLANT", ship.performance.power_plant_capacity, 10, " MW")
        self.power_card.add_stat("fuel", "FUEL CAPACITY", ship.performance.fuel_capacity, 50, " t")
        
        # Update combat
        self.combat_stats_card.clear_stats()
        self.combat_stats_card.add_stat("shields", "BASE SHIELDS", ship.performance.base_shield_strength, 600, " MJ")
        self.combat_stats_card.add_stat("hull", "HULL INTEGRITY", ship.performance.hull_integrity, 1500)
        self.combat_stats_card.add_stat("firepower", "FIREPOWER RATING", ship.firepower_rating, 20)
        
        # Update hardpoints display
        self.hardpoints_display.set_hardpoints(ship.hardpoints)
        
        # Update internals
        self.storage_card.clear_stats()
        max_cargo = ship.internal_slots.max_cargo_capacity
        self.storage_card.add_stat("cargo", "MAX CARGO", max_cargo, 800, " t")
        self.storage_card.add_stat("slots", "TOTAL SLOTS", ship.internal_slots.total_slots, 20)
        
        # Update internal slots display
        self.slots_display.set_internal_slots(ship.internal_slots)
        
        # Update economics
        self.cost_card.clear_stats()
        self.cost_card.add_stat("base_cost", "BASE COST", ship.base_cost / 1000000, 250, " M CR", "{:.1f}")
        self.cost_card.add_stat("insurance", "INSURANCE", ship.insurance_cost / 1000000, 15, " M CR", "{:.1f}")
        
        self.value_card.clear_stats()
        cost_per_ton = ship.cost_per_ton
        self.value_card.add_stat("cost_per_ton", "COST/TON", cost_per_ton / 1000, 1000, " K CR/t", "{:.0f}")
        
        # Rating calculations
        cargo_rating = {"Minimal": 1, "Limited": 2, "Fair": 3, "Good": 4, "Very Good": 5, "Excellent": 6}
        exploration_rating = {"Limited": 1, "Fair": 2, "Good": 3, "Very Good": 4, "Excellent": 5, "Exceptional": 6}
        
        cargo_score = cargo_rating.get(ship.cargo_rating, 1)
        exploration_score = exploration_rating.get(ship.exploration_rating, 1)
        
        self.value_card.add_stat("cargo_rating", "CARGO RATING", cargo_score, 6, "", "{:.0f}")
        self.value_card.add_stat("exploration_rating", "EXPLORATION RATING", exploration_score, 6, "", "{:.0f}")
    
    def request_comparison(self):
        """Request ship comparison"""
        if self.current_ship:
            self.comparison_requested.emit(self.current_ship.name)
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme to panel"""
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


# Export main classes
__all__ = ['AnimatedStatBar', 'ShipStatsCard', 'HardpointDisplay', 
           'InternalSlotsDisplay', 'ShipSpecificationPanel']