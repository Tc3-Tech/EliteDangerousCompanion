# WSL GUI Troubleshooting Guide for Elite Dangerous Companion App

## Quick Start

Run the UI examples with automatic WSL configuration:
```bash
python3 run_ui_examples.py
```

Or setup environment manually:
```bash
python3 wsl_qt_setup.py
python3 ui/examples/example_launcher.py
```

## Common Issues and Solutions

### 1. "Failed to create wl_display" Error
**Problem**: WSL trying to use Wayland instead of X11
**Solution**: Force X11/XCB platform
```bash
export QT_QPA_PLATFORM=xcb
```

### 2. "Could not load Qt platform plugin wayland"
**Problem**: Same as above - Wayland issues in WSL
**Solution**: Use the provided setup script or set manually:
```bash
export QT_QPA_PLATFORM=xcb
export DISPLAY=:0
```

### 3. "ThemeSelector.apply_theme() missing argument" Error
**Status**: ✅ FIXED
**Solution**: Method renamed to avoid conflict with theme system
- `apply_theme()` → `apply_selected_theme()` for UI buttons
- Theme system uses single-argument `apply_theme(theme)` for widgets

### 4. CSS Warning: "Unknown property transform/transition"
**Status**: ✅ FIXED  
**Problem**: Qt stylesheets don't support CSS transform/transition properties
**Solution**: Removed unsupported CSS properties, use Qt animations instead

### 5. Display Not Working
Check your WSL GUI setup:

#### For Windows 11 (22H2+) with WSLg:
```bash
echo $DISPLAY  # Should show :0 or similar
export DISPLAY=:0
```

#### For Windows 10 or older Windows 11:
1. Install VcXsrv or Xming
2. Launch with "Disable access control" checked
3. Set Windows host IP:
```bash
export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0.0
```

#### Test X11 connection:
```bash
xset q  # Should show server information
python3 -c "from PyQt6.QtWidgets import QApplication; QApplication([]); print('Qt works')"
```

### 6. Import Errors
**Problem**: Missing dependencies or path issues
**Solutions**:
```bash
# Install PyQt6
pip install PyQt6

# Check Python path
python3 -c "import sys; print(sys.path)"

# Run from correct directory
cd /path/to/elite_companion_app
python3 run_ui_examples.py
```

## Environment Variables Reference

Required for WSL PyQt6 applications:
```bash
export QT_QPA_PLATFORM=xcb          # Force X11 platform
export DISPLAY=:0                   # X11 display (adjust as needed)
export QT_X11_NO_MITSHM=1          # Disable problematic X11 extension
export QT_QUICK_BACKEND=software   # Use software rendering
```

## Testing Your Setup

### 1. Basic Qt Test:
```bash
python3 wsl_qt_setup.py
```

### 2. UI Examples Test:
```bash
python3 -c "
import os
os.environ['QT_QPA_PLATFORM'] = 'xcb'
from PyQt6.QtWidgets import QApplication
from ui.examples.example_launcher import ExampleLauncherWindow
app = QApplication([])
window = ExampleLauncherWindow()
print('✅ UI Examples working!')
"
```

### 3. Individual Example Test:
```bash
export QT_QPA_PLATFORM=xcb
python3 ui/examples/elite_dashboard.py
```

## Performance Tips

1. **Use Hardware Acceleration** (if available):
   - Remove `QT_QUICK_BACKEND=software` if graphics work properly
   
2. **Optimize for 1024x768** (secondary displays):
   - Examples are designed for this resolution
   - Scale UI if needed: `export QT_SCALE_FACTOR=1.2`

3. **Reduce Animations** for better WSL performance:
   - Disable theme transitions in settings
   - Lower animation frame rates in config

## Advanced Troubleshooting

### Debug Qt Platform:
```python
from PyQt6.QtWidgets import QApplication
app = QApplication([])
print("Platform:", app.platformName())
print("Available platforms:", app.availablePlugins())
```

### Check X11 Server:
```bash
ps aux | grep -E "(Xvfb|Xorg|VcXsrv)"
netstat -an | grep :6000  # X11 typically runs on port 6000
```

### WSL Version Check:
```bash
wsl --version
cat /proc/version | grep -i microsoft
```

## Files Modified in This Fix

1. **`/ui/examples/example_launcher.py`**:
   - Fixed `ThemeSelector.apply_theme()` method signature conflict
   - Renamed to `apply_selected_theme()` for UI button callbacks

2. **`/ui/elite_widgets.py`**:
   - Removed unsupported CSS `transform` and `transition` properties
   - Added Qt-compatible styling comments

3. **`/wsl_qt_setup.py`** (new):
   - Automatic WSL Qt environment configuration
   - X11 server detection and setup
   - Comprehensive diagnostics

4. **`/run_ui_examples.py`** (new):
   - Wrapper script for UI examples
   - Automatic WSL setup integration
   - Error handling and diagnostics

## Success Indicators

When everything is working correctly, you should see:
```
✓ WSL Qt environment configured successfully!
✓ PyQt6 QApplication created successfully  
✓ Platform: xcb
✓ ExampleLauncherWindow created successfully
✓ All imports successful
```

The UI Examples Launcher should open without errors and display:
- Gallery of 5 examples on the left
- Example details panel on the right
- Theme selector with 6 theme options
- All buttons and controls responding properly

## Getting Help

If issues persist:
1. Run `python3 wsl_qt_setup.py` for detailed diagnostics
2. Check Windows Firewall isn't blocking X11 (port 6000-6010)
3. Try different DISPLAY values: `:0`, `localhost:0.0`, `<windows-ip>:0.0`
4. Verify WSLg is enabled (Windows 11 22H2+) or X server is running