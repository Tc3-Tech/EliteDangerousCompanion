"""
WSL-Windows Integration Utilities
Provides seamless access to Windows file system, processes, and APIs from WSL2.
"""
import os
import sys
import subprocess
import platform
from pathlib import Path, PurePath, PureWindowsPath
from typing import Optional, List, Dict, Any, Callable
import time
import threading
import logging
from dataclasses import dataclass
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class WindowsPath:
    """Represents a Windows path with WSL translation capabilities"""
    windows_path: str
    wsl_path: Optional[str] = None
    
    def __post_init__(self):
        if self.wsl_path is None:
            self.wsl_path = self._windows_to_wsl_path(self.windows_path)
    
    @staticmethod
    def _windows_to_wsl_path(windows_path: str) -> str:
        """Convert Windows path to WSL mount path"""
        # Handle environment variables
        if '%' in windows_path:
            # Get Windows environment variables through PowerShell
            try:
                result = subprocess.run([
                    'powershell.exe', '-c', f'echo "{windows_path}"'
                ], capture_output=True, text=True, check=True)
                windows_path = result.stdout.strip()
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to expand Windows path: {windows_path}")
        
        # Convert drive letter to WSL mount
        if re.match(r'^[A-Za-z]:', windows_path):
            drive = windows_path[0].lower()
            path_part = windows_path[2:].replace('\\', '/')
            return f"/mnt/{drive}{path_part}"
        
        return windows_path.replace('\\', '/')
    
    def exists(self) -> bool:
        """Check if the path exists in WSL"""
        return Path(self.wsl_path).exists() if self.wsl_path else False
    
    def to_pathlib(self) -> Path:
        """Convert to pathlib.Path for WSL"""
        return Path(self.wsl_path) if self.wsl_path else None


class WSLWindowsIntegration:
    """Main class for WSL-Windows integration functionality"""
    
    def __init__(self):
        self.is_wsl = self._detect_wsl()
        self._windows_username = None
        self._elite_paths = None
        
        if not self.is_wsl:
            logger.warning("Not running in WSL environment")
    
    def _detect_wsl(self) -> bool:
        """Detect if running in WSL environment"""
        try:
            # Check for WSL-specific indicators
            with open('/proc/version', 'r') as f:
                version_info = f.read().lower()
                return 'microsoft' in version_info or 'wsl' in version_info
        except FileNotFoundError:
            return False
    
    @property
    def windows_username(self) -> Optional[str]:
        """Get the Windows username"""
        if self._windows_username is None:
            try:
                # Get Windows username through PowerShell
                result = subprocess.run([
                    'powershell.exe', '-c', '$env:USERNAME'
                ], capture_output=True, text=True, check=True)
                self._windows_username = result.stdout.strip()
            except subprocess.CalledProcessError:
                logger.error("Failed to get Windows username")
                return None
        
        return self._windows_username
    
    def get_windows_userprofile(self) -> Optional[WindowsPath]:
        """Get the Windows USERPROFILE directory"""
        try:
            result = subprocess.run([
                'powershell.exe', '-c', '$env:USERPROFILE'
            ], capture_output=True, text=True, check=True)
            profile_path = result.stdout.strip()
            return WindowsPath(profile_path)
        except subprocess.CalledProcessError:
            logger.error("Failed to get Windows USERPROFILE")
            return None
    
    def get_elite_dangerous_paths(self) -> Dict[str, WindowsPath]:
        """Get Elite Dangerous file paths"""
        if self._elite_paths is None:
            userprofile = self.get_windows_userprofile()
            if not userprofile:
                return {}
            
            self._elite_paths = {
                'journal_dir': WindowsPath(
                    f"{userprofile.windows_path}\\Saved Games\\Frontier Developments\\Elite Dangerous"
                ),
                'screenshots_dir': WindowsPath(
                    f"{userprofile.windows_path}\\Pictures\\Frontier Developments\\Elite Dangerous"
                ),
                'config_dir': WindowsPath(
                    f"{userprofile.windows_path}\\AppData\\Local\\Frontier Developments\\Elite Dangerous\\Options"
                )
            }
        
        return self._elite_paths
    
    def is_process_running(self, process_name: str) -> bool:
        """Check if a Windows process is running"""
        try:
            result = subprocess.run([
                'powershell.exe', '-c',
                f'Get-Process -Name "{process_name}" -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count'
            ], capture_output=True, text=True, check=True)
            
            count = int(result.stdout.strip())
            return count > 0
        except (subprocess.CalledProcessError, ValueError):
            return False
    
    def get_running_processes(self, filter_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of running Windows processes"""
        try:
            cmd = 'Get-Process'
            if filter_name:
                cmd += f' -Name "*{filter_name}*"'
            cmd += ' | Select-Object Name,Id,CPU,WorkingSet | ConvertTo-Json'
            
            result = subprocess.run([
                'powershell.exe', '-c', cmd
            ], capture_output=True, text=True, check=True)
            
            processes = json.loads(result.stdout)
            if isinstance(processes, dict):
                processes = [processes]  # Single result
            
            return processes
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
    
    def get_windows_audio_devices(self) -> List[Dict[str, Any]]:
        """Get Windows audio devices"""
        try:
            result = subprocess.run([
                'powershell.exe', '-c',
                'Get-AudioDevice | Select-Object Name,Type,Default | ConvertTo-Json'
            ], capture_output=True, text=True, check=True)
            
            devices = json.loads(result.stdout)
            if isinstance(devices, dict):
                devices = [devices]
            
            return devices
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            logger.warning("Failed to get Windows audio devices")
            return []
    
    def execute_windows_command(self, command: str, shell: str = 'cmd') -> subprocess.CompletedProcess:
        """Execute a command in Windows"""
        if shell.lower() == 'powershell':
            cmd = ['powershell.exe', '-c', command]
        else:
            cmd = ['cmd.exe', '/c', command]
        
        return subprocess.run(cmd, capture_output=True, text=True)
    
    def get_file_info(self, path: WindowsPath) -> Optional[Dict[str, Any]]:
        """Get detailed file information from Windows"""
        try:
            result = subprocess.run([
                'powershell.exe', '-c',
                f'Get-Item "{path.windows_path}" | Select-Object Name,Length,LastWriteTime,CreationTime | ConvertTo-Json'
            ], capture_output=True, text=True, check=True)
            
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return None


class EliteDangerousMonitor:
    """Monitor Elite Dangerous game state and journal files"""
    
    def __init__(self, wsl_integration: WSLWindowsIntegration):
        self.wsl = wsl_integration
        self.is_running = False
        self._monitor_thread = None
        self._callbacks = {
            'process_state': [],
            'journal_update': [],
            'file_created': []
        }
        self._last_journal_file = None
        self._last_journal_size = 0
        
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
                logger.error(f"Callback error for {event_type}: {e}")
    
    def is_elite_running(self) -> bool:
        """Check if Elite Dangerous is currently running"""
        return self.wsl.is_process_running("EliteDangerous64")
    
    def get_latest_journal_file(self) -> Optional[Path]:
        """Get the most recent journal file"""
        paths = self.wsl.get_elite_dangerous_paths()
        journal_dir = paths.get('journal_dir')
        
        if not journal_dir or not journal_dir.exists():
            return None
        
        journal_path = journal_dir.to_pathlib()
        journal_files = list(journal_path.glob("Journal.*.log"))
        
        if not journal_files:
            return None
        
        # Return the most recently modified journal file
        return max(journal_files, key=lambda x: x.stat().st_mtime)
    
    def start_monitoring(self, poll_interval: float = 1.0):
        """Start monitoring Elite Dangerous"""
        if self.is_running:
            return
        
        self.is_running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(poll_interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Elite Dangerous monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        logger.info("Elite Dangerous monitoring stopped")
    
    def _monitor_loop(self, poll_interval: float):
        """Main monitoring loop"""
        last_process_state = False
        
        while self.is_running:
            try:
                # Check process state
                current_process_state = self.is_elite_running()
                if current_process_state != last_process_state:
                    self._emit_event('process_state', {
                        'running': current_process_state,
                        'timestamp': time.time()
                    })
                    last_process_state = current_process_state
                
                # Check journal files
                if current_process_state:
                    self._check_journal_updates()
                
                time.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(poll_interval)
    
    def _check_journal_updates(self):
        """Check for journal file updates"""
        try:
            current_journal = self.get_latest_journal_file()
            
            if current_journal is None:
                return
            
            # Check if this is a new journal file
            if self._last_journal_file != str(current_journal):
                self._last_journal_file = str(current_journal)
                self._last_journal_size = 0
                self._emit_event('file_created', {
                    'file': current_journal,
                    'timestamp': time.time()
                })
            
            # Check for size changes (new content)
            current_size = current_journal.stat().st_size
            if current_size > self._last_journal_size:
                # Read new content
                with open(current_journal, 'r', encoding='utf-8') as f:
                    f.seek(self._last_journal_size)
                    new_content = f.read()
                
                self._emit_event('journal_update', {
                    'file': current_journal,
                    'new_content': new_content,
                    'size_delta': current_size - self._last_journal_size,
                    'timestamp': time.time()
                })
                
                self._last_journal_size = current_size
                
        except Exception as e:
            logger.error(f"Journal check error: {e}")


# Convenience functions
def get_elite_journal_directory() -> Optional[Path]:
    """Quick access to Elite Dangerous journal directory"""
    integration = WSLWindowsIntegration()
    paths = integration.get_elite_dangerous_paths()
    journal_dir = paths.get('journal_dir')
    return journal_dir.to_pathlib() if journal_dir and journal_dir.exists() else None


def is_elite_dangerous_running() -> bool:
    """Quick check if Elite Dangerous is running"""
    integration = WSLWindowsIntegration()
    return integration.is_process_running("EliteDangerous64")


def get_windows_username() -> Optional[str]:
    """Quick access to Windows username"""
    integration = WSLWindowsIntegration()
    return integration.windows_username