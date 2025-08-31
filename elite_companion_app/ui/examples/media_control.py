"""
Elite Dangerous Media Control Interface
Spotify/Media control with Elite theming and visualization.
"""
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QSlider, QListWidget,
                           QListWidgetItem, QTabWidget, QTextEdit, QSplitter,
                           QScrollArea, QButtonGroup)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QPainter, QPen, QBrush, QFont, QColor, QLinearGradient, QPixmap
import math
import random
from typing import List, Dict

# Add the parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from elite_widgets import (ElitePanel, EliteLabel, EliteButton, EliteProgressBar, 
                          EliteMediaControl, apply_elite_theme)
from config.themes import ThemeManager, PredefinedThemes


class AudioVisualizerWidget(QWidget):
    """Audio spectrum visualizer with Elite styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 150)
        self.spectrum_data = [0] * 32  # 32 frequency bands
        self.peak_data = [0] * 32
        self.decay_rate = 0.95
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_spectrum)
        self.animation_timer.start(50)  # 20 FPS
        
        self.is_playing = False
    
    def set_playing(self, playing: bool):
        """Set whether audio is playing to control visualization"""
        self.is_playing = playing
    
    def update_spectrum(self):
        """Update spectrum data (simulated)"""
        if self.is_playing:
            # Simulate audio spectrum data
            for i in range(len(self.spectrum_data)):
                # Create some variation in the spectrum
                base_amplitude = random.random() * 0.8
                frequency_factor = 1.0 - (i / len(self.spectrum_data)) * 0.5  # Lower frequencies stronger
                beat_factor = 1.0 + 0.3 * math.sin(i * 0.5)  # Some rhythm variation
                
                new_value = base_amplitude * frequency_factor * beat_factor
                
                # Smooth transitions
                self.spectrum_data[i] = self.spectrum_data[i] * 0.7 + new_value * 0.3
                
                # Update peaks
                if self.spectrum_data[i] > self.peak_data[i]:
                    self.peak_data[i] = self.spectrum_data[i]
                else:
                    self.peak_data[i] *= self.decay_rate
        else:
            # Fade out when not playing
            for i in range(len(self.spectrum_data)):
                self.spectrum_data[i] *= 0.9
                self.peak_data[i] *= 0.9
        
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for spectrum visualizer"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(10, 10, 20))
        
        # Calculate bar dimensions
        bar_width = (self.width() - 10) // len(self.spectrum_data)
        max_height = self.height() - 20
        
        for i, amplitude in enumerate(self.spectrum_data):
            x = 5 + i * bar_width
            bar_height = int(amplitude * max_height)
            y = self.height() - bar_height - 10
            
            # Gradient color based on frequency
            hue = (i / len(self.spectrum_data)) * 240  # Blue to red spectrum
            color = QColor.fromHsv(int(hue), 255, 255)
            
            # Draw spectrum bar
            painter.fillRect(x, y, bar_width - 2, bar_height, color)
            
            # Draw peak indicator
            peak_y = self.height() - int(self.peak_data[i] * max_height) - 10
            painter.fillRect(x, peak_y - 2, bar_width - 2, 2, color.lighter())
        
        # Draw frequency labels
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        font = QFont("Arial", 8)
        painter.setFont(font)
        
        labels = ["32Hz", "64Hz", "125Hz", "250Hz", "500Hz", "1kHz", "2kHz", "4kHz", 
                 "8kHz", "16kHz"]
        label_spacing = len(self.spectrum_data) // len(labels)
        
        for i, label in enumerate(labels):
            if i * label_spacing < len(self.spectrum_data):
                x = 5 + (i * label_spacing) * bar_width
                painter.drawText(x, self.height() - 2, label)


class PlaylistPanel(ElitePanel):
    """Panel for playlist management and track selection"""
    
    track_selected = pyqtSignal(dict)  # Signal when track is selected
    
    def __init__(self, parent=None):
        super().__init__("PLAYLIST", parent)
        self.current_playlist = []
        self.setup_playlist_ui()
        self.load_sample_playlist()
    
    def setup_playlist_ui(self):
        """Setup playlist UI"""
        # Playlist tabs for different sources
        playlist_tabs = QTabWidget()
        
        # Spotify tab
        spotify_tab = QWidget()
        spotify_layout = QVBoxLayout(spotify_tab)
        
        self.spotify_list = QListWidget()
        self.spotify_list.itemDoubleClicked.connect(self.on_track_selected)
        spotify_layout.addWidget(self.spotify_list)
        
        playlist_tabs.addTab(spotify_tab, "SPOTIFY")
        
        # Local files tab
        local_tab = QWidget()
        local_layout = QVBoxLayout(local_tab)
        
        self.local_list = QListWidget()
        self.local_list.itemDoubleClicked.connect(self.on_track_selected)
        local_layout.addWidget(self.local_list)
        
        playlist_tabs.addTab(local_tab, "LOCAL FILES")
        
        # Radio tab
        radio_tab = QWidget()
        radio_layout = QVBoxLayout(radio_tab)
        
        self.radio_list = QListWidget()
        self.radio_list.itemDoubleClicked.connect(self.on_track_selected)
        radio_layout.addWidget(self.radio_list)
        
        playlist_tabs.addTab(radio_tab, "RADIO")
        
        self.add_widget(playlist_tabs)
    
    def load_sample_playlist(self):
        """Load sample tracks for demonstration"""
        spotify_tracks = [
            {"title": "Supermassive Black Hole", "artist": "Muse", "duration": "3:29", "source": "spotify"},
            {"title": "Space Oddity", "artist": "David Bowie", "duration": "5:18", "source": "spotify"},
            {"title": "Interstellar Overdrive", "artist": "Pink Floyd", "duration": "9:41", "source": "spotify"},
            {"title": "The Final Countdown", "artist": "Europe", "duration": "5:09", "source": "spotify"},
            {"title": "Bohemian Rhapsody", "artist": "Queen", "duration": "5:55", "source": "spotify"},
            {"title": "Tom Sawyer", "artist": "Rush", "duration": "4:33", "source": "spotify"},
            {"title": "Knights of Cydonia", "artist": "Muse", "duration": "6:04", "source": "spotify"}
        ]
        
        local_tracks = [
            {"title": "Elite Theme", "artist": "David Lowe", "duration": "2:45", "source": "local"},
            {"title": "Docking Computer", "artist": "Elite OST", "duration": "1:30", "source": "local"},
            {"title": "Hyperspace", "artist": "Elite: Dangerous OST", "duration": "3:15", "source": "local"}
        ]
        
        radio_stations = [
            {"title": "Lave Radio", "artist": "Elite Community", "duration": "LIVE", "source": "radio"},
            {"title": "Radio Sidewinder", "artist": "Elite Community", "duration": "LIVE", "source": "radio"},
            {"title": "Hutton Orbital Radio", "artist": "Elite Community", "duration": "LIVE", "source": "radio"}
        ]
        
        # Populate lists
        for track in spotify_tracks:
            item = QListWidgetItem(f"{track['title']} - {track['artist']} [{track['duration']}]")
            item.setData(Qt.ItemDataRole.UserRole, track)
            self.spotify_list.addItem(item)
        
        for track in local_tracks:
            item = QListWidgetItem(f"{track['title']} - {track['artist']} [{track['duration']}]")
            item.setData(Qt.ItemDataRole.UserRole, track)
            self.local_list.addItem(item)
        
        for station in radio_stations:
            item = QListWidgetItem(f"{station['title']} - {station['artist']} [{station['duration']}]")
            item.setData(Qt.ItemDataRole.UserRole, station)
            self.radio_list.addItem(item)
    
    def on_track_selected(self, item):
        """Handle track selection"""
        track_data = item.data(Qt.ItemDataRole.UserRole)
        if track_data:
            self.track_selected.emit(track_data)


class AdvancedMediaControls(ElitePanel):
    """Advanced media controls with EQ and effects"""
    
    eq_changed = pyqtSignal(list)  # Signal for EQ changes
    effect_toggled = pyqtSignal(str, bool)  # Signal for effect changes
    
    def __init__(self, parent=None):
        super().__init__("AUDIO CONTROLS", parent)
        self.eq_bands = [0] * 10  # 10-band EQ
        self.setup_controls_ui()
    
    def setup_controls_ui(self):
        """Setup advanced controls UI"""
        # Equalizer
        eq_layout = QVBoxLayout()
        eq_layout.addWidget(EliteLabel("EQUALIZER", "header"))
        
        # EQ sliders
        eq_sliders_layout = QHBoxLayout()
        self.eq_sliders = []
        
        frequencies = ["32", "64", "125", "250", "500", "1K", "2K", "4K", "8K", "16K"]
        
        for i, freq in enumerate(frequencies):
            slider_layout = QVBoxLayout()
            
            # Frequency label
            freq_label = EliteLabel(freq, "small")
            freq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            slider_layout.addWidget(freq_label)
            
            # Slider
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(-20, 20)  # -20dB to +20dB
            slider.setValue(0)
            slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
            slider.setTickInterval(5)
            slider.valueChanged.connect(lambda val, idx=i: self.on_eq_changed(idx, val))
            
            self.eq_sliders.append(slider)
            slider_layout.addWidget(slider)
            
            # Value label
            value_label = EliteLabel("0dB", "small")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            slider_layout.addWidget(value_label)
            setattr(slider, 'value_label', value_label)  # Store reference
            
            eq_sliders_layout.addLayout(slider_layout)
        
        eq_layout.addLayout(eq_sliders_layout)
        self.add_layout(eq_layout)
        
        # Audio effects
        effects_layout = QVBoxLayout()
        effects_layout.addWidget(EliteLabel("AUDIO EFFECTS", "header"))
        
        effects_grid = QGridLayout()
        
        effects = [
            ("REVERB", "Add spatial depth"),
            ("COMPRESSOR", "Dynamic range control"),
            ("BASS BOOST", "Enhanced low frequencies"),
            ("SURROUND", "Virtual 3D audio")
        ]
        
        self.effect_buttons = {}
        
        for i, (effect_name, description) in enumerate(effects):
            effect_btn = EliteButton(effect_name)
            effect_btn.setCheckable(True)
            effect_btn.toggled.connect(lambda checked, name=effect_name: 
                                     self.effect_toggled.emit(name, checked))
            
            effects_grid.addWidget(effect_btn, i // 2, i % 2)
            self.effect_buttons[effect_name] = effect_btn
        
        effects_layout.addLayout(effects_grid)
        self.add_layout(effects_layout)
        
        # Preset buttons
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(EliteLabel("PRESETS:", "small"))
        
        presets = ["FLAT", "ROCK", "CLASSICAL", "ELECTRONIC", "VOCAL"]
        
        for preset in presets:
            preset_btn = EliteButton(preset)
            preset_btn.clicked.connect(lambda checked, p=preset: self.apply_preset(p))
            presets_layout.addWidget(preset_btn)
        
        self.add_layout(presets_layout)
    
    def on_eq_changed(self, band_index: int, value: int):
        """Handle EQ slider change"""
        self.eq_bands[band_index] = value
        
        # Update value label
        slider = self.eq_sliders[band_index]
        slider.value_label.setText(f"{value:+d}dB")
        
        self.eq_changed.emit(self.eq_bands)
    
    def apply_preset(self, preset_name: str):
        """Apply EQ preset"""
        presets = {
            "FLAT": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "ROCK": [-2, 0, 3, 5, 2, -1, 0, 2, 4, 3],
            "CLASSICAL": [3, 2, 0, -2, -3, -2, 0, 2, 4, 5],
            "ELECTRONIC": [4, 3, 1, 0, -2, 2, 1, 3, 4, 3],
            "VOCAL": [-2, -1, 1, 3, 4, 4, 2, 1, 0, -1]
        }
        
        if preset_name in presets:
            values = presets[preset_name]
            for i, value in enumerate(values):
                self.eq_sliders[i].setValue(value)


class MediaControlWindow(QMainWindow):
    """Main Media Control Window"""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.current_track = None
        self.is_playing = False
        self.setup_window()
        self.setup_ui()
        
        # Apply initial theme
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
        
        # Timer for updating playback progress
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.current_position = 0
        self.track_duration = 100  # Default duration in seconds
    
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("Elite Dangerous - Media Control")
        self.setGeometry(100, 100, 1024, 768)
        self.setMinimumSize(800, 600)
    
    def setup_ui(self):
        """Setup the media control UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Top section - Now playing and visualizer
        top_layout = QHBoxLayout()
        
        # Now playing info
        now_playing_panel = ElitePanel("NOW PLAYING")
        now_playing_layout = QVBoxLayout()
        
        self.track_title = EliteLabel("No Track Selected", "header")
        now_playing_layout.addWidget(self.track_title)
        
        self.track_artist = EliteLabel("", "value")
        now_playing_layout.addWidget(self.track_artist)
        
        self.track_source = EliteLabel("", "small")
        now_playing_layout.addWidget(self.track_source)
        
        # Progress bar
        progress_layout = QHBoxLayout()
        self.progress_time = EliteLabel("0:00", "small")
        progress_layout.addWidget(self.progress_time)
        
        self.progress_bar = EliteProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.duration_time = EliteLabel("0:00", "small")
        progress_layout.addWidget(self.duration_time)
        
        now_playing_layout.addLayout(progress_layout)
        
        # Main transport controls
        transport_layout = QHBoxLayout()
        
        self.prev_btn = EliteButton("⏮")
        self.prev_btn.clicked.connect(self.previous_track)
        transport_layout.addWidget(self.prev_btn)
        
        self.play_pause_btn = EliteButton("▶")
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        transport_layout.addWidget(self.play_pause_btn)
        
        self.next_btn = EliteButton("⏭")
        self.next_btn.clicked.connect(self.next_track)
        transport_layout.addWidget(self.next_btn)
        
        self.shuffle_btn = EliteButton("🔀")
        self.shuffle_btn.setCheckable(True)
        transport_layout.addWidget(self.shuffle_btn)
        
        self.repeat_btn = EliteButton("🔁")
        self.repeat_btn.setCheckable(True)
        transport_layout.addWidget(self.repeat_btn)
        
        now_playing_layout.addLayout(transport_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(EliteLabel("VOLUME:", "small"))
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(75)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = EliteLabel("75%", "small")
        volume_layout.addWidget(self.volume_label)
        
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        
        now_playing_layout.addLayout(volume_layout)
        
        now_playing_panel.add_layout(now_playing_layout)
        top_layout.addWidget(now_playing_panel, 1)
        
        # Audio visualizer
        visualizer_panel = ElitePanel("AUDIO SPECTRUM")
        self.visualizer = AudioVisualizerWidget()
        visualizer_panel.add_widget(self.visualizer)
        top_layout.addWidget(visualizer_panel, 1)
        
        main_layout.addLayout(top_layout)
        
        # Bottom section - Playlist and advanced controls
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Playlist panel
        self.playlist_panel = PlaylistPanel()
        self.playlist_panel.track_selected.connect(self.on_track_selected)
        bottom_splitter.addWidget(self.playlist_panel)
        
        # Advanced controls panel
        self.advanced_controls = AdvancedMediaControls()
        self.advanced_controls.eq_changed.connect(self.on_eq_changed)
        self.advanced_controls.effect_toggled.connect(self.on_effect_toggled)
        bottom_splitter.addWidget(self.advanced_controls)
        
        # Set splitter proportions
        bottom_splitter.setSizes([400, 400])
        
        main_layout.addWidget(bottom_splitter)
        
        # Theme controls
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
        
        main_layout.addWidget(theme_widget)
    
    def on_track_selected(self, track_data: dict):
        """Handle track selection from playlist"""
        self.current_track = track_data
        self.track_title.setText(track_data["title"])
        self.track_artist.setText(track_data["artist"])
        self.track_source.setText(f"SOURCE: {track_data['source'].upper()}")
        
        # Set duration
        if track_data["duration"] != "LIVE":
            duration_parts = track_data["duration"].split(":")
            self.track_duration = int(duration_parts[0]) * 60 + int(duration_parts[1])
            self.duration_time.setText(track_data["duration"])
        else:
            self.track_duration = 0
            self.duration_time.setText("LIVE")
        
        # Reset progress
        self.current_position = 0
        self.progress_bar.setValue(0)
        self.progress_time.setText("0:00")
        
        # Auto-play if not already playing
        if not self.is_playing:
            self.toggle_play_pause()
    
    def toggle_play_pause(self):
        """Toggle play/pause state"""
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.play_pause_btn.setText("⏸")
            self.progress_timer.start(1000)  # Update every second
            self.visualizer.set_playing(True)
        else:
            self.play_pause_btn.setText("▶")
            self.progress_timer.stop()
            self.visualizer.set_playing(False)
    
    def previous_track(self):
        """Go to previous track"""
        # Implementation would handle actual playlist navigation
        pass
    
    def next_track(self):
        """Go to next track"""
        # Implementation would handle actual playlist navigation
        pass
    
    def update_progress(self):
        """Update playback progress"""
        if self.is_playing and self.track_duration > 0:
            self.current_position += 1
            
            if self.current_position >= self.track_duration:
                # Track finished
                self.current_position = 0
                self.next_track()  # Auto-advance
            
            # Update progress bar
            progress = int((self.current_position / self.track_duration) * 100)
            self.progress_bar.setValue(progress)
            
            # Update time display
            minutes = self.current_position // 60
            seconds = self.current_position % 60
            self.progress_time.setText(f"{minutes}:{seconds:02d}")
    
    def on_eq_changed(self, eq_values: List[int]):
        """Handle EQ changes"""
        # Implementation would apply EQ settings to audio engine
        print(f"EQ changed: {eq_values}")
    
    def on_effect_toggled(self, effect_name: str, enabled: bool):
        """Handle audio effect toggle"""
        # Implementation would toggle audio effects
        print(f"Effect {effect_name}: {'ON' if enabled else 'OFF'}")
    
    def change_theme(self, theme_name: str):
        """Change the application theme"""
        self.theme_manager.set_predefined_theme(theme_name)
        apply_elite_theme(QApplication.instance(), self.theme_manager.current_theme)
        
        # Force refresh
        self.update()
        for widget in self.findChildren(QWidget):
            widget.update()


def main():
    """Main function to run the Media Control example"""
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show media control window
    window = MediaControlWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())