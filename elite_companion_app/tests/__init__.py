"""
Elite Dangerous Companion App Test Suite
Contains comprehensive tests for all components including fidget mode.
"""

# Test configuration
import os
import sys

# Add the app root to the path for testing
app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_root not in sys.path:
    sys.path.insert(0, app_root)

__all__ = ['app_root']