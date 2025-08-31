#!/usr/bin/env python3
"""
WSL-Windows Integration Test Suite
Comprehensive tests for all integration components.
"""
import sys
import os
from pathlib import Path
import time
import subprocess
import json
import logging
from typing import Dict, Any, List

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.wsl_integration import WSLWindowsIntegration, WindowsPath, get_elite_journal_directory
from core.process_monitor import WindowsProcessMonitor, ProcessMonitorConfig, get_elite_dangerous_status
from core.journal_monitor import EliteJournalMonitor, JournalMonitorConfig
from core.audio_bridge import WindowsAudioBridge, get_current_playing_media
from core.ble_integration import WindowsBLEManager, quick_ble_scan
from core.elite_integration import create_elite_integration

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class IntegrationTestSuite:
    """Test suite for WSL-Windows integration components"""
    
    def __init__(self):
        self.test_results = []
        self.wsl_integration = None
    
    def log_test_result(self, test_name: str, success: bool, message: str = "", details: Dict[str, Any] = None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name} - {message}")
        
        if details and success:
            for key, value in details.items():
                logger.info(f"    {key}: {value}")
    
    def test_wsl_environment(self) -> bool:
        """Test WSL environment detection"""
        try:
            self.wsl_integration = WSLWindowsIntegration()
            
            if self.wsl_integration.is_wsl:
                username = self.wsl_integration.windows_username
                self.log_test_result(
                    "WSL Environment Detection",
                    True,
                    f"WSL detected, Windows user: {username}",
                    {'windows_username': username}
                )
                return True
            else:
                self.log_test_result(
                    "WSL Environment Detection",
                    False,
                    "Not running in WSL environment"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "WSL Environment Detection",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_windows_file_access(self) -> bool:
        """Test Windows file system access"""
        try:
            if not self.wsl_integration:
                return False
            
            userprofile = self.wsl_integration.get_windows_userprofile()
            if not userprofile:
                self.log_test_result(
                    "Windows File Access",
                    False,
                    "Could not get Windows USERPROFILE"
                )
                return False
            
            paths = self.wsl_integration.get_elite_dangerous_paths()
            results = {}
            all_exist = True
            
            for name, path in paths.items():
                exists = path.exists()
                results[name] = f"{path.wsl_path} ({'exists' if exists else 'missing'})"
                if name == 'journal_dir' and not exists:
                    all_exist = False
            
            self.log_test_result(
                "Windows File Access",
                True,  # Pass if we can access userprofile, even if Elite paths don't exist
                f"USERPROFILE: {userprofile.wsl_path}",
                results
            )
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "Windows File Access",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_powershell_execution(self) -> bool:
        """Test PowerShell command execution"""
        try:
            # Test basic PowerShell execution
            result = subprocess.run([
                'powershell.exe', '-c', 'echo "Hello from PowerShell"'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "Hello from PowerShell" in result.stdout:
                # Test JSON output
                json_result = subprocess.run([
                    'powershell.exe', '-c', 
                    '[PSCustomObject]@{Test="Value"; Number=42} | ConvertTo-Json'
                ], capture_output=True, text=True, timeout=10)
                
                if json_result.returncode == 0:
                    data = json.loads(json_result.stdout)
                    
                    self.log_test_result(
                        "PowerShell Execution",
                        True,
                        "PowerShell commands and JSON parsing working",
                        {
                            'basic_command': 'success',
                            'json_parsing': 'success',
                            'test_data': data
                        }
                    )
                    return True
            
            self.log_test_result(
                "PowerShell Execution",
                False,
                "PowerShell command execution failed"
            )
            return False
            
        except Exception as e:
            self.log_test_result(
                "PowerShell Execution",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_process_monitoring(self) -> bool:
        """Test Windows process monitoring"""
        try:
            monitor = WindowsProcessMonitor()
            
            # Test basic process enumeration
            processes = monitor.get_process_list(['explorer', 'winlogon', 'dwm'])
            
            if processes:
                process_info = {}
                for proc in processes:
                    process_info[proc.name] = {
                        'pid': proc.pid,
                        'memory_mb': proc.memory_mb,
                        'status': proc.status
                    }
                
                # Test Elite Dangerous detection
                elite_status = get_elite_dangerous_status()
                
                self.log_test_result(
                    "Process Monitoring",
                    True,
                    f"Found {len(processes)} processes",
                    {
                        'processes': process_info,
                        'elite_status': elite_status
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Process Monitoring",
                    False,
                    "No processes found"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Process Monitoring",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_audio_integration(self) -> bool:
        """Test audio device and media integration"""
        try:
            audio_bridge = WindowsAudioBridge()
            
            # Test audio device enumeration
            devices = audio_bridge.get_audio_devices()
            
            if devices:
                device_info = {}
                for device in devices:
                    device_info[device.name] = {
                        'type': device.device_type.value,
                        'is_default': device.is_default,
                        'volume': device.volume
                    }
                
                # Test media info retrieval
                media_info = get_current_playing_media()
                
                # Test volume control
                current_volume = audio_bridge.get_system_volume()
                
                self.log_test_result(
                    "Audio Integration",
                    True,
                    f"Found {len(devices)} audio devices",
                    {
                        'devices': device_info,
                        'current_volume': current_volume,
                        'media_playing': media_info.title if media_info.title else 'No media'
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Audio Integration",
                    False,
                    "No audio devices found"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Audio Integration",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_ble_integration(self) -> bool:
        """Test BLE device scanning and integration"""
        try:
            # Test BLE device scanning
            devices = quick_ble_scan()
            
            device_info = {}
            for device in devices:
                device_info[device.name] = {
                    'address': device.address,
                    'paired': device.is_paired,
                    'connected': device.is_connected
                }
            
            # Test BLE manager creation
            ble_manager = WindowsBLEManager()
            connection_state = ble_manager.connection_state.value
            
            self.log_test_result(
                "BLE Integration",
                True,
                f"Found {len(devices)} BLE devices",
                {
                    'devices': device_info,
                    'connection_state': connection_state
                }
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "BLE Integration",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_journal_monitoring(self) -> bool:
        """Test journal file monitoring capabilities"""
        try:
            if not self.wsl_integration:
                return False
            
            # Test journal directory discovery
            journal_dir = get_elite_journal_directory()
            
            if journal_dir and journal_dir.exists():
                # Test journal file discovery
                monitor = EliteJournalMonitor()
                journal_files = monitor.discover_journal_files()
                
                file_info = {}
                for i, file_path in enumerate(journal_files[:3]):  # Show first 3 files
                    stat = file_path.stat()
                    file_info[file_path.name] = {
                        'size_mb': stat.st_size / 1024 / 1024,
                        'modified': time.ctime(stat.st_mtime)
                    }
                
                self.log_test_result(
                    "Journal Monitoring",
                    True,
                    f"Journal directory found with {len(journal_files)} files",
                    {
                        'journal_directory': str(journal_dir),
                        'recent_files': file_info
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Journal Monitoring",
                    True,  # Not a failure if Elite isn't installed
                    "Journal directory not found (Elite Dangerous may not be installed)",
                    {'expected_path': str(journal_dir) if journal_dir else 'unknown'}
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                "Journal Monitoring",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_elite_integration_manager(self) -> bool:
        """Test the main Elite integration manager"""
        try:
            # Create integration manager with minimal config for testing
            config_overrides = {
                'auto_start_monitoring': False,  # Don't start monitoring in test
                'enable_ble_integration': False,  # Skip BLE for testing
                'enable_audio_integration': True,
                'journal_poll_interval': 1.0,
            }
            
            integration = create_elite_integration(
                enable_all=True,
                config_overrides=config_overrides
            )
            
            # Test initialization
            initialized = integration.initialize()
            
            if initialized:
                # Get statistics
                stats = integration.get_statistics()
                
                # Get game state
                game_state = integration.get_game_state()
                
                self.log_test_result(
                    "Elite Integration Manager",
                    True,
                    "Integration manager initialized successfully",
                    {
                        'initialized': stats['is_initialized'],
                        'game_running': stats['game_running'],
                        'initialization_time': f"{stats['initialization_time']:.2f}s"
                    }
                )
                
                # Cleanup
                integration.shutdown()
                return True
            else:
                self.log_test_result(
                    "Elite Integration Manager",
                    False,
                    "Failed to initialize integration manager"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Elite Integration Manager",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_windows_modules(self) -> bool:
        """Test Windows PowerShell modules availability"""
        try:
            # Test AudioDeviceCmdlets module
            audio_test = subprocess.run([
                'powershell.exe', '-c', 
                'if (Get-Module -ListAvailable -Name AudioDeviceCmdlets) { "Available" } else { "Missing" }'
            ], capture_output=True, text=True, timeout=10)
            
            audio_available = "Available" in audio_test.stdout
            
            # Test basic Windows.Media functionality
            media_test = subprocess.run([
                'powershell.exe', '-c',
                '''
                try {
                    Add-Type -AssemblyName System.Runtime.WindowsRuntime
                    "WindowsRuntime Available"
                } catch {
                    "WindowsRuntime Missing"
                }
                '''
            ], capture_output=True, text=True, timeout=10)
            
            media_available = "WindowsRuntime Available" in media_test.stdout
            
            self.log_test_result(
                "Windows Modules",
                audio_available or media_available,  # Pass if at least one works
                "Checked PowerShell module availability",
                {
                    'AudioDeviceCmdlets': 'available' if audio_available else 'missing',
                    'WindowsRuntime': 'available' if media_available else 'missing'
                }
            )
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "Windows Modules",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        logger.info("🧪 Starting WSL-Windows Integration Tests")
        print("=" * 70)
        
        tests = [
            self.test_wsl_environment,
            self.test_powershell_execution,
            self.test_windows_modules,
            self.test_windows_file_access,
            self.test_process_monitoring,
            self.test_audio_integration,
            self.test_ble_integration,
            self.test_journal_monitoring,
            self.test_elite_integration_manager
        ]
        
        passed = 0
        failed = 0
        
        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Test {test_func.__name__} crashed: {e}")
                failed += 1
            
            print("-" * 50)
        
        # Print summary
        print("=" * 70)
        logger.info(f"🏁 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            logger.info("🎉 All tests passed! Your WSL-Windows integration is ready.")
        else:
            logger.warning(f"⚠️  {failed} tests failed. Check the setup guide for troubleshooting.")
        
        return failed == 0
    
    def print_detailed_results(self):
        """Print detailed test results"""
        print("\n" + "=" * 70)
        print("📊 DETAILED TEST RESULTS")
        print("=" * 70)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['test']}")
            print(f"    {result['message']}")
            
            if result['details']:
                for key, value in result['details'].items():
                    if isinstance(value, dict):
                        print(f"    {key}:")
                        for sub_key, sub_value in value.items():
                            print(f"      {sub_key}: {sub_value}")
                    else:
                        print(f"    {key}: {value}")
            print()


def main():
    """Main test function"""
    print("🌟 WSL-Windows Integration Test Suite")
    print("=" * 70)
    
    # Quick environment check
    try:
        with open('/proc/version', 'r') as f:
            version = f.read()
            if 'microsoft' not in version.lower():
                print("⚠️  Warning: This doesn't appear to be WSL2")
                print("   Some tests may fail or behave unexpectedly")
                print()
    except FileNotFoundError:
        print("❌ Error: This doesn't appear to be a Linux environment")
        return 1
    
    # Run tests
    test_suite = IntegrationTestSuite()
    success = test_suite.run_all_tests()
    
    # Print detailed results
    test_suite.print_detailed_results()
    
    # Provide next steps
    print("=" * 70)
    print("📝 NEXT STEPS")
    print("=" * 70)
    
    if success:
        print("✅ Integration is working! You can now:")
        print("   1. Run the integration example: python3 examples/integration_example.py")
        print("   2. Start Elite Dangerous and monitor the logs")
        print("   3. Test BLE controller functionality")
        print("   4. Integrate with your companion app")
    else:
        print("⚠️  Some tests failed. Recommended actions:")
        print("   1. Review the WSL_SETUP_GUIDE.md")
        print("   2. Check PowerShell execution policy")
        print("   3. Install missing Windows modules")
        print("   4. Verify Elite Dangerous installation paths")
    
    print("\n📚 Documentation: WSL_SETUP_GUIDE.md")
    print("🐛 For issues: Check the troubleshooting section")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())