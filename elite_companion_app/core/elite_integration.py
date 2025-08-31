"""
Elite Dangerous Integration Manager
Coordinates all WSL-Windows integrations for the Elite Dangerous companion app.
"""
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .wsl_integration import WSLWindowsIntegration, EliteDangerousMonitor
from .process_monitor import WindowsProcessMonitor, ProcessMonitorConfig, get_elite_dangerous_status
from .journal_monitor import EliteJournalMonitor, JournalMonitorConfig, JournalEntry, JournalEventType
from .audio_bridge import WindowsAudioBridge, AudioConfig, EliteAudioIntegration
from .ble_integration import WindowsBLEManager, EliteBLEController, BLEConfig, setup_elite_ble_controller

logger = logging.getLogger(__name__)


@dataclass
class EliteIntegrationConfig:
    """Configuration for Elite Dangerous integration"""
    # File monitoring
    enable_journal_monitoring: bool = True
    journal_poll_interval: float = 0.5
    journal_history_size: int = 500
    
    # Process monitoring
    enable_process_monitoring: bool = True
    process_poll_interval: float = 2.0
    
    # Audio integration
    enable_audio_integration: bool = True
    enable_media_monitoring: bool = True
    audio_profile_on_game_start: bool = True
    
    # BLE integration
    enable_ble_integration: bool = True
    ble_device_name: str = "EDMC_Controller"
    ble_auto_connect: bool = True
    
    # Advanced settings
    auto_start_monitoring: bool = True
    game_detection_timeout: float = 30.0
    enable_performance_monitoring: bool = True


@dataclass
class EliteGameState:
    """Current state of Elite Dangerous game"""
    is_running: bool = False
    process_id: Optional[int] = None
    memory_usage_mb: float = 0.0
    cpu_usage: float = 0.0
    
    # Commander info
    commander_name: str = ""
    current_ship: str = ""
    current_system: str = ""
    current_station: str = ""
    credits: int = 0
    
    # Game state
    docked: bool = False
    landed: bool = False
    in_supercruise: bool = False
    in_hyperspace: bool = False
    
    # Last update
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_from_journal_entry(self, entry: JournalEntry):
        """Update state from journal entry"""
        self.last_updated = entry.timestamp
        
        if entry.event == JournalEventType.LOADGAME:
            self.commander_name = entry.get('Commander', '')
            self.current_ship = entry.get('Ship', '')
            self.credits = entry.get('Credits', 0)
        
        elif entry.event == JournalEventType.FSDJUMP:
            self.current_system = entry.get('StarSystem', '')
            self.in_hyperspace = False
            self.in_supercruise = True
            
        elif entry.event == JournalEventType.DOCKED:
            self.docked = True
            self.current_station = entry.get('StationName', '')
            self.in_supercruise = False
            
        elif entry.event == JournalEventType.UNDOCKED:
            self.docked = False
            self.current_station = ""
            
        elif entry.event == JournalEventType.TOUCHDOWN:
            self.landed = True
            self.in_supercruise = False
            
        elif entry.event == JournalEventType.LIFTOFF:
            self.landed = False
            
        elif entry.event == JournalEventType.SUPERCRUISEENTRY:
            self.in_supercruise = True
            self.docked = False
            self.landed = False
            
        elif entry.event == JournalEventType.SUPERCRUISEEXIT:
            self.in_supercruise = False


class EliteIntegrationManager:
    """Main manager for all Elite Dangerous integrations"""
    
    def __init__(self, config: EliteIntegrationConfig = None):
        self.config = config or EliteIntegrationConfig()
        
        # Core integrations
        self.wsl_integration = WSLWindowsIntegration()
        self.process_monitor = None
        self.journal_monitor = None
        self.audio_bridge = None
        self.ble_manager = None
        self.elite_controller = None
        
        # State management
        self.game_state = EliteGameState()
        self.is_initialized = False
        self.is_monitoring = False
        
        # Event callbacks
        self._callbacks = {
            'game_started': [],
            'game_stopped': [],
            'commander_loaded': [],
            'system_changed': [],
            'docking_changed': [],
            'journal_event': [],
            'audio_changed': [],
            'ble_event': [],
            'error': []
        }
        
        # Statistics
        self._stats = {
            'initialization_time': None,
            'journal_entries_processed': 0,
            'game_sessions': 0,
            'last_game_start': None,
            'last_game_stop': None
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
                logger.error(f"Integration callback error for {event_type}: {e}")
    
    def initialize(self) -> bool:
        """Initialize all integrations"""
        if self.is_initialized:
            return True
        
        start_time = datetime.now()
        logger.info("Initializing Elite Dangerous integrations...")
        
        try:
            # Check WSL environment
            if not self.wsl_integration.is_wsl:
                raise RuntimeError("Not running in WSL environment")
            
            # Initialize process monitoring
            if self.config.enable_process_monitoring:
                process_config = ProcessMonitorConfig(
                    poll_interval=self.config.process_poll_interval,
                    performance_monitoring=self.config.enable_performance_monitoring
                )
                self.process_monitor = WindowsProcessMonitor(process_config)
                self.process_monitor.add_callback('process_started', self._on_process_started)
                self.process_monitor.add_callback('process_stopped', self._on_process_stopped)
                self.process_monitor.add_callback('process_updated', self._on_process_updated)
                logger.info("Process monitor initialized")
            
            # Initialize journal monitoring
            if self.config.enable_journal_monitoring:
                journal_config = JournalMonitorConfig(
                    poll_interval=self.config.journal_poll_interval,
                    max_history_size=self.config.journal_history_size
                )
                self.journal_monitor = EliteJournalMonitor(journal_config)
                self.journal_monitor.add_callback('journal_entry', self._on_journal_entry)
                logger.info("Journal monitor initialized")
            
            # Initialize audio integration
            if self.config.enable_audio_integration:
                audio_config = AudioConfig(
                    enable_media_monitoring=self.config.enable_media_monitoring
                )
                self.audio_bridge = WindowsAudioBridge(audio_config)
                self.audio_bridge.add_callback('media_changed', self._on_media_changed)
                logger.info("Audio bridge initialized")
            
            # Initialize BLE integration
            if self.config.enable_ble_integration:
                ble_config = BLEConfig(
                    device_name_pattern=self.config.ble_device_name,
                    auto_connect=self.config.ble_auto_connect
                )
                self.ble_manager, self.elite_controller = setup_elite_ble_controller(
                    self.config.ble_device_name
                )
                self.ble_manager.add_callback('connection_changed', self._on_ble_connection_changed)
                logger.info("BLE integration initialized")
            
            self.is_initialized = True
            self._stats['initialization_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Elite Dangerous integrations initialized in {self._stats['initialization_time']:.2f}s")
            
            # Auto-start monitoring if configured
            if self.config.auto_start_monitoring:
                self.start_monitoring()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize integrations: {e}")
            self._emit_event('error', {'error': str(e), 'operation': 'initialize'})
            return False
    
    def start_monitoring(self) -> bool:
        """Start all monitoring services"""
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        if self.is_monitoring:
            logger.warning("Monitoring is already active")
            return True
        
        logger.info("Starting Elite Dangerous monitoring...")
        
        try:
            # Start process monitoring
            if self.process_monitor:
                self.process_monitor.start_monitoring()
            
            # Start journal monitoring
            if self.journal_monitor:
                self.journal_monitor.start_monitoring()
            
            # Start audio monitoring
            if self.audio_bridge and self.config.enable_media_monitoring:
                self.audio_bridge.start_media_monitoring()
            
            # Start BLE monitoring
            if self.ble_manager:
                self.ble_manager.start_monitoring()
            
            self.is_monitoring = True
            logger.info("All monitoring services started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            self._emit_event('error', {'error': str(e), 'operation': 'start_monitoring'})
            return False
    
    def stop_monitoring(self):
        """Stop all monitoring services"""
        if not self.is_monitoring:
            return
        
        logger.info("Stopping Elite Dangerous monitoring...")
        
        # Stop all monitors
        if self.process_monitor:
            self.process_monitor.stop_monitoring()
        
        if self.journal_monitor:
            self.journal_monitor.stop_monitoring()
        
        if self.audio_bridge:
            self.audio_bridge.stop_media_monitoring()
        
        if self.ble_manager:
            self.ble_manager.stop_monitoring()
        
        self.is_monitoring = False
        logger.info("All monitoring services stopped")
    
    def shutdown(self):
        """Shutdown all integrations"""
        logger.info("Shutting down Elite Dangerous integrations...")
        
        self.stop_monitoring()
        
        # Disconnect BLE devices
        if self.ble_manager and self.ble_manager.connected_device:
            self.ble_manager.disconnect_from_device()
        
        # Restore audio profile
        if self.audio_bridge:
            try:
                integration = EliteAudioIntegration(self.audio_bridge)
                integration.restore_audio_profile()
            except:
                pass
        
        self.is_initialized = False
        logger.info("Elite Dangerous integrations shutdown complete")
    
    def _on_process_started(self, data: Dict[str, Any]):
        """Handle process started event"""
        process = data['process']
        
        if process.name.lower() == 'elitedangerous64':
            logger.info(f"Elite Dangerous started (PID: {process.pid})")
            
            self.game_state.is_running = True
            self.game_state.process_id = process.pid
            self._stats['game_sessions'] += 1
            self._stats['last_game_start'] = data['timestamp']
            
            # Setup gaming audio profile
            if self.config.audio_profile_on_game_start and self.audio_bridge:
                try:
                    integration = EliteAudioIntegration(self.audio_bridge)
                    integration.setup_gaming_audio_profile()
                except Exception as e:
                    logger.error(f"Failed to setup audio profile: {e}")
            
            self._emit_event('game_started', {
                'process': process,
                'game_state': self.game_state,
                'timestamp': data['timestamp']
            })
    
    def _on_process_stopped(self, data: Dict[str, Any]):
        """Handle process stopped event"""
        process = data['process']
        
        if process.name.lower() == 'elitedangerous64':
            logger.info(f"Elite Dangerous stopped (PID: {process.pid})")
            
            self.game_state.is_running = False
            self.game_state.process_id = None
            self._stats['last_game_stop'] = data['timestamp']
            
            # Restore audio profile
            if self.audio_bridge:
                try:
                    integration = EliteAudioIntegration(self.audio_bridge)
                    integration.restore_audio_profile()
                except Exception as e:
                    logger.error(f"Failed to restore audio profile: {e}")
            
            self._emit_event('game_stopped', {
                'process': process,
                'game_state': self.game_state,
                'timestamp': data['timestamp']
            })
    
    def _on_process_updated(self, data: Dict[str, Any]):
        """Handle process updated event"""
        process = data['process']
        
        if process.name.lower() == 'elitedangerous64':
            self.game_state.memory_usage_mb = process.memory_mb
            self.game_state.cpu_usage = process.cpu_percent
    
    def _on_journal_entry(self, entry: JournalEntry):
        """Handle journal entry"""
        logger.debug(f"Journal entry: {entry.event_name}")
        
        # Update game state
        old_state = EliteGameState(
            commander_name=self.game_state.commander_name,
            current_system=self.game_state.current_system,
            docked=self.game_state.docked
        )
        
        self.game_state.update_from_journal_entry(entry)
        self._stats['journal_entries_processed'] += 1
        
        # Emit specific events for significant state changes
        if entry.event == JournalEventType.LOADGAME:
            self._emit_event('commander_loaded', {
                'entry': entry,
                'commander': self.game_state.commander_name,
                'ship': self.game_state.current_ship
            })
        
        elif entry.event == JournalEventType.FSDJUMP:
            self._emit_event('system_changed', {
                'entry': entry,
                'old_system': old_state.current_system,
                'new_system': self.game_state.current_system
            })
        
        elif entry.event in [JournalEventType.DOCKED, JournalEventType.UNDOCKED]:
            self._emit_event('docking_changed', {
                'entry': entry,
                'docked': self.game_state.docked,
                'station': self.game_state.current_station
            })
        
        # Emit general journal event
        self._emit_event('journal_event', {
            'entry': entry,
            'game_state': self.game_state
        })
    
    def _on_media_changed(self, media_info):
        """Handle media changed event"""
        self._emit_event('audio_changed', {
            'media_info': media_info,
            'timestamp': datetime.now()
        })
    
    def _on_ble_connection_changed(self, data: Dict[str, Any]):
        """Handle BLE connection changed event"""
        logger.info(f"BLE connection state: {data['state'].value}")
        self._emit_event('ble_event', data)
    
    def get_game_state(self) -> EliteGameState:
        """Get current game state"""
        return self.game_state
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics"""
        stats = dict(self._stats)
        
        if self.journal_monitor:
            journal_stats = self.journal_monitor.get_statistics()
            stats.update({f'journal_{k}': v for k, v in journal_stats.items()})
        
        if self.process_monitor:
            try:
                system_perf = self.process_monitor.get_system_performance()
                stats.update({f'system_{k}': v for k, v in system_perf.items()})
            except:
                pass
        
        stats.update({
            'is_initialized': self.is_initialized,
            'is_monitoring': self.is_monitoring,
            'game_running': self.game_state.is_running
        })
        
        return stats
    
    def send_elite_command(self, command: str) -> bool:
        """Send a command to Elite Dangerous via BLE"""
        if not self.elite_controller:
            logger.error("BLE controller not available")
            return False
        
        return self.elite_controller.send_elite_command(command)
    
    def wait_for_game_start(self, timeout: float = None) -> bool:
        """Wait for Elite Dangerous to start"""
        if timeout is None:
            timeout = self.config.game_detection_timeout
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if self.game_state.is_running:
                return True
            time.sleep(1.0)
        
        return False
    
    def get_journal_directory(self) -> Optional[Path]:
        """Get Elite Dangerous journal directory"""
        if self.journal_monitor:
            return self.journal_monitor.get_journal_directory()
        
        paths = self.wsl_integration.get_elite_dangerous_paths()
        journal_dir = paths.get('journal_dir')
        return journal_dir.to_pathlib() if journal_dir and journal_dir.exists() else None


# Convenience function for easy setup
def create_elite_integration(
    enable_all: bool = True,
    config_overrides: Dict[str, Any] = None
) -> EliteIntegrationManager:
    """Create and configure Elite integration manager"""
    
    config = EliteIntegrationConfig()
    
    if not enable_all:
        config.enable_journal_monitoring = False
        config.enable_process_monitoring = False
        config.enable_audio_integration = False
        config.enable_ble_integration = False
    
    # Apply config overrides
    if config_overrides:
        for key, value in config_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    manager = EliteIntegrationManager(config)
    
    # Add some default logging callbacks
    def log_game_events(data):
        if 'game_state' in data:
            state = data['game_state']
            logger.info(f"Game state: Running={state.is_running}, Commander={state.commander_name}")
    
    manager.add_callback('game_started', log_game_events)
    manager.add_callback('game_stopped', log_game_events)
    
    return manager