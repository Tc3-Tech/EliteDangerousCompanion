"""
Elite Dangerous UI Examples Launcher
Demonstrates all the UI examples with theme switching and window management.
"""
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QTabWidget, QSplitter,
                           QListWidget, QListWidgetItem, QTextEdit, QLabel,
                           QStatusBar, QMenuBar, QMenu)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction, QDesktopServices
from PyQt6.QtCore import QUrl
import importlib.util
import subprocess

# Add the parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from elite_widgets import (ElitePanel, EliteLabel, EliteButton, EliteProgressBar, 
                          apply_elite_theme)
from config.themes import ThemeManager, PredefinedThemes


class ExampleInfo:
    """Information about an example application"""
    
    def __init__(self, name, description, file_path, preview_image=None, 
                 features=None, difficulty="Beginner"):
        self.name = name
        self.description = description
        self.file_path = file_path
        self.preview_image = preview_image
        self.features = features or []
        self.difficulty = difficulty
        self.is_running = False
        self.process = None


class ExampleGallery(ElitePanel):
    """Gallery showing all available UI examples"""
    
    example_selected = pyqtSignal(ExampleInfo)
    launch_requested = pyqtSignal(ExampleInfo)
    
    def __init__(self, parent=None):
        super().__init__("UI EXAMPLES GALLERY", parent)
        self.examples = []
        self.setup_gallery_ui()
        self.load_examples()
    
    def setup_gallery_ui(self):
        """Setup gallery UI"""
        # Search/filter bar
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(EliteLabel("FILTER:", "small"))
        
        self.filter_buttons = []
        categories = ["ALL", "DASHBOARD", "SHIP", "EXPLORATION", "MEDIA", "SETTINGS"]
        
        for category in categories:
            filter_btn = EliteButton(category)
            filter_btn.setCheckable(True)
            filter_btn.clicked.connect(lambda checked, cat=category: self.filter_examples(cat))
            filter_layout.addWidget(filter_btn)
            self.filter_buttons.append(filter_btn)
        
        # Set "ALL" as default
        self.filter_buttons[0].setChecked(True)
        
        self.add_layout(filter_layout)
        
        # Examples list
        self.examples_list = QListWidget()
        self.examples_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.examples_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.add_widget(self.examples_list)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.launch_btn = EliteButton("LAUNCH EXAMPLE")
        self.launch_btn.setEnabled(False)
        self.launch_btn.clicked.connect(self.launch_selected_example)
        actions_layout.addWidget(self.launch_btn)
        
        self.view_code_btn = EliteButton("VIEW SOURCE")
        self.view_code_btn.setEnabled(False)
        self.view_code_btn.clicked.connect(self.view_source_code)
        actions_layout.addWidget(self.view_code_btn)
        
        self.add_layout(actions_layout)
    
    def load_examples(self):
        """Load all available examples"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.examples = [
            ExampleInfo(
                name="Main Dashboard",
                description="Comprehensive dashboard showing commander status, ship health, system information, and mission tracking with real-time HUD visualization.",
                file_path=os.path.join(current_dir, "elite_dashboard.py"),
                features=[
                    "Real-time HUD display with crosshair and scan lines",
                    "Commander status and credit tracking",
                    "Ship health monitoring with damage simulation",
                    "System information display",
                    "Mission tracking with progress bars",
                    "Dynamic ship visualization",
                    "Theme switching capabilities"
                ],
                difficulty="Intermediate"
            ),
            ExampleInfo(
                name="Ship Details Panel",
                description="Detailed ship information with 3D visualization, technical specifications, loadout management, and power distribution controls.",
                file_path=os.path.join(current_dir, "ship_details.py"),
                features=[
                    "3D ship viewer with rotation and hover effects",
                    "Tabbed specification display",
                    "Complete loadout tree view",
                    "Interactive power management (SYS/ENG/WEP)",
                    "Technical overlay with scan lines",
                    "Ship asset integration",
                    "Modular loadout system"
                ],
                difficulty="Advanced"
            ),
            ExampleInfo(
                name="System Exploration",
                description="Interactive star system map with clickable celestial bodies, discovery tracking, and detailed planetary information.",
                file_path=os.path.join(current_dir, "exploration_display.py"),
                features=[
                    "Interactive system map with zoom and pan",
                    "Clickable planetary bodies",
                    "Realistic orbital mechanics simulation",
                    "Discovery and mapping status tracking",
                    "Detailed body information panels",
                    "Exploration statistics",
                    "Scanning simulation"
                ],
                difficulty="Advanced"
            ),
            ExampleInfo(
                name="Media Control Interface",
                description="Spotify/media control with audio visualization, playlist management, and advanced equalizer controls.",
                file_path=os.path.join(current_dir, "media_control.py"),
                features=[
                    "Real-time audio spectrum visualizer",
                    "Multi-source playlist support",
                    "10-band graphic equalizer",
                    "Audio effects controls",
                    "Transport controls with progress tracking",
                    "Volume management",
                    "EQ presets"
                ],
                difficulty="Intermediate"
            ),
            ExampleInfo(
                name="Settings & Theme Editor",
                description="Comprehensive settings panel with live theme customization, HSV color controls, and application preferences.",
                file_path=os.path.join(current_dir, "settings_panel.py"),
                features=[
                    "Live theme preview",
                    "Custom color picker components",
                    "HSV color space controls",
                    "Predefined theme selection",
                    "Application settings management",
                    "Theme import/export",
                    "Real-time preview updates"
                ],
                difficulty="Advanced"
            )
        ]
        
        # Validate example file paths
        self.validate_example_files()
        
        self.populate_examples_list()
    
    def validate_example_files(self):
        """Validate that all example files exist"""
        valid_examples = []
        for example in self.examples:
            if os.path.exists(example.file_path):
                valid_examples.append(example)
            else:
                print(f"Warning: Example file not found: {example.file_path}")
        
        self.examples = valid_examples
    
    def populate_examples_list(self):
        """Populate the examples list"""
        self.examples_list.clear()
        
        for example in self.examples:
            item = QListWidgetItem()
            item.setText(f"{example.name} - {example.difficulty}")
            item.setData(Qt.ItemDataRole.UserRole, example)
            
            # Add status indicator if running
            if example.is_running:
                item.setText(f"{example.name} - {example.difficulty} [RUNNING]")
            
            self.examples_list.addItem(item)
    
    def filter_examples(self, category: str):
        """Filter examples by category"""
        # Uncheck other filter buttons
        for btn in self.filter_buttons:
            if btn.text() != category:
                btn.setChecked(False)
        
        # For now, just show all examples (filtering logic can be added later)
        self.populate_examples_list()
    
    def on_selection_changed(self):
        """Handle example selection change"""
        current_item = self.examples_list.currentItem()
        if current_item:
            example = current_item.data(Qt.ItemDataRole.UserRole)
            self.launch_btn.setEnabled(True)
            self.view_code_btn.setEnabled(True)
            self.example_selected.emit(example)
        else:
            self.launch_btn.setEnabled(False)
            self.view_code_btn.setEnabled(False)
    
    def on_item_double_clicked(self, item):
        """Handle double-click to launch example"""
        example = item.data(Qt.ItemDataRole.UserRole)
        if example:
            self.launch_requested.emit(example)
    
    def launch_selected_example(self):
        """Launch the currently selected example"""
        current_item = self.examples_list.currentItem()
        if current_item:
            example = current_item.data(Qt.ItemDataRole.UserRole)
            self.launch_requested.emit(example)
    
    def view_source_code(self):
        """Open source code in default editor"""
        current_item = self.examples_list.currentItem()
        if current_item:
            example = current_item.data(Qt.ItemDataRole.UserRole)
            if os.path.exists(example.file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(example.file_path))


class ExampleDetails(ElitePanel):
    """Panel showing detailed information about selected example"""
    
    def __init__(self, parent=None):
        super().__init__("EXAMPLE DETAILS", parent)
        self.current_example = None
        self.setup_details_ui()
    
    def setup_details_ui(self):
        """Setup details UI"""
        # Initially show "No example selected" message
        self.no_selection_label = EliteLabel("SELECT AN EXAMPLE TO VIEW DETAILS", "header")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.add_widget(self.no_selection_label)
        
        # Details container (initially hidden)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_widget.hide()
        self.add_widget(self.details_widget)
    
    def clear_details_layout(self):
        """Safely clear all widgets from the details layout"""
        try:
            while self.details_layout.count():
                item = self.details_layout.takeAt(0)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
                        widget.deleteLater()
        except Exception as e:
            print(f"Error clearing details layout: {e}")
    
    def show_example_details(self, example: ExampleInfo):
        """Show details for the selected example"""
        try:
            self.current_example = example
            
            # Hide no selection message and show details
            self.no_selection_label.hide()
            self.details_widget.show()
            
            # Clear previous details safely
            self.clear_details_layout()
            
            # Example name
            name_label = EliteLabel(example.name.upper(), "header")
            self.details_layout.addWidget(name_label)
            
            # Difficulty level
            difficulty_layout = QHBoxLayout()
            difficulty_layout.addWidget(EliteLabel("DIFFICULTY:", "small"))
            difficulty_label = EliteLabel(example.difficulty.upper(), "value")
            
            # Color code difficulty
            if example.difficulty == "Beginner":
                difficulty_label.setStyleSheet("color: #00FF00;")
            elif example.difficulty == "Intermediate":
                difficulty_label.setStyleSheet("color: #FFFF00;")
            else:  # Advanced
                difficulty_label.setStyleSheet("color: #FF4444;")
            
            difficulty_layout.addWidget(difficulty_label)
            difficulty_layout.addStretch()
            self.details_layout.addLayout(difficulty_layout)
            
            # Description
            desc_label = EliteLabel("DESCRIPTION:", "small")
            self.details_layout.addWidget(desc_label)
            
            desc_text = QTextEdit()
            desc_text.setPlainText(example.description)
            desc_text.setMaximumHeight(80)
            desc_text.setReadOnly(True)
            self.details_layout.addWidget(desc_text)
            
            # Features list
            if example.features:
                features_label = EliteLabel("KEY FEATURES:", "small")
                self.details_layout.addWidget(features_label)
                
                for feature in example.features:
                    feature_item = EliteLabel(f"• {feature}", "small")
                    feature_item.setWordWrap(True)
                    self.details_layout.addWidget(feature_item)
            
            # File path
            path_layout = QHBoxLayout()
            path_layout.addWidget(EliteLabel("SOURCE FILE:", "small"))
            path_label = EliteLabel(os.path.basename(example.file_path), "value")
            path_layout.addWidget(path_label)
            path_layout.addStretch()
            self.details_layout.addLayout(path_layout)
            
            # Status
            status_layout = QHBoxLayout()
            status_layout.addWidget(EliteLabel("STATUS:", "small"))
            status_text = "RUNNING" if example.is_running else "READY"
            status_color = "#00FF00" if example.is_running else "#FFFF00"
            status_label = EliteLabel(status_text, "value")
            status_label.setStyleSheet(f"color: {status_color};")
            status_layout.addWidget(status_label)
            status_layout.addStretch()
            self.details_layout.addLayout(status_layout)
            
            self.details_layout.addStretch()
            
        except Exception as e:
            print(f"Error showing example details: {e}")


class ThemeSelector(ElitePanel):
    """Panel for quick theme switching"""
    
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__("THEME SELECTOR", parent)
        self.theme_manager = ThemeManager()
        self.setup_theme_ui()
    
    def setup_theme_ui(self):
        """Setup theme selector UI"""
        # Current theme display
        current_layout = QHBoxLayout()
        current_layout.addWidget(EliteLabel("CURRENT THEME:", "small"))
        self.current_theme_label = EliteLabel("ICE BLUE", "value")
        current_layout.addWidget(self.current_theme_label)
        current_layout.addStretch()
        self.add_layout(current_layout)
        
        # Theme buttons grid
        themes_grid = QGridLayout()
        
        themes = [
            ("ICE BLUE", "Ice Blue"),
            ("MATRIX GREEN", "Matrix Green"),
            ("DEEP PURPLE", "Deep Purple"),
            ("PLASMA PINK", "Plasma Pink"),
            ("ARCTIC WHITE", "Arctic White"),
            ("EMBER RED", "Ember Red")
        ]
        
        for i, (display_name, theme_name) in enumerate(themes):
            theme_btn = EliteButton(display_name)
            theme_btn.clicked.connect(lambda checked, t=theme_name, d=display_name: 
                                    self.apply_selected_theme(t, d))
            themes_grid.addWidget(theme_btn, i // 2, i % 2)
        
        self.add_layout(themes_grid)
        
        # Launch settings button
        settings_btn = EliteButton("ADVANCED THEME EDITOR")
        settings_btn.clicked.connect(self.launch_theme_editor)
        self.add_widget(settings_btn)
    
    def apply_selected_theme(self, theme_name: str, display_name: str):
        """Apply selected theme from UI button"""
        self.theme_manager.set_predefined_theme(theme_name)
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
        self.current_theme_label.setText(display_name)
        self.theme_changed.emit(theme_name)
        
        # Force refresh of all widgets
        for widget in QApplication.instance().allWidgets():
            widget.update()
    
    def launch_theme_editor(self):
        """Launch the theme editor"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            settings_path = os.path.join(current_dir, "settings_panel.py")
            subprocess.Popen([sys.executable, settings_path])
        except Exception as e:
            print(f"Failed to launch theme editor: {e}")


class ExampleLauncherWindow(QMainWindow):
    """Main Example Launcher Window"""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.running_processes = []
        self.setup_window()
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Apply initial theme
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
        
        # Timer to check running processes
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self.check_running_processes)
        self.process_timer.start(2000)  # Check every 2 seconds
    
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("Elite Dangerous - UI Examples Launcher")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # Set window icon if available
        icon_path = "/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets/sidewinder.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Left side - Examples gallery
        self.gallery = ExampleGallery()
        self.gallery.example_selected.connect(self.on_example_selected)
        self.gallery.launch_requested.connect(self.launch_example)
        main_layout.addWidget(self.gallery, 2)
        
        # Right side - Details and theme selector
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Example details
        self.example_details = ExampleDetails()
        right_splitter.addWidget(self.example_details)
        
        # Theme selector
        self.theme_selector = ThemeSelector()
        self.theme_selector.theme_changed.connect(self.on_theme_changed)
        right_splitter.addWidget(self.theme_selector)
        
        # Set splitter proportions
        right_splitter.setSizes([400, 200])
        
        main_layout.addWidget(right_splitter, 1)
    
    def setup_menu(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        launch_all_action = QAction("&Launch All Examples", self)
        launch_all_action.triggered.connect(self.launch_all_examples)
        file_menu.addAction(launch_all_action)
        
        close_all_action = QAction("&Close All Examples", self)
        close_all_action.triggered.connect(self.close_all_examples)
        file_menu.addAction(close_all_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        refresh_action = QAction("&Refresh Examples", self)
        refresh_action.triggered.connect(self.refresh_examples)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_bar.showMessage("Elite Dangerous UI Examples - Ready to launch")
        
        # Add permanent widgets
        self.running_count_label = QLabel("Running: 0")
        self.status_bar.addPermanentWidget(self.running_count_label)
    
    def on_example_selected(self, example: ExampleInfo):
        """Handle example selection"""
        self.example_details.show_example_details(example)
        self.status_bar.showMessage(f"Selected: {example.name}")
    
    def launch_example(self, example: ExampleInfo):
        """Launch an example application"""
        if example.is_running:
            self.status_bar.showMessage(f"{example.name} is already running")
            return
        
        try:
            # Check if file exists before launching
            if not os.path.exists(example.file_path):
                self.status_bar.showMessage(f"Example file not found: {example.name}")
                return
                
            # Launch the example in a separate process
            process = subprocess.Popen([sys.executable, example.file_path])
            example.process = process
            example.is_running = True
            self.running_processes.append(example)
            
            self.gallery.populate_examples_list()
            self.update_running_count()
            self.status_bar.showMessage(f"Launched: {example.name}")
            
        except Exception as e:
            self.status_bar.showMessage(f"Failed to launch {example.name}: {str(e)}")
    
    def launch_all_examples(self):
        """Launch all available examples"""
        for example in self.gallery.examples:
            if not example.is_running:
                self.launch_example(example)
    
    def close_all_examples(self):
        """Close all running examples"""
        for example in self.running_processes[:]:  # Copy list to avoid modification during iteration
            if example.process and example.process.poll() is None:
                example.process.terminate()
            example.is_running = False
            example.process = None
        
        self.running_processes.clear()
        self.gallery.populate_examples_list()
        self.update_running_count()
        self.status_bar.showMessage("All examples closed")
    
    def check_running_processes(self):
        """Check status of running processes"""
        try:
            for example in self.running_processes[:]:  # Copy list
                if example.process and example.process.poll() is not None:
                    # Process has terminated
                    example.is_running = False
                    example.process = None
                    self.running_processes.remove(example)
            
            self.gallery.populate_examples_list()
            self.update_running_count()
        except Exception as e:
            print(f"Error checking running processes: {e}")
    
    def update_running_count(self):
        """Update running process count in status bar"""
        count = len(self.running_processes)
        self.running_count_label.setText(f"Running: {count}")
    
    def refresh_examples(self):
        """Refresh the examples list"""
        self.gallery.load_examples()
        self.status_bar.showMessage("Examples list refreshed")
    
    def on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        self.status_bar.showMessage(f"Applied theme: {theme_name}")
    
    def show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        
        about_text = """
        <h3>Elite Dangerous UI Examples</h3>
        <p>A collection of PyQt6 UI examples showcasing the Elite Dangerous aesthetic.</p>
        
        <p><b>Features:</b></p>
        <ul>
        <li>Authentic Elite Dangerous theming</li>
        <li>Customizable color schemes</li>
        <li>Real-time visualizations</li>
        <li>Interactive components</li>
        <li>1024x768 secondary display optimization</li>
        </ul>
        
        <p><b>Examples Include:</b></p>
        <ul>
        <li>Main Dashboard with HUD</li>
        <li>Ship Details with 3D viewer</li>
        <li>System Exploration map</li>
        <li>Media Control interface</li>
        <li>Settings & Theme editor</li>
        </ul>
        """
        
        QMessageBox.about(self, "About Elite Dangerous UI Examples", about_text)
    
    def closeEvent(self, event):
        """Handle application close"""
        # Close all running examples
        self.close_all_examples()
        event.accept()


def main():
    """Main function to run the Example Launcher"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Elite Dangerous UI Examples")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Elite Dangerous Companion")
    
    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show launcher window
    launcher = ExampleLauncherWindow()
    launcher.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())