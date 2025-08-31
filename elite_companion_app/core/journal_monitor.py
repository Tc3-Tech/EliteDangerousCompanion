"""
Elite Dangerous Journal File Monitoring System
Real-time monitoring and parsing of Elite Dangerous journal files with event processing.
"""
import json
import time
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
from enum import Enum
import hashlib
from collections import deque

from .wsl_integration import WSLWindowsIntegration, WindowsPath

logger = logging.getLogger(__name__)


class JournalEventType(Enum):
    """Elite Dangerous journal event types"""
    # Core Events
    FILEHEADER = "Fileheader"
    SHUTDOWN = "Shutdown"
    LOADGAME = "LoadGame"
    NEWCOMMANDER = "NewCommander"
    LOADOUT = "Loadout"
    
    # Ship and Station Events
    DOCKED = "Docked"
    UNDOCKED = "Undocked"
    FSDJUMP = "FSDJump"
    SUPERCRUISEENTRY = "SupercruiseEntry"
    SUPERCRUISEEXIT = "SupercruiseExit"
    TOUCHDOWN = "Touchdown"
    LIFTOFF = "Liftoff"
    
    # Market and Trading
    MARKET = "Market"
    MARKETBUY = "MarketBuy"
    MARKETSELL = "MarketSell"
    OUTFITTING = "Outfitting"
    SHIPYARD = "Shipyard"
    
    # Exploration
    SCAN = "Scan"
    FSSDISCOVERYSCAN = "FSSDiscoveryScan"
    SAASIGNALSFOUND = "SAASignalsFound"
    SCREENSHOT = "Screenshot"
    
    # Combat
    INTERDICTION = "Interdiction"
    INTERDICTED = "Interdicted"
    PVPKILL = "PvPKill"
    SHIPKILLED = "ShipKilled"
    
    # Missions
    MISSIONACCEPTED = "MissionAccepted"
    MISSIONCOMPLETED = "MissionCompleted"
    MISSIONFAILED = "MissionFailed"
    MISSIONABANDONED = "MissionAbandoned"
    
    # Engineering
    ENGINEERCRAFT = "EngineerCraft"
    ENGINEERCONTRIBUTION = "EngineerContribution"
    
    # Fleet Carrier
    CARRIERJUMP = "CarrierJump"
    CARRIERSTATS = "CarrierStats"
    
    # Unknown/Custom
    UNKNOWN = "Unknown"


@dataclass
class JournalEntry:
    """Represents a parsed journal entry"""
    timestamp: datetime
    event: JournalEventType
    raw_data: Dict[str, Any]
    file_path: Path
    line_number: int
    checksum: str = field(default="")
    
    def __post_init__(self):
        if not self.checksum:
            # Generate checksum for duplicate detection
            content = f"{self.timestamp.isoformat()}{self.event.value}{json.dumps(self.raw_data, sort_keys=True)}"
            self.checksum = hashlib.md5(content.encode()).hexdigest()
    
    @property
    def event_name(self) -> str:
        return self.event.value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the raw journal data"""
        return self.raw_data.get(key, default)
    
    def has_key(self, key: str) -> bool:
        """Check if a key exists in the journal data"""
        return key in self.raw_data


@dataclass
class JournalMonitorConfig:
    """Configuration for journal monitoring"""
    poll_interval: float = 0.5  # Fast polling for real-time updates
    max_history_size: int = 1000  # Maximum number of entries to keep in memory
    enable_duplicate_detection: bool = True
    parse_all_events: bool = True
    event_filters: Set[JournalEventType] = field(default_factory=set)
    max_file_age_hours: int = 24  # Only monitor files modified within this time
    buffer_size: int = 8192  # File read buffer size
    
    def should_process_event(self, event_type: JournalEventType) -> bool:
        """Check if an event should be processed based on filters"""
        if not self.event_filters:
            return True  # Process all events if no filter is set
        return event_type in self.event_filters


class JournalFileMonitor:
    """Monitors a specific journal file for changes"""
    
    def __init__(self, file_path: Path, config: JournalMonitorConfig):
        self.file_path = file_path
        self.config = config
        self._last_size = 0
        self._last_mtime = 0
        self._processed_checksums = set()
        self._file_handle = None
        
        # Initialize file state
        if self.file_path.exists():
            stat = self.file_path.stat()
            self._last_size = stat.st_size
            self._last_mtime = stat.st_mtime
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the file handle"""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
    
    def has_changes(self) -> bool:
        """Check if the file has been modified"""
        if not self.file_path.exists():
            return False
        
        stat = self.file_path.stat()
        return (stat.st_size != self._last_size or 
                stat.st_mtime != self._last_mtime)
    
    def read_new_entries(self) -> List[JournalEntry]:
        """Read new entries from the file"""
        if not self.file_path.exists():
            return []
        
        entries = []
        
        try:
            # Open file if not already open
            if not self._file_handle:
                self._file_handle = open(self.file_path, 'r', encoding='utf-8')
                self._file_handle.seek(self._last_size)
            
            # Seek to last position
            self._file_handle.seek(self._last_size)
            
            line_number = self._get_current_line_number()
            
            # Read new content
            while True:
                line = self._file_handle.readline()
                if not line:
                    break  # End of file
                
                line = line.strip()
                if not line:
                    continue
                
                line_number += 1
                
                try:
                    entry = self._parse_journal_line(line, line_number)
                    if entry and self._should_include_entry(entry):
                        entries.append(entry)
                except Exception as e:
                    logger.error(f"Failed to parse journal line {line_number}: {e}")
                    logger.debug(f"Problematic line: {line}")
            
            # Update file state
            stat = self.file_path.stat()
            self._last_size = stat.st_size
            self._last_mtime = stat.st_mtime
            
        except Exception as e:
            logger.error(f"Error reading journal file {self.file_path}: {e}")
            self.close()  # Close and reopen on next attempt
        
        return entries
    
    def _get_current_line_number(self) -> int:
        """Estimate current line number based on file position"""
        if not self._file_handle:
            return 0
        
        # This is an approximation - for exact line numbers, we'd need to track them
        current_pos = self._file_handle.tell()
        if current_pos == 0:
            return 0
        
        # Rough estimate based on average line length
        return max(0, int(current_pos / 150))  # Assume ~150 chars per line on average
    
    def _parse_journal_line(self, line: str, line_number: int) -> Optional[JournalEntry]:
        """Parse a single journal line into a JournalEntry"""
        try:
            data = json.loads(line)
            
            # Extract timestamp
            timestamp_str = data.get('timestamp', '')
            if not timestamp_str:
                return None
            
            # Parse Elite's timestamp format
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Extract event type
            event_name = data.get('event', '')
            event_type = JournalEventType.UNKNOWN
            
            # Try to match known event types
            for event_enum in JournalEventType:
                if event_enum.value.lower() == event_name.lower():
                    event_type = event_enum
                    break
            
            if event_type == JournalEventType.UNKNOWN and event_name:
                # Log unknown events for future handling
                logger.debug(f"Unknown journal event: {event_name}")
            
            return JournalEntry(
                timestamp=timestamp,
                event=event_type,
                raw_data=data,
                file_path=self.file_path,
                line_number=line_number
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse journal line: {e}")
            return None
    
    def _should_include_entry(self, entry: JournalEntry) -> bool:
        """Check if an entry should be included based on config"""
        # Check event filter
        if not self.config.should_process_event(entry.event):
            return False
        
        # Check for duplicates
        if self.config.enable_duplicate_detection:
            if entry.checksum in self._processed_checksums:
                return False
            self._processed_checksums.add(entry.checksum)
            
            # Limit checksum cache size
            if len(self._processed_checksums) > self.config.max_history_size:
                # Remove oldest checksums (simple approach)
                old_checksums = list(self._processed_checksums)[:100]
                for checksum in old_checksums:
                    self._processed_checksums.discard(checksum)
        
        return True


class EliteJournalMonitor:
    """Main journal monitoring system for Elite Dangerous"""
    
    def __init__(self, config: JournalMonitorConfig = None):
        self.config = config or JournalMonitorConfig()
        self.wsl_integration = WSLWindowsIntegration()
        
        self.is_running = False
        self._monitor_thread = None
        self._file_monitors = {}  # Path -> JournalFileMonitor
        self._entry_history = deque(maxlen=self.config.max_history_size)
        
        # Event callbacks
        self._callbacks = {
            'journal_entry': [],
            'file_rotated': [],
            'monitoring_started': [],
            'monitoring_stopped': [],
            'error': []
        }
        
        # Statistics
        self._stats = {
            'entries_processed': 0,
            'files_monitored': 0,
            'last_entry_time': None,
            'monitoring_start_time': None
        }
    
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
    
    def get_journal_directory(self) -> Optional[Path]:
        """Get the Elite Dangerous journal directory"""
        paths = self.wsl_integration.get_elite_dangerous_paths()
        journal_dir = paths.get('journal_dir')
        
        if journal_dir and journal_dir.exists():
            return journal_dir.to_pathlib()
        
        return None
    
    def discover_journal_files(self) -> List[Path]:
        """Discover all current journal files"""
        journal_dir = self.get_journal_directory()
        if not journal_dir:
            return []
        
        journal_files = []
        
        try:
            # Find all journal files
            pattern = "Journal.*.log"
            files = list(journal_dir.glob(pattern))
            
            # Filter by age if configured
            if self.config.max_file_age_hours > 0:
                cutoff_time = time.time() - (self.config.max_file_age_hours * 3600)
                files = [f for f in files if f.stat().st_mtime > cutoff_time]
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            journal_files.extend(files)
            
        except Exception as e:
            logger.error(f"Error discovering journal files: {e}")
        
        return journal_files
    
    def get_active_journal_file(self) -> Optional[Path]:
        """Get the currently active journal file"""
        files = self.discover_journal_files()
        return files[0] if files else None
    
    def start_monitoring(self):
        """Start journal file monitoring"""
        if self.is_running:
            logger.warning("Journal monitoring is already running")
            return
        
        journal_dir = self.get_journal_directory()
        if not journal_dir:
            raise RuntimeError("Cannot find Elite Dangerous journal directory")
        
        self.is_running = True
        self._stats['monitoring_start_time'] = datetime.now()
        
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        
        logger.info(f"Journal monitoring started for directory: {journal_dir}")
        self._emit_event('monitoring_started', {
            'journal_directory': journal_dir,
            'timestamp': self._stats['monitoring_start_time']
        })
    
    def stop_monitoring(self):
        """Stop journal file monitoring"""
        self.is_running = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        
        # Close all file monitors
        for monitor in self._file_monitors.values():
            monitor.close()
        self._file_monitors.clear()
        
        logger.info("Journal monitoring stopped")
        self._emit_event('monitoring_stopped', {
            'timestamp': datetime.now(),
            'stats': self.get_statistics()
        })
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Journal monitor loop started")
        
        while self.is_running:
            try:
                # Discover current journal files
                current_files = self.discover_journal_files()
                current_paths = {str(f) for f in current_files}
                
                # Remove monitors for files that no longer exist
                to_remove = []
                for path_str in self._file_monitors:
                    if path_str not in current_paths:
                        to_remove.append(path_str)
                
                for path_str in to_remove:
                    monitor = self._file_monitors.pop(path_str)
                    monitor.close()
                    logger.info(f"Stopped monitoring removed file: {path_str}")
                
                # Add monitors for new files
                for file_path in current_files:
                    path_str = str(file_path)
                    if path_str not in self._file_monitors:
                        monitor = JournalFileMonitor(file_path, self.config)
                        self._file_monitors[path_str] = monitor
                        logger.info(f"Started monitoring new file: {path_str}")
                        
                        self._emit_event('file_rotated', {
                            'file_path': file_path,
                            'timestamp': datetime.now()
                        })
                
                # Check all monitored files for changes
                all_new_entries = []
                
                for path_str, monitor in list(self._file_monitors.items()):
                    try:
                        if monitor.has_changes():
                            new_entries = monitor.read_new_entries()
                            all_new_entries.extend(new_entries)
                    except Exception as e:
                        logger.error(f"Error reading from {path_str}: {e}")
                        self._emit_event('error', {
                            'error': str(e),
                            'file_path': path_str,
                            'timestamp': datetime.now()
                        })
                
                # Process new entries
                for entry in sorted(all_new_entries, key=lambda x: x.timestamp):
                    self._process_journal_entry(entry)
                
                # Update statistics
                self._stats['files_monitored'] = len(self._file_monitors)
                
                time.sleep(self.config.poll_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                self._emit_event('error', {
                    'error': str(e),
                    'timestamp': datetime.now()
                })
                time.sleep(self.config.poll_interval)
    
    def _process_journal_entry(self, entry: JournalEntry):
        """Process a new journal entry"""
        # Add to history
        self._entry_history.append(entry)
        
        # Update statistics
        self._stats['entries_processed'] += 1
        self._stats['last_entry_time'] = entry.timestamp
        
        # Emit event
        self._emit_event('journal_entry', entry)
        
        logger.debug(f"Processed journal entry: {entry.event_name} at {entry.timestamp}")
    
    def get_recent_entries(self, count: int = 100, 
                          event_filter: Optional[Set[JournalEventType]] = None) -> List[JournalEntry]:
        """Get recent journal entries"""
        entries = list(self._entry_history)
        
        if event_filter:
            entries = [e for e in entries if e.event in event_filter]
        
        return entries[-count:] if count > 0 else entries
    
    def get_latest_entry(self, event_type: Optional[JournalEventType] = None) -> Optional[JournalEntry]:
        """Get the most recent journal entry, optionally filtered by event type"""
        entries = list(self._entry_history)
        entries.reverse()  # Search from most recent
        
        for entry in entries:
            if event_type is None or entry.event == event_type:
                return entry
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return {
            **self._stats,
            'history_size': len(self._entry_history),
            'active_monitors': len(self._file_monitors),
            'is_running': self.is_running
        }
    
    def wait_for_event(self, event_type: JournalEventType, 
                      timeout: float = 30.0) -> Optional[JournalEntry]:
        """Wait for a specific event type (blocking)"""
        start_time = time.time()
        
        # Check if event already exists in recent history
        latest = self.get_latest_entry(event_type)
        if latest and (time.time() - latest.timestamp.timestamp()) < 60:
            return latest
        
        # Wait for new event
        event_received = threading.Event()
        received_entry = None
        
        def event_callback(entry: JournalEntry):
            nonlocal received_entry
            if entry.event == event_type:
                received_entry = entry
                event_received.set()
        
        self.add_callback('journal_entry', event_callback)
        
        try:
            if event_received.wait(timeout):
                return received_entry
        finally:
            self.remove_callback('journal_entry', event_callback)
        
        return None


# Convenience functions
def monitor_elite_journal(callback: Callable[[JournalEntry], None], 
                         event_filter: Optional[Set[JournalEventType]] = None) -> EliteJournalMonitor:
    """Create and start a journal monitor with a callback"""
    config = JournalMonitorConfig()
    if event_filter:
        config.event_filters = event_filter
    
    monitor = EliteJournalMonitor(config)
    monitor.add_callback('journal_entry', callback)
    monitor.start_monitoring()
    
    return monitor


def get_commander_status() -> Dict[str, Any]:
    """Get current commander status from journal"""
    monitor = EliteJournalMonitor()
    
    # Look for recent LoadGame event
    recent_files = monitor.discover_journal_files()
    if not recent_files:
        return {'error': 'No journal files found'}
    
    # Quick scan of the most recent file
    try:
        with open(recent_files[0], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Look for the most recent LoadGame event
        for line in reversed(lines):
            try:
                data = json.loads(line.strip())
                if data.get('event') == 'LoadGame':
                    return {
                        'commander': data.get('Commander'),
                        'ship': data.get('Ship'),
                        'ship_id': data.get('ShipID'),
                        'game_mode': data.get('GameMode'),
                        'group': data.get('Group'),
                        'credits': data.get('Credits'),
                        'loan': data.get('Loan'),
                        'timestamp': data.get('timestamp')
                    }
            except (json.JSONDecodeError, KeyError):
                continue
    except Exception as e:
        return {'error': str(e)}
    
    return {'error': 'No recent LoadGame event found'}