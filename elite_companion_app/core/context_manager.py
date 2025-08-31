"""
Context Manager for handling context-sensitive hardware controls.
Manages what each button and potentiometer does based on current app state.
"""
from typing import Dict, Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass


class AppContext(Enum):
    """Different contexts/modes the app can be in"""
    MAIN_MENU = "main_menu"
    HUD_TUNING = "hud_tuning"
    SHIP_VIEWER = "ship_viewer"
    MEDIA_CONTROL = "media_control"
    ELITE_DATA = "elite_data"
    SETTINGS = "settings"


@dataclass
class InputBinding:
    """Defines what a hardware input does in a specific context"""
    action: Callable
    description: str
    icon: Optional[str] = None


class ContextManager:
    """Manages context-sensitive hardware input mappings"""
    
    def __init__(self):
        self.current_context = AppContext.MAIN_MENU
        self.context_stack = [AppContext.MAIN_MENU]  # For nested menus
        
        # Hardware input mappings per context
        self.button_mappings: Dict[AppContext, Dict[int, InputBinding]] = {}
        self.pot_mappings: Dict[AppContext, InputBinding] = {}
        
        # Context change callbacks
        self.context_change_callbacks = []
        
    def set_context(self, context: AppContext, push_to_stack: bool = False):
        """Change the current context"""
        if push_to_stack:
            self.context_stack.append(context)
        else:
            self.context_stack = [context]
            
        old_context = self.current_context
        self.current_context = context
        
        # Notify listeners of context change
        for callback in self.context_change_callbacks:
            callback(old_context, context)
    
    def pop_context(self):
        """Return to previous context"""
        if len(self.context_stack) > 1:
            self.context_stack.pop()
            old_context = self.current_context
            self.current_context = self.context_stack[-1]
            
            for callback in self.context_change_callbacks:
                callback(old_context, self.current_context)
    
    def register_button_mapping(self, context: AppContext, button_id: int, binding: InputBinding):
        """Register what a button does in a specific context"""
        if context not in self.button_mappings:
            self.button_mappings[context] = {}
        self.button_mappings[context][button_id] = binding
    
    def register_pot_mapping(self, context: AppContext, binding: InputBinding):
        """Register what the potentiometer does in a specific context"""
        self.pot_mappings[context] = binding
    
    def handle_button_press(self, button_id: int):
        """Handle a button press in the current context"""
        if (self.current_context in self.button_mappings and 
            button_id in self.button_mappings[self.current_context]):
            binding = self.button_mappings[self.current_context][button_id]
            binding.action()
    
    def handle_pot_change(self, value: float):
        """Handle potentiometer change in the current context"""
        if self.current_context in self.pot_mappings:
            binding = self.pot_mappings[self.current_context]
            binding.action(value)
    
    def get_button_description(self, button_id: int) -> str:
        """Get description of what a button does in current context"""
        if (self.current_context in self.button_mappings and 
            button_id in self.button_mappings[self.current_context]):
            return self.button_mappings[self.current_context][button_id].description
        return "Unassigned"
    
    def get_pot_description(self) -> str:
        """Get description of what the pot does in current context"""
        if self.current_context in self.pot_mappings:
            return self.pot_mappings[self.current_context].description
        return "Unassigned"
    
    def add_context_change_callback(self, callback: Callable[[AppContext, AppContext], None]):
        """Add callback for when context changes"""
        self.context_change_callbacks.append(callback)