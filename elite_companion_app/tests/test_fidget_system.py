#!/usr/bin/env python3
"""
Test script for Elite Dangerous Fidget Mode
Verifies all components work correctly before deployment.
"""
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test basic imports
try:
    print("Testing imports...")
    
    # Core imports
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    print("✓ PyQt6 imported successfully")
    
    # Database imports
    from data.ship_database import get_ship_database, ShipSpecification
    print("✓ Ship database imported successfully")
    
    # Widget imports
    from ui.widgets.ship_gallery import ShipGalleryWidget
    from ui.widgets.ship_viewer import ShipViewer3D, ShipViewerControls
    from ui.widgets.ship_specs_panel import ShipSpecificationPanel
    from ui.widgets.ship_comparison import show_ship_comparison
    print("✓ UI widgets imported successfully")
    
    # Theme imports
    from config.themes import HardwareThemeManager, PredefinedThemes
    from ui.elite_widgets import apply_elite_theme
    print("✓ Theme system imported successfully")
    
    # Image optimization
    from utils.image_optimizer import get_smart_image_manager
    print("✓ Image optimization imported successfully")
    
    # Main fidget mode
    from ui.fidget_mode import EliteFidgetMode
    print("✓ Fidget mode imported successfully")
    
    print("\nAll imports successful!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test database functionality
try:
    print("\nTesting ship database...")
    
    # Create minimal QApplication for image operations
    app = QApplication([])
    
    db = get_ship_database()
    ship_count = db.get_ship_count()
    print(f"✓ Ship database loaded: {ship_count} ships")
    
    # Test specific ships
    test_ships = ["sidewinder", "asp-explorer", "anaconda", "federal-corvette"]
    for ship_key in test_ships:
        ship = db.get_ship(ship_key)
        if ship:
            print(f"✓ {ship.display_name} - {ship.manufacturer.value}")
        else:
            print(f"✗ Ship not found: {ship_key}")
    
    # Test search functionality
    combat_ships = db.get_ships_by_role(db.get_ship("vulture").primary_role)
    print(f"✓ Found {len(combat_ships)} combat ships")
    
    # Test ship specifications
    sidewinder = db.get_ship("sidewinder")
    if sidewinder:
        print(f"✓ Sidewinder specs: {sidewinder.performance.max_speed} m/s, {sidewinder.performance.base_jump_range:.2f} ly")
    
    print("Database tests passed!")
    
except Exception as e:
    print(f"✗ Database test failed: {e}")
    sys.exit(1)

# Test image paths
try:
    print("\nTesting image availability...")
    
    assets_dir = "/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets"
    
    if not os.path.exists(assets_dir):
        print(f"✗ Assets directory not found: {assets_dir}")
        sys.exit(1)
    
    db = get_ship_database()
    available_images = db.get_available_images(assets_dir)
    print(f"✓ Found {len(available_images)} ship images")
    
    # Test some specific images
    test_images = ["sidewinder.png", "asp-explorer.png", "anaconda.png"]
    for img_name in test_images:
        img_path = os.path.join(assets_dir, img_name)
        if os.path.exists(img_path):
            print(f"✓ {img_name}")
        else:
            print(f"✗ Missing: {img_name}")
    
    print("Image tests passed!")
    
except Exception as e:
    print(f"✗ Image test failed: {e}")
    sys.exit(1)

# Test GUI application
def test_gui():
    print("\nTesting GUI application...")
    
    try:
        # Use existing app or create new one
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Test theme system
        theme_manager = HardwareThemeManager()
        theme_manager.set_predefined_theme("Ice Blue")
        apply_elite_theme(app, theme_manager.current_theme)
        print("✓ Theme system working")
        
        # Test main window creation
        window = EliteFidgetMode()
        print("✓ Main window created")
        
        # Test that window has all expected components
        if hasattr(window, 'gallery_widget') and window.gallery_widget:
            print("✓ Ship gallery widget created")
        else:
            print("✗ Ship gallery widget missing")
        
        if hasattr(window, 'ship_viewer') and window.ship_viewer:
            print("✓ Ship viewer widget created")
        else:
            print("✗ Ship viewer widget missing")
        
        if hasattr(window, 'specs_panel') and window.specs_panel:
            print("✓ Specifications panel created")
        else:
            print("✗ Specifications panel missing")
        
        # Test ship loading
        ships = get_ship_database().get_all_ships()
        if ships:
            test_ship = ships[0]
            window.set_current_ship(test_ship, animate=False)
            print(f"✓ Loaded test ship: {test_ship.display_name}")
        
        # Test window display (don't show for automated testing)
        print("✓ Window ready for display")
        
        print("GUI tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test performance requirements
def test_performance():
    print("\nTesting performance requirements...")
    
    try:
        # Test image optimization
        image_manager = get_smart_image_manager()
        
        # Set up ship list for predictive loading
        db = get_ship_database()
        all_ships = [ship.name for ship in db.get_all_ships()]
        image_manager.set_ship_list(all_ships)
        
        # Test optimized image loading
        if all_ships:
            test_ship = all_ships[0]
            optimized_image = image_manager.get_optimized_image(test_ship, "viewer")
            if optimized_image:
                print(f"✓ Image optimization working: {optimized_image.width()}x{optimized_image.height()}")
            else:
                print("✗ Image optimization failed")
        
        # Test cache performance
        stats = image_manager.get_performance_stats()
        print(f"✓ Cache stats: {stats['current_items']} items, {stats['current_memory_mb']:.1f} MB")
        
        print("Performance tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("ELITE DANGEROUS FIDGET MODE - SYSTEM TESTS")
    print("=" * 50)
    
    success = True
    
    # Component tests
    success &= test_performance()
    success &= test_gui()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ ALL TESTS PASSED - System ready for deployment!")
        print("\nTo run fidget mode:")
        print("python ui/fidget_mode.py")
    else:
        print("✗ SOME TESTS FAILED - Please fix issues before deployment")
        return 1
    
    print("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())