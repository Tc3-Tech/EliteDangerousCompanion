"""
Elite Dangerous Ship Gallery Widget
Interactive carousel/gallery for browsing ship collection with Elite aesthetic.
"""
import sys
import os
import math
import time
from typing import List, Optional, Dict, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QScrollArea, QFrame, QGridLayout,
                           QButtonGroup, QSizePolicy)
from PyQt6.QtCore import (Qt, QTimer, pyqtSignal, QPropertyAnimation, 
                        QEasingCurve, QRect, QSize, QPoint, QParallelAnimationGroup,
                        QSequentialAnimationGroup)
from PyQt6.QtGui import (QPainter, QPen, QBrush, QLinearGradient, QPixmap, 
                       QTransform, QFont, QFontMetrics, QIcon, QPalette, QColor)

# Add app root to path for imports
from pathlib import Path
app_root = Path(__file__).parent.parent.parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

from data.ship_database import get_ship_database, ShipSpecification, ShipClass, ShipRole
from ui.elite_widgets import (ElitePanel, EliteLabel, EliteButton, ThemeAwareWidget, 
                          get_global_theme_manager)
from config.themes import ThemeColors


class ShipThumbnail(QWidget, ThemeAwareWidget):
    """Individual ship thumbnail with hover effects and selection state"""
    
    clicked = pyqtSignal(str)  # Emits ship key when clicked
    hover_changed = pyqtSignal(bool)  # Emits hover state
    
    def __init__(self, ship_spec: ShipSpecification, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.ship_spec = ship_spec
        self.ship_image = None
        self.is_selected = False
        self.is_hovered = False
        self.hover_animation_progress = 0.0
        self._current_theme = None
        
        self.setFixedSize(120, 90)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Load ship image
        self.load_ship_image()
        
        # Hover animation
        self.hover_timer = QTimer()
        self.hover_timer.timeout.connect(self.update_hover_animation)
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def load_ship_image(self):
        """Load ship image from assets"""
        image_path = self.ship_spec.get_image_path()
        if os.path.exists(image_path):
            self.ship_image = QPixmap(image_path)
            if not self.ship_image.isNull():
                # Scale for thumbnail
                self.ship_image = self.ship_image.scaled(
                    100, 70, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
        self.update()
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme colors"""
        self._current_theme = theme
        self.update()
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        self.update()
    
    def enterEvent(self, event):
        """Mouse enter event"""
        self.is_hovered = True
        self.hover_changed.emit(True)
        self.start_hover_animation(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse leave event"""
        self.is_hovered = False
        self.hover_changed.emit(False)
        self.start_hover_animation(False)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Mouse press event"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.ship_spec.name)
        super().mousePressEvent(event)
    
    def start_hover_animation(self, hover_in: bool):
        """Start hover animation"""
        self.hover_timer.stop()
        self.target_progress = 1.0 if hover_in else 0.0
        self.hover_timer.start(16)  # 60 FPS
    
    def update_hover_animation(self):
        """Update hover animation"""
        step = 0.1
        if self.hover_animation_progress < self.target_progress:
            self.hover_animation_progress = min(1.0, self.hover_animation_progress + step)
        elif self.hover_animation_progress > self.target_progress:
            self.hover_animation_progress = max(0.0, self.hover_animation_progress - step)
        else:
            self.hover_timer.stop()
            return
        
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for thumbnail"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get theme colors
        if self._current_theme:
            primary_color = QColor(self._current_theme.primary)
            accent_color = QColor(self._current_theme.accent)
            surface_color = QColor(self._current_theme.surface)
            text_color = QColor(self._current_theme.text)
            border_color = QColor(self._current_theme.border)
        else:
            palette = self.palette()
            primary_color = palette.highlight().color()
            accent_color = palette.highlightedText().color()
            surface_color = palette.base().color()
            text_color = palette.text().color()
            border_color = palette.mid().color()
        
        # Background with hover effect
        bg_alpha = int(50 + (self.hover_animation_progress * 50))
        if self.is_selected:
            bg_alpha = int(100 + (self.hover_animation_progress * 50))
        
        bg_color = QColor(surface_color)
        bg_color.setAlpha(bg_alpha)
        painter.fillRect(self.rect(), bg_color)
        
        # Border
        border_width = 2 if self.is_selected else 1
        border_pen = QPen(primary_color if self.is_selected else border_color, border_width)
        if self.is_hovered:
            border_pen.setColor(accent_color)
        
        painter.setPen(border_pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        
        # Ship image
        if self.ship_image:
            img_rect = self.ship_image.rect()
            img_rect.moveCenter(QPoint(self.width() // 2, self.height() // 2 - 5))
            
            # Hover scale effect
            if self.hover_animation_progress > 0:
                scale = 1.0 + (self.hover_animation_progress * 0.1)
                transform = QTransform()
                transform.translate(img_rect.center().x(), img_rect.center().y())
                transform.scale(scale, scale)
                transform.translate(-img_rect.center().x(), -img_rect.center().y())
                painter.setTransform(transform)
            
            painter.drawPixmap(img_rect, self.ship_image)
            painter.resetTransform()
        
        # Ship name
        painter.setPen(QPen(text_color, 1))
        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        
        text_rect = QRect(2, self.height() - 18, self.width() - 4, 16)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.ship_spec.display_name)
        
        # Class indicator
        class_text = self.ship_spec.ship_class.value[0]  # First letter
        class_rect = QRect(self.width() - 20, 2, 18, 16)
        
        painter.setPen(QPen(accent_color, 1))
        painter.setBrush(QBrush(accent_color))
        painter.drawRect(class_rect)
        
        painter.setPen(QPen(QColor("black"), 1))
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(class_rect, Qt.AlignmentFlag.AlignCenter, class_text)


class ShipGalleryGrid(QScrollArea, ThemeAwareWidget):
    """Scrollable grid of ship thumbnails"""
    
    ship_selected = pyqtSignal(str)  # Emits selected ship key
    ship_hovered = pyqtSignal(str)   # Emits hovered ship key
    
    def __init__(self, parent=None):
        QScrollArea.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.ship_database = get_ship_database()
        self.thumbnails = {}
        self.current_filter = {}
        self.selected_ship_key = None
        self._current_theme = None
        
        self.setup_ui()
        self.populate_ships()
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def setup_ui(self):
        """Setup scrollable grid UI"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        self.content_widget = QWidget()
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(5)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        self.setWidget(self.content_widget)
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme to scroll area"""
        self._current_theme = theme
        
        # Apply theme to scroll area
        colors = theme.to_dict()
        stylesheet = f"""
        QScrollArea {{
            background-color: {colors['background']};
            border: 1px solid {colors['border']};
        }}
        QScrollBar:vertical {{
            background-color: {colors['surface']};
            width: 15px;
            border-radius: 7px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {colors['primary']};
            border-radius: 7px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['accent']};
        }}
        """
        self.setStyleSheet(stylesheet)
    
    def populate_ships(self):
        """Populate grid with ship thumbnails"""
        # Clear existing thumbnails
        for thumbnail in self.thumbnails.values():
            thumbnail.deleteLater()
        self.thumbnails.clear()
        
        # Get filtered ships
        ships = self.get_filtered_ships()
        
        # Calculate grid dimensions
        columns = max(1, (self.width() - 40) // 130)  # Account for margins and spacing
        
        # Add thumbnails to grid
        for i, ship in enumerate(ships):
            thumbnail = ShipThumbnail(ship, self.content_widget)
            thumbnail.clicked.connect(self.on_ship_clicked)
            thumbnail.hover_changed.connect(lambda hovered, key=ship.name: self.on_ship_hovered(key, hovered))
            
            self.thumbnails[ship.name] = thumbnail
            
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(thumbnail, row, col)
        
        # Add stretch to fill remaining space
        self.grid_layout.setRowStretch(len(ships) // columns + 1, 1)
        self.grid_layout.setColumnStretch(columns, 1)
    
    def get_filtered_ships(self) -> List[ShipSpecification]:
        """Get ships based on current filter"""
        if not self.current_filter:
            return self.ship_database.get_all_ships()
        
        return self.ship_database.search_ships(**self.current_filter)
    
    def on_ship_clicked(self, ship_key: str):
        """Handle ship thumbnail click"""
        self.select_ship(ship_key)
        self.ship_selected.emit(ship_key)
    
    def on_ship_hovered(self, ship_key: str, hovered: bool):
        """Handle ship thumbnail hover"""
        if hovered:
            self.ship_hovered.emit(ship_key)
    
    def select_ship(self, ship_key: str):
        """Select a ship thumbnail"""
        # Deselect previous
        if self.selected_ship_key and self.selected_ship_key in self.thumbnails:
            self.thumbnails[self.selected_ship_key].set_selected(False)
        
        # Select new
        self.selected_ship_key = ship_key
        if ship_key in self.thumbnails:
            self.thumbnails[ship_key].set_selected(True)
            
            # Ensure visible
            thumbnail = self.thumbnails[ship_key]
            self.ensureWidgetVisible(thumbnail)
    
    def set_filter(self, filter_criteria: Dict):
        """Set filter criteria and refresh grid"""
        self.current_filter = filter_criteria.copy()
        self.populate_ships()
    
    def clear_filter(self):
        """Clear all filters"""
        self.current_filter.clear()
        self.populate_ships()
    
    def resizeEvent(self, event):
        """Handle resize to adjust grid columns"""
        super().resizeEvent(event)
        # Repopulate to adjust columns
        QTimer.singleShot(100, self.populate_ships)


class ShipFilterPanel(ElitePanel):
    """Filter panel for ship selection"""
    
    filter_changed = pyqtSignal(dict)  # Emits new filter criteria
    
    def __init__(self, parent=None):
        super().__init__("SHIP FILTERS", parent)
        self.setup_filter_ui()
    
    def setup_filter_ui(self):
        """Setup filter controls"""
        # Class filter
        class_layout = QHBoxLayout()
        class_layout.addWidget(EliteLabel("CLASS:", "small"))
        
        self.class_buttons = QButtonGroup(self)
        self.class_buttons.setExclusive(False)
        
        class_btn_all = EliteButton("ALL")
        class_btn_all.setCheckable(True)
        class_btn_all.setChecked(True)
        class_btn_all.clicked.connect(lambda: self.on_class_filter_changed("all"))
        class_layout.addWidget(class_btn_all)
        
        for ship_class in [ShipClass.SMALL, ShipClass.MEDIUM, ShipClass.LARGE]:
            btn = EliteButton(ship_class.value[0])  # S, M, L
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, sc=ship_class: self.on_class_filter_changed(sc.value))
            self.class_buttons.addButton(btn)
            class_layout.addWidget(btn)
        
        self.add_layout(class_layout)
        
        # Role filter
        role_layout = QHBoxLayout()
        role_layout.addWidget(EliteLabel("ROLE:", "small"))
        
        self.role_buttons = QButtonGroup(self)
        self.role_buttons.setExclusive(False)
        
        role_btn_all = EliteButton("ALL")
        role_btn_all.setCheckable(True)
        role_btn_all.setChecked(True)
        role_btn_all.clicked.connect(lambda: self.on_role_filter_changed("all"))
        role_layout.addWidget(role_btn_all)
        
        for role in [ShipRole.COMBAT, ShipRole.EXPLORER, ShipRole.TRADER, ShipRole.MULTIPURPOSE]:
            btn = EliteButton(role.value[:3])  # First 3 letters
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, r=role: self.on_role_filter_changed(r.value))
            self.role_buttons.addButton(btn)
            role_layout.addWidget(btn)
        
        self.add_layout(role_layout)
        
        # Cost filter
        cost_layout = QHBoxLayout()
        cost_layout.addWidget(EliteLabel("BUDGET:", "small"))
        
        self.cost_buttons = QButtonGroup(self)
        self.cost_buttons.setExclusive(True)
        
        cost_ranges = [
            ("ALL", None),
            ("< 1M", 1000000),
            ("< 10M", 10000000),
            ("< 50M", 50000000),
            ("50M+", None)
        ]
        
        for label, max_cost in cost_ranges:
            btn = EliteButton(label)
            btn.setCheckable(True)
            if label == "ALL":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, mc=max_cost: self.on_cost_filter_changed(mc))
            self.cost_buttons.addButton(btn)
            cost_layout.addWidget(btn)
        
        self.add_layout(cost_layout)
        
        # Clear filters button
        clear_btn = EliteButton("CLEAR ALL")
        clear_btn.clicked.connect(self.clear_all_filters)
        self.add_widget(clear_btn)
        
        # Initialize filter state
        self.current_filter = {}
    
    def on_class_filter_changed(self, ship_class):
        """Handle class filter change"""
        if ship_class == "all":
            self.current_filter.pop('ship_class', None)
        else:
            # Find ShipClass enum value
            for sc in ShipClass:
                if sc.value == ship_class:
                    self.current_filter['ship_class'] = sc
                    break
        
        self.filter_changed.emit(self.current_filter)
    
    def on_role_filter_changed(self, role):
        """Handle role filter change"""
        if role == "all":
            self.current_filter.pop('primary_role', None)
        else:
            # Find ShipRole enum value
            for sr in ShipRole:
                if sr.value == role:
                    self.current_filter['primary_role'] = sr
                    break
        
        self.filter_changed.emit(self.current_filter)
    
    def on_cost_filter_changed(self, max_cost):
        """Handle cost filter change"""
        if max_cost is None:
            self.current_filter.pop('max_cost', None)
        else:
            self.current_filter['max_cost'] = max_cost
        
        self.filter_changed.emit(self.current_filter)
    
    def clear_all_filters(self):
        """Clear all active filters"""
        self.current_filter.clear()
        
        # Reset button states
        for button in self.class_buttons.buttons():
            button.setChecked(False)
        for button in self.role_buttons.buttons():
            button.setChecked(False)
        for button in self.cost_buttons.buttons():
            button.setChecked(False)
        
        self.filter_changed.emit(self.current_filter)


class ShipGalleryCarousel(QWidget, ThemeAwareWidget):
    """Horizontal carousel for featured ships"""
    
    ship_selected = pyqtSignal(str)
    ship_changed = pyqtSignal(str)
    
    def __init__(self, featured_ships: List[str] = None, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.ship_database = get_ship_database()
        self.featured_ships = featured_ships or self.get_default_featured_ships()
        self.current_index = 0
        self.ship_widgets = []
        self._current_theme = None
        
        self.setFixedHeight(200)
        self.setMinimumWidth(600)
        
        self.setup_ui()
        self.populate_carousel()
        
        # Auto-advance timer
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.next_ship)
        self.auto_timer.start(5000)  # 5 seconds
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def get_default_featured_ships(self) -> List[str]:
        """Get default featured ships"""
        return [
            "sidewinder", "cobra-mk-iii", "asp-explorer", "python", "anaconda",
            "imperial-cutter", "federal-corvette", "vulture", "fer-de-lance"
        ]
    
    def setup_ui(self):
        """Setup carousel UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Previous button
        self.prev_btn = EliteButton("◀")
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.clicked.connect(self.previous_ship)
        layout.addWidget(self.prev_btn)
        
        # Carousel area
        self.carousel_area = QWidget()
        self.carousel_area.setFixedHeight(180)
        layout.addWidget(self.carousel_area, 1)
        
        # Next button
        self.next_btn = EliteButton("▶")
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.clicked.connect(self.next_ship)
        layout.addWidget(self.next_btn)
        
        # Ship info panel
        self.info_panel = QWidget()
        self.info_layout = QVBoxLayout(self.info_panel)
        self.ship_name_label = EliteLabel("", "header")
        self.ship_class_label = EliteLabel("", "value")
        self.ship_role_label = EliteLabel("", "small")
        
        self.info_layout.addWidget(self.ship_name_label)
        self.info_layout.addWidget(self.ship_class_label)
        self.info_layout.addWidget(self.ship_role_label)
        self.info_layout.addStretch()
        
        layout.addWidget(self.info_panel)
    
    def populate_carousel(self):
        """Populate carousel with ship widgets"""
        self.ship_widgets.clear()
        
        for ship_key in self.featured_ships:
            ship = self.ship_database.get_ship(ship_key)
            if ship:
                widget = ShipCarouselItem(ship, self.carousel_area)
                widget.clicked.connect(lambda sk=ship_key: self.select_ship(sk))
                self.ship_widgets.append(widget)
        
        self.update_carousel_layout()
        self.update_ship_info()
    
    def update_carousel_layout(self):
        """Update carousel layout and positioning"""
        if not self.ship_widgets:
            return
        
        carousel_width = self.carousel_area.width()
        item_width = 150
        center_x = carousel_width // 2
        
        for i, widget in enumerate(self.ship_widgets):
            # Calculate position relative to current index
            offset = i - self.current_index
            x = center_x + (offset * (item_width + 10)) - (item_width // 2)
            y = 10
            
            widget.setGeometry(x, y, item_width, 160)
            widget.set_active(i == self.current_index)
            widget.setVisible(abs(offset) <= 2)  # Show only nearby items
    
    def update_ship_info(self):
        """Update ship information display"""
        if self.current_index < len(self.ship_widgets):
            current_ship = self.ship_widgets[self.current_index].ship_spec
            self.ship_name_label.setText(current_ship.display_name)
            self.ship_class_label.setText(f"{current_ship.ship_class.value} Class")
            self.ship_role_label.setText(f"Primary Role: {current_ship.primary_role.value}")
            
            self.ship_changed.emit(current_ship.name)
    
    def select_ship(self, ship_key: str):
        """Select a specific ship"""
        for i, widget in enumerate(self.ship_widgets):
            if widget.ship_spec.name == ship_key:
                self.current_index = i
                self.update_carousel_layout()
                self.update_ship_info()
                self.ship_selected.emit(ship_key)
                break
    
    def next_ship(self):
        """Move to next ship"""
        if self.ship_widgets:
            self.current_index = (self.current_index + 1) % len(self.ship_widgets)
            self.update_carousel_layout()
            self.update_ship_info()
    
    def previous_ship(self):
        """Move to previous ship"""
        if self.ship_widgets:
            self.current_index = (self.current_index - 1) % len(self.ship_widgets)
            self.update_carousel_layout()
            self.update_ship_info()
    
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        QTimer.singleShot(50, self.update_carousel_layout)
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme to carousel"""
        self._current_theme = theme
        self.update()


class ShipCarouselItem(QWidget):
    """Individual ship item in carousel"""
    
    clicked = pyqtSignal()
    
    def __init__(self, ship_spec: ShipSpecification, parent=None):
        super().__init__(parent)
        
        self.ship_spec = ship_spec
        self.ship_image = None
        self.is_active = False
        
        self.setFixedSize(150, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.load_ship_image()
    
    def load_ship_image(self):
        """Load ship image"""
        image_path = self.ship_spec.get_image_path()
        if os.path.exists(image_path):
            self.ship_image = QPixmap(image_path)
            if not self.ship_image.isNull():
                self.ship_image = self.ship_image.scaled(
                    120, 90, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
    
    def set_active(self, active: bool):
        """Set active state"""
        self.is_active = active
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
    
    def paintEvent(self, event):
        """Custom paint for carousel item"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        if self.is_active:
            painter.fillRect(self.rect(), QColor(0, 150, 255, 50))
            painter.setPen(QPen(QColor(0, 200, 255), 2))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        
        # Ship image
        if self.ship_image:
            img_rect = self.ship_image.rect()
            img_rect.moveCenter(QPoint(self.width() // 2, self.height() // 2 - 10))
            painter.drawPixmap(img_rect, self.ship_image)
        
        # Ship name
        painter.setPen(QPen(self.palette().text().color(), 1))
        font = QFont("Arial", 10, QFont.Weight.Bold if self.is_active else QFont.Weight.Normal)
        painter.setFont(font)
        
        text_rect = QRect(5, self.height() - 25, self.width() - 10, 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.ship_spec.display_name)


class ShipGalleryWidget(QWidget, ThemeAwareWidget):
    """Main ship gallery widget combining grid and carousel"""
    
    ship_selected = pyqtSignal(str, object)  # ship_key, ShipSpecification
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        ThemeAwareWidget.__init__(self)
        
        self.current_ship_key = None
        self.setup_ui()
        
        # Register with theme manager
        get_global_theme_manager().register_widget(self)
    
    def setup_ui(self):
        """Setup main gallery UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Featured carousel
        carousel_panel = ElitePanel("FEATURED SHIPS")
        self.carousel = ShipGalleryCarousel()
        self.carousel.ship_selected.connect(self.on_ship_selected)
        carousel_panel.add_widget(self.carousel)
        layout.addWidget(carousel_panel, 0)
        
        # Filter and grid section
        bottom_layout = QHBoxLayout()
        
        # Filter panel
        self.filter_panel = ShipFilterPanel()
        self.filter_panel.filter_changed.connect(self.on_filter_changed)
        bottom_layout.addWidget(self.filter_panel, 0)
        
        # Ship grid
        grid_panel = ElitePanel("SHIP COLLECTION")
        self.ship_grid = ShipGalleryGrid()
        self.ship_grid.ship_selected.connect(self.on_ship_selected)
        self.ship_grid.ship_hovered.connect(self.on_ship_hovered)
        grid_panel.add_widget(self.ship_grid)
        bottom_layout.addWidget(grid_panel, 1)
        
        layout.addLayout(bottom_layout, 1)
    
    def on_ship_selected(self, ship_key: str):
        """Handle ship selection"""
        ship_database = get_ship_database()
        ship_spec = ship_database.get_ship(ship_key)
        
        if ship_spec:
            self.current_ship_key = ship_key
            self.ship_grid.select_ship(ship_key)
            self.ship_selected.emit(ship_key, ship_spec)
    
    def on_ship_hovered(self, ship_key: str):
        """Handle ship hover for preview"""
        # Could show quick preview info
        pass
    
    def on_filter_changed(self, filter_criteria: dict):
        """Handle filter change"""
        self.ship_grid.set_filter(filter_criteria)
    
    def select_ship(self, ship_key: str):
        """Programmatically select a ship"""
        self.on_ship_selected(ship_key)
    
    def apply_theme(self, theme: ThemeColors):
        """Apply theme to gallery"""
        self._current_theme = theme


# Export main classes
__all__ = [
    'ShipThumbnail', 'ShipGalleryGrid', 'ShipFilterPanel', 
    'ShipGalleryCarousel', 'ShipGalleryWidget'
]