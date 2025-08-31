"""
Elite Dangerous Utilities Package
Contains utility functions and classes for the application.
"""

from .image_optimizer import get_smart_image_manager, ImageCache, ImageOptimizer, SmartImageManager

__all__ = [
    'get_smart_image_manager',
    'ImageCache', 
    'ImageOptimizer',
    'SmartImageManager'
]