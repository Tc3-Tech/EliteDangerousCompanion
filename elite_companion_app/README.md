# Elite Dangerous Companion App

A custom companion display for Elite Dangerous with customizable themes, ship displays, and integrated controls.

## Project Structure

```
elite_companion_app/
├── main.py                     # Application entry point
├── config/
│   ├── __init__.py
│   ├── settings.py            # User settings and HUD colors
│   └── themes.py              # Theme definitions and color schemes
├── core/
│   ├── __init__.py
│   ├── app.py                 # Main application class
│   ├── data_manager.py        # EDMC data integration
│   └── hardware_manager.py    # BLE keyboard input handling
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Main display window
│   ├── widgets/               # Custom UI widgets
│   │   ├── __init__.py
│   │   ├── ship_display.py    # Ship schematic viewer
│   │   ├── status_panel.py    # Game status display
│   │   ├── media_control.py   # Spotify controls
│   │   └── asset_viewer.py    # Gif/asset display
│   └── themes/
│       ├── __init__.py
│       ├── base_theme.py      # Base theme class
│       └── styles.qss         # Qt stylesheet templates
├── data/
│   ├── __init__.py
│   ├── edmc_connector.py      # EDMC plugin integration
│   ├── spotify_client.py     # Spotify API client
│   └── asset_loader.py       # Load ships/gifs/assets
├── assets/
│   ├── ships/                 # Ship PNG files
│   ├── gifs/                  # Elite Dangerous gifs
│   ├── sounds/                # UI sounds
│   └── fonts/                 # Custom fonts (EUROCAPS.TTF)
└── requirements.txt
```

## Features

### HUD Customization
- Full color theming system
- Real-time color changes
- Preset color schemes (Matrix Green, Ice Blue, Deep Purple, etc.)
- Hardware pot control for hue adjustment

### Display Modes
1. **Elite Active**: Full game integration when ED is running
2. **Idle Mode**: Ship viewer, assets, media controls when ED not running
3. **Screensaver**: Rotating ship displays and gifs

### Hardware Integration
- 9-key BLE keyboard support
- Toggle switch for mode switching
- Potentiometer for color adjustment