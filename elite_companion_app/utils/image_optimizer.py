"""
Elite Dangerous Asset Image Optimizer
Optimizes ship images for 1024x768 display with memory-efficient loading.
"""
import os
import sys
import time
from typing import Dict, Tuple, List, Optional, Callable
from PyQt6.QtGui import QPixmap, QImage, QPainter, QTransform
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QObject, QTimer

# Add app root to path for imports
from pathlib import Path
app_root = Path(__file__).parent.parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

from data.ship_database import get_ship_database


class ImageCache(QObject):
    """Memory-efficient image cache with LRU eviction"""
    
    cache_hit = pyqtSignal(str)  # Cache hit signal
    cache_miss = pyqtSignal(str)  # Cache miss signal
    
    def __init__(self, parent=None, max_memory_mb: int = 50, max_items: int = 100):
        super().__init__(parent)
        
        self.max_memory_bytes = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.max_items = max_items
        
        self.cache = {}  # key -> {"image": QPixmap, "size": int, "last_used": float}
        self.current_memory = 0
        self.access_order = []  # LRU tracking
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[QPixmap]:
        """Get image from cache"""
        if key in self.cache:
            # Update access time
            self.cache[key]["last_used"] = time.time()
            
            # Update LRU order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            self.hits += 1
            self.cache_hit.emit(key)
            return self.cache[key]["image"]
        
        self.misses += 1
        self.cache_miss.emit(key)
        return None
    
    def put(self, key: str, image: QPixmap):
        """Add image to cache"""
        if key in self.cache:
            # Update existing
            old_size = self.cache[key]["size"]
            new_size = self.estimate_image_memory(image)
            
            self.cache[key] = {
                "image": image,
                "size": new_size,
                "last_used": time.time()
            }
            
            self.current_memory += (new_size - old_size)
            
            # Update LRU order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new
            size = self.estimate_image_memory(image)
            
            self.cache[key] = {
                "image": image,
                "size": size,
                "last_used": time.time()
            }
            
            self.current_memory += size
            self.access_order.append(key)
        
        # Evict if necessary
        self.evict_if_necessary()
    
    def estimate_image_memory(self, image: QPixmap) -> int:
        """Estimate memory usage of QPixmap"""
        # Rough estimate: width * height * 4 bytes per pixel (ARGB)
        return image.width() * image.height() * 4
    
    def evict_if_necessary(self):
        """Evict oldest items if memory/count limits exceeded"""
        while (self.current_memory > self.max_memory_bytes or 
               len(self.cache) > self.max_items) and self.access_order:
            
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                self.current_memory -= self.cache[oldest_key]["size"]
                del self.cache[oldest_key]
                self.evictions += 1
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.access_order.clear()
        self.current_memory = 0
    
    def get_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": hit_rate,
            "current_items": len(self.cache),
            "max_items": self.max_items,
            "current_memory_mb": self.current_memory / (1024 * 1024),
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024)
        }


class ImageOptimizer(QObject):
    """Optimizes images for display performance"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_display_size = QSize(1024, 768)
        self.cache = ImageCache(self)
        
        # Optimization presets
        self.presets = {
            "thumbnail": QSize(120, 90),
            "gallery": QSize(150, 120),
            "viewer": QSize(400, 300),
            "fullscreen": QSize(800, 600)
        }
    
    def optimize_for_preset(self, image_path: str, preset: str) -> Optional[QPixmap]:
        """Optimize image for specific preset"""
        if preset not in self.presets:
            return None
        
        target_size = self.presets[preset]
        cache_key = f"{image_path}_{preset}"
        
        # Check cache first
        cached_image = self.cache.get(cache_key)
        if cached_image:
            return cached_image
        
        # Load and optimize image
        optimized = self.load_and_optimize(image_path, target_size)
        if optimized:
            self.cache.put(cache_key, optimized)
        
        return optimized
    
    def load_and_optimize(self, image_path: str, target_size: QSize) -> Optional[QPixmap]:
        """Load and optimize image for target size"""
        if not os.path.exists(image_path):
            return None
        
        try:
            # Load original image
            original = QPixmap(image_path)
            if original.isNull():
                return None
            
            # Skip optimization if already smaller than target
            if (original.width() <= target_size.width() and 
                original.height() <= target_size.height()):
                return original
            
            # Scale image maintaining aspect ratio
            optimized = original.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            return optimized
            
        except Exception as e:
            print(f"Error optimizing image {image_path}: {e}")
            return None
    
    def preload_ship_images(self, ship_keys: List[str], preset: str = "viewer",
                          progress_callback: Optional[Callable] = None):
        """Preload ship images for better performance"""
        ship_database = get_ship_database()
        total_ships = len(ship_keys)
        
        for i, ship_key in enumerate(ship_keys):
            ship = ship_database.get_ship(ship_key)
            if ship:
                image_path = ship.get_image_path()
                self.optimize_for_preset(image_path, preset)
            
            if progress_callback:
                progress_callback(i + 1, total_ships)
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get image cache statistics"""
        return self.cache.get_stats()
    
    def clear_cache(self):
        """Clear image cache"""
        self.cache.clear()


class AsynchronousImageLoader(QThread):
    """Background thread for loading images"""
    
    image_loaded = pyqtSignal(str, QPixmap)  # ship_key, optimized_image
    progress_updated = pyqtSignal(int, int)  # current, total
    loading_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ship_keys = []
        self.preset = "viewer"
        self.optimizer = ImageOptimizer()
        self.should_stop = False
    
    def load_ships(self, ship_keys: List[str], preset: str = "viewer"):
        """Start loading ships in background"""
        self.ship_keys = ship_keys.copy()
        self.preset = preset
        self.should_stop = False
        self.start()
    
    def stop_loading(self):
        """Stop background loading"""
        self.should_stop = True
        self.wait()
    
    def run(self):
        """Background loading thread"""
        ship_database = get_ship_database()
        total_ships = len(self.ship_keys)
        
        for i, ship_key in enumerate(self.ship_keys):
            if self.should_stop:
                break
            
            ship = ship_database.get_ship(ship_key)
            if ship:
                image_path = ship.get_image_path()
                optimized_image = self.optimizer.optimize_for_preset(image_path, self.preset)
                
                if optimized_image and not self.should_stop:
                    self.image_loaded.emit(ship_key, optimized_image)
            
            self.progress_updated.emit(i + 1, total_ships)
        
        if not self.should_stop:
            self.loading_completed.emit()


class SmartImageManager(QObject):
    """Smart image management with predictive loading"""
    
    images_preloaded = pyqtSignal(int)  # Number of images preloaded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.optimizer = ImageOptimizer()
        self.background_loader = AsynchronousImageLoader(self)
        
        # Predictive loading settings
        self.preload_radius = 3  # Number of adjacent ships to preload
        self.current_ship_index = 0
        self.ship_list = []
        
        # Connect signals
        self.background_loader.image_loaded.connect(self.on_image_loaded)
        self.background_loader.loading_completed.connect(self.on_loading_completed)
        
        # Preload timer for delayed loading
        self.preload_timer = QTimer()
        self.preload_timer.timeout.connect(self.perform_predictive_preload)
        self.preload_timer.setSingleShot(True)
    
    def set_ship_list(self, ship_keys: List[str]):
        """Set the current ship list for predictive loading"""
        self.ship_list = ship_keys
        self.current_ship_index = 0
    
    def set_current_ship(self, ship_key: str):
        """Set current ship and trigger predictive loading"""
        try:
            self.current_ship_index = self.ship_list.index(ship_key)
            
            # Schedule predictive preload after short delay
            self.preload_timer.stop()
            self.preload_timer.start(500)  # 500ms delay
            
        except ValueError:
            # Ship not in current list
            pass
    
    def perform_predictive_preload(self):
        """Preload adjacent ships for smooth navigation"""
        if not self.ship_list:
            return
        
        # Calculate range of ships to preload
        start_idx = max(0, self.current_ship_index - self.preload_radius)
        end_idx = min(len(self.ship_list), self.current_ship_index + self.preload_radius + 1)
        
        ships_to_preload = self.ship_list[start_idx:end_idx]
        
        # Start background loading
        self.background_loader.load_ships(ships_to_preload, "viewer")
    
    def get_optimized_image(self, ship_key: str, preset: str = "viewer") -> Optional[QPixmap]:
        """Get optimized image (from cache or load immediately)"""
        ship_database = get_ship_database()
        ship = ship_database.get_ship(ship_key)
        
        if not ship:
            return None
        
        image_path = ship.get_image_path()
        return self.optimizer.optimize_for_preset(image_path, preset)
    
    def on_image_loaded(self, ship_key: str, image: QPixmap):
        """Handle background image loading completion"""
        # Image is already cached by optimizer
        pass
    
    def on_loading_completed(self):
        """Handle background loading completion"""
        cache_stats = self.optimizer.get_cache_stats()
        self.images_preloaded.emit(cache_stats["current_items"])
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics"""
        return self.optimizer.get_cache_stats()
    
    def cleanup(self):
        """Cleanup resources"""
        self.background_loader.stop_loading()
        self.optimizer.clear_cache()


# Global instance for application-wide use
_smart_image_manager = None

def get_smart_image_manager() -> SmartImageManager:
    """Get global smart image manager instance with proper lifecycle management"""
    global _smart_image_manager
    
    # Check if instance exists and is still valid
    if _smart_image_manager is None:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        _smart_image_manager = SmartImageManager(app)
    
    return _smart_image_manager


def optimize_all_ship_images(assets_dir: str, output_dir: str = None, 
                           progress_callback: Optional[Callable] = None):
    """Batch optimize all ship images"""
    if not output_dir:
        output_dir = os.path.join(assets_dir, "optimized")
    
    os.makedirs(output_dir, exist_ok=True)
    
    ship_database = get_ship_database()
    optimizer = ImageOptimizer()
    
    ships = ship_database.get_all_ships()
    total_ships = len(ships)
    
    for i, ship in enumerate(ships):
        image_path = ship.get_image_path()
        
        if os.path.exists(image_path):
            # Optimize for different presets
            for preset, size in optimizer.presets.items():
                optimized = optimizer.load_and_optimize(image_path, size)
                if optimized:
                    output_path = os.path.join(output_dir, f"{ship.name}_{preset}.png")
                    optimized.save(output_path)
        
        if progress_callback:
            progress_callback(i + 1, total_ships)
    
    print(f"Optimized {total_ships} ship images to {output_dir}")


# Export main classes and functions
__all__ = [
    'ImageCache', 'ImageOptimizer', 'AsynchronousImageLoader',
    'SmartImageManager', 'get_smart_image_manager', 'optimize_all_ship_images'
]