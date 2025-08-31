# Elite Dangerous Fidget Mode

A comprehensive, interactive ship database browser designed for the Elite Dangerous community. This application serves as the primary interface when Elite Dangerous is not running, providing an immersive way to explore ship specifications, compare vessels, and enjoy the Elite aesthetic.

## Features

### 🚀 **Core Functionality**
- **Complete Ship Database**: 38+ ships with detailed technical specifications
- **Interactive 3D Ship Viewer**: Rotating ship display with technical overlays
- **Advanced Ship Gallery**: Thumbnail grid with filtering and search capabilities
- **Detailed Specifications**: Comprehensive ship data with animated stat bars
- **Ship Comparison System**: Side-by-side analysis with radar charts

### 🎨 **Elite Dangerous Aesthetic**
- **Authentic HUD Elements**: Scanning lines, targeting reticles, technical readouts
- **Dynamic Theme System**: 6 predefined themes (Ice Blue, Matrix Green, etc.)
- **Hardware Theme Control**: Real-time theme changes via potentiometer
- **Smooth Animations**: 60fps performance with fluid transitions
- **Elite-Style UI**: Angular panels, technical fonts, and authentic colors

### ⚙️ **Hardware Integration**
- **9-Button Navigation**: Full hardware control support
- **Potentiometer Input**: Theme, rotation, or zoom control
- **Hardware Simulation**: Built-in testing for development

### 🖥️ **Display Optimization**
- **1024x768 Optimized**: Perfect for target display resolution
- **Memory Efficient**: LRU cache with 50MB limit
- **Predictive Loading**: Smooth navigation with preloaded adjacent ships
- **Performance Monitoring**: Real-time FPS and cache statistics

## Installation

### Requirements
- Python 3.8+
- PyQt6
- Ship image assets in `/Assets/` directory

### Setup
```bash
# Install dependencies
pip install PyQt6

# Verify installation
python test_fidget_mode.py

# Run fidget mode
python ui/fidget_mode.py
```

## Usage

### Basic Navigation
- **Mouse**: Click and drag ship viewer to rotate, scroll to zoom
- **Gallery**: Click thumbnails to select ships, use filters to narrow selection
- **Specifications**: Browse detailed stats across multiple tabs
- **Comparison**: Click "Compare" button for side-by-side analysis

### Hardware Controls (if connected)
- **Button 1-3**: Gallery navigation (previous, select, next)
- **Button 4-6**: Ship rotation and zoom controls
- **Button 7-9**: Specification tab navigation
- **Potentiometer**: Dynamic theme control, ship rotation, or zoom

### Keyboard Shortcuts
- **Ctrl+S**: Export screenshot
- **Ctrl+Q**: Exit application

## Architecture

### Core Components

#### Ship Database (`data/ship_database.py`)
- Complete specifications for all Elite Dangerous ships
- Manufacturer details, performance metrics, hardpoint configurations
- Role-based categorization and search functionality
- Authentic technical data from the Elite Dangerous universe

#### Ship Gallery (`ui/widgets/ship_gallery.py`)
- Thumbnail grid with smooth hover effects
- Featured ship carousel with auto-advance
- Advanced filtering by class, role, and cost
- Optimized for 1024x768 display

#### 3D Ship Viewer (`ui/widgets/ship_viewer.py`)
- Real-time rotation with mouse control
- Technical scanning animations
- HUD overlays with ship telemetry
- Performance-optimized rendering (60fps target)

#### Specifications Panel (`ui/widgets/ship_specs_panel.py`)
- Tabbed interface with animated statistics
- Visual hardpoint and internal slot displays
- Real-time stat comparison highlighting
- Category-organized information

#### Ship Comparison (`ui/widgets/ship_comparison.py`)
- Radar chart visualization
- Detailed comparison tables
- Performance highlighting (best/worst values)
- Support for up to 4 ships simultaneously

#### Image Optimization (`utils/image_optimizer.py`)
- Memory-efficient caching system
- Multiple resolution presets
- Background loading with progress tracking
- LRU eviction policy

### Theme System
- **Hardware Integration**: Real-time theme control via potentiometer
- **Smooth Transitions**: Animated color interpolation
- **Elite Aesthetic**: Authentic color schemes and styling
- **Performance Optimized**: Efficient theme application

### Performance Features
- **60fps Target**: Optimized animations and rendering
- **Memory Management**: 50MB cache limit with LRU eviction
- **Predictive Loading**: Adjacent ships preloaded for smooth navigation
- **Image Optimization**: Multiple resolution presets for different contexts

## Technical Specifications

### Display Requirements
- **Primary Target**: 1024x768 resolution
- **Minimum**: 800x600 resolution
- **Recommended**: Hardware acceleration enabled

### Memory Usage
- **Image Cache**: 50MB maximum (configurable)
- **Application**: ~20-30MB typical usage
- **Database**: <5MB ship specifications

### Performance Metrics
- **Frame Rate**: 60fps target for animations
- **Load Time**: <100ms for ship transitions
- **Cache Hit Rate**: >90% for frequently accessed ships

## File Structure

```
elite_companion_app/
├── data/
│   └── ship_database.py          # Complete ship specifications
├── ui/
│   ├── fidget_mode.py            # Main application window
│   ├── elite_widgets.py          # Elite-themed UI components
│   └── widgets/
│       ├── ship_gallery.py       # Ship browsing interface
│       ├── ship_viewer.py        # 3D ship display
│       ├── ship_specs_panel.py   # Detailed specifications
│       └── ship_comparison.py    # Ship comparison tools
├── config/
│   └── themes.py                 # Theme system and hardware integration
├── utils/
│   └── image_optimizer.py        # Performance optimization
└── test_fidget_mode.py           # Comprehensive test suite
```

## Development

### Testing
```bash
# Run comprehensive test suite
python test_fidget_mode.py

# Test specific components
python -c "from ui.fidget_mode import EliteFidgetMode; print('Import successful')"
```

### Hardware Integration
The system includes simulation capabilities for hardware testing:
```python
# Enable hardware simulation
hardware_nav.enable_hardware_simulation(True)
```

### Theme Development
Add new themes in `config/themes.py`:
```python
NEW_THEME = ThemeColors(
    primary="#FF6B35",
    secondary="#F7931E", 
    accent="#FFE66D",
    # ... additional colors
)
```

### Performance Tuning
Key performance settings in `utils/image_optimizer.py`:
- Cache size: `max_memory_mb=50`
- Preload radius: `preload_radius=3`
- Target FPS: `target_fps=60`

## Ship Database

### Included Ships (38 total)
**Small Ships**: Sidewinder, Eagle, Hauler, Adder, Imperial Eagle, Viper III/IV, Cobra III/IV, Diamondback Scout/Explorer, Imperial Courier, Asp Scout

**Medium Ships**: Type-6, Asp Explorer, Vulture, Keelback, Federal Dropship/Assault Ship/Gunship, Python, Krait II/Phantom, Fer-de-Lance, Mamba, Alliance Chieftain/Challenger/Crusader

**Large Ships**: Type-7/9/10, Imperial Clipper/Cutter, Federal Corvette, Anaconda, Beluga Liner, Orca, Dolphin

### Technical Data
Each ship includes:
- **Performance**: Speed, jump range, maneuverability
- **Combat**: Hardpoints, shields, hull integrity
- **Utility**: Cargo capacity, internal compartments
- **Economics**: Cost, insurance, efficiency ratings
- **Physical**: Dimensions, mass, crew capacity

## License

This is a community tool for Elite Dangerous players. Ship specifications and imagery are derived from the Elite Dangerous universe, created by Frontier Developments.

## Support

For issues or feature requests, please refer to the test suite output and system requirements. The application includes comprehensive error handling and performance monitoring.

---

**Fly safe, Commander! o7**