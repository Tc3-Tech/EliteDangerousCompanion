"""
Cross-Platform Audio/Media API Bridge
Provides access to Windows audio and media APIs from WSL for Elite Dangerous companion features.
"""
import subprocess
import json
import threading
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import base64
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioDeviceType(Enum):
    """Audio device types"""
    PLAYBACK = "Playback"
    RECORDING = "Recording"
    BOTH = "Both"


class MediaPlayerState(Enum):
    """Media player states"""
    PLAYING = "Playing"
    PAUSED = "Paused"
    STOPPED = "Stopped"
    UNKNOWN = "Unknown"


@dataclass
class AudioDevice:
    """Represents an audio device"""
    name: str
    device_type: AudioDeviceType
    is_default: bool = False
    is_enabled: bool = True
    volume: float = 1.0
    device_id: str = ""


@dataclass
class MediaInfo:
    """Current media information"""
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: int = 0  # seconds
    position: int = 0  # seconds
    state: MediaPlayerState = MediaPlayerState.UNKNOWN
    application: str = ""
    thumbnail: Optional[str] = None  # Base64 encoded thumbnail


@dataclass
class AudioConfig:
    """Audio bridge configuration"""
    enable_media_monitoring: bool = True
    enable_audio_control: bool = True
    media_poll_interval: float = 2.0
    volume_change_step: float = 0.05
    supported_apps: List[str] = field(default_factory=lambda: [
        "Spotify", "iTunes", "Windows Media Player", "VLC", "Chrome", "Firefox"
    ])


class WindowsAudioBridge:
    """Bridge for Windows audio and media APIs"""
    
    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()
        self.is_monitoring = False
        self._monitor_thread = None
        self._current_media = MediaInfo()
        self._callbacks = {
            'media_changed': [],
            'volume_changed': [],
            'device_changed': []
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
                logger.error(f"Audio bridge callback error for {event_type}: {e}")
    
    def get_audio_devices(self) -> List[AudioDevice]:
        """Get list of available audio devices"""
        devices = []
        
        try:
            # PowerShell script to get audio devices
            ps_script = '''
            Add-Type -AssemblyName System.Windows.Forms
            $devices = @()
            
            # Get playback devices
            $playbackDevices = Get-AudioDevice -List | Where-Object { $_.Type -eq "Playback" }
            foreach ($device in $playbackDevices) {
                $devices += [PSCustomObject]@{
                    Name = $device.Name
                    Type = "Playback"
                    IsDefault = $device.Default
                    IsEnabled = $device.Enabled
                    Volume = if ($device.Volume) { $device.Volume / 100 } else { 1.0 }
                    DeviceId = $device.Id
                }
            }
            
            # Get recording devices
            $recordingDevices = Get-AudioDevice -List | Where-Object { $_.Type -eq "Recording" }
            foreach ($device in $recordingDevices) {
                $devices += [PSCustomObject]@{
                    Name = $device.Name
                    Type = "Recording"
                    IsDefault = $device.Default
                    IsEnabled = $device.Enabled
                    Volume = if ($device.Volume) { $device.Volume / 100 } else { 1.0 }
                    DeviceId = $device.Id
                }
            }
            
            $devices | ConvertTo-Json
            '''
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_script
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                device_data = json.loads(result.stdout)
                if isinstance(device_data, dict):
                    device_data = [device_data]
                
                for data in device_data:
                    device_type = AudioDeviceType.PLAYBACK
                    if data.get('Type') == 'Recording':
                        device_type = AudioDeviceType.RECORDING
                    
                    devices.append(AudioDevice(
                        name=data.get('Name', ''),
                        device_type=device_type,
                        is_default=data.get('IsDefault', False),
                        is_enabled=data.get('IsEnabled', True),
                        volume=float(data.get('Volume', 1.0)),
                        device_id=data.get('DeviceId', '')
                    ))
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, 
                json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to get audio devices: {e}")
        
        return devices
    
    def set_default_audio_device(self, device_name: str, device_type: AudioDeviceType) -> bool:
        """Set the default audio device"""
        try:
            type_str = "Playback" if device_type == AudioDeviceType.PLAYBACK else "Recording"
            
            result = subprocess.run([
                'powershell.exe', '-c',
                f'Set-AudioDevice -Name "{device_name}" -Type {type_str}'
            ], capture_output=True, text=True, timeout=10)
            
            success = result.returncode == 0
            if success:
                self._emit_event('device_changed', {
                    'device_name': device_name,
                    'device_type': device_type,
                    'action': 'set_default'
                })
            
            return success
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def set_volume(self, volume: float, device_name: Optional[str] = None) -> bool:
        """Set system or device volume (0.0 to 1.0)"""
        try:
            volume_percent = max(0, min(100, int(volume * 100)))
            
            cmd = f'Set-AudioDevice -Volume {volume_percent}'
            if device_name:
                cmd += f' -Name "{device_name}"'
            
            result = subprocess.run([
                'powershell.exe', '-c', cmd
            ], capture_output=True, text=True, timeout=5)
            
            success = result.returncode == 0
            if success:
                self._emit_event('volume_changed', {
                    'volume': volume,
                    'device_name': device_name,
                    'volume_percent': volume_percent
                })
            
            return success
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def get_system_volume(self) -> float:
        """Get current system volume (0.0 to 1.0)"""
        try:
            result = subprocess.run([
                'powershell.exe', '-c',
                'Get-AudioDevice -Default | Select-Object -ExpandProperty Volume'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                volume_percent = int(result.stdout.strip())
                return volume_percent / 100.0
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return 1.0  # Default fallback
    
    def mute_audio(self, mute: bool = True, device_name: Optional[str] = None) -> bool:
        """Mute or unmute audio"""
        try:
            cmd = f'Set-AudioDevice -Mute:{str(mute).lower()}'
            if device_name:
                cmd += f' -Name "{device_name}"'
            
            result = subprocess.run([
                'powershell.exe', '-c', cmd
            ], capture_output=True, text=True, timeout=5)
            
            return result.returncode == 0
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def get_current_media_info(self) -> MediaInfo:
        """Get current media information from Windows"""
        try:
            # PowerShell script to get media session info
            ps_script = '''
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            
            $mediaManager = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync().GetAwaiter().GetResult()
            $currentSession = $mediaManager.GetCurrentSession()
            
            if ($currentSession) {
                $mediaProperties = $currentSession.TryGetMediaPropertiesAsync().GetAwaiter().GetResult()
                $playbackInfo = $currentSession.GetPlaybackInfo()
                $timelineProperties = $currentSession.GetTimelineProperties()
                
                $state = "Unknown"
                switch ($playbackInfo.PlaybackStatus) {
                    "Playing" { $state = "Playing" }
                    "Paused" { $state = "Paused" }
                    "Stopped" { $state = "Stopped" }
                }
                
                $mediaInfo = [PSCustomObject]@{
                    Title = $mediaProperties.Title
                    Artist = $mediaProperties.Artist
                    Album = $mediaProperties.AlbumTitle
                    Duration = if ($timelineProperties.EndTime) { $timelineProperties.EndTime.TotalSeconds } else { 0 }
                    Position = if ($timelineProperties.Position) { $timelineProperties.Position.TotalSeconds } else { 0 }
                    State = $state
                    Application = $currentSession.SourceAppUserModelId
                }
                
                # Try to get thumbnail
                if ($mediaProperties.Thumbnail) {
                    try {
                        $stream = $mediaProperties.Thumbnail.OpenReadAsync().GetAwaiter().GetResult()
                        $bytes = New-Object byte[] $stream.Size
                        $stream.ReadAsync($bytes, 0, $stream.Size).GetAwaiter().GetResult()
                        $stream.Close()
                        $mediaInfo | Add-Member -Name "Thumbnail" -Value ([Convert]::ToBase64String($bytes)) -MemberType NoteProperty
                    } catch {
                        $mediaInfo | Add-Member -Name "Thumbnail" -Value $null -MemberType NoteProperty
                    }
                } else {
                    $mediaInfo | Add-Member -Name "Thumbnail" -Value $null -MemberType NoteProperty
                }
                
                $mediaInfo | ConvertTo-Json
            } else {
                [PSCustomObject]@{
                    Title = ""
                    Artist = ""
                    Album = ""
                    Duration = 0
                    Position = 0
                    State = "Stopped"
                    Application = ""
                    Thumbnail = $null
                } | ConvertTo-Json
            }
            '''
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_script
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                
                state = MediaPlayerState.UNKNOWN
                try:
                    state = MediaPlayerState(data.get('State', 'Unknown'))
                except ValueError:
                    state = MediaPlayerState.UNKNOWN
                
                return MediaInfo(
                    title=data.get('Title', ''),
                    artist=data.get('Artist', ''),
                    album=data.get('Album', ''),
                    duration=int(float(data.get('Duration', 0))),
                    position=int(float(data.get('Position', 0))),
                    state=state,
                    application=data.get('Application', ''),
                    thumbnail=data.get('Thumbnail')
                )
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, 
                json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to get media info: {e}")
        
        return MediaInfo()
    
    def control_media(self, action: str) -> bool:
        """Control media playback (play, pause, next, previous, stop)"""
        try:
            # PowerShell script for media control
            ps_script = f'''
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            
            $mediaManager = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync().GetAwaiter().GetResult()
            $currentSession = $mediaManager.GetCurrentSession()
            
            if ($currentSession) {{
                switch ("{action}") {{
                    "play" {{ $currentSession.TryPlayAsync().GetAwaiter().GetResult() }}
                    "pause" {{ $currentSession.TryPauseAsync().GetAwaiter().GetResult() }}
                    "stop" {{ $currentSession.TryStopAsync().GetAwaiter().GetResult() }}
                    "next" {{ $currentSession.TrySkipNextAsync().GetAwaiter().GetResult() }}
                    "previous" {{ $currentSession.TrySkipPreviousAsync().GetAwaiter().GetResult() }}
                }}
                "Success"
            }} else {{
                "No active session"
            }}
            '''
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_script
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0 and "Success" in result.stdout
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def start_media_monitoring(self):
        """Start monitoring media changes"""
        if self.is_monitoring:
            return
        
        if not self.config.enable_media_monitoring:
            logger.info("Media monitoring disabled in configuration")
            return
        
        self.is_monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._media_monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Media monitoring started")
    
    def stop_media_monitoring(self):
        """Stop media monitoring"""
        self.is_monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        logger.info("Media monitoring stopped")
    
    def _media_monitor_loop(self):
        """Media monitoring loop"""
        logger.info("Media monitor loop started")
        
        while self.is_monitoring:
            try:
                current_media = self.get_current_media_info()
                
                # Check if media info has changed significantly
                if self._has_media_changed(current_media):
                    logger.debug(f"Media changed: {current_media.title} by {current_media.artist}")
                    self._current_media = current_media
                    self._emit_event('media_changed', current_media)
                
                time.sleep(self.config.media_poll_interval)
                
            except Exception as e:
                logger.error(f"Media monitor loop error: {e}")
                time.sleep(self.config.media_poll_interval)
    
    def _has_media_changed(self, new_media: MediaInfo) -> bool:
        """Check if media info has changed significantly"""
        if not self._current_media:
            return True
        
        # Compare key fields
        return (new_media.title != self._current_media.title or
                new_media.artist != self._current_media.artist or
                new_media.album != self._current_media.album or
                new_media.state != self._current_media.state or
                new_media.application != self._current_media.application)
    
    def get_cached_media_info(self) -> MediaInfo:
        """Get cached media information"""
        return self._current_media
    
    def play_sound_file(self, file_path: Path, volume: float = 1.0) -> bool:
        """Play a sound file"""
        try:
            volume_percent = max(0, min(100, int(volume * 100)))
            
            ps_script = f'''
            Add-Type -AssemblyName presentationCore
            $mediaPlayer = New-Object System.Windows.Media.MediaPlayer
            $mediaPlayer.Volume = {volume / 100.0}
            $mediaPlayer.Open([uri]::new("{file_path.as_posix()}"))
            $mediaPlayer.Play()
            Start-Sleep -Seconds 1
            '''
            
            result = subprocess.run([
                'powershell.exe', '-c', ps_script
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


class EliteAudioIntegration:
    """Elite Dangerous specific audio integration"""
    
    def __init__(self, audio_bridge: WindowsAudioBridge):
        self.audio_bridge = audio_bridge
        self._game_audio_profile = None
        self._original_volume = None
    
    def setup_gaming_audio_profile(self):
        """Setup audio profile optimized for Elite Dangerous"""
        try:
            # Save current volume
            self._original_volume = self.audio_bridge.get_system_volume()
            
            # Set optimal gaming volume (adjust as needed)
            self.audio_bridge.set_volume(0.7)  # 70% volume
            
            logger.info("Gaming audio profile activated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup gaming audio profile: {e}")
            return False
    
    def restore_audio_profile(self):
        """Restore original audio settings"""
        try:
            if self._original_volume is not None:
                self.audio_bridge.set_volume(self._original_volume)
                logger.info("Original audio profile restored")
                return True
        except Exception as e:
            logger.error(f"Failed to restore audio profile: {e}")
        
        return False
    
    def handle_docking_sound(self):
        """Play docking confirmation sound"""
        # This would play a custom docking sound
        # Implementation depends on having sound files
        pass
    
    def handle_jump_sound(self):
        """Play jump confirmation sound"""
        # This would play a custom jump sound
        # Implementation depends on having sound files
        pass


# Convenience functions
def get_current_playing_media() -> MediaInfo:
    """Quick access to current media info"""
    bridge = WindowsAudioBridge()
    return bridge.get_current_media_info()


def control_spotify(action: str) -> bool:
    """Control Spotify specifically"""
    bridge = WindowsAudioBridge()
    return bridge.control_media(action)


def set_elite_audio_profile() -> bool:
    """Quick setup for Elite Dangerous audio"""
    bridge = WindowsAudioBridge()
    integration = EliteAudioIntegration(bridge)
    return integration.setup_gaming_audio_profile()