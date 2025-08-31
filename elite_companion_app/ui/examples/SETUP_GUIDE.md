# Elite Dangerous UI Examples - Setup Guide

## Installation

### 1. Install Required Dependencies
```bash
cd /home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/elite_companion_app/ui/examples
pip install -r requirements.txt
```

### 2. Verify Setup
```bash
python test_setup.py
```

This will check:
- ✓ Python 3.8+ compatibility
- ✓ PyQt6 installation
- ✓ Elite UI modules
- ✓ Ship assets availability

### 3. Launch Examples

#### Option A: Use the Example Launcher (Recommended)
```bash
python example_launcher.py
```

The launcher provides:
- Gallery view of all examples
- Detailed descriptions and features
- One-click launching
- Theme switching
- Process management

#### Option B: Run Individual Examples
```bash
# Main Dashboard with HUD
python elite_dashboard.py

# Ship Details with 3D viewer
python ship_details.py

# System Exploration with interactive map
python exploration_display.py

# Media Control with spectrum analyzer
python media_control.py

# Settings & Theme customization
python settings_panel.py
```

## Troubleshooting

### PyQt6 Installation Issues
If you encounter PyQt6 installation problems:

```bash
# Try with pip upgrade
pip install --upgrade pip
pip install PyQt6

# Or use conda if available
conda install -c conda-forge pyqt6
```

### Missing Assets
The examples expect ship assets in:
```
/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets/
```

Assets are automatically loaded by name (e.g., `asp-explorer.png`).

### Import Errors
If you get module import errors, make sure you're running from the examples directory:
```bash
cd /home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/elite_companion_app/ui/examples
```

### Display Issues
For optimal display on secondary monitors:
- Set resolution to 1024x768 
- Enable "Always on top" in window settings
- Use the built-in theme selector for best visibility

## System Requirements

- **Python**: 3.8 or higher
- **PyQt6**: 6.4.0 or higher  
- **OS**: Linux, Windows, or macOS
- **Display**: 1024x768 minimum (optimized for secondary displays)
- **Memory**: 512MB RAM recommended
- **Storage**: ~50MB for all examples and assets

## Performance Notes

- Examples are optimized for 60FPS rendering
- Use hardware acceleration when available
- Close unused examples to free system resources
- Theme changes apply instantly across all running examples

## Next Steps

After successfully running the examples:

1. **Explore Themes**: Try different color schemes using the theme selector
2. **Customize**: Use the Settings panel to create custom themes
3. **Integrate**: Adapt the widgets for your own Elite Dangerous projects
4. **Extend**: Add new features or integrate with actual game data

Enjoy exploring the Elite Dangerous UI examples! 🚀