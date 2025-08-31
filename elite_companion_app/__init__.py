"""
Elite Dangerous Companion App
A performance-optimized overlay application for Elite Dangerous.
"""

__version__ = "1.0.0"
__author__ = "Elite Dangerous Companion Team"

# Standard path setup for all modules
import sys
import os
from pathlib import Path

# Add the app root to Python path if not already there
app_root = Path(__file__).parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))