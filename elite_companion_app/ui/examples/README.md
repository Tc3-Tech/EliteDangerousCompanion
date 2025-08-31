# Elite Dangerous UI Examples

This collection showcases PyQt6 UI examples designed with an authentic Elite Dangerous aesthetic, optimized for 1024x768 secondary displays. Each example demonstrates different aspects of creating compelling space-themed interfaces.

## Quick Start

### Run the Example Launcher
```bash
cd /home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/elite_companion_app/ui/examples
python example_launcher.py
```

The launcher provides a gallery view of all examples with detailed descriptions, theme switching, and one-click launching capabilities.

### Run Individual Examples
```bash
# Main Dashboard
python elite_dashboard.py

# Ship Details Panel  
python ship_details.py

# System Exploration Display
python exploration_display.py

# Media Control Interface
python media_control.py

# Settings & Theme Editor
python settings_panel.py
```

## Examples Overview

### 1. Main Dashboard (`elite_dashboard.py`)
**Comprehensive status display with real-time visualization**

**Features:**
- Real-time HUD display with crosshair and scanning animation
- Commander status tracking (credits, ranks, progress)
- Ship health monitoring with simulated damage/repair
- System information display
- Mission tracking with progress visualization
- Dynamic ship asset integration
- Theme switching capabilities

**Key Components:**
- `EliteHUD` - Custom painted HUD with technical overlays
- `CommanderStatus` - Live updating status panels
- `ShipStatus` - Health bars with animation
- `SystemInfo` - Current location details
- `MissionTracker` - Active objectives display

### 2. Ship Details Panel (`ship_details.py`)
**Detailed ship information with 3D visualization**

**Features:**
- 3D ship viewer with rotation and hover effects
- Tabbed specification display (Basic, Performance, Hardpoints, Internals)
- Complete loadout tree view with module status
- Interactive power management (SYS/ENG/WEP pips)
- Technical overlay with animated scan lines
- Asset integration from ship image collection

**Key Components:**
- `Ship3DViewer` - Rotating ship display with technical readouts
- `ShipSpecsPanel` - Tabbed technical specifications
- `ShipLoadoutPanel` - Tree view of all modules
- `PowerManagementPanel` - Interactive pip distribution

### 3. System Exploration Display (`exploration_display.py`)
**Interactive star system mapping and discovery tracking**

**Features:**
- Interactive system map with zoom, pan, and selection
- Clickable planetary bodies with detailed information
- Realistic orbital mechanics simulation
- Discovery and mapping status tracking
- Detailed body information panels
- Exploration statistics and progress
- Scanning simulation with state changes

**Key Components:**
- `InteractiveSystemMap` - Full mouse interaction with celestial bodies
- `BodyDetailsPanel` - Comprehensive planetary data
- `ExplorationDataPanel` - Statistics and recent discoveries
- `PlanetaryBody` - Data model for celestial objects

### 4. Media Control Interface (`media_control.py`)
**Spotify/media control with audio visualization**

**Features:**
- Real-time audio spectrum visualizer (32 frequency bands)
- Multi-source playlist support (Spotify, Local, Radio)
- 10-band graphic equalizer with presets
- Audio effects controls (Reverb, Compressor, Bass Boost, Surround)
- Transport controls with progress tracking
- Volume management and muting
- EQ preset system (Flat, Rock, Classical, Electronic, Vocal)

**Key Components:**
- `AudioVisualizerWidget` - Real-time spectrum analysis display
- `PlaylistPanel` - Multi-tab music source management
- `AdvancedMediaControls` - EQ and effects processing
- `MediaControlWindow` - Integrated transport controls

### 5. Settings & Theme Editor (`settings_panel.py`)
**Comprehensive theme customization with live preview**

**Features:**
- Live theme preview with sample UI elements
- Custom color picker components
- HSV color space controls for intuitive adjustment
- Predefined theme selection
- Application settings management
- Theme import/export capabilities
- Real-time preview updates

**Key Components:**
- `ThemePreview` - Live preview of theme changes
- `CustomThemeEditor` - Full color customization tools
- `ColorPicker` - Elite-styled color selection buttons
- `ApplicationSettings` - General app configuration

## Design Philosophy

### Elite Dangerous Aesthetic
- **Clean Geometric Panels**: Technical readouts with beveled edges
- **Holographic Styling**: Subtle transparency and glow effects
- **Color Schemes**: Blues, greens, purples, cyans (NO orange - overused!)
- **Technical Precision**: Spacecraft control system authenticity
- **High Contrast**: Readable in various lighting conditions

### Technical Implementation
- **60FPS Performance**: Optimized rendering and updates
- **Context Sensitivity**: Controls change based on application state  
- **Hardware Integration**: Mouse, keyboard, and potential controller support
- **Multi-Monitor Ready**: Designed for 1024x768 secondary displays
- **Theme System**: Complete customization with live preview

## Theme System

### Predefined Themes
- **Ice Blue**: Cool cyan palette (default)
- **Matrix Green**: Classic terminal green
- **Deep Purple**: Royal purple with highlights  
- **Plasma Pink**: Vibrant magenta scheme
- **Arctic White**: Light mode alternative
- **Ember Red**: Warm red/orange palette

### Custom Theme Creation
The theme editor supports:
- Individual color component editing
- HSV color space controls
- Live preview updates
- One-click presets
- Theme save/load functionality

### Color Roles
Each theme defines colors for:
- Primary/Secondary UI elements
- Accent colors for highlights
- Background and surface colors
- Text (primary and secondary)
- Border and divider elements
- Status colors (success, warning, error)

## Architecture

### Widget Hierarchy
```
ElitePanel (base container)
├── EliteLabel (styled text)
├── EliteButton (interactive controls)
├── EliteProgressBar (status indicators)
├── EliteHUD (custom painted displays)
├── EliteShipDisplay (asset integration)
└── EliteSystemMap (interactive graphics)
```

### Theme Application
```python
from config.themes import ThemeManager
from elite_widgets import apply_elite_theme

theme_manager = ThemeManager()
theme_manager.set_predefined_theme("Ice Blue")
apply_elite_theme(app, theme_manager.current_theme)
```

## Requirements

- Python 3.8+
- PyQt6
- Ship assets (included in /Assets directory)

## Development Notes

### Performance Optimization
- Uses `QTimer` for 60FPS animations
- Implements efficient `paintEvent` handling
- Minimizes widget repaints through careful update management
- Uses `QPixmapCache` for frequently rendered graphics

### Asset Integration
Ship images are automatically loaded from:
```
/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets/
```

Supported formats: PNG with transparent backgrounds
Naming convention: `ship-name-lowercase.png` (e.g., `asp-explorer.png`)

### Extending Examples
Each example is self-contained and can be extended by:
1. Subclassing existing Elite widgets
2. Adding new paint methods for custom graphics
3. Implementing additional theme color roles
4. Adding new signal/slot connections for interactivity

## Future Enhancements

- **Audio Integration**: Real Spotify/media player connections
- **Elite Journal Integration**: Live game data reading
- **Hardware Controls**: Physical button/joystick support  
- **Network Features**: Multi-instance synchronization
- **Plugin System**: Custom widget extensions
- **Performance Profiling**: Built-in performance monitoring

---

**Note**: This is a demonstration framework. For production use, implement proper error handling, configuration persistence, and security measures for any external integrations.