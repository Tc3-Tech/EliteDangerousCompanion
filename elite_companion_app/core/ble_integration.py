"""
BLE Keyboard Integration for Windows from WSL
Provides BLE keyboard input functionality for Elite Dangerous companion app.
"""
import subprocess
import json
import threading
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class BLEConnectionState(Enum):
    """BLE connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    PAIRING = "pairing"
    ERROR = "error"


class KeyCode(Enum):
    """Common key codes for Elite Dangerous"""
    # Function keys
    F1 = 0x3A
    F2 = 0x3B
    F3 = 0x3C
    F4 = 0x3D
    F5 = 0x3E
    F6 = 0x3F
    F7 = 0x40
    F8 = 0x41
    F9 = 0x42
    F10 = 0x43
    F11 = 0x44
    F12 = 0x45
    
    # Number keys
    KEY_1 = 0x1E
    KEY_2 = 0x1F
    KEY_3 = 0x20
    KEY_4 = 0x21
    KEY_5 = 0x22
    KEY_6 = 0x23
    KEY_7 = 0x24
    KEY_8 = 0x25
    KEY_9 = 0x26
    KEY_0 = 0x27
    
    # Letters
    A = 0x04
    B = 0x05
    C = 0x06
    D = 0x07
    E = 0x08
    F = 0x09
    G = 0x0A
    H = 0x0B
    I = 0x0C
    J = 0x0D
    K = 0x0E
    L = 0x0F
    M = 0x10
    N = 0x11
    O = 0x12
    P = 0x13
    Q = 0x14
    R = 0x15
    S = 0x16
    T = 0x17
    U = 0x18
    V = 0x19
    W = 0x1A
    X = 0x1B
    Y = 0x1C
    Z = 0x1D
    
    # Special keys
    ENTER = 0x28
    ESCAPE = 0x29
    BACKSPACE = 0x2A
    TAB = 0x2B
    SPACE = 0x2C
    CTRL = 0xE0
    SHIFT = 0xE1
    ALT = 0xE2
    
    # Arrow keys
    RIGHT_ARROW = 0x4F
    LEFT_ARROW = 0x50
    DOWN_ARROW = 0x51
    UP_ARROW = 0x52


@dataclass
class BLEDevice:
    """BLE device information"""
    name: str
    address: str
    is_paired: bool = False
    is_connected: bool = False
    signal_strength: int = 0
    device_type: str = "Unknown"
    services: List[str] = field(default_factory=list)


@dataclass
class KeyboardEvent:
    """Keyboard input event"""
    key_code: Union[KeyCode, int]
    is_pressed: bool
    modifiers: List[KeyCode] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class BLEConfig:
    """BLE integration configuration"""
    device_name_pattern: str = "EDMC_Controller"
    auto_connect: bool = True
    connection_timeout: float = 30.0
    reconnect_interval: float = 5.0
    max_reconnect_attempts: int = 5
    input_debounce_ms: int = 50
    battery_monitoring: bool = True


class WindowsBLEManager:
    """Manages BLE connections and keyboard input through Windows"""
    
    def __init__(self, config: BLEConfig = None):
        self.config = config or BLEConfig()
        self._connection_state = BLEConnectionState.DISCONNECTED
        self._connected_device = None
        self._monitoring = False
        self._monitor_thread = None
        self._callbacks = {
            'connection_changed': [],
            'key_event': [],
            'device_discovered': [],
            'battery_level': [],
            'error': []
        }
        self._last_key_time = {}
        
    def add_callback(self, event_type: str, callback: Callable):
        """Add event callback"""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable):
        """Remove event callback"""
        if event_type in self._callbacks and callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)
    
    def _emit_event(self, event_type: str, data: Any):
        """Emit event to callbacks"""
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"BLE callback error for {event_type}: {e}")
    
    @property
    def connection_state(self) -> BLEConnectionState:
        """Get current connection state"""
        return self._connection_state
    
    @property
    def connected_device(self) -> Optional[BLEDevice]:
        """Get currently connected device"""
        return self._connected_device
    
    def scan_for_devices(self, timeout: float = 10.0) -> List[BLEDevice]:
        """Scan for BLE devices"""
        devices = []
        
        try:
            # PowerShell script to scan for BLE devices
            ps_script = f'''
            $timeout = {timeout}
            $devices = @()
            
            # Get paired Bluetooth devices
            $pairedDevices = Get-PnpDevice -Class Bluetooth | Where-Object {{ $_.Status -eq "OK" }}
            
            foreach ($device in $pairedDevices) {{
                $deviceInfo = Get-PnpDeviceProperty -InstanceId $device.InstanceId -KeyName DEVPKEY_Device_FriendlyName -ErrorAction SilentlyContinue
                $addressInfo = Get-PnpDeviceProperty -InstanceId $device.InstanceId -KeyName DEVPKEY_Bluetooth_DeviceAddress -ErrorAction SilentlyContinue
                
                if ($deviceInfo -and $addressInfo) {{
                    $devices += [PSCustomObject]@{{
                        Name = $deviceInfo.Data
                        Address = $addressInfo.Data
                        IsPaired = $true
                        IsConnected = $device.Status -eq "OK"
                        SignalStrength = -50
                        DeviceType = "Bluetooth"
                        Services = @()
                    }}
                }}
            }}
            
            $devices | ConvertTo-Json
            '''
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_script
            ], capture_output=True, text=True, timeout=timeout + 5)
            
            if result.returncode == 0 and result.stdout.strip():
                device_data = json.loads(result.stdout)
                if isinstance(device_data, dict):
                    device_data = [device_data]
                
                for data in device_data:
                    device = BLEDevice(
                        name=data.get('Name', ''),
                        address=data.get('Address', ''),
                        is_paired=data.get('IsPaired', False),
                        is_connected=data.get('IsConnected', False),
                        signal_strength=data.get('SignalStrength', 0),
                        device_type=data.get('DeviceType', 'Unknown'),
                        services=data.get('Services', [])
                    )
                    devices.append(device)
                    
                    # Emit device discovery event
                    self._emit_event('device_discovered', device)
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, 
                json.JSONDecodeError) as e:
            logger.error(f"Failed to scan for BLE devices: {e}")
            self._emit_event('error', {'error': str(e), 'operation': 'scan'})
        
        return devices
    
    def find_target_device(self) -> Optional[BLEDevice]:
        """Find the target EDMC controller device"""
        devices = self.scan_for_devices()
        
        for device in devices:
            if self.config.device_name_pattern.lower() in device.name.lower():
                return device
        
        return None
    
    def connect_to_device(self, device: BLEDevice) -> bool:
        """Connect to a BLE device"""
        try:
            self._connection_state = BLEConnectionState.CONNECTING
            self._emit_event('connection_changed', {
                'state': self._connection_state,
                'device': device
            })
            
            # PowerShell script to connect to device
            ps_script = f'''
            $deviceAddress = "{device.address}"
            
            # Try to connect to the Bluetooth device
            try {{
                $device = Get-PnpDevice | Where-Object {{ $_.InstanceId -like "*$deviceAddress*" }}
                if ($device) {{
                    Enable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false
                    Start-Sleep -Seconds 3
                    
                    # Check connection status
                    $updatedDevice = Get-PnpDevice -InstanceId $device.InstanceId
                    if ($updatedDevice.Status -eq "OK") {{
                        "Connected"
                    }} else {{
                        "Failed"
                    }}
                }} else {{
                    "Device not found"
                }}
            }} catch {{
                "Error: $($_.Exception.Message)"
            }}
            '''
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_script
            ], capture_output=True, text=True, timeout=self.config.connection_timeout)
            
            if result.returncode == 0 and "Connected" in result.stdout:
                self._connection_state = BLEConnectionState.CONNECTED
                self._connected_device = device
                device.is_connected = True
                
                self._emit_event('connection_changed', {
                    'state': self._connection_state,
                    'device': device
                })
                
                logger.info(f"Connected to BLE device: {device.name}")
                return True
            else:
                self._connection_state = BLEConnectionState.ERROR
                error_msg = result.stdout.strip() if result.stdout else "Unknown error"
                logger.error(f"Failed to connect to BLE device: {error_msg}")
                
                self._emit_event('error', {
                    'error': error_msg,
                    'operation': 'connect',
                    'device': device
                })
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self._connection_state = BLEConnectionState.ERROR
            logger.error(f"Connection error: {e}")
            self._emit_event('error', {
                'error': str(e),
                'operation': 'connect',
                'device': device
            })
        
        return False
    
    def disconnect_from_device(self) -> bool:
        """Disconnect from current BLE device"""
        if not self._connected_device:
            return True
        
        try:
            device = self._connected_device
            
            # PowerShell script to disconnect
            ps_script = f'''
            $deviceAddress = "{device.address}"
            
            try {{
                $device = Get-PnpDevice | Where-Object {{ $_.InstanceId -like "*$deviceAddress*" }}
                if ($device) {{
                    Disable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false
                    "Disconnected"
                }} else {{
                    "Device not found"
                }}
            }} catch {{
                "Error: $($_.Exception.Message)"
            }}
            '''
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_script
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self._connection_state = BLEConnectionState.DISCONNECTED
                device.is_connected = False
                self._connected_device = None
                
                self._emit_event('connection_changed', {
                    'state': self._connection_state,
                    'device': device
                })
                
                logger.info(f"Disconnected from BLE device: {device.name}")
                return True
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"Disconnect error: {e}")
            self._emit_event('error', {
                'error': str(e),
                'operation': 'disconnect'
            })
        
        return False
    
    def send_key_input(self, key_event: KeyboardEvent) -> bool:
        """Send keyboard input to Windows"""
        if not self._should_process_key_event(key_event):
            return False
        
        try:
            # Convert key code to Windows virtual key code
            vk_code = self._get_virtual_key_code(key_event.key_code)
            if vk_code is None:
                return False
            
            # Build modifier keys
            modifier_codes = []
            for modifier in key_event.modifiers:
                mod_code = self._get_virtual_key_code(modifier)
                if mod_code:
                    modifier_codes.append(mod_code)
            
            # PowerShell script for key input
            modifier_press = ""
            modifier_release = ""
            
            for mod_code in modifier_codes:
                modifier_press += f"[System.Windows.Forms.SendKeys]::SendWait('^');"
            
            action = "down" if key_event.is_pressed else "up"
            
            ps_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            
            # Send the key input
            try {{
                {modifier_press}
                [System.Windows.Forms.SendKeys]::SendWait("{{{vk_code}}}")
                {modifier_release}
                "Success"
            }} catch {{
                "Error: $($_.Exception.Message)"
            }}
            '''
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_script
            ], capture_output=True, text=True, timeout=5)
            
            success = result.returncode == 0 and "Success" in result.stdout
            
            if success:
                # Update last key time for debouncing
                key_id = f"{key_event.key_code}_{key_event.is_pressed}"
                self._last_key_time[key_id] = time.time()
                
                logger.debug(f"Sent key input: {key_event.key_code.name if isinstance(key_event.key_code, KeyCode) else key_event.key_code}")
            else:
                logger.error(f"Failed to send key input: {result.stdout}")
            
            return success
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"Key input error: {e}")
            return False
    
    def _should_process_key_event(self, key_event: KeyboardEvent) -> bool:
        """Check if key event should be processed (debouncing)"""
        if self.config.input_debounce_ms <= 0:
            return True
        
        key_id = f"{key_event.key_code}_{key_event.is_pressed}"
        last_time = self._last_key_time.get(key_id, 0)
        current_time = time.time()
        
        debounce_seconds = self.config.input_debounce_ms / 1000.0
        
        return (current_time - last_time) >= debounce_seconds
    
    def _get_virtual_key_code(self, key: Union[KeyCode, int]) -> Optional[int]:
        """Convert KeyCode to Windows virtual key code"""
        if isinstance(key, int):
            return key
        
        # Mapping from our KeyCode enum to Windows VK codes
        vk_mapping = {
            KeyCode.F1: 0x70, KeyCode.F2: 0x71, KeyCode.F3: 0x72, KeyCode.F4: 0x73,
            KeyCode.F5: 0x74, KeyCode.F6: 0x75, KeyCode.F7: 0x76, KeyCode.F8: 0x77,
            KeyCode.F9: 0x78, KeyCode.F10: 0x79, KeyCode.F11: 0x7A, KeyCode.F12: 0x7B,
            
            KeyCode.KEY_1: 0x31, KeyCode.KEY_2: 0x32, KeyCode.KEY_3: 0x33, KeyCode.KEY_4: 0x34,
            KeyCode.KEY_5: 0x35, KeyCode.KEY_6: 0x36, KeyCode.KEY_7: 0x37, KeyCode.KEY_8: 0x38,
            KeyCode.KEY_9: 0x39, KeyCode.KEY_0: 0x30,
            
            KeyCode.A: 0x41, KeyCode.B: 0x42, KeyCode.C: 0x43, KeyCode.D: 0x44, KeyCode.E: 0x45,
            KeyCode.F: 0x46, KeyCode.G: 0x47, KeyCode.H: 0x48, KeyCode.I: 0x49, KeyCode.J: 0x4A,
            KeyCode.K: 0x4B, KeyCode.L: 0x4C, KeyCode.M: 0x4D, KeyCode.N: 0x4E, KeyCode.O: 0x4F,
            KeyCode.P: 0x50, KeyCode.Q: 0x51, KeyCode.R: 0x52, KeyCode.S: 0x53, KeyCode.T: 0x54,
            KeyCode.U: 0x55, KeyCode.V: 0x56, KeyCode.W: 0x57, KeyCode.X: 0x58, KeyCode.Y: 0x59,
            KeyCode.Z: 0x5A,
            
            KeyCode.ENTER: 0x0D, KeyCode.ESCAPE: 0x1B, KeyCode.BACKSPACE: 0x08,
            KeyCode.TAB: 0x09, KeyCode.SPACE: 0x20,
            KeyCode.CTRL: 0x11, KeyCode.SHIFT: 0x10, KeyCode.ALT: 0x12,
            
            KeyCode.RIGHT_ARROW: 0x27, KeyCode.LEFT_ARROW: 0x25,
            KeyCode.DOWN_ARROW: 0x28, KeyCode.UP_ARROW: 0x26
        }
        
        return vk_mapping.get(key)
    
    def start_monitoring(self):
        """Start BLE device monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("BLE monitoring started")
    
    def stop_monitoring(self):
        """Stop BLE device monitoring"""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        logger.info("BLE monitoring stopped")
    
    def _monitoring_loop(self):
        """Main BLE monitoring loop"""
        logger.info("BLE monitor loop started")
        reconnect_attempts = 0
        
        while self._monitoring:
            try:
                # Auto-connect if enabled and not connected
                if (self.config.auto_connect and 
                    self._connection_state == BLEConnectionState.DISCONNECTED and
                    reconnect_attempts < self.config.max_reconnect_attempts):
                    
                    target_device = self.find_target_device()
                    if target_device:
                        logger.info(f"Attempting to connect to {target_device.name}")
                        if self.connect_to_device(target_device):
                            reconnect_attempts = 0  # Reset on successful connection
                        else:
                            reconnect_attempts += 1
                    else:
                        logger.debug("Target BLE device not found")
                
                # Monitor battery level if connected and enabled
                if (self.config.battery_monitoring and 
                    self._connected_device and 
                    self._connection_state == BLEConnectionState.CONNECTED):
                    
                    battery_level = self._get_battery_level()
                    if battery_level is not None:
                        self._emit_event('battery_level', {
                            'device': self._connected_device,
                            'battery_level': battery_level
                        })
                
                time.sleep(self.config.reconnect_interval)
                
            except Exception as e:
                logger.error(f"BLE monitor loop error: {e}")
                time.sleep(self.config.reconnect_interval)
    
    def _get_battery_level(self) -> Optional[int]:
        """Get battery level of connected device"""
        if not self._connected_device:
            return None
        
        try:
            # This is a simplified implementation
            # Real battery monitoring would require specific BLE services
            ps_script = f'''
            $deviceAddress = "{self._connected_device.address}"
            
            # Try to get battery information
            try {{
                $battery = Get-WmiObject Win32_Battery | Select-Object -First 1
                if ($battery) {{
                    $battery.EstimatedChargeRemaining
                }} else {{
                    $null
                }}
            }} catch {{
                $null
            }}
            '''
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_script
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return None


class EliteBLEController:
    """Elite Dangerous specific BLE controller"""
    
    def __init__(self, ble_manager: WindowsBLEManager):
        self.ble_manager = ble_manager
        self._key_mappings = self._setup_elite_key_mappings()
        
        # Register for BLE events
        self.ble_manager.add_callback('key_event', self._handle_key_event)
    
    def _setup_elite_key_mappings(self) -> Dict[str, KeyCode]:
        """Setup Elite Dangerous key mappings"""
        return {
            'target_next': KeyCode.T,
            'target_previous': KeyCode.Y,
            'target_next_hostile': KeyCode.H,
            'landing_gear': KeyCode.L,
            'cargo_scoop': KeyCode.C,
            'hardpoints': KeyCode.U,
            'lights': KeyCode.INSERT,
            'flight_assist': KeyCode.Z,
            'boost': KeyCode.TAB,
            'fsd_jump': KeyCode.J,
            'supercruise': KeyCode.J,  # With modifiers
            'galaxy_map': KeyCode.M,
            'system_map': KeyCode.N,
            'comms_panel': KeyCode.KEY_1,
            'ship_panel': KeyCode.KEY_4
        }
    
    def _handle_key_event(self, event: KeyboardEvent):
        """Handle BLE key events for Elite Dangerous"""
        logger.debug(f"Elite controller received key event: {event.key_code}")
        
        # Process the key event for Elite Dangerous specific actions
        # This would contain game-specific logic
        pass
    
    def send_elite_command(self, command: str) -> bool:
        """Send a command specific to Elite Dangerous"""
        if command not in self._key_mappings:
            logger.error(f"Unknown Elite command: {command}")
            return False
        
        key_code = self._key_mappings[command]
        
        # Send key press
        press_event = KeyboardEvent(key_code=key_code, is_pressed=True)
        if not self.ble_manager.send_key_input(press_event):
            return False
        
        # Small delay
        time.sleep(0.05)
        
        # Send key release
        release_event = KeyboardEvent(key_code=key_code, is_pressed=False)
        return self.ble_manager.send_key_input(release_event)
    
    def toggle_landing_gear(self) -> bool:
        """Toggle landing gear"""
        return self.send_elite_command('landing_gear')
    
    def toggle_hardpoints(self) -> bool:
        """Toggle hardpoints"""
        return self.send_elite_command('hardpoints')
    
    def target_next_ship(self) -> bool:
        """Target next ship"""
        return self.send_elite_command('target_next')
    
    def boost(self) -> bool:
        """Boost"""
        return self.send_elite_command('boost')


# Convenience functions
def setup_elite_ble_controller(device_name: str = "EDMC_Controller") -> Tuple[WindowsBLEManager, EliteBLEController]:
    """Setup BLE controller for Elite Dangerous"""
    config = BLEConfig(device_name_pattern=device_name)
    ble_manager = WindowsBLEManager(config)
    elite_controller = EliteBLEController(ble_manager)
    
    return ble_manager, elite_controller


def quick_ble_scan() -> List[BLEDevice]:
    """Quick BLE device scan"""
    manager = WindowsBLEManager()
    return manager.scan_for_devices(timeout=5.0)