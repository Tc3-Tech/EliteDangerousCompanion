"""
Elite Dangerous UI Widgets Package
Contains specialized widgets for ship viewing, gallery, and specifications.
"""

from .ship_gallery import ShipGalleryWidget, ShipThumbnail, ShipGalleryGrid, ShipFilterPanel, ShipGalleryCarousel
from .ship_viewer import ShipViewer3D, ShipViewerControls  
from .ship_specs_panel import ShipSpecificationPanel, AnimatedStatBar, ShipStatsCard, HardpointDisplay, InternalSlotsDisplay
from .ship_comparison import show_ship_comparison, ShipComparisonDialog, RadarChart, ComparisonTable

__all__ = [
    # Ship Gallery
    'ShipGalleryWidget',
    'ShipThumbnail', 
    'ShipGalleryGrid',
    'ShipFilterPanel',
    'ShipGalleryCarousel',
    
    # Ship Viewer
    'ShipViewer3D',
    'ShipViewerControls',
    
    # Ship Specifications
    'ShipSpecificationPanel',
    'AnimatedStatBar',
    'ShipStatsCard', 
    'HardpointDisplay',
    'InternalSlotsDisplay',
    
    # Ship Comparison
    'show_ship_comparison',
    'ShipComparisonDialog',
    'RadarChart',
    'ComparisonTable'
]