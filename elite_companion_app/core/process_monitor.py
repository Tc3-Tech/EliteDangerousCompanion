"""
Windows Process Monitoring from WSL
Advanced process detection and monitoring with performance metrics.
"""
import subprocess
import threading
import time
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import psutil

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a Windows process"""
    name: str
    pid: int
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    start_time: Optional[datetime] = None
    command_line: Optional[str] = None
    window_title: Optional[str] = None
    status: str = "running"
    
    def __post_init__(self):
        if isinstance(self.start_time, str):
            # Parse PowerShell datetime format
            try:
                self.start_time = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                self.start_time = None


@dataclass
class ProcessMonitorConfig:
    """Configuration for process monitoring"""
    target_processes: List[str] = field(default_factory=lambda: [
        "EliteDangerous64",
        "EDLaunch", 
        "EDH",
        "EDMC",
        "VoiceAttack",
        "obs64",
        "OBS",
        "Steam"
    ])
    poll_interval: float = 2.0
    performance_monitoring: bool = True
    window_title_monitoring: bool = True
    detailed_logging: bool = False


class WindowsProcessMonitor:
    """Monitor Windows processes from WSL with advanced features"""
    
    def __init__(self, config: ProcessMonitorConfig = None):
        self.config = config or ProcessMonitorConfig()
        self.is_running = False
        self._monitor_thread = None
        self._process_cache = {}
        self._callbacks = {
            'process_started': [],
            'process_stopped': [],
            'process_updated': [],
            'performance_alert': []
        }
        self._performance_thresholds = {
            'cpu_high': 80.0,  # High CPU usage percentage
            'memory_high': 2048.0,  # High memory usage in MB
        }
    
    def add_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Add event callback for process events"""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable):
        """Remove event callback"""
        if event_type in self._callbacks and callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)
    
    def set_performance_thresholds(self, cpu_high: float = 80.0, memory_high_mb: float = 2048.0):
        """Set performance alert thresholds"""
        self._performance_thresholds['cpu_high'] = cpu_high
        self._performance_thresholds['memory_high'] = memory_high_mb
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to all registered callbacks"""
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Callback error for {event_type}: {e}")
    
    def get_process_list(self, process_names: Optional[List[str]] = None) -> List[ProcessInfo]:
        """Get detailed information about Windows processes"""
        if process_names is None:
            process_names = self.config.target_processes
        
        processes = []
        
        for process_name in process_names:
            try:
                # Build PowerShell command for detailed process info
                ps_cmd = f"""
                Get-Process -Name "{process_name}" -ErrorAction SilentlyContinue | ForEach-Object {{
                    $proc = $_
                    $startTime = try {{ $proc.StartTime.ToString('o') }} catch {{ $null }}
                    $commandLine = try {{ 
                        (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine 
                    }} catch {{ $null }}
                    
                    [PSCustomObject]@{{
                        Name = $proc.Name
                        Id = $proc.Id
                        CPU = if ($proc.CPU) {{ [math]::Round($proc.CPU, 2) }} else {{ 0 }}
                        WorkingSet = [math]::Round($proc.WorkingSet / 1MB, 2)
                        StartTime = $startTime
                        CommandLine = $commandLine
                        Status = $proc.Responding.ToString()
                    }}
                }} | ConvertTo-Json
                """
                
                result = subprocess.run([
                    'powershell.exe', '-c', ps_cmd
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout.strip():
                    data = json.loads(result.stdout)
                    if isinstance(data, dict):
                        data = [data]  # Single process result
                    
                    for proc_data in data:
                        process_info = ProcessInfo(
                            name=proc_data.get('Name', process_name),
                            pid=proc_data.get('Id', 0),
                            cpu_percent=float(proc_data.get('CPU', 0)),
                            memory_mb=float(proc_data.get('WorkingSet', 0)),
                            start_time=proc_data.get('StartTime'),
                            command_line=proc_data.get('CommandLine'),
                            status=proc_data.get('Status', 'unknown')
                        )
                        processes.append(process_info)
                
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, 
                    json.JSONDecodeError, ValueError) as e:
                if self.config.detailed_logging:
                    logger.debug(f"Failed to get info for {process_name}: {e}")
        
        return processes
    
    def is_process_running(self, process_name: str) -> bool:
        """Quick check if a specific process is running"""
        try:
            result = subprocess.run([
                'powershell.exe', '-c',
                f'Get-Process -Name "{process_name}" -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                count = int(result.stdout.strip())
                return count > 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return False
    
    def get_process_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """Get process information by PID"""
        try:
            ps_cmd = f"""
            Get-Process -Id {pid} -ErrorAction SilentlyContinue | ForEach-Object {{
                $proc = $_
                $startTime = try {{ $proc.StartTime.ToString('o') }} catch {{ $null }}
                $commandLine = try {{ 
                    (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine 
                }} catch {{ $null }}
                
                [PSCustomObject]@{{
                    Name = $proc.Name
                    Id = $proc.Id
                    CPU = if ($proc.CPU) {{ [math]::Round($proc.CPU, 2) }} else {{ 0 }}
                    WorkingSet = [math]::Round($proc.WorkingSet / 1MB, 2)
                    StartTime = $startTime
                    CommandLine = $commandLine
                    Status = $proc.Responding.ToString()
                }}
            }} | ConvertTo-Json
            """
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_cmd
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                return ProcessInfo(
                    name=data.get('Name', ''),
                    pid=data.get('Id', pid),
                    cpu_percent=float(data.get('CPU', 0)),
                    memory_mb=float(data.get('WorkingSet', 0)),
                    start_time=data.get('StartTime'),
                    command_line=data.get('CommandLine'),
                    status=data.get('Status', 'unknown')
                )
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, 
                json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to get process info for PID {pid}: {e}")
        
        return None
    
    def get_elite_dangerous_info(self) -> Optional[ProcessInfo]:
        """Get detailed Elite Dangerous process information"""
        processes = self.get_process_list(["EliteDangerous64"])
        return processes[0] if processes else None
    
    def start_monitoring(self):
        """Start continuous process monitoring"""
        if self.is_running:
            logger.warning("Process monitoring is already running")
            return
        
        self.is_running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Process monitoring started")
    
    def stop_monitoring(self):
        """Stop process monitoring"""
        self.is_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        logger.info("Process monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Process monitor loop started")
        
        while self.is_running:
            try:
                current_processes = self.get_process_list()
                current_pids = {proc.pid: proc for proc in current_processes}
                previous_pids = set(self._process_cache.keys())
                current_pid_set = set(current_pids.keys())
                
                # Detect new processes
                new_pids = current_pid_set - previous_pids
                for pid in new_pids:
                    process = current_pids[pid]
                    self._process_cache[pid] = process
                    self._emit_event('process_started', {
                        'process': process,
                        'timestamp': datetime.now()
                    })
                    logger.info(f"Process started: {process.name} (PID: {process.pid})")
                
                # Detect stopped processes
                stopped_pids = previous_pids - current_pid_set
                for pid in stopped_pids:
                    if pid in self._process_cache:
                        process = self._process_cache.pop(pid)
                        self._emit_event('process_stopped', {
                            'process': process,
                            'timestamp': datetime.now()
                        })
                        logger.info(f"Process stopped: {process.name} (PID: {pid})")
                
                # Update existing processes and check performance
                if self.config.performance_monitoring:
                    for pid, process in current_pids.items():
                        if pid in self._process_cache:
                            old_process = self._process_cache[pid]
                            
                            # Check for performance alerts
                            if (process.cpu_percent > self._performance_thresholds['cpu_high'] or
                                process.memory_mb > self._performance_thresholds['memory_high']):
                                
                                self._emit_event('performance_alert', {
                                    'process': process,
                                    'alert_type': 'high_usage',
                                    'cpu_percent': process.cpu_percent,
                                    'memory_mb': process.memory_mb,
                                    'timestamp': datetime.now()
                                })
                            
                            # Emit update event if significant changes
                            if (abs(process.cpu_percent - old_process.cpu_percent) > 10 or
                                abs(process.memory_mb - old_process.memory_mb) > 100):
                                
                                self._emit_event('process_updated', {
                                    'process': process,
                                    'previous': old_process,
                                    'timestamp': datetime.now()
                                })
                        
                        self._process_cache[pid] = process
                
                time.sleep(self.config.poll_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(self.config.poll_interval)
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get overall system performance metrics"""
        try:
            result = subprocess.run([
                'powershell.exe', '-c',
                '''
                $cpu = Get-Counter "\\Processor(_Total)\\% Processor Time" -SampleInterval 1 -MaxSamples 1
                $mem = Get-CimInstance Win32_OperatingSystem
                $totalMem = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
                $freeMem = [math]::Round($mem.FreePhysicalMemory / 1MB, 2)
                $usedMem = $totalMem - $freeMem
                
                [PSCustomObject]@{
                    CPUPercent = [math]::Round($cpu.CounterSamples[0].CookedValue, 2)
                    TotalMemoryGB = $totalMem
                    UsedMemoryGB = $usedMem
                    FreeMemoryGB = $freeMem
                    MemoryUsagePercent = [math]::Round(($usedMem / $totalMem) * 100, 2)
                } | ConvertTo-Json
                '''
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.error(f"Failed to get system performance: {e}")
        
        return {}
    
    def kill_process(self, pid: int) -> bool:
        """Terminate a Windows process by PID"""
        try:
            result = subprocess.run([
                'powershell.exe', '-c',
                f'Stop-Process -Id {pid} -Force -PassThru'
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


# Convenience functions
def get_elite_dangerous_status() -> Dict[str, Any]:
    """Get comprehensive Elite Dangerous status"""
    monitor = WindowsProcessMonitor()
    
    elite_info = monitor.get_elite_dangerous_info()
    is_running = elite_info is not None
    
    status = {
        'running': is_running,
        'process_info': elite_info,
        'launcher_running': monitor.is_process_running("EDLaunch"),
        'timestamp': datetime.now()
    }
    
    if is_running:
        # Get additional process details
        status.update({
            'cpu_usage': elite_info.cpu_percent,
            'memory_usage_mb': elite_info.memory_mb,
            'responding': elite_info.status.lower() == 'true'
        })
    
    return status


def wait_for_elite_dangerous(timeout: int = 300) -> bool:
    """Wait for Elite Dangerous to start (with timeout in seconds)"""
    monitor = WindowsProcessMonitor()
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if monitor.is_process_running("EliteDangerous64"):
            return True
        time.sleep(2)
    
    return False