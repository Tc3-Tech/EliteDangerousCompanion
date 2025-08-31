# Elite Dangerous Companion App - Project Documentation

## Project Orchestration
**This document serves as the master plan for the Elite Dangerous Companion App project. As the orchestrator, I will coordinate the work of specialized agents to ensure efficient, high-quality development.**

### Active Specialized Agents:
- `elite-dangerous-integrator` - Elite Dangerous APIs and journal integration
- `elite-ui-designer` - PyQt6 UI/UX design and Elite Dangerous theming
- `realtime-data-architect` - Real-time data flow and state management
- `asset-optimization-specialist` - Asset management and optimization
- `hardware-qa-specialist` - Testing and quality assurance
- `config-management-specialist` - Configuration and settings systems
- `performance-optimization-specialist` - Performance optimization and profiling

**Orchestration Strategy**: All development tasks will be delegated to appropriate specialized agents based on their expertise. This ensures deep domain knowledge is applied to each component while maintaining overall project coordination.

## Project Overview
A custom companion display application for Elite Dangerous that serves as both an information powerhouse during gameplay and an interactive "fidget screen" when the game is not running. Designed for a 7" secondary display (1024x768) with custom BLE keyboard hardware control.

## Hardware Setup
- **Display**: 7" secondary monitor (1024x768) via USB-C to HDMI
- **Input**: Custom BLE keyboard with ESP32-C3 (9 keys + toggle switch + potentiometer)
- **Connection**: BLE keyboard → Windows hotkeys + mouse control

## Application Modes

### 1. Elite Mode (Active Gameplay)
**Triggers**: Elite Dangerous process running + player logged in (detected via journal file monitoring)

**Core Features**:
- Real-time exploration data display
- Hyperspace jump transition screens
- System entry information (star types, planet data, terraformable indicators)
- Biological signals detection and tracking
- First discovery notifications
- Detailed planetary approach information
- Route planning visualization
- Material and resource tracking

**Data Sources**:
- Elite Dangerous Journal files (real-time monitoring)
- EDMC integration (separate process, API calls)
- EDSM, INARA, EDDN data feeds

### 2. Fidget Mode (Game Inactive)
**Triggers**: Elite Dangerous not running or player logged out

**Core Features**:
- Interactive ship model viewer with technical specifications
- Elite Dangerous asset gallery (GIFs, concept art, loading screens)
- Spotify/media player controls
- System status display (PC performance, weather, etc.)
- Rotating screensaver with Elite content

## Technical Architecture

### Data Flow
```
Elite Dangerous → Journal Files → EDMC (Process) → API → Our App → Display
Windows Input ← BLE Keyboard ← ESP32-C3 Controller
```

### Core Components
- **Journal Monitor**: Real-time file watching for Elite state changes
- **Context Manager**: Dynamic input mapping based on current app mode
- **Theme Engine**: Customizable HUD colors (no more orange!)
- **Asset Manager**: Efficient loading of ships, GIFs, and UI elements
- **EDMC Connector**: API integration with existing EDMC installation

### Technology Stack
- **Framework**: Python + PyQt6
- **Hardware Interface**: BLE communication via Windows keyboard/mouse APIs
- **Data Integration**: JSON parsing (journal files) + HTTP APIs (EDMC/web services)
- **Graphics**: Qt widgets with custom styling + image/video playback

## Key Features

### Dynamic Input System
- **Context-Sensitive Controls**: Same 9 buttons do different things in different screens
- **Potentiometer Functions**: 
  - HUD color tuning (HSV adjustment)
  - Ship model rotation
  - Media volume control
  - Data scrolling
- **Smart Transitions**: Auto-switch between Elite/Fidget modes

### Customizable Theming
- **Predefined Themes**: Matrix Green, Ice Blue, Deep Purple, Plasma Pink, Arctic White, Ember Red
- **Real-time Color Tuning**: Hardware potentiometer for live HSV adjustment
- **Elite-Authentic Styling**: Clean geometric panels, technical readouts, no orange

### Elite Integration Depth
**Inspiration from Elite Dangerous Exploration Buddy**:
- Comprehensive system analysis
- Biological signal identification
- Terraformable planet highlighting
- First discovery tracking
- Material farming assistance
- Route optimization display

## Development Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Basic PyQt6 application structure
- [ ] Context management system
- [ ] Theme engine with color customization
- [ ] BLE keyboard input handling
- [ ] Elite Dangerous process detection

### Phase 2: Core Functionality (Weeks 3-4)
- [ ] Journal file monitoring and parsing
- [ ] EDMC API integration
- [ ] Basic Elite mode data display
- [ ] Ship viewer for fidget mode
- [ ] Screen transitions and mode switching

### Phase 3: Elite Integration (Weeks 5-6)
- [ ] Real-time exploration data display
- [ ] System and planet information screens
- [ ] Hyperspace and transition animations
- [ ] Route planning visualization
- [ ] Material and discovery tracking

### Phase 4: Fidget Features (Weeks 7-8)
- [ ] Complete ship model viewer
- [ ] Elite asset gallery system
- [ ] Spotify API integration
- [ ] System monitoring widgets
- [ ] Screensaver mode with rotating content

### Phase 5: Polish & Enhancement (Weeks 9-10)
- [ ] Advanced theming options
- [ ] Performance optimization
- [ ] Hardware calibration tools
- [ ] User preferences and settings
- [ ] Documentation and setup guides

## Success Metrics
- **Responsiveness**: Sub-100ms input response time
- **Reliability**: 99%+ uptime during Elite sessions
- **Visual Quality**: Smooth 60fps animations on 1024x768 display
- **Data Accuracy**: Real-time sync with Elite Dangerous state
- **Usability**: Intuitive context-sensitive controls

## Technical Requirements
- Windows 10/11 (for BLE keyboard support)
- Python 3.9+ with PyQt6
- Elite Dangerous (any version)
- EDMC 5.0+ installation
- Secondary display support
- Bluetooth Low Energy capability

## Project Structure
```
elite_companion_app/
├── main.py                     # Application entry point
├── core/                       # Core application logic
├── ui/                         # User interface components
├── data/                       # Data integration modules  
├── config/                     # Settings and themes
├── assets/                     # Ships, GIFs, fonts, sounds
└── tests/                      # Test suites
```

## Notes for Development
- **Journal File Location**: `%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous\`
- **EDMC Integration**: Use HTTP API calls to running EDMC process
- **Asset Optimization**: Pre-process images for 1024x768 display efficiency
- **Theme System**: HSV color space for smooth potentiometer control
- **Context System**: Plan ahead for multi-function button mappings