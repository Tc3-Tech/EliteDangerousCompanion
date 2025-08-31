"""
Elite Dangerous Fidget Mode - Main Interface
Primary interactive interface when Elite Dangerous is not running.
Features smooth animations, ship browsing, and hardware integration.
"""
import sys
import os
import time
from typing import Optional, Dict, List, Callable
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QSplitter, QStackedWidget, QFrame, QPushButton,
                           QApplication, QLabel, QStatusBar, QMenuBar, QMenu)
from PyQt6.QtCore import (Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, 
                        QRect, QParallelAnimationGroup, QSequentialAnimationGroup,
                        QThread, pyqtSlot, QObject, QPoint)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction, QKeySequence

# Add parent directories to path for imports
app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_root not in sys.path:
    sys.path.insert(0, app_root)

try:
    from data.ship_database import get_ship_database, ShipSpecification
    from ui.elite_widgets import (ElitePanel, EliteLabel, EliteButton, apply_elite_theme,
                              get_global_theme_manager, setup_hardware_theme_integration)
    from config.themes import HardwareThemeManager, PredefinedThemes, ThemeColors
    from ui.widgets.ship_gallery import ShipGalleryWidget
    from ui.widgets.ship_viewer import ShipViewer3D, ShipViewerControls
    from ui.widgets.ship_specs_panel import ShipSpecificationPanel
    from ui.widgets.ship_comparison import show_ship_comparison
except ImportError as e:
    print(f"Critical import error in fidget_mode.py: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
    raise


class AnimatedTransition(QObject):
    """Manages smooth transitions between ships with various effects"""
    
    transition_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_transitioning = False
        self.transition_duration = 500  # ms
        self.animation_group = None
        self._cleanup_performed = False
    
    def fade_transition(self, widget_from: QWidget, widget_to: QWidget):
        """Perform fade transition between widgets"""
        if self.is_transitioning:
            return
        
        self.is_transitioning = True
        
        # Fade out animation
        self.fade_out_anim = QPropertyAnimation(widget_from, b"windowOpacity")
        self.fade_out_anim.setDuration(self.transition_duration // 2)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # Fade in animation
        self.fade_in_anim = QPropertyAnimation(widget_to, b"windowOpacity")
        self.fade_in_anim.setDuration(self.transition_duration // 2)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # Chain animations
        self.animation_group = QSequentialAnimationGroup()
        self.animation_group.addAnimation(self.fade_out_anim)
        self.animation_group.addAnimation(self.fade_in_anim)
        
        self.animation_group.finished.connect(self.on_transition_finished)
        self.animation_group.start()
    
    def slide_transition(self, widget_from: QWidget, widget_to: QWidget, direction: str = "left"):
        """Perform slide transition between widgets"""
        if self.is_transitioning:
            return
        
        self.is_transitioning = True
        
        # Calculate slide distances
        parent_width = widget_from.parent().width()
        start_pos_from = widget_from.pos()
        
        if direction == "left":
            end_pos_from = QPoint(-parent_width, start_pos_from.y())
            start_pos_to = QPoint(parent_width, start_pos_from.y())
        else:  # right
            end_pos_from = QPoint(parent_width, start_pos_from.y())
            start_pos_to = QPoint(-parent_width, start_pos_from.y())
        
        end_pos_to = start_pos_from
        
        # Position target widget
        widget_to.move(start_pos_to)
        widget_to.show()
        
        # Slide out animation
        self.slide_out_anim = QPropertyAnimation(widget_from, b"pos")
        self.slide_out_anim.setDuration(self.transition_duration)
        self.slide_out_anim.setStartValue(start_pos_from)
        self.slide_out_anim.setEndValue(end_pos_from)
        self.slide_out_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Slide in animation
        self.slide_in_anim = QPropertyAnimation(widget_to, b"pos")
        self.slide_in_anim.setDuration(self.transition_duration)
        self.slide_in_anim.setStartValue(start_pos_to)
        self.slide_in_anim.setEndValue(end_pos_to)
        self.slide_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Run animations in parallel
        self.animation_group = QParallelAnimationGroup()
        self.animation_group.addAnimation(self.slide_out_anim)
        self.animation_group.addAnimation(self.slide_in_anim)
        
        self.animation_group.finished.connect(self.on_transition_finished)
        self.animation_group.start()
    
    def on_transition_finished(self):
        """Handle transition completion"""
        self.is_transitioning = False
        self.transition_completed.emit()
    
    def cleanup_resources(self):
        """Cleanup animation resources"""
        if self._cleanup_performed:
            return
        self._cleanup_performed = True
        
        try:
            if self.animation_group:
                self.animation_group.stop()
                self.animation_group = None
        except Exception as e:
            print(f"Error cleaning up AnimatedTransition: {e}")


class HardwareNavigationManager(QObject):
    """Manages 9-button hardware navigation integration"""
    
    button_pressed = pyqtSignal(int)  # Button number (1-9)
    pot_changed = pyqtSignal(float)   # Potentiometer value (0.0-1.0)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.button_mappings = {
            1: "gallery_prev",
            2: "gallery_select", 
            3: "gallery_next",
            4: "viewer_rotate_left",
            5: "viewer_zoom_toggle",
            6: "viewer_rotate_right",
            7: "specs_prev_tab",
            8: "specs_compare",
            9: "specs_next_tab"
        }
        self.pot_mode = "theme"  # "theme", "rotation", "zoom"
        self._cleanup_performed = False
        
        # Simulate hardware input for development
        self.simulation_timer = QTimer(self)
        self.simulation_timer.timeout.connect(self.simulate_input)
        self.enable_simulation = False
    
    def enable_hardware_simulation(self, enabled: bool = True):
        """Enable hardware simulation for testing"""
        self.enable_simulation = enabled
        if enabled:
            self.simulation_timer.start(5000)  # Simulate every 5 seconds
        else:
            self.simulation_timer.stop()
    
    def simulate_input(self):
        """Simulate hardware input for testing"""
        import random
        
        # Simulate random button press
        button = random.randint(1, 9)
        self.button_pressed.emit(button)
        
        # Simulate potentiometer change
        pot_value = random.random()
        self.pot_changed.emit(pot_value)
    
    def handle_button_press(self, button: int):
        """Handle hardware button press"""
        self.button_pressed.emit(button)
    
    def handle_pot_change(self, value: float):
        """Handle potentiometer change"""
        self.pot_changed.emit(value)
    
    def set_pot_mode(self, mode: str):
        """Set potentiometer control mode"""
        if mode in ["theme", "rotation", "zoom"]:
            self.pot_mode = mode
    
    def cleanup_resources(self):
        """Cleanup hardware navigation resources"""
        if self._cleanup_performed:
            return
        self._cleanup_performed = True
        
        try:
            if hasattr(self, 'simulation_timer') and self.simulation_timer:
                self.simulation_timer.stop()
                self.simulation_timer.timeout.disconnect()
                self.simulation_timer = None
        except Exception as e:
            print(f"Error cleaning up HardwareNavigationManager: {e}")


class EliteFidgetMode(QMainWindow):
    """Main fidget mode window with full ship browsing functionality"""
    
    def __init__(self):
        try:
            super().__init__()
            
            # Cleanup tracking - CRITICAL for preventing segfaults
            self._is_destroyed = False
            self._cleanup_performed = False
            self._cleanup_in_progress = False
            
            # Core components - initialize safely
            self.ship_database = None
            self.current_ship = None
            self.theme_manager = None
            self.hardware_nav = None
            self.transition_manager = None
            
            # Performance tracking
            self.fps_counter = 0
            self.last_fps_time = time.time()
            
            # UI components - initialize as None first
            self.gallery_widget = None
            self.ship_viewer = None
            self.viewer_controls = None
            self.specs_panel = None
            
            # Animation tracking for cleanup
            self.ship_transition_anim = None
            
            # Initialize step by step with error handling
            self.initialize_components()
            
        except Exception as e:
            print(f"Critical error in EliteFidgetMode.__init__: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup_resources()  # Emergency cleanup
            raise
    
    def initialize_components(self):
        """Initialize all components step by step with error handling"""
        try:
            # Step 1: Basic window setup
            self.setup_window()
            
            # Step 2: Initialize database
            self.ship_database = get_ship_database()
            
            # Step 3: Theme management
            self.setup_theme_management()
            
            # Step 4: Create transition manager after theme setup
            self.transition_manager = AnimatedTransition(self)
            
            # Step 5: Setup UI components
            self.setup_ui()
            
            # Step 6: Hardware integration
            self.setup_hardware_integration()
            
            # Step 7: Menu and status bars
            self.setup_menu_bar()
            self.setup_status_bar()
            
            # Step 8: Animations
            self.setup_animations()
            
            # Step 9: Signal connections
            self.setup_connections()
            
            # Step 10: Load initial ship
            self.load_default_ship()
            
            # Step 11: Performance monitoring with parent for cleanup
            self.fps_timer = QTimer(self)
            self.fps_timer.timeout.connect(self.safe_update_performance_metrics)
            self.fps_timer.start(1000)
            
        except Exception as e:
            print(f"Error in initialize_components: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def setup_window(self):
        """Setup main window properties optimized for 1024x768 secondary display"""
        self.setWindowTitle("Elite Dangerous - Ship Database")
        
        # Optimize for 1024x768 secondary display
        target_width = 1024
        target_height = 768
        
        # Position window for secondary display (typically to the right)
        self.setGeometry(1024, 0, target_width, target_height)
        
        # Set exact size for 1024x768 optimization
        self.setFixedSize(target_width, target_height)  # Fixed size for optimal display
        
        # Set window icon if available
        icon_path = "/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets/cyclops.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Window flags for clean appearance
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint)
    
    def setup_theme_management(self):
        """Setup advanced theme management with hardware integration"""
        try:
            # Create theme manager with error handling
            self.theme_manager = HardwareThemeManager(self)
            
            # Start with Ice Blue theme
            self.theme_manager.set_predefined_theme("Ice Blue")
            
            # Connect theme changes
            self.theme_manager.theme_changed.connect(self.on_theme_changed)
            
            # Setup global theme manager safely
            try:
                global_theme_manager = get_global_theme_manager()
                app_instance = QApplication.instance()
                if app_instance:
                    global_theme_manager.set_application(app_instance)
            except Exception as e:
                print(f"Warning: Could not setup global theme manager: {e}")
                
        except Exception as e:
            print(f"Error in setup_theme_management: {e}")
            # Create minimal theme manager
            self.theme_manager = None
    
    def setup_ui(self):
        """Setup main user interface with clean single-window design"""
        try:
            # Create central widget with modern, clean design
            central_widget = QWidget(self)
            central_widget.setMinimumSize(800, 600)
            self.setCentralWidget(central_widget)
            
            # Main layout with minimal margins for clean look
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)
            
            # Header section with ship name and basic info
            header_layout = QHBoxLayout()
            header_layout.setSpacing(15)
            
            # Ship name display
            self.ship_name_label = QLabel("SHIP DATABASE")
            self.ship_name_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #00d4ff;
                    padding: 5px 10px;
                    background-color: rgba(0, 212, 255, 0.1);
                    border: 1px solid #00d4ff;
                    border-radius: 3px;
                }
            """)
            header_layout.addWidget(self.ship_name_label)
            
            header_layout.addStretch()
            
            # Quick stats display
            self.stats_label = QLabel("Ready")
            self.stats_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #88ccff;
                    padding: 5px 10px;
                }
            """)
            header_layout.addWidget(self.stats_label)
            
            main_layout.addLayout(header_layout)
            
            # Main content area - single integrated layout
            content_layout = QHBoxLayout()
            content_layout.setSpacing(15)
            
            # Left side - Ship Gallery (optimized for 1024x768)
            try:
                gallery_container = QWidget()
                gallery_container.setFixedWidth(200)  # Slightly smaller for 1024x768
                gallery_container.setStyleSheet("""
                    QWidget {
                        background-color: rgba(0, 0, 0, 0.3);
                        border: 1px solid #444;
                        border-radius: 5px;
                    }
                """)
                
                gallery_layout = QVBoxLayout(gallery_container)
                gallery_layout.setContentsMargins(8, 8, 8, 8)
                
                gallery_title = QLabel("SHIPS")
                gallery_title.setStyleSheet("""
                    QLabel {
                        color: #00d4ff;
                        font-weight: bold;
                        font-size: 11px;
                        padding: 3px 5px;
                        border-bottom: 1px solid #444;
                    }
                """)
                gallery_layout.addWidget(gallery_title)
                
                self.gallery_widget = ShipGalleryWidget(gallery_container)
                gallery_layout.addWidget(self.gallery_widget)
                
                content_layout.addWidget(gallery_container)
                
            except Exception as e:
                print(f"Warning: Failed to create gallery widget: {e}")
                fallback_gallery = QLabel("Gallery\nUnavailable")
                fallback_gallery.setFixedWidth(200)  # Match updated width
                fallback_gallery.setAlignment(Qt.AlignmentFlag.AlignCenter)
                content_layout.addWidget(fallback_gallery)
                self.gallery_widget = None
            
            # Center - Ship Viewer (main focus)
            try:
                viewer_container = QWidget()
                viewer_container.setStyleSheet("""
                    QWidget {
                        background-color: rgba(0, 0, 0, 0.2);
                        border: 1px solid #555;
                        border-radius: 5px;
                    }
                """)
                
                viewer_layout = QVBoxLayout(viewer_container)
                viewer_layout.setContentsMargins(10, 10, 10, 10)
                viewer_layout.setSpacing(8)
                
                # Ship viewer
                self.ship_viewer = ShipViewer3D(viewer_container)
                viewer_layout.addWidget(self.ship_viewer, 1)
                
                # Integrated viewer controls (compact)
                controls_layout = QHBoxLayout()
                controls_layout.setSpacing(10)
                
                try:
                    self.viewer_controls = ShipViewerControls(viewer_container)
                    # Make controls horizontal and compact
                    self.viewer_controls.setMaximumHeight(40)
                    controls_layout.addWidget(self.viewer_controls)
                except Exception as e:
                    print(f"Warning: Failed to create viewer controls: {e}")
                    self.viewer_controls = None
                
                controls_layout.addStretch()
                viewer_layout.addLayout(controls_layout)
                
                content_layout.addWidget(viewer_container, 1)
                
            except Exception as e:
                print(f"Warning: Failed to create ship viewer: {e}")
                fallback_viewer = QLabel("3D Viewer\nUnavailable")
                fallback_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
                content_layout.addWidget(fallback_viewer, 1)
                self.ship_viewer = None
                self.viewer_controls = None
            
            # Right side - Ship Specifications (optimized for 1024x768)
            try:
                specs_container = QWidget()
                specs_container.setFixedWidth(250)  # Optimized for 1024x768
                specs_container.setStyleSheet("""
                    QWidget {
                        background-color: rgba(0, 0, 0, 0.3);
                        border: 1px solid #444;
                        border-radius: 5px;
                    }
                """)
                
                specs_layout = QVBoxLayout(specs_container)
                specs_layout.setContentsMargins(8, 8, 8, 8)
                
                specs_title = QLabel("SPECIFICATIONS")
                specs_title.setStyleSheet("""
                    QLabel {
                        color: #00d4ff;
                        font-weight: bold;
                        font-size: 11px;
                        padding: 3px 5px;
                        border-bottom: 1px solid #444;
                    }
                """)
                specs_layout.addWidget(specs_title)
                
                self.specs_panel = ShipSpecificationPanel(specs_container)
                specs_layout.addWidget(self.specs_panel)
                
                content_layout.addWidget(specs_container)
                
            except Exception as e:
                print(f"Warning: Failed to create specs panel: {e}")
                fallback_specs = QLabel("Specifications\nUnavailable")
                fallback_specs.setFixedWidth(250)  # Match updated width
                fallback_specs.setAlignment(Qt.AlignmentFlag.AlignCenter)
                content_layout.addWidget(fallback_specs)
                self.specs_panel = None
            
            main_layout.addLayout(content_layout, 1)
            
            # Apply global styling for clean, modern appearance
            central_widget.setStyleSheet("""
                QWidget {
                    background-color: #0a0a0a;
                    color: #cccccc;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QLabel {
                    border: none;
                    background: transparent;
                }
            """)
            
            # Set professional window styling
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #0a0a0a;
                    border: 1px solid #333;
                }
                QMenuBar {
                    background-color: #1a1a1a;
                    color: #cccccc;
                    border-bottom: 1px solid #333;
                }
                QMenuBar::item {
                    padding: 4px 8px;
                }
                QMenuBar::item:selected {
                    background-color: #00d4ff;
                    color: #000;
                }
                QStatusBar {
                    background-color: #1a1a1a;
                    color: #888;
                    border-top: 1px solid #333;
                }
            """)
            
            # Force immediate layout update
            central_widget.updateGeometry()
            self.update()
            
        except Exception as e:
            print(f"Critical error in setup_ui: {e}")
            # Create emergency fallback UI
            fallback_widget = QWidget(self)
            fallback_layout = QVBoxLayout(fallback_widget)
            fallback_layout.addWidget(QLabel(f"UI Setup Error: {e}"))
            self.setCentralWidget(fallback_widget)
            raise
    
    # OLD PANEL METHODS REMOVED - Now using integrated single-window design
    # These methods are no longer needed with the new clean layout
    
    def setup_hardware_integration(self):
        """Setup hardware navigation integration"""
        self.hardware_nav = HardwareNavigationManager(self)
        
        # Connect hardware signals
        self.hardware_nav.button_pressed.connect(self.on_hardware_button_pressed)
        self.hardware_nav.pot_changed.connect(self.on_hardware_pot_changed)
        
        # Enable hardware simulation for development/testing
        # Remove this in production
        self.hardware_nav.enable_hardware_simulation(True)
    
    def setup_menu_bar(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("FILE")
        
        # Export screenshot action
        export_action = QAction("Export Screenshot", self)
        export_action.setShortcut(QKeySequence("Ctrl+S"))
        export_action.triggered.connect(self.export_screenshot)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("VIEW")
        
        # Theme submenu
        theme_submenu = view_menu.addMenu("THEMES")
        
        theme_actions = []
        for theme_name in ["Ice Blue", "Matrix Green", "Deep Purple", "Plasma Pink", "Arctic White", "Ember Red"]:
            action = QAction(theme_name, self)
            action.setCheckable(True)
            if theme_name == "Ice Blue":
                action.setChecked(True)
            action.triggered.connect(lambda checked, name=theme_name: self.change_theme(name))
            theme_submenu.addAction(action)
            theme_actions.append(action)
        
        self.theme_actions = theme_actions
        
        # Hardware menu
        hardware_menu = menubar.addMenu("HARDWARE")
        
        # Enable hardware theme control
        hw_theme_action = QAction("Hardware Theme Control", self)
        hw_theme_action.setCheckable(True)
        hw_theme_action.toggled.connect(self.toggle_hardware_theme_control)
        hardware_menu.addAction(hw_theme_action)
        
        # Potentiometer mode submenu
        pot_mode_submenu = hardware_menu.addMenu("Potentiometer Mode")
        
        pot_modes = [("Theme", "theme"), ("Ship Rotation", "rotation"), ("Viewer Zoom", "zoom")]
        for mode_name, mode_key in pot_modes:
            action = QAction(mode_name, self)
            action.setCheckable(True)
            if mode_key == "theme":
                action.setChecked(True)
            action.triggered.connect(lambda checked, mode=mode_key: self.set_pot_mode(mode))
            pot_mode_submenu.addAction(action)
        
        # Help menu
        help_menu = menubar.addMenu("HELP")
        
        # Controls help
        controls_action = QAction("Controls", self)
        controls_action.triggered.connect(self.show_controls_help)
        help_menu.addAction(controls_action)
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Ship count
        ship_count = self.ship_database.get_ship_count()
        self.status_bar.showMessage(f"Elite Dangerous Ship Database - {ship_count} ships loaded")
        
        # Performance indicator (right side)
        self.fps_label = QLabel("FPS: --")
        self.status_bar.addPermanentWidget(self.fps_label)
        
        # Hardware status
        self.hardware_status_label = QLabel("Hardware: Disconnected")
        self.status_bar.addPermanentWidget(self.hardware_status_label)
    
    def setup_animations(self):
        """Setup animation systems"""
        # Ship transition animations
        self.transition_manager.transition_completed.connect(self.on_ship_transition_completed)
    
    def setup_connections(self):
        """Setup signal connections between components with error handling"""
        try:
            # Gallery to viewer
            if self.gallery_widget and hasattr(self.gallery_widget, 'ship_selected'):
                try:
                    self.gallery_widget.ship_selected.connect(self.on_ship_selected)
                except Exception as e:
                    print(f"Warning: Could not connect gallery signals: {e}")
            
            # Viewer controls
            if self.viewer_controls:
                try:
                    if hasattr(self.viewer_controls, 'rotation_changed'):
                        self.viewer_controls.rotation_changed.connect(self.on_viewer_rotation_changed)
                    if hasattr(self.viewer_controls, 'zoom_changed'):
                        self.viewer_controls.zoom_changed.connect(self.on_viewer_zoom_changed)
                    if hasattr(self.viewer_controls, 'auto_rotate_toggled'):
                        self.viewer_controls.auto_rotate_toggled.connect(self.on_auto_rotate_toggled)
                    if hasattr(self.viewer_controls, 'scanning_toggled'):
                        self.viewer_controls.scanning_toggled.connect(self.on_scanning_toggled)
                    if hasattr(self.viewer_controls, 'view_reset'):
                        self.viewer_controls.view_reset.connect(self.on_view_reset)
                except Exception as e:
                    print(f"Warning: Could not connect viewer control signals: {e}")
            
            # Specs panel
            if self.specs_panel and hasattr(self.specs_panel, 'comparison_requested'):
                try:
                    self.specs_panel.comparison_requested.connect(self.on_comparison_requested)
                except Exception as e:
                    print(f"Warning: Could not connect specs panel signals: {e}")
                    
        except Exception as e:
            print(f"Error in setup_connections: {e}")
            # Continue without connections - better than crashing
    
    def load_default_ship(self):
        """Load default ship (Sidewinder)"""
        default_ship = self.ship_database.get_ship("sidewinder")
        if default_ship:
            self.set_current_ship(default_ship, animate=False)
        else:
            # Fallback to first available ship
            ships = self.ship_database.get_all_ships()
            if ships:
                self.set_current_ship(ships[0], animate=False)
    
    def set_current_ship(self, ship_spec: ShipSpecification, animate: bool = True):
        """Set the currently displayed ship"""
        old_ship = self.current_ship
        self.current_ship = ship_spec
        
        if animate and old_ship:
            self.start_ship_transition(old_ship, ship_spec)
        else:
            self.update_ship_displays()
    
    def start_ship_transition(self, old_ship: ShipSpecification, new_ship: ShipSpecification):
        """Start animated transition between ships"""
        # Update displays immediately for responsiveness
        self.update_ship_displays()
        
        # Visual transition effects could be added here
        # For now, we'll use a simple fade effect on the viewer
        if self.ship_viewer:
            # Simple opacity animation
            self.ship_transition_anim = QPropertyAnimation(self.ship_viewer, b"windowOpacity")
            self.ship_transition_anim.setDuration(300)
            self.ship_transition_anim.setStartValue(0.5)
            self.ship_transition_anim.setEndValue(1.0)
            self.ship_transition_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            self.ship_transition_anim.start()
    
    def update_ship_displays(self):
        """Update all ship displays with current ship"""
        if not self.current_ship:
            return
        
        try:
            # Update ship viewer
            if self.ship_viewer:
                try:
                    self.ship_viewer.set_ship(self.current_ship)
                except Exception as e:
                    print(f"Warning: Failed to update ship viewer: {e}")
            
            # Update specifications panel
            if self.specs_panel and hasattr(self.specs_panel, 'set_ship'):
                try:
                    self.specs_panel.set_ship(self.current_ship)
                except Exception as e:
                    print(f"Warning: Failed to update specs panel: {e}")
            
            # Update header displays
            if hasattr(self, 'ship_name_label'):
                try:
                    self.ship_name_label.setText(self.current_ship.display_name.upper())
                except Exception as e:
                    print(f"Warning: Failed to update ship name label: {e}")
            
            if hasattr(self, 'stats_label'):
                try:
                    stats_text = (f"{self.current_ship.manufacturer.value} • "
                                f"{self.current_ship.ship_class.value} Class • "
                                f"{self.current_ship.performance.max_speed} m/s")
                    self.stats_label.setText(stats_text)
                except Exception as e:
                    print(f"Warning: Failed to update stats label: {e}")
            
            # Update status bar
            if hasattr(self, 'status_bar') and self.status_bar:
                try:
                    self.status_bar.showMessage(
                        f"Current Ship: {self.current_ship.display_name} - "
                        f"{self.current_ship.manufacturer.value} - "
                        f"{self.current_ship.ship_class.value} Class"
                    )
                except Exception as e:
                    print(f"Warning: Failed to update status bar: {e}")
                    
        except Exception as e:
            print(f"Error in update_ship_displays: {e}")
            # Continue execution despite display update errors
    
    # Event handlers
    
    def on_ship_selected(self, ship_key: str, ship_spec: ShipSpecification):
        """Handle ship selection from gallery"""
        self.set_current_ship(ship_spec, animate=True)
    
    def on_ship_transition_completed(self):
        """Handle ship transition completion"""
        # Additional post-transition logic could go here
        pass
    
    def on_viewer_rotation_changed(self, delta: float):
        """Handle viewer rotation change"""
        if self.ship_viewer and hasattr(self.ship_viewer, 'set_rotation'):
            # ShipViewer3D uses static presentation, simulate rotation visually
            try:
                self.ship_viewer.hover_phase += delta * 0.1  # Visual feedback
                self.ship_viewer.update()
            except Exception as e:
                print(f"Warning: Viewer rotation change failed: {e}")
    
    def on_viewer_zoom_changed(self, factor: float):
        """Handle viewer zoom change"""
        if self.ship_viewer and hasattr(self.ship_viewer, 'set_zoom'):
            try:
                current_zoom = getattr(self.ship_viewer, 'zoom_level', 1.0)
                new_zoom = current_zoom * factor
                self.ship_viewer.set_zoom(new_zoom)
            except Exception as e:
                print(f"Warning: Viewer zoom change failed: {e}")
    
    def on_auto_rotate_toggled(self, enabled: bool):
        """Handle auto-rotate toggle"""
        if self.ship_viewer and hasattr(self.ship_viewer, 'set_auto_rotate'):
            try:
                self.ship_viewer.set_auto_rotate(enabled)
            except Exception as e:
                print(f"Warning: Auto-rotate toggle failed: {e}")
    
    def on_scanning_toggled(self):
        """Handle scanning toggle"""
        if self.ship_viewer and hasattr(self.ship_viewer, 'toggle_scanning'):
            try:
                self.ship_viewer.toggle_scanning()
            except Exception as e:
                print(f"Warning: Scanning toggle failed: {e}")
    
    def on_view_reset(self):
        """Handle view reset"""
        if self.ship_viewer and hasattr(self.ship_viewer, 'reset_view'):
            try:
                self.ship_viewer.reset_view()
            except Exception as e:
                print(f"Warning: View reset failed: {e}")
    
    def on_comparison_requested(self, ship_key: str):
        """Handle ship comparison request - disabled automatic popup"""
        # REMOVED: Automatic popup that was appearing without user request
        # Users can access ship comparison via the menu if needed
        print(f"Ship comparison requested for: {ship_key} (popup disabled for better UX)")
    
    def on_theme_changed(self, theme: ThemeColors):
        """Handle theme change"""
        apply_elite_theme(QApplication.instance(), theme)
    
    def on_hardware_button_pressed(self, button: int):
        """Handle hardware button press"""
        mapping = self.hardware_nav.button_mappings.get(button)
        
        if mapping == "gallery_prev":
            # Navigate to previous ship in gallery
            self.navigate_ship(-1)
        elif mapping == "gallery_next":
            # Navigate to next ship in gallery
            self.navigate_ship(1)
        elif mapping == "gallery_select":
            # Select current ship (could open detailed view)
            pass
        elif mapping == "viewer_rotate_left":
            self.on_viewer_rotation_changed(-15)
        elif mapping == "viewer_rotate_right":
            self.on_viewer_rotation_changed(15)
        elif mapping == "viewer_zoom_toggle":
            # Toggle between zoom levels
            if self.ship_viewer and hasattr(self.ship_viewer, 'set_zoom'):
                try:
                    current_zoom = getattr(self.ship_viewer, 'zoom_level', 1.0)
                    new_zoom = 2.0 if current_zoom < 1.5 else 1.0
                    self.ship_viewer.set_zoom(new_zoom)
                except Exception as e:
                    print(f"Warning: Zoom toggle failed: {e}")
        elif mapping == "specs_prev_tab":
            self.navigate_specs_tab(-1)
        elif mapping == "specs_next_tab":
            self.navigate_specs_tab(1)
        elif mapping == "specs_compare":
            # REMOVED: Automatic comparison popup trigger
            # Users can manually access comparisons if desired
            print("Ship comparison button pressed (popup disabled)")
        
        # Update hardware status
        self.hardware_status_label.setText(f"Hardware: Button {button}")
        QTimer.singleShot(2000, lambda: self.hardware_status_label.setText("Hardware: Connected"))
    
    def on_hardware_pot_changed(self, value: float):
        """Handle potentiometer change"""
        if self.hardware_nav.pot_mode == "theme":
            # Update theme based on potentiometer value
            if self.theme_manager:
                self.theme_manager.update_from_hardware(value)
        elif self.hardware_nav.pot_mode == "rotation" and self.ship_viewer:
            # Control ship rotation (visual effect)
            try:
                self.ship_viewer.hover_phase = value * 6.28  # 0 to 2*PI
                self.ship_viewer.update()
            except Exception as e:
                print(f"Warning: Rotation control failed: {e}")
        elif self.hardware_nav.pot_mode == "zoom" and self.ship_viewer:
            # Control viewer zoom
            try:
                zoom = 0.3 + (value * 2.7)  # 0.3 to 3.0
                self.ship_viewer.set_zoom(zoom)
            except Exception as e:
                print(f"Warning: Zoom control failed: {e}")
    
    def navigate_ship(self, direction: int):
        """Navigate to next/previous ship"""
        if not self.current_ship:
            return
        
        ships = self.ship_database.get_all_ships()
        current_index = -1
        
        for i, ship in enumerate(ships):
            if ship.name == self.current_ship.name:
                current_index = i
                break
        
        if current_index >= 0:
            new_index = (current_index + direction) % len(ships)
            new_ship = ships[new_index]
            self.set_current_ship(new_ship, animate=True)
            
            # Update gallery selection
            if self.gallery_widget:
                self.gallery_widget.select_ship(new_ship.name)
    
    def navigate_specs_tab(self, direction: int):
        """Navigate specification tabs"""
        if self.specs_panel and self.specs_panel.tabs:
            current_index = self.specs_panel.tabs.currentIndex()
            tab_count = self.specs_panel.tabs.count()
            new_index = (current_index + direction) % tab_count
            self.specs_panel.tabs.setCurrentIndex(new_index)
    
    def change_theme(self, theme_name: str):
        """Change application theme"""
        if self.theme_manager:
            self.theme_manager.set_predefined_theme(theme_name)
        
        # Update menu checkmarks
        for action in self.theme_actions:
            action.setChecked(action.text() == theme_name)
    
    def toggle_hardware_theme_control(self, enabled: bool):
        """Toggle hardware theme control"""
        if self.theme_manager:
            self.theme_manager.enable_hardware_control(enabled)
        
        status = "Enabled" if enabled else "Disabled"
        self.status_bar.showMessage(f"Hardware theme control: {status}", 3000)
    
    def set_pot_mode(self, mode: str):
        """Set potentiometer control mode"""
        if self.hardware_nav:
            self.hardware_nav.set_pot_mode(mode)
        
        self.status_bar.showMessage(f"Potentiometer mode: {mode.title()}", 3000)
    
    def export_screenshot(self):
        """Export screenshot of current view"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Screenshot", 
            f"elite_ship_{self.current_ship.name if self.current_ship else 'unknown'}.png",
            "PNG Files (*.png);;All Files (*)"
        )
        
        if filename:
            screenshot = self.grab()
            screenshot.save(filename)
            self.status_bar.showMessage(f"Screenshot saved: {filename}", 3000)
    
    def show_controls_help(self):
        """Show controls help dialog"""
        from PyQt6.QtWidgets import QMessageBox
        
        help_text = """
ELITE DANGEROUS FIDGET MODE - CONTROLS

Mouse Controls:
• Click and drag on ship viewer to rotate
• Mouse wheel to zoom in/out
• Click ship thumbnails to select

Hardware Controls (if connected):
• Button 1-3: Gallery navigation
• Button 4-6: Ship rotation and zoom
• Button 7-9: Specification tabs
• Potentiometer: Theme/rotation/zoom (configurable)

Keyboard Shortcuts:
• Ctrl+S: Export screenshot
• Ctrl+Q: Exit application

Navigation:
• Use ship gallery to browse collection
• Detailed specifications in right panel
• 3D viewer shows ship with technical overlays
        """
        
        QMessageBox.information(self, "Controls Help", help_text)
    
    def show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        
        about_text = f"""
ELITE DANGEROUS SHIP DATABASE FIDGET MODE

A comprehensive interactive ship browser for Elite Dangerous.

Features:
• {self.ship_database.get_ship_count()} detailed ship specifications
• 3D-style ship viewer with technical overlays
• Hardware integration for immersive control
• Dynamic theme system with Elite aesthetic
• Optimized for 1024x768 displays

Built with PyQt6 and optimized for 60fps performance.

Version 1.0 - Elite Dangerous Community Tool
        """
        
        QMessageBox.about(self, "About Elite Ship Database", about_text)
    
    def update_performance_metrics(self):
        """Update performance metrics display"""
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        
        if elapsed > 0:
            fps = self.fps_counter / elapsed
            self.fps_label.setText(f"FPS: {fps:.1f}")
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    def paintEvent(self, event):
        """Override paint event for FPS counting"""
        super().paintEvent(event)
        self.fps_counter += 1
    
    def safe_update_performance_metrics(self):
        """Safely update performance metrics"""
        if self._is_destroyed or self._cleanup_performed:
            return
        try:
            self.update_performance_metrics()
        except Exception as e:
            print(f"Performance metrics update error: {e}")
    
    def cleanup_resources(self):
        """Critical cleanup method to prevent segmentation faults"""
        if self._cleanup_performed or self._cleanup_in_progress:
            return
        
        print("EliteFidgetMode: Starting comprehensive cleanup...")
        self._cleanup_in_progress = True
        self._is_destroyed = True
        
        try:
            # Stop FPS timer first
            if hasattr(self, 'fps_timer') and self.fps_timer:
                self.fps_timer.stop()
                self.fps_timer.timeout.disconnect()
                self.fps_timer.deleteLater()
                self.fps_timer = None
            
            # Cleanup animation objects
            if hasattr(self, 'ship_transition_anim') and self.ship_transition_anim:
                self.ship_transition_anim.stop()
                self.ship_transition_anim = None
            
            # Cleanup UI components in reverse order
            if self.ship_viewer and hasattr(self.ship_viewer, 'cleanup_resources'):
                self.ship_viewer.cleanup_resources()
            
            if self.viewer_controls and hasattr(self.viewer_controls, 'cleanup_resources'):
                self.viewer_controls.cleanup_resources()
            
            if self.specs_panel and hasattr(self.specs_panel, 'cleanup_resources'):
                try:
                    self.specs_panel.cleanup_resources()
                except AttributeError:
                    pass  # May not have cleanup method
            
            if self.gallery_widget and hasattr(self.gallery_widget, 'cleanup_resources'):
                try:
                    self.gallery_widget.cleanup_resources()
                except AttributeError:
                    pass  # May not have cleanup method
            
            # Cleanup managers
            if self.transition_manager and hasattr(self.transition_manager, 'cleanup_resources'):
                self.transition_manager.cleanup_resources()
            
            if self.hardware_nav and hasattr(self.hardware_nav, 'cleanup_resources'):
                self.hardware_nav.cleanup_resources()
            
            # Clear references
            self.ship_database = None
            self.current_ship = None
            self.theme_manager = None
            self.hardware_nav = None
            self.transition_manager = None
            
            self.gallery_widget = None
            self.ship_viewer = None
            self.viewer_controls = None
            self.specs_panel = None
            
            self._cleanup_performed = True
            print("EliteFidgetMode: Cleanup completed successfully")
            
        except Exception as e:
            print(f"Error during EliteFidgetMode cleanup: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._cleanup_in_progress = False
    
    def closeEvent(self, event):
        """Handle window close event with proper cleanup"""
        print("EliteFidgetMode: Close event received, performing cleanup...")
        self.cleanup_resources()
        event.accept()
    
    def __del__(self):
        """Destructor with cleanup"""
        try:
            self.cleanup_resources()
        except Exception:
            pass


def main():
    """Main function to run Elite Fidget Mode with comprehensive error handling"""
    window = None
    app = None
    
    try:
        # Check if QApplication already exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Set up application cleanup handler
        app.aboutToQuit.connect(lambda: cleanup_application(window))
        
        # Set application properties
        try:
            app.setApplicationName("Elite Dangerous Fidget Mode")
            app.setApplicationVersion("1.0")
            app.setOrganizationName("Elite Dangerous Community")
            
            # Set application font
            font = QFont("Segoe UI", 9)
            app.setFont(font)
        except Exception as e:
            print(f"Warning: Could not set application properties: {e}")
        
        # Create main window with error handling
        try:
            print("Creating EliteFidgetMode window...")
            window = EliteFidgetMode()
            print("Window created successfully")
            
            # Show window
            window.show()
            print("Window shown")
            
            # Force window update
            window.update()
            app.processEvents()
            
        except Exception as e:
            print(f"Critical error creating main window: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to create a minimal error window
            try:
                from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
                error_window = QMainWindow()
                error_window.setWindowTitle("Elite Fidget Mode - Error")
                error_widget = QWidget()
                error_layout = QVBoxLayout(error_widget)
                error_layout.addWidget(QLabel(f"Failed to initialize Elite Fidget Mode:\n\n{str(e)}"))
                error_window.setCentralWidget(error_widget)
                error_window.resize(500, 200)
                error_window.show()
                window = error_window
            except:
                return 1
        
        # Run event loop
        return app.exec()
        
    except Exception as e:
        print(f"Fatal error in main(): {e}")
        import traceback
        traceback.print_exc()
        return 1


def cleanup_application(window):
    """Global cleanup function for application shutdown"""
    if window and hasattr(window, 'cleanup_resources'):
        try:
            window.cleanup_resources()
        except Exception as e:
            print(f"Error during global cleanup: {e}")


if __name__ == "__main__":
    sys.exit(main())