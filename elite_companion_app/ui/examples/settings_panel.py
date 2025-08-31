"""
Elite Dangerous Settings and Theme Customization Panel
Real-time theme preview and application settings management.
"""
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QTabWidget, QSlider, 
                           QColorDialog, QComboBox, QSpinBox, QCheckBox,
                           QButtonGroup, QRadioButton, QGroupBox, QSplitter,
                           QScrollArea, QTextEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QPainter, QPen, QBrush, QFont, QColor, QLinearGradient, QPixmap
import colorsys

# Add the parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from elite_widgets import (ElitePanel, EliteLabel, EliteButton, EliteProgressBar, 
                          apply_elite_theme)
from config.themes import ThemeManager, PredefinedThemes, ThemeColors


class ColorPicker(EliteButton):
    """Custom color picker button with Elite styling"""
    
    color_changed = pyqtSignal(QColor)
    
    def __init__(self, initial_color: QColor = QColor(255, 255, 255), parent=None):
        super().__init__("", parent)
        self.current_color = initial_color
        self.setMinimumSize(60, 30)
        self.clicked.connect(self.pick_color)
        self.update_appearance()
    
    def update_appearance(self):
        """Update button appearance to show current color"""
        color_hex = self.current_color.name()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 2px solid #ffffff;
                color: {'#000000' if self.current_color.lightness() > 128 else '#ffffff'};
            }}
        """)
        self.setText(color_hex.upper())
    
    def pick_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(self.current_color, self, "Select Color")
        if color.isValid():
            self.current_color = color
            self.update_appearance()
            self.color_changed.emit(color)
    
    def set_color(self, color: QColor):
        """Set color programmatically"""
        self.current_color = color
        self.update_appearance()


class ThemePreview(QWidget):
    """Widget showing a preview of the current theme"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 200)
        self.current_theme = None
    
    def set_theme(self, theme: ThemeColors):
        """Set the theme to preview"""
        self.current_theme = theme
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for theme preview"""
        if not self.current_theme:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        colors = self.current_theme.to_dict()
        
        # Background
        painter.fillRect(self.rect(), QColor(colors['background']))
        
        # Panel frame
        panel_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(QPen(QColor(colors['border']), 2))
        painter.setBrush(QBrush(QColor(colors['surface'])))
        painter.drawRoundedRect(panel_rect, 5, 5)
        
        # Title bar
        title_rect = panel_rect.adjusted(5, 5, -5, -panel_rect.height() + 30)
        gradient = QLinearGradient(title_rect.topLeft(), title_rect.bottomLeft())
        gradient.setColorAt(0, QColor(colors['primary']))
        gradient.setColorAt(1, QColor(colors['secondary']))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(title_rect, 3, 3)
        
        # Title text
        painter.setPen(QPen(QColor(colors['background']), 1))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, "PREVIEW PANEL")
        
        # Sample text
        text_y = 60
        painter.setPen(QPen(QColor(colors['text']), 1))
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.drawText(20, text_y, "Primary Text")
        
        painter.setPen(QPen(QColor(colors['text_secondary']), 1))
        painter.drawText(20, text_y + 20, "Secondary Text")
        
        # Sample progress bar
        progress_rect = panel_rect.adjusted(15, 90, -15, -90)
        painter.setPen(QPen(QColor(colors['border']), 1))
        painter.setBrush(QBrush(QColor(colors['background'])))
        painter.drawRect(progress_rect)
        
        # Progress fill
        fill_rect = progress_rect.adjusted(2, 2, -progress_rect.width()//2, -2)
        progress_gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
        progress_gradient.setColorAt(0, QColor(colors['primary']))
        progress_gradient.setColorAt(1, QColor(colors['accent']))
        painter.setBrush(QBrush(progress_gradient))
        painter.drawRect(fill_rect)
        
        # Sample button
        button_rect = panel_rect.adjusted(15, 120, -15, -60)
        button_rect.setHeight(25)
        
        button_gradient = QLinearGradient(button_rect.topLeft(), button_rect.bottomLeft())
        button_gradient.setColorAt(0, QColor(colors['primary']))
        button_gradient.setColorAt(1, QColor(colors['secondary']))
        painter.setBrush(QBrush(button_gradient))
        painter.setPen(QPen(QColor(colors['primary']), 2))
        painter.drawRoundedRect(button_rect, 3, 3)
        
        painter.setPen(QPen(QColor(colors['background']), 1))
        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(button_rect, Qt.AlignmentFlag.AlignCenter, "SAMPLE BUTTON")


class CustomThemeEditor(ElitePanel):
    """Panel for creating custom themes"""
    
    theme_changed = pyqtSignal(ThemeColors)
    
    def __init__(self, parent=None):
        super().__init__("CUSTOM THEME EDITOR", parent)
        self.custom_theme = ThemeColors(
            primary="#00D4FF",
            secondary="#0099CC",
            accent="#40E0FF",
            background="#0A0F1A",
            surface="#152030",
            text="#E0F8FF",
            text_secondary="#B0D4E8",
            border="#0099CC",
            success="#00FF88",
            warning="#FFD700",
            error="#FF4444"
        )
        self.setup_editor_ui()
    
    def setup_editor_ui(self):
        """Setup custom theme editor UI"""
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        
        # Quick presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(EliteLabel("QUICK START:", "small"))
        
        quick_presets = [
            ("BLUE", 210),
            ("GREEN", 120),
            ("PURPLE", 270),
            ("RED", 0),
            ("ORANGE", 30),
            ("CYAN", 180)
        ]
        
        for name, hue in quick_presets:
            preset_btn = EliteButton(name)
            preset_btn.clicked.connect(lambda checked, h=hue: self.generate_theme_from_hue(h))
            presets_layout.addWidget(preset_btn)
        
        layout.addLayout(presets_layout)
        
        # Color pickers for each theme element
        colors_grid = QGridLayout()
        
        self.color_pickers = {}
        color_definitions = [
            ("primary", "Primary Color", "Main UI elements"),
            ("secondary", "Secondary Color", "Darker variant of primary"),
            ("accent", "Accent Color", "Highlights and focus"),
            ("background", "Background", "Window background"),
            ("surface", "Surface", "Panel backgrounds"),
            ("text", "Text Color", "Primary text"),
            ("text_secondary", "Secondary Text", "Dimmed text"),
            ("border", "Border Color", "Borders and dividers"),
            ("success", "Success Color", "Success states"),
            ("warning", "Warning Color", "Warning states"),
            ("error", "Error Color", "Error states")
        ]
        
        for i, (key, display_name, description) in enumerate(color_definitions):
            # Color name
            name_label = EliteLabel(display_name, "small")
            colors_grid.addWidget(name_label, i, 0)
            
            # Color picker
            initial_color = QColor(getattr(self.custom_theme, key))
            color_picker = ColorPicker(initial_color)
            color_picker.color_changed.connect(lambda color, k=key: self.on_color_changed(k, color))
            self.color_pickers[key] = color_picker
            colors_grid.addWidget(color_picker, i, 1)
            
            # Description
            desc_label = EliteLabel(description, "small")
            desc_label.setStyleSheet("color: gray;")
            colors_grid.addWidget(desc_label, i, 2)
        
        layout.addLayout(colors_grid)
        
        # HSV Controls for primary color
        hsv_group = QGroupBox("PRIMARY COLOR HSV CONTROLS")
        hsv_layout = QGridLayout(hsv_group)
        
        # Hue slider
        hsv_layout.addWidget(EliteLabel("HUE:", "small"), 0, 0)
        self.hue_slider = QSlider(Qt.Orientation.Horizontal)
        self.hue_slider.setRange(0, 360)
        self.hue_slider.setValue(210)
        self.hue_slider.valueChanged.connect(self.on_hsv_changed)
        hsv_layout.addWidget(self.hue_slider, 0, 1)
        
        self.hue_label = EliteLabel("210°", "small")
        hsv_layout.addWidget(self.hue_label, 0, 2)
        
        # Saturation slider
        hsv_layout.addWidget(EliteLabel("SATURATION:", "small"), 1, 0)
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setRange(0, 100)
        self.saturation_slider.setValue(80)
        self.saturation_slider.valueChanged.connect(self.on_hsv_changed)
        hsv_layout.addWidget(self.saturation_slider, 1, 1)
        
        self.saturation_label = EliteLabel("80%", "small")
        hsv_layout.addWidget(self.saturation_label, 1, 2)
        
        # Value/Brightness slider
        hsv_layout.addWidget(EliteLabel("BRIGHTNESS:", "small"), 2, 0)
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(90)
        self.brightness_slider.valueChanged.connect(self.on_hsv_changed)
        hsv_layout.addWidget(self.brightness_slider, 2, 1)
        
        self.brightness_label = EliteLabel("90%", "small")
        hsv_layout.addWidget(self.brightness_label, 2, 2)
        
        layout.addWidget(hsv_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        save_btn = EliteButton("SAVE THEME")
        save_btn.clicked.connect(self.save_theme)
        actions_layout.addWidget(save_btn)
        
        load_btn = EliteButton("LOAD THEME")
        load_btn.clicked.connect(self.load_theme)
        actions_layout.addWidget(load_btn)
        
        reset_btn = EliteButton("RESET")
        reset_btn.clicked.connect(self.reset_theme)
        actions_layout.addWidget(reset_btn)
        
        layout.addLayout(actions_layout)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.add_widget(scroll_area)
    
    def generate_theme_from_hue(self, hue: int):
        """Generate a theme from a base hue"""
        self.hue_slider.setValue(hue)
        self.on_hsv_changed()
    
    def on_hsv_changed(self):
        """Handle HSV slider changes"""
        hue = self.hue_slider.value()
        saturation = self.saturation_slider.value() / 100.0
        brightness = self.brightness_slider.value() / 100.0
        
        # Update labels
        self.hue_label.setText(f"{hue}°")
        self.saturation_label.setText(f"{int(saturation * 100)}%")
        self.brightness_label.setText(f"{int(brightness * 100)}%")
        
        # Generate new theme
        r, g, b = colorsys.hsv_to_rgb(hue / 360.0, saturation, brightness)
        primary_color = QColor(int(r * 255), int(g * 255), int(b * 255))
        
        # Update primary color picker
        self.color_pickers['primary'].set_color(primary_color)
        
        # Generate complementary colors
        secondary_r, secondary_g, secondary_b = colorsys.hsv_to_rgb(hue / 360.0, saturation, brightness * 0.7)
        secondary_color = QColor(int(secondary_r * 255), int(secondary_g * 255), int(secondary_b * 255))
        self.color_pickers['secondary'].set_color(secondary_color)
        
        accent_r, accent_g, accent_b = colorsys.hsv_to_rgb(hue / 360.0, saturation * 0.6, brightness)
        accent_color = QColor(int(accent_r * 255), int(accent_g * 255), int(accent_b * 255))
        self.color_pickers['accent'].set_color(accent_color)
        
        border_color = secondary_color
        self.color_pickers['border'].set_color(border_color)
        
        text_brightness = 0.95 if brightness < 0.5 else 0.95
        text_r, text_g, text_b = colorsys.hsv_to_rgb(hue / 360.0, saturation * 0.2, text_brightness)
        text_color = QColor(int(text_r * 255), int(text_g * 255), int(text_b * 255))
        self.color_pickers['text'].set_color(text_color)
        
        text_secondary_color = secondary_color.lighter() if brightness < 0.5 else secondary_color.darker()
        self.color_pickers['text_secondary'].set_color(text_secondary_color)
        
        # Update custom theme
        self.update_custom_theme()
    
    def on_color_changed(self, color_key: str, color: QColor):
        """Handle individual color changes"""
        setattr(self.custom_theme, color_key, color.name())
        self.theme_changed.emit(self.custom_theme)
    
    def update_custom_theme(self):
        """Update custom theme from all color pickers"""
        for key, picker in self.color_pickers.items():
            setattr(self.custom_theme, key, picker.current_color.name())
        
        self.theme_changed.emit(self.custom_theme)
    
    def save_theme(self):
        """Save current theme to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Theme", "", "Theme Files (*.theme);;All Files (*)"
        )
        if filename:
            # Implementation would save theme data
            QMessageBox.information(self, "Theme Saved", f"Theme saved to {filename}")
    
    def load_theme(self):
        """Load theme from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Theme", "", "Theme Files (*.theme);;All Files (*)"
        )
        if filename:
            # Implementation would load theme data
            QMessageBox.information(self, "Theme Loaded", f"Theme loaded from {filename}")
    
    def reset_theme(self):
        """Reset theme to defaults"""
        self.custom_theme = ThemeColors(
            primary="#00D4FF",
            secondary="#0099CC",
            accent="#40E0FF",
            background="#0A0F1A",
            surface="#152030",
            text="#E0F8FF",
            text_secondary="#B0D4E8",
            border="#0099CC",
            success="#00FF88",
            warning="#FFD700",
            error="#FF4444"
        )
        
        # Update all color pickers
        for key, picker in self.color_pickers.items():
            color = QColor(getattr(self.custom_theme, key))
            picker.set_color(color)
        
        self.theme_changed.emit(self.custom_theme)


class ApplicationSettings(ElitePanel):
    """Panel for general application settings"""
    
    def __init__(self, parent=None):
        super().__init__("APPLICATION SETTINGS", parent)
        self.setup_settings_ui()
    
    def setup_settings_ui(self):
        """Setup application settings UI"""
        # Display settings
        display_group = QGroupBox("DISPLAY SETTINGS")
        display_layout = QGridLayout(display_group)
        
        # Window mode
        display_layout.addWidget(EliteLabel("WINDOW MODE:", "small"), 0, 0)
        window_mode_combo = QComboBox()
        window_mode_combo.addItems(["Windowed", "Fullscreen", "Borderless"])
        display_layout.addWidget(window_mode_combo, 0, 1)
        
        # Resolution
        display_layout.addWidget(EliteLabel("RESOLUTION:", "small"), 1, 0)
        resolution_combo = QComboBox()
        resolution_combo.addItems(["1024x768", "1280x720", "1366x768", "1920x1080"])
        resolution_combo.setCurrentText("1024x768")
        display_layout.addWidget(resolution_combo, 1, 1)
        
        # Always on top
        always_on_top = QCheckBox("ALWAYS ON TOP")
        always_on_top.setChecked(True)
        display_layout.addWidget(always_on_top, 2, 0, 1, 2)
        
        # Transparency
        display_layout.addWidget(EliteLabel("TRANSPARENCY:", "small"), 3, 0)
        transparency_slider = QSlider(Qt.Orientation.Horizontal)
        transparency_slider.setRange(70, 100)
        transparency_slider.setValue(100)
        display_layout.addWidget(transparency_slider, 3, 1)
        
        self.add_widget(display_group)
        
        # Audio settings
        audio_group = QGroupBox("AUDIO SETTINGS")
        audio_layout = QGridLayout(audio_group)
        
        # Master volume
        audio_layout.addWidget(EliteLabel("MASTER VOLUME:", "small"), 0, 0)
        master_volume = QSlider(Qt.Orientation.Horizontal)
        master_volume.setRange(0, 100)
        master_volume.setValue(75)
        audio_layout.addWidget(master_volume, 0, 1)
        
        # UI sounds
        ui_sounds = QCheckBox("UI SOUND EFFECTS")
        ui_sounds.setChecked(True)
        audio_layout.addWidget(ui_sounds, 1, 0, 1, 2)
        
        # Voice notifications
        voice_notifications = QCheckBox("VOICE NOTIFICATIONS")
        voice_notifications.setChecked(False)
        audio_layout.addWidget(voice_notifications, 2, 0, 1, 2)
        
        self.add_widget(audio_group)
        
        # Integration settings
        integration_group = QGroupBox("INTEGRATION SETTINGS")
        integration_layout = QGridLayout(integration_group)
        
        # Elite Dangerous integration
        ed_integration = QCheckBox("ELITE DANGEROUS INTEGRATION")
        ed_integration.setChecked(True)
        integration_layout.addWidget(ed_integration, 0, 0, 1, 2)
        
        # Spotify integration
        spotify_integration = QCheckBox("SPOTIFY INTEGRATION")
        spotify_integration.setChecked(False)
        integration_layout.addWidget(spotify_integration, 1, 0, 1, 2)
        
        # Auto-start with Windows
        auto_start = QCheckBox("AUTO-START WITH WINDOWS")
        auto_start.setChecked(False)
        integration_layout.addWidget(auto_start, 2, 0, 1, 2)
        
        # Journal monitoring
        integration_layout.addWidget(EliteLabel("JOURNAL PATH:", "small"), 3, 0)
        journal_path_btn = EliteButton("BROWSE")
        integration_layout.addWidget(journal_path_btn, 3, 1)
        
        self.add_widget(integration_group)
        
        # Performance settings
        perf_group = QGroupBox("PERFORMANCE SETTINGS")
        perf_layout = QGridLayout(perf_group)
        
        # Update frequency
        perf_layout.addWidget(EliteLabel("UPDATE FREQUENCY:", "small"), 0, 0)
        update_freq = QSpinBox()
        update_freq.setRange(1, 60)
        update_freq.setValue(20)
        update_freq.setSuffix(" FPS")
        perf_layout.addWidget(update_freq, 0, 1)
        
        # Hardware acceleration
        hw_accel = QCheckBox("HARDWARE ACCELERATION")
        hw_accel.setChecked(True)
        perf_layout.addWidget(hw_accel, 1, 0, 1, 2)
        
        # Low power mode
        low_power = QCheckBox("LOW POWER MODE")
        low_power.setChecked(False)
        perf_layout.addWidget(low_power, 2, 0, 1, 2)
        
        self.add_widget(perf_group)


class SettingsWindow(QMainWindow):
    """Main Settings Window"""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.current_preview_theme = self.theme_manager.current_theme
        self.setup_window()
        self.setup_ui()
        
        # Apply initial theme
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
    
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("Elite Dangerous - Settings & Theme Customization")
        self.setGeometry(100, 100, 1024, 768)
        self.setMinimumSize(900, 650)
    
    def setup_ui(self):
        """Setup the settings UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Left side - Settings tabs
        settings_tabs = QTabWidget()
        
        # Theme selection tab
        theme_tab = QWidget()
        theme_layout = QVBoxLayout(theme_tab)
        
        # Predefined themes
        predefined_panel = ElitePanel("PREDEFINED THEMES")
        predefined_layout = QGridLayout()
        
        themes = [
            ("Ice Blue", "Ice Blue"),
            ("Matrix Green", "Matrix Green"),
            ("Deep Purple", "Deep Purple"),
            ("Plasma Pink", "Plasma Pink"),
            ("Arctic White", "Arctic White"),
            ("Ember Red", "Ember Red")
        ]
        
        for i, (display_name, theme_name) in enumerate(themes):
            theme_btn = EliteButton(display_name)
            theme_btn.setCheckable(True)
            theme_btn.clicked.connect(lambda checked, t=theme_name: self.apply_predefined_theme(t))
            predefined_layout.addWidget(theme_btn, i // 2, i % 2)
        
        predefined_panel.add_layout(predefined_layout)
        theme_layout.addWidget(predefined_panel)
        
        # Custom theme editor
        self.custom_editor = CustomThemeEditor()
        self.custom_editor.theme_changed.connect(self.on_custom_theme_changed)
        theme_layout.addWidget(self.custom_editor)
        
        settings_tabs.addTab(theme_tab, "THEMES")
        
        # Application settings tab
        self.app_settings = ApplicationSettings()
        settings_tabs.addTab(self.app_settings, "SETTINGS")
        
        main_layout.addWidget(settings_tabs, 2)
        
        # Right side - Live preview
        preview_panel = ElitePanel("LIVE PREVIEW")
        self.theme_preview = ThemePreview()
        self.theme_preview.set_theme(self.current_preview_theme)
        preview_panel.add_widget(self.theme_preview)
        
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(preview_panel)
        
        # Apply buttons
        apply_layout = QHBoxLayout()
        
        apply_btn = EliteButton("APPLY THEME")
        apply_btn.clicked.connect(self.apply_current_theme)
        apply_layout.addWidget(apply_btn)
        
        revert_btn = EliteButton("REVERT")
        revert_btn.clicked.connect(self.revert_theme)
        apply_layout.addWidget(revert_btn)
        
        preview_layout.addLayout(apply_layout)
        
        main_layout.addLayout(preview_layout, 1)
    
    def apply_predefined_theme(self, theme_name: str):
        """Apply a predefined theme"""
        if theme_name in self.theme_manager.predefined_themes:
            new_theme = self.theme_manager.predefined_themes[theme_name]
            self.current_preview_theme = new_theme
            self.theme_preview.set_theme(new_theme)
    
    def on_custom_theme_changed(self, theme: ThemeColors):
        """Handle custom theme changes"""
        self.current_preview_theme = theme
        self.theme_preview.set_theme(theme)
    
    def apply_current_theme(self):
        """Apply the currently previewed theme"""
        self.theme_manager.set_theme(self.current_preview_theme)
        apply_elite_theme(QApplication.instance(), self.current_preview_theme)
        
        # Force refresh of all widgets
        self.update()
        for widget in QApplication.instance().allWidgets():
            widget.update()
    
    def revert_theme(self):
        """Revert to the original theme"""
        original_theme = self.theme_manager.current_theme
        self.current_preview_theme = original_theme
        self.theme_preview.set_theme(original_theme)


def main():
    """Main function to run the Settings Panel example"""
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show settings window
    window = SettingsWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())