# WSL-Windows Integration Setup Guide for Elite Dangerous Companion App

This guide provides step-by-step instructions for setting up seamless WSL-Windows integration for your Elite Dangerous companion app.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [WSL2 Configuration](#wsl2-configuration)
3. [PowerShell Execution Policy](#powershell-execution-policy)
4. [File System Access Setup](#file-system-access-setup)
5. [Audio Module Installation](#audio-module-installation)
6. [BLE Integration Setup](#ble-integration-setup)
7. [Testing the Integration](#testing-the-integration)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Windows 11 (recommended) or Windows 10 version 2004+
- WSL2 installed and configured
- Elite Dangerous installed on Windows
- Python 3.8+ in WSL
- PowerShell 5.1+ (comes with Windows)

### Initial WSL2 Setup
If WSL2 is not already installed:

```bash
# Run in Windows PowerShell as Administrator
wsl --install
wsl --set-default-version 2
```

Restart your computer and set up your preferred Linux distribution.

## WSL2 Configuration

### 1. Enable Required Windows Features
Run in PowerShell as Administrator:

```powershell
# Enable WSL and Virtual Machine Platform
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform

# Enable Hyper-V (for better performance)
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
```

### 2. Configure WSL2 Settings
Create or edit `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
swapFile=C:\\temp\\wsl-swap.vhdx
localhostForwarding=true
```

### 3. Restart WSL
```bash
wsl --shutdown
# Wait a few seconds, then start your WSL distribution
```

## PowerShell Execution Policy

Configure PowerShell to allow script execution from WSL:

```powershell
# Run in Windows PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine

# Verify the policy
Get-ExecutionPolicy -List
```

## File System Access Setup

### 1. Verify Windows Drive Access
In WSL, verify you can access Windows drives:

```bash
# Check if Windows C: drive is accessible
ls /mnt/c/Users/

# Check Elite Dangerous directory
ls "/mnt/c/Users/$(whoami.exe | tr -d '\r')/Saved Games/Frontier Developments/"
```

### 2. Create Symbolic Links (Optional)
For easier access, create symbolic links in your WSL home directory:

```bash
# Create shortcuts to common directories
cd ~
ln -s "/mnt/c/Users/$(whoami.exe | tr -d '\r')/Saved Games/Frontier Developments/Elite Dangerous" elite_logs
ln -s "/mnt/c/Users/$(whoami.exe | tr -d '\r')/Pictures/Frontier Developments/Elite Dangerous" elite_screenshots

# Verify links work
ls -la elite_logs/
```

### 3. Set Up File Permissions
Ensure WSL can read Elite Dangerous files:

```bash
# Add yourself to required groups (if needed)
sudo usermod -a -G root $USER

# Set appropriate umask for file access
echo "umask 022" >> ~/.bashrc
```

## Audio Module Installation

### 1. Install AudioDeviceCmdlets PowerShell Module
Run in Windows PowerShell as Administrator:

```powershell
# Install the audio control module
Install-Module -Name AudioDeviceCmdlets -Force -AllowClobber

# Import the module
Import-Module AudioDeviceCmdlets

# Test audio device access
Get-AudioDevice -List
```

### 2. Test Audio Functionality
In WSL:

```bash
# Test basic audio device discovery
powershell.exe -c "Get-AudioDevice -List | ConvertTo-Json"

# Test volume control
powershell.exe -c "Set-AudioDevice -Volume 50"
```

## BLE Integration Setup

### 1. Enable Bluetooth Services
In Windows PowerShell as Administrator:

```powershell
# Start Bluetooth services
Start-Service bthserv
Set-Service bthserv -StartupType Automatic

# Verify Bluetooth is working
Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq "OK"}
```

### 2. Pair Your BLE Device
1. Open Windows Settings > Devices > Bluetooth & other devices
2. Click "Add Bluetooth or other device"
3. Select "Bluetooth"
4. Put your EDMC controller in pairing mode
5. Select and pair the device

### 3. Test BLE Communication
In WSL:

```bash
# Test BLE device discovery
python3 -c "
from core.ble_integration import quick_ble_scan
devices = quick_ble_scan()
for device in devices:
    print(f'Found: {device.name} ({device.address})')
"
```

## Testing the Integration

### 1. Test File System Access
Create and run this test script:

```python
# test_integration.py
import sys
sys.path.append('/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/elite_companion_app')

from core.wsl_integration import WSLWindowsIntegration

def test_file_access():
    wsl = WSLWindowsIntegration()
    
    print(f"WSL detected: {wsl.is_wsl}")
    print(f"Windows username: {wsl.windows_username}")
    
    # Test Elite Dangerous paths
    paths = wsl.get_elite_dangerous_paths()
    for name, path in paths.items():
        print(f"{name}: {path.wsl_path} (exists: {path.exists()})")

if __name__ == "__main__":
    test_file_access()
```

Run the test:
```bash
python3 test_integration.py
```

### 2. Test Process Monitoring
```python
# test_processes.py
from core.process_monitor import get_elite_dangerous_status

status = get_elite_dangerous_status()
print(f"Elite Dangerous Status: {status}")
```

### 3. Test Journal Monitoring
```python
# test_journal.py
from core.journal_monitor import EliteJournalMonitor
import time

def on_journal_entry(entry):
    print(f"Journal Event: {entry.event_name} at {entry.timestamp}")

monitor = EliteJournalMonitor()
monitor.add_callback('journal_entry', on_journal_entry)

try:
    monitor.start_monitoring()
    print("Monitoring journal files... Press Ctrl+C to stop")
    time.sleep(60)  # Monitor for 1 minute
except KeyboardInterrupt:
    monitor.stop_monitoring()
    print("Monitoring stopped")
```

## Performance Optimization

### 1. File System Performance
Add to `~/.bashrc` for better file system performance:

```bash
# Optimize WSL file system access
export WSLENV="PATH/l:USERPROFILE/p"

# Use Windows Git for better performance on Windows files
alias git='git.exe'
```

### 2. Memory Configuration
Create `/etc/wsl.conf` in WSL:

```ini
[automount]
enabled = true
root = /mnt/
options = "metadata,umask=22,fmask=111"
mountFsTab = false

[network]
generateHosts = true
generateResolvConf = true

[interop]
enabled = true
appendWindowsPath = true
```

### 3. PowerShell Optimization
For faster PowerShell execution, disable progress bars:

```bash
# Add to ~/.bashrc
export POWERSHELL_TELEMETRY_OPTOUT=1
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "Permission Denied" Errors
```bash
# Check file permissions
ls -la "/mnt/c/Users/$(whoami.exe | tr -d '\r')/Saved Games/"

# Fix WSL permissions
sudo mount -o remount,uid=1000,gid=1000,umask=022 /mnt/c
```

#### 2. PowerShell Execution Errors
```powershell
# In Windows PowerShell as Administrator
Set-ExecutionPolicy Unrestricted -Scope CurrentUser
```

#### 3. Audio Module Not Found
```powershell
# Reinstall audio module
Uninstall-Module AudioDeviceCmdlets -Force
Install-Module AudioDeviceCmdlets -Force -AllowClobber
```

#### 4. Journal Files Not Found
```bash
# Debug file path resolution
powershell.exe -c 'echo $env:USERPROFILE'
powershell.exe -c 'Test-Path "$env:USERPROFILE\Saved Games\Frontier Developments\Elite Dangerous"'
```

#### 5. BLE Connection Issues
```powershell
# Restart Bluetooth services
Restart-Service bthserv
Get-Service bth*
```

### Performance Issues

#### Slow File Access
- Avoid accessing Windows files from WSL when possible
- Use symbolic links for frequently accessed directories
- Consider using Windows-native tools for file operations

#### High CPU Usage
- Reduce journal monitoring poll interval
- Use event filters to process only relevant journal entries
- Disable unnecessary background monitoring

#### Memory Usage
- Limit journal entry history size
- Implement proper cleanup in monitoring loops
- Use WSL2 memory limits in `.wslconfig`

### Debug Logging

Enable debug logging in your Python code:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/elite_companion_debug.log'),
        logging.StreamHandler()
    ]
)

# Enable debug logging for specific modules
logging.getLogger('core.wsl_integration').setLevel(logging.DEBUG)
logging.getLogger('core.journal_monitor').setLevel(logging.DEBUG)
```

## Security Considerations

### File Access Security
- Only access necessary Windows directories
- Use read-only access when possible
- Avoid storing sensitive data in WSL-accessible locations

### PowerShell Security
- Keep execution policy as restrictive as possible
- Regularly audit PowerShell modules
- Monitor PowerShell execution logs

### Network Security
- BLE connections should use proper authentication
- Monitor network traffic between WSL and Windows
- Use localhost forwarding only when necessary

## Maintenance

### Regular Tasks
1. Update PowerShell modules monthly:
   ```powershell
   Update-Module AudioDeviceCmdlets
   ```

2. Clear WSL cache weekly:
   ```bash
   sudo apt clean
   sudo apt autoremove
   ```

3. Monitor log files for errors:
   ```bash
   tail -f /tmp/elite_companion_debug.log
   ```

### Backup Configuration
Back up these important files:
- `%USERPROFILE%\.wslconfig`
- `/etc/wsl.conf`
- Your app configuration files
- PowerShell execution policy settings

## Next Steps

After completing this setup:
1. Run the integration tests to verify everything works
2. Configure your Elite Dangerous companion app settings
3. Set up monitoring for your specific use case
4. Consider creating startup scripts for automatic initialization

For advanced configuration and custom integrations, refer to the API documentation in each module's source code.