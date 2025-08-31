#!/usr/bin/env python3
"""
Elite Dangerous WSL Integration Example
Demonstrates how to use the WSL-Windows integration components.
"""
import sys
import os
from pathlib import Path
import time
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.elite_integration import create_elite_integration, EliteIntegrationConfig
from core.journal_monitor import JournalEventType
from core.ble_integration import KeyCode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EliteCompanionExample:
    """Example Elite Dangerous companion app using WSL integration"""
    
    def __init__(self):
        # Create integration manager with custom config
        config_overrides = {
            'journal_poll_interval': 0.3,  # Fast polling for demo
            'enable_performance_monitoring': True,
            'enable_media_monitoring': True,
            'ble_auto_connect': True
        }
        
        self.integration = create_elite_integration(
            enable_all=True,
            config_overrides=config_overrides
        )
        
        # Setup event handlers
        self.setup_event_handlers()
        
        # Game state tracking
        self.current_commander = None
        self.current_system = None
        self.jump_count = 0
    
    def setup_event_handlers(self):
        """Setup event handlers for various integration events"""
        
        # Game lifecycle events
        self.integration.add_callback('game_started', self.on_game_started)
        self.integration.add_callback('game_stopped', self.on_game_stopped)
        self.integration.add_callback('commander_loaded', self.on_commander_loaded)
        
        # Journal events
        self.integration.add_callback('journal_event', self.on_journal_event)
        self.integration.add_callback('system_changed', self.on_system_changed)
        self.integration.add_callback('docking_changed', self.on_docking_changed)
        
        # Audio events
        self.integration.add_callback('audio_changed', self.on_audio_changed)
        
        # BLE events
        self.integration.add_callback('ble_event', self.on_ble_event)
        
        # Error handling
        self.integration.add_callback('error', self.on_error)
    
    def on_game_started(self, data):
        """Handle Elite Dangerous game start"""
        process = data['process']
        logger.info(f"🚀 Elite Dangerous started! PID: {process.pid}")
        logger.info(f"   Memory: {process.memory_mb:.1f} MB")
        logger.info(f"   CPU: {process.cpu_percent:.1f}%")
        
        # Reset tracking variables
        self.jump_count = 0
        
        print("\n" + "="*60)
        print("🌟 ELITE DANGEROUS COMPANION ACTIVE 🌟")
        print("="*60)
    
    def on_game_stopped(self, data):
        """Handle Elite Dangerous game stop"""
        logger.info("👋 Elite Dangerous stopped")
        
        # Print session summary
        if self.current_commander:
            print(f"\n📊 Session Summary for CMDR {self.current_commander}:")
            print(f"   💫 Systems visited: {self.jump_count}")
            if self.current_system:
                print(f"   📍 Last system: {self.current_system}")
        
        print("\n" + "="*60)
        print("🌙 COMPANION STANDING BY")
        print("="*60)
    
    def on_commander_loaded(self, data):
        """Handle commander load"""
        entry = data['entry']
        commander = data['commander']
        ship = data['ship']
        
        self.current_commander = commander
        
        logger.info(f"👨‍🚀 Commander loaded: {commander}")
        logger.info(f"🚢 Ship: {ship}")
        
        if entry.get('Credits'):
            credits = entry.get('Credits')
            logger.info(f"💰 Credits: {credits:,}")
        
        # Send a welcome message via BLE (if connected)
        try:
            # This would trigger a custom BLE command
            # For demo, we'll just log it
            logger.info("📡 Sending welcome signal to BLE controller...")
        except Exception as e:
            logger.debug(f"BLE welcome signal failed: {e}")
    
    def on_journal_event(self, data):
        """Handle general journal events"""
        entry = data['entry']
        
        # Log interesting events
        if entry.event in [
            JournalEventType.FSDJUMP,
            JournalEventType.DOCKED,
            JournalEventType.UNDOCKED,
            JournalEventType.TOUCHDOWN,
            JournalEventType.LIFTOFF
        ]:
            logger.info(f"📝 Journal: {entry.event_name}")
        
        # Handle specific events with custom logic
        if entry.event == JournalEventType.INTERDICTION:
            logger.warning("⚠️  INTERDICTION DETECTED!")
            self.handle_interdiction(entry)
        
        elif entry.event == JournalEventType.SCREENSHOT:
            screenshot_file = entry.get('Filename', '')
            logger.info(f"📸 Screenshot saved: {screenshot_file}")
        
        elif entry.event == JournalEventType.MARKETBUY:
            commodity = entry.get('Type', 'Unknown')
            count = entry.get('Count', 0)
            cost = entry.get('TotalCost', 0)
            logger.info(f"🛒 Bought {count}x {commodity} for {cost:,} CR")
        
        elif entry.event == JournalEventType.MARKETSELL:
            commodity = entry.get('Type', 'Unknown')
            count = entry.get('Count', 0)
            profit = entry.get('TotalSale', 0)
            logger.info(f"💵 Sold {count}x {commodity} for {profit:,} CR")
    
    def on_system_changed(self, data):
        """Handle system jump"""
        entry = data['entry']
        old_system = data['old_system']
        new_system = data['new_system']
        
        self.current_system = new_system
        self.jump_count += 1
        
        logger.info(f"🌟 Jumped to {new_system}")
        
        if entry.get('JumpDist'):
            distance = entry.get('JumpDist')
            logger.info(f"   📏 Jump distance: {distance:.2f} ly")
        
        if entry.get('FuelUsed'):
            fuel_used = entry.get('FuelUsed')
            fuel_level = entry.get('FuelLevel', 0)
            logger.info(f"   ⛽ Fuel: {fuel_level:.1f}T (-{fuel_used:.1f}T)")
            
            # Warn if fuel is getting low
            if fuel_level < 1.0:
                logger.warning("⚠️  LOW FUEL WARNING!")
        
        # Update BLE controller with system info (if available)
        try:
            # This would send system name to BLE display
            logger.debug(f"📡 Updating BLE display: {new_system}")
        except Exception as e:
            logger.debug(f"BLE update failed: {e}")
    
    def on_docking_changed(self, data):
        """Handle docking/undocking"""
        entry = data['entry']
        docked = data['docked']
        station = data.get('station', '')
        
        if docked:
            logger.info(f"🏗️  Docked at {station}")
            
            # Play docking sound
            try:
                # This would trigger audio feedback
                logger.info("🔊 Playing docking confirmation sound")
            except Exception as e:
                logger.debug(f"Audio feedback failed: {e}")
        else:
            logger.info(f"🚀 Undocked from {station}")
    
    def on_audio_changed(self, data):
        """Handle audio/media changes"""
        media_info = data['media_info']
        
        if media_info.title and media_info.artist:
            logger.info(f"🎵 Now playing: {media_info.title} by {media_info.artist}")
            
            # You could integrate with Spotify/other media players
            if media_info.state.value == "Playing":
                logger.debug("🎶 Music is playing - adjusting game audio")
    
    def on_ble_event(self, data):
        """Handle BLE events"""
        state = data['state']
        device = data.get('device')
        
        if device:
            logger.info(f"📱 BLE {device.name}: {state.value}")
        else:
            logger.info(f"📱 BLE: {state.value}")
        
        # Handle BLE connection for Elite controls
        if state.value == "connected":
            logger.info("🎮 Elite controller ready!")
        elif state.value == "disconnected":
            logger.warning("🔌 Elite controller disconnected")
    
    def on_error(self, data):
        """Handle integration errors"""
        error = data['error']
        operation = data.get('operation', 'unknown')
        logger.error(f"❌ Integration error in {operation}: {error}")
    
    def handle_interdiction(self, entry):
        """Handle interdiction event"""
        submitted = entry.get('Submitted', False)
        is_player = entry.get('IsPlayer', False)
        interdicted_by = entry.get('Interdictor', 'Unknown')
        
        if submitted:
            logger.warning(f"😰 Submitted to interdiction by {interdicted_by}")
        else:
            logger.info(f"💪 Escaped interdiction by {interdicted_by}")
        
        if is_player:
            logger.warning("🏴‍☠️ PLAYER INTERDICTION - PvP ALERT!")
        
        # Could trigger BLE alert or audio warning here
    
    def demonstrate_ble_commands(self):
        """Demonstrate BLE command sending"""
        if not self.integration.elite_controller:
            logger.info("🎮 BLE controller not available for demo")
            return
        
        logger.info("🎮 Demonstrating BLE commands...")
        
        commands = [
            ('target_next', '🎯 Targeting next ship'),
            ('landing_gear', '🛬 Toggling landing gear'),
            ('hardpoints', '🔫 Toggling hardpoints')
        ]
        
        for command, description in commands:
            logger.info(description)
            success = self.integration.send_elite_command(command)
            if success:
                logger.info(f"   ✅ Command sent successfully")
            else:
                logger.warning(f"   ❌ Command failed")
            time.sleep(2)
    
    def run(self):
        """Run the example application"""
        try:
            logger.info("🔧 Initializing Elite Dangerous integration...")
            
            if not self.integration.initialize():
                logger.error("❌ Failed to initialize integration")
                return False
            
            logger.info("✅ Integration initialized successfully")
            
            # Start monitoring
            if not self.integration.start_monitoring():
                logger.error("❌ Failed to start monitoring")
                return False
            
            logger.info("👁️  Monitoring started - waiting for Elite Dangerous...")
            print("\n" + "="*60)
            print("🔍 MONITORING FOR ELITE DANGEROUS")
            print("   Start Elite Dangerous to see integration in action!")
            print("   Press Ctrl+C to stop monitoring")
            print("="*60)
            
            # Main monitoring loop
            try:
                while True:
                    time.sleep(5)
                    
                    # Print periodic statistics
                    stats = self.integration.get_statistics()
                    if stats.get('game_running'):
                        game_state = self.integration.get_game_state()
                        logger.debug(f"📊 Game running - Memory: {game_state.memory_usage_mb:.1f}MB, "
                                   f"CPU: {game_state.cpu_usage:.1f}%")
                    
                    # Demonstrate BLE commands if game is running and commander is loaded
                    # (Uncomment to test BLE functionality)
                    # if (stats.get('game_running') and self.current_commander and 
                    #     stats.get('journal_entries_processed', 0) > 5):
                    #     self.demonstrate_ble_commands()
                    #     time.sleep(30)  # Wait before next demo
            
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping monitoring...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
        
        finally:
            # Cleanup
            logger.info("🧹 Cleaning up...")
            self.integration.shutdown()
            logger.info("👋 Integration example completed")


def main():
    """Main function"""
    print("🌟 Elite Dangerous WSL Integration Example")
    print("="*60)
    
    # Check if we're in WSL
    try:
        with open('/proc/version', 'r') as f:
            if 'microsoft' not in f.read().lower():
                print("⚠️  This example should be run in WSL2 environment")
                return 1
    except FileNotFoundError:
        print("⚠️  This doesn't appear to be a Linux environment")
        return 1
    
    # Create and run the example
    example = EliteCompanionExample()
    success = example.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())