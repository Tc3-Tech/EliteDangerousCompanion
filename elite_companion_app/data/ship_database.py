"""
Elite Dangerous Comprehensive Ship Database
Contains detailed technical specifications for all ship types with authentic Elite Dangerous data.
"""
from typing import Dict, List, Optional, NamedTuple, Any
from dataclasses import dataclass
from enum import Enum
import os


class ShipClass(Enum):
    """Ship class categories"""
    SMALL = "Small"
    MEDIUM = "Medium" 
    LARGE = "Large"


class ShipRole(Enum):
    """Primary ship roles"""
    FIGHTER = "Fighter"
    EXPLORER = "Explorer"
    TRADER = "Trader"
    MINER = "Miner"
    PASSENGER = "Passenger"
    COMBAT = "Combat"
    MULTIPURPOSE = "Multipurpose"


class Manufacturer(Enum):
    """Ship manufacturers"""
    LAKON = "Lakon Spaceways"
    CORE_DYNAMICS = "Core Dynamics"
    FAULCON_DELACY = "Faulcon DeLacy"
    SAUD_KRUGER = "Saud Kruger"
    ZORGON_PETERSON = "Zorgon Peterson"
    GUTAMAYA = "Gutamaya"
    ALLIANCE = "Alliance Shipyard"


@dataclass
class HardpointLoadout:
    """Hardpoint configuration"""
    large: int = 0
    medium: int = 0
    small: int = 0
    utility: int = 0
    
    @property
    def total_hardpoints(self) -> int:
        return self.large + self.medium + self.small
    
    @property
    def total_with_utility(self) -> int:
        return self.total_hardpoints + self.utility


@dataclass
class InternalSlots:
    """Internal compartment configuration"""
    class_8: int = 0
    class_7: int = 0
    class_6: int = 0
    class_5: int = 0
    class_4: int = 0
    class_3: int = 0
    class_2: int = 0
    class_1: int = 0
    
    @property
    def total_slots(self) -> int:
        return (self.class_8 + self.class_7 + self.class_6 + self.class_5 + 
                self.class_4 + self.class_3 + self.class_2 + self.class_1)
    
    @property
    def max_cargo_capacity(self) -> int:
        """Maximum possible cargo capacity if all slots used for cargo"""
        return (self.class_8 * 256 + self.class_7 * 128 + self.class_6 * 64 + 
                self.class_5 * 32 + self.class_4 * 16 + self.class_3 * 8 + 
                self.class_2 * 4 + self.class_1 * 2)


@dataclass
class ShipDimensions:
    """Physical ship dimensions"""
    length: float  # meters
    width: float   # meters
    height: float  # meters
    
    @property
    def volume(self) -> float:
        """Approximate volume"""
        return self.length * self.width * self.height


@dataclass
class ShipPerformance:
    """Ship performance characteristics"""
    max_speed: int          # m/s
    boost_speed: int        # m/s
    base_jump_range: float  # light years (A-rated FSD)
    max_jump_range: float   # light years (engineered)
    base_shield_strength: int  # MJ (A-rated shields)
    hull_mass: float        # tons
    hull_integrity: int     # base armor rating
    fuel_capacity: int      # tons
    power_plant_capacity: int  # MW


@dataclass
class ShipSpecification:
    """Complete ship specification data"""
    name: str
    display_name: str
    manufacturer: Manufacturer
    ship_class: ShipClass
    primary_role: ShipRole
    secondary_roles: List[ShipRole]
    
    # Economic data
    base_cost: int         # credits
    insurance_cost: int    # credits (5% of base cost)
    
    # Physical characteristics
    dimensions: ShipDimensions
    crew_seats: int
    
    # Combat characteristics
    hardpoints: HardpointLoadout
    internal_slots: InternalSlots
    performance: ShipPerformance
    
    # Optional characteristics with defaults
    fighter_hangar_capacity: int = 0
    srv_hangar_capacity: int = 0
    
    # Asset information
    image_filename: str = ""
    description: str = ""
    manufacturer_description: str = ""
    
    @property
    def cost_per_ton(self) -> float:
        """Cost efficiency per ton of hull mass"""
        return self.base_cost / self.performance.hull_mass if self.performance.hull_mass > 0 else 0
    
    @property
    def firepower_rating(self) -> int:
        """Simple firepower rating based on hardpoints"""
        return (self.hardpoints.large * 4 + self.hardpoints.medium * 2 + self.hardpoints.small * 1)
    
    @property
    def cargo_rating(self) -> str:
        """Cargo capacity rating"""
        max_cargo = self.internal_slots.max_cargo_capacity
        if max_cargo > 700: return "Excellent"
        elif max_cargo > 400: return "Very Good"
        elif max_cargo > 200: return "Good"
        elif max_cargo > 100: return "Fair"
        elif max_cargo > 50: return "Limited"
        else: return "Minimal"
    
    @property
    def exploration_rating(self) -> str:
        """Exploration capability rating"""
        jump_range = self.performance.max_jump_range
        if jump_range > 65: return "Exceptional"
        elif jump_range > 55: return "Excellent"
        elif jump_range > 45: return "Very Good"
        elif jump_range > 35: return "Good"
        elif jump_range > 25: return "Fair"
        else: return "Limited"
    
    def get_image_path(self, base_assets_dir: str = "/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets") -> str:
        """Get full path to ship image"""
        if self.image_filename:
            return os.path.join(base_assets_dir, self.image_filename)
        return os.path.join(base_assets_dir, f"{self.name.lower().replace(' ', '-').replace('_', '-')}.png")
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for UI display"""
        return {
            "name": self.display_name,
            "manufacturer": self.manufacturer.value,
            "class": self.ship_class.value,
            "role": self.primary_role.value,
            "cost": f"{self.base_cost:,} CR",
            "insurance": f"{self.insurance_cost:,} CR",
            "mass": f"{self.performance.hull_mass:.1f}t",
            "max_speed": f"{self.performance.max_speed} m/s",
            "boost_speed": f"{self.performance.boost_speed} m/s",
            "jump_range": f"{self.performance.base_jump_range:.2f} ly",
            "max_jump_range": f"{self.performance.max_jump_range:.2f} ly",
            "shields": f"{self.performance.base_shield_strength} MJ",
            "hull_integrity": f"{self.performance.hull_integrity}",
            "crew": str(self.crew_seats),
            "length": f"{self.dimensions.length:.1f}m",
            "width": f"{self.dimensions.width:.1f}m",
            "height": f"{self.dimensions.height:.1f}m",
            "hardpoints": f"L:{self.hardpoints.large} M:{self.hardpoints.medium} S:{self.hardpoints.small} U:{self.hardpoints.utility}",
            "firepower_rating": self.firepower_rating,
            "cargo_rating": self.cargo_rating,
            "exploration_rating": self.exploration_rating,
            "description": self.description
        }


class EliteShipDatabase:
    """Complete Elite Dangerous ship database"""
    
    def __init__(self):
        self.ships = self._initialize_ship_database()
        self._build_indices()
    
    def _initialize_ship_database(self) -> Dict[str, ShipSpecification]:
        """Initialize complete ship database with authentic Elite Dangerous specifications"""
        
        ships = {}
        
        # SMALL SHIPS
        
        # Sidewinder MK I
        ships["sidewinder"] = ShipSpecification(
            name="sidewinder",
            display_name="Sidewinder MK I",
            manufacturer=Manufacturer.FAULCON_DELACY,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.EXPLORER],
            base_cost=32000,
            insurance_cost=1600,
            dimensions=ShipDimensions(length=14.9, width=21.3, height=5.4),
            crew_seats=1,
            hardpoints=HardpointLoadout(small=2, utility=2),
            internal_slots=InternalSlots(class_2=2, class_1=2),
            performance=ShipPerformance(
                max_speed=220, boost_speed=320, base_jump_range=7.56, max_jump_range=37.77,
                base_shield_strength=40, hull_mass=25, hull_integrity=60,
                fuel_capacity=2, power_plant_capacity=3
            ),
            image_filename="sidewinder.png",
            description="The Sidewinder is every new pilot's first ship. Cheap, reliable, and surprisingly versatile.",
            manufacturer_description="Faulcon DeLacy's entry-level ship, designed for new pilots entering the galaxy."
        )
        
        # Eagle MK II
        ships["eagle"] = ShipSpecification(
            name="eagle",
            display_name="Eagle MK II",
            manufacturer=Manufacturer.CORE_DYNAMICS,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.FIGHTER,
            secondary_roles=[ShipRole.COMBAT],
            base_cost=44800,
            insurance_cost=2240,
            dimensions=ShipDimensions(length=31.2, width=29.7, height=7.0),
            crew_seats=1,
            hardpoints=HardpointLoadout(small=3, utility=2),
            internal_slots=InternalSlots(class_3=1, class_2=2, class_1=2),
            performance=ShipPerformance(
                max_speed=240, boost_speed=350, base_jump_range=6.63, max_jump_range=28.95,
                base_shield_strength=60, hull_mass=50, hull_integrity=120,
                fuel_capacity=2, power_plant_capacity=3
            ),
            image_filename="eagle-mk-ii.png",
            description="A nimble fighter craft with excellent maneuverability. Popular with bounty hunters and pirates alike.",
            manufacturer_description="Core Dynamics' agile light fighter, built for speed and precision."
        )
        
        # Hauler
        ships["hauler"] = ShipSpecification(
            name="hauler",
            display_name="Hauler",
            manufacturer=Manufacturer.ZORGON_PETERSON,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.TRADER,
            secondary_roles=[ShipRole.EXPLORER],
            base_cost=52720,
            insurance_cost=2636,
            dimensions=ShipDimensions(length=38.0, width=24.0, height=12.0),
            crew_seats=1,
            hardpoints=HardpointLoadout(small=1, utility=2),
            internal_slots=InternalSlots(class_3=1, class_2=3, class_1=1),
            performance=ShipPerformance(
                max_speed=200, boost_speed=300, base_jump_range=9.41, max_jump_range=37.20,
                base_shield_strength=50, hull_mass=14, hull_integrity=90,
                fuel_capacity=2, power_plant_capacity=2
            ),
            image_filename="hauler.png",
            description="A budget cargo vessel with surprising jump range. Often used by new traders and explorers.",
            manufacturer_description="Zorgon Peterson's economical cargo hauler, designed for maximum efficiency."
        )
        
        # Adder
        ships["adder"] = ShipSpecification(
            name="adder",
            display_name="Adder",
            manufacturer=Manufacturer.ZORGON_PETERSON,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.TRADER, ShipRole.EXPLORER],
            base_cost=87808,
            insurance_cost=4390,
            dimensions=ShipDimensions(length=35.0, width=18.0, height=8.0),
            crew_seats=2,
            hardpoints=HardpointLoadout(medium=1, small=2, utility=2),
            internal_slots=InternalSlots(class_3=2, class_2=2, class_1=3),
            performance=ShipPerformance(
                max_speed=220, boost_speed=320, base_jump_range=8.50, max_jump_range=36.21,
                base_shield_strength=60, hull_mass=35, hull_integrity=120,
                fuel_capacity=4, power_plant_capacity=4
            ),
            image_filename="adder.png",
            description="A versatile small ship that bridges the gap between starter vessels and more specialized craft.",
            manufacturer_description="Zorgon Peterson's multi-role vessel, combining cargo capacity with combat capability."
        )
        
        # Imperial Eagle
        ships["imperial-eagle"] = ShipSpecification(
            name="imperial-eagle",
            display_name="Imperial Eagle",
            manufacturer=Manufacturer.GUTAMAYA,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.FIGHTER,
            secondary_roles=[ShipRole.COMBAT],
            base_cost=110825,
            insurance_cost=5541,
            dimensions=ShipDimensions(length=31.2, width=29.7, height=7.0),
            crew_seats=1,
            hardpoints=HardpointLoadout(small=3, utility=3),
            internal_slots=InternalSlots(class_3=1, class_2=2, class_1=2),
            performance=ShipPerformance(
                max_speed=300, boost_speed=400, base_jump_range=6.57, max_jump_range=27.58,
                base_shield_strength=80, hull_mass=50, hull_integrity=120,
                fuel_capacity=2, power_plant_capacity=3
            ),
            image_filename="imperial-eagle.png",
            description="Gutamaya's refined take on the Eagle design, with enhanced speed and elegant Imperial styling.",
            manufacturer_description="The Empire's premier light fighter, combining Gutamaya craftsmanship with lethal efficiency."
        )
        
        # MEDIUM SHIPS
        
        # Viper MK III
        ships["viper-mk-iii"] = ShipSpecification(
            name="viper-mk-iii",
            display_name="Viper MK III",
            manufacturer=Manufacturer.FAULCON_DELACY,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.FIGHTER,
            secondary_roles=[ShipRole.COMBAT],
            base_cost=142931,
            insurance_cost=7147,
            dimensions=ShipDimensions(length=29.7, width=24.2, height=8.1),
            crew_seats=1,
            hardpoints=HardpointLoadout(medium=2, small=2, utility=2),
            internal_slots=InternalSlots(class_3=2, class_2=2, class_1=2),
            performance=ShipPerformance(
                max_speed=320, boost_speed=400, base_jump_range=6.47, max_jump_range=26.57,
                base_shield_strength=105, hull_mass=50, hull_integrity=150,
                fuel_capacity=4, power_plant_capacity=4
            ),
            image_filename="viper-mk-iii.png",
            description="A fast, maneuverable fighter favored by security forces and bounty hunters throughout the galaxy.",
            manufacturer_description="Faulcon DeLacy's proven interceptor, trusted by law enforcement across human space."
        )
        
        # Cobra MK III
        ships["cobra-mk-iii"] = ShipSpecification(
            name="cobra-mk-iii",
            display_name="Cobra MK III",
            manufacturer=Manufacturer.FAULCON_DELACY,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.TRADER, ShipRole.EXPLORER, ShipRole.COMBAT],
            base_cost=379718,
            insurance_cost=18986,
            dimensions=ShipDimensions(length=27.1, width=44.0, height=7.3),
            crew_seats=2,
            hardpoints=HardpointLoadout(medium=2, small=2, utility=4),
            internal_slots=InternalSlots(class_4=2, class_3=2, class_2=4),
            performance=ShipPerformance(
                max_speed=280, boost_speed=400, base_jump_range=8.57, max_jump_range=35.28,
                base_shield_strength=120, hull_mass=180, hull_integrity=300,
                fuel_capacity=8, power_plant_capacity=6
            ),
            image_filename="cobra-mk-iii.png",
            description="The quintessential multipurpose ship. Fast, well-armed, and with decent cargo space.",
            manufacturer_description="Faulcon DeLacy's legendary all-rounder, equally at home trading, exploring, or fighting."
        )
        
        # Type-6 Transporter
        ships["type-6"] = ShipSpecification(
            name="type-6",
            display_name="Type-6 Transporter",
            manufacturer=Manufacturer.LAKON,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.TRADER,
            secondary_roles=[ShipRole.EXPLORER],
            base_cost=1045945,
            insurance_cost=52297,
            dimensions=ShipDimensions(length=54.2, width=23.2, height=11.9),
            crew_seats=2,
            hardpoints=HardpointLoadout(small=2, utility=2),
            internal_slots=InternalSlots(class_5=1, class_4=2, class_3=1, class_2=4, class_1=2),
            performance=ShipPerformance(
                max_speed=220, boost_speed=350, base_jump_range=9.41, max_jump_range=33.49,
                base_shield_strength=90, hull_mass=155, hull_integrity=270,
                fuel_capacity=8, power_plant_capacity=4
            ),
            image_filename="type-6-transporter.png",
            description="A dedicated cargo vessel with excellent jump range for its class and reasonable operating costs.",
            manufacturer_description="Lakon's efficient medium cargo hauler, designed for profitability and reliability."
        )
        
        # Asp Explorer
        ships["asp-explorer"] = ShipSpecification(
            name="asp-explorer",
            display_name="Asp Explorer",
            manufacturer=Manufacturer.LAKON,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.EXPLORER,
            secondary_roles=[ShipRole.MULTIPURPOSE, ShipRole.TRADER],
            base_cost=6661154,
            insurance_cost=333058,
            dimensions=ShipDimensions(length=56.0, width=51.3, height=11.0),
            crew_seats=2,
            hardpoints=HardpointLoadout(medium=2, small=4, utility=4),
            internal_slots=InternalSlots(class_6=1, class_5=2, class_4=2, class_3=3, class_2=4, class_1=2),
            performance=ShipPerformance(
                max_speed=254, boost_speed=340, base_jump_range=11.28, max_jump_range=68.13,
                base_shield_strength=105, hull_mass=280, hull_integrity=315,
                fuel_capacity=16, power_plant_capacity=5
            ),
            image_filename="asp-explorer.png",
            description="The galaxy's premier exploration vessel, with exceptional jump range and excellent visibility.",
            manufacturer_description="Lakon's legendary explorer, chosen by more deep-space pilots than any other ship."
        )
        
        # Vulture
        ships["vulture"] = ShipSpecification(
            name="vulture",
            display_name="Vulture",
            manufacturer=Manufacturer.CORE_DYNAMICS,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.FIGHTER],
            base_cost=4925615,
            insurance_cost=246281,
            dimensions=ShipDimensions(length=19.8, width=26.4, height=7.8),
            crew_seats=1,
            hardpoints=HardpointLoadout(large=2, utility=4),
            internal_slots=InternalSlots(class_4=1, class_3=1, class_2=3, class_1=3),
            performance=ShipPerformance(
                max_speed=210, boost_speed=340, base_jump_range=6.20, max_jump_range=19.74,
                base_shield_strength=210, hull_mass=230, hull_integrity=420,
                fuel_capacity=8, power_plant_capacity=4
            ),
            image_filename="vulture.png",
            description="A dedicated combat vessel with two large hardpoints and exceptional maneuverability.",
            manufacturer_description="Core Dynamics' specialist combat ship, engineered for maximum firepower and agility."
        )
        
        # Keelback
        ships["keelback"] = ShipSpecification(
            name="keelback",
            display_name="Keelback",
            manufacturer=Manufacturer.LAKON,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.TRADER,
            secondary_roles=[ShipRole.COMBAT],
            base_cost=3126150,
            insurance_cost=156308,
            dimensions=ShipDimensions(length=54.2, width=23.2, height=11.9),
            crew_seats=2,
            fighter_hangar_capacity=1,
            hardpoints=HardpointLoadout(medium=1, small=2, utility=4),
            internal_slots=InternalSlots(class_5=1, class_4=2, class_3=1, class_2=4, class_1=2),
            performance=ShipPerformance(
                max_speed=200, boost_speed=300, base_jump_range=8.78, max_jump_range=29.76,
                base_shield_strength=150, hull_mass=180, hull_integrity=330,
                fuel_capacity=8, power_plant_capacity=5
            ),
            image_filename="keelback.png",
            description="Based on the Type-6, but with better armor and weapons. Can deploy a fighter.",
            manufacturer_description="Lakon's combat-oriented cargo vessel, featuring fighter deployment capability."
        )
        
        # Federal Dropship
        ships["federal-dropship"] = ShipSpecification(
            name="federal-dropship",
            display_name="Federal Dropship",
            manufacturer=Manufacturer.CORE_DYNAMICS,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.TRADER],
            base_cost=14314205,
            insurance_cost=715710,
            dimensions=ShipDimensions(length=73.6, width=51.2, height=16.0),
            crew_seats=2,
            hardpoints=HardpointLoadout(medium=2, small=4, utility=4),
            internal_slots=InternalSlots(class_6=1, class_5=1, class_4=3, class_3=3, class_2=2, class_1=1),
            performance=ShipPerformance(
                max_speed=180, boost_speed=300, base_jump_range=6.86, max_jump_range=19.66,
                base_shield_strength=200, hull_mass=580, hull_integrity=450,
                fuel_capacity=16, power_plant_capacity=6
            ),
            image_filename="federal-dropship.png",
            description="A heavily armored Federal Navy vessel. Slow but tough, with good cargo capacity.",
            manufacturer_description="Core Dynamics' military transport, built to Federal Navy specifications."
        )
        
        # Federal Assault Ship
        ships["federal-assault-ship"] = ShipSpecification(
            name="federal-assault-ship",
            display_name="Federal Assault Ship",
            manufacturer=Manufacturer.CORE_DYNAMICS,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.FIGHTER],
            base_cost=19814205,
            insurance_cost=990710,
            dimensions=ShipDimensions(length=73.6, width=51.2, height=16.0),
            crew_seats=2,
            hardpoints=HardpointLoadout(large=2, medium=2, utility=4),
            internal_slots=InternalSlots(class_5=1, class_4=2, class_3=3, class_2=2, class_1=3),
            performance=ShipPerformance(
                max_speed=210, boost_speed=350, base_jump_range=6.45, max_jump_range=18.57,
                base_shield_strength=200, hull_mass=480, hull_integrity=360,
                fuel_capacity=16, power_plant_capacity=6
            ),
            image_filename="federal-assault-ship.png",
            description="An upgraded Dropship focused on combat. Better speed and firepower than its predecessor.",
            manufacturer_description="Core Dynamics' dedicated assault vessel, optimized for Federal Navy operations."
        )
        
        # Federal Gunship
        ships["federal-gunship"] = ShipSpecification(
            name="federal-gunship",
            display_name="Federal Gunship",
            manufacturer=Manufacturer.CORE_DYNAMICS,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.FIGHTER],
            base_cost=35814205,
            insurance_cost=1790710,
            dimensions=ShipDimensions(length=73.6, width=51.2, height=16.0),
            crew_seats=2,
            fighter_hangar_capacity=1,
            hardpoints=HardpointLoadout(large=1, medium=2, small=4, utility=4),
            internal_slots=InternalSlots(class_6=1, class_4=2, class_3=3, class_2=2, class_1=3),
            performance=ShipPerformance(
                max_speed=170, boost_speed=280, base_jump_range=6.20, max_jump_range=17.81,
                base_shield_strength=250, hull_mass=580, hull_integrity=540,
                fuel_capacity=16, power_plant_capacity=7
            ),
            image_filename="federal-gunship.png",
            description="The ultimate Federal combat vessel. Massive firepower and fighter deployment capability.",
            manufacturer_description="Core Dynamics' heavy combat platform, the Federation's answer to capital threats."
        )
        
        # LARGE SHIPS
        
        # Python
        ships["python"] = ShipSpecification(
            name="python",
            display_name="Python",
            manufacturer=Manufacturer.FAULCON_DELACY,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.TRADER, ShipRole.COMBAT],
            base_cost=56978179,
            insurance_cost=2848909,
            dimensions=ShipDimensions(length=87.2, width=58.1, height=16.7),
            crew_seats=3,
            hardpoints=HardpointLoadout(large=2, medium=3, utility=4),
            internal_slots=InternalSlots(class_6=2, class_5=2, class_4=3, class_3=2),
            performance=ShipPerformance(
                max_speed=230, boost_speed=300, base_jump_range=8.17, max_jump_range=35.64,
                base_shield_strength=260, hull_mass=350, hull_integrity=525,
                fuel_capacity=16, power_plant_capacity=7
            ),
            image_filename="python.png",
            description="A versatile medium ship that can land at outposts. Excellent for trading and combat.",
            manufacturer_description="Faulcon DeLacy's premium medium ship, combining cargo capacity with combat prowess."
        )
        
        # Type-7 Transporter
        ships["type-7"] = ShipSpecification(
            name="type-7",
            display_name="Type-7 Transporter",
            manufacturer=Manufacturer.LAKON,
            ship_class=ShipClass.LARGE,
            primary_role=ShipRole.TRADER,
            secondary_roles=[],
            base_cost=17472252,
            insurance_cost=873613,
            dimensions=ShipDimensions(length=74.1, width=32.6, height=17.5),
            crew_seats=1,
            hardpoints=HardpointLoadout(small=4, utility=2),
            internal_slots=InternalSlots(class_6=1, class_5=2, class_4=4, class_3=2, class_2=2),
            performance=ShipPerformance(
                max_speed=180, boost_speed=300, base_jump_range=9.41, max_jump_range=37.15,
                base_shield_strength=150, hull_mass=350, hull_integrity=420,
                fuel_capacity=16, power_plant_capacity=5
            ),
            image_filename="type-7.png",
            description="A large cargo vessel with excellent capacity and jump range. Requires large landing pads.",
            manufacturer_description="Lakon's heavy cargo hauler, designed for maximum freight capacity."
        )
        
        # Imperial Clipper
        ships["imperial-clipper"] = ShipSpecification(
            name="imperial-clipper",
            display_name="Imperial Clipper",
            manufacturer=Manufacturer.GUTAMAYA,
            ship_class=ShipClass.LARGE,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.TRADER, ShipRole.COMBAT],
            base_cost=22295860,
            insurance_cost=1114793,
            dimensions=ShipDimensions(length=88.4, width=54.2, height=15.0),
            crew_seats=2,
            hardpoints=HardpointLoadout(large=2, medium=2, utility=4),
            internal_slots=InternalSlots(class_6=1, class_5=1, class_4=4, class_3=2, class_2=3, class_1=2),
            performance=ShipPerformance(
                max_speed=300, boost_speed=380, base_jump_range=8.61, max_jump_range=30.34,
                base_shield_strength=180, hull_mass=400, hull_integrity=450,
                fuel_capacity=16, power_plant_capacity=6
            ),
            image_filename="imperial-clipper.png",
            description="A fast, elegant Imperial ship. Good cargo capacity and surprising speed for its size.",
            manufacturer_description="Gutamaya's graceful multipurpose vessel, embodying Imperial engineering excellence."
        )
        
        # Fer-de-Lance
        ships["fer-de-lance"] = ShipSpecification(
            name="fer-de-lance",
            display_name="Fer-de-Lance",
            manufacturer=Manufacturer.ZORGON_PETERSON,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.FIGHTER],
            base_cost=51567040,
            insurance_cost=2578352,
            dimensions=ShipDimensions(length=73.6, width=35.8, height=11.9),
            crew_seats=1,
            hardpoints=HardpointLoadout(large=1, medium=4, utility=4),
            internal_slots=InternalSlots(class_4=2, class_3=2, class_2=3, class_1=3),
            performance=ShipPerformance(
                max_speed=260, boost_speed=350, base_jump_range=7.65, max_jump_range=24.33,
                base_shield_strength=200, hull_mass=250, hull_integrity=300,
                fuel_capacity=8, power_plant_capacity=6
            ),
            image_filename="fer-de-lance.png",
            description="A deadly combat ship with exceptional firepower and maneuverability.",
            manufacturer_description="Zorgon Peterson's premium combat vessel, engineered for supremacy in battle."
        )
        
        # Type-9 Heavy
        ships["type-9"] = ShipSpecification(
            name="type-9",
            display_name="Type-9 Heavy",
            manufacturer=Manufacturer.LAKON,
            ship_class=ShipClass.LARGE,
            primary_role=ShipRole.TRADER,
            secondary_roles=[ShipRole.MINER],
            base_cost=76555842,
            insurance_cost=3827792,
            dimensions=ShipDimensions(length=117.4, width=115.3, height=33.1),
            crew_seats=3,
            hardpoints=HardpointLoadout(small=2, utility=8),
            internal_slots=InternalSlots(class_8=1, class_7=2, class_6=2, class_5=3, class_3=3, class_2=2),
            performance=ShipPerformance(
                max_speed=130, boost_speed=200, base_jump_range=7.56, max_jump_range=35.15,
                base_shield_strength=150, hull_mass=1000, hull_integrity=900,
                fuel_capacity=32, power_plant_capacity=7
            ),
            image_filename="type-9-heavy.png",
            description="The ultimate cargo vessel. Massive capacity but poor maneuverability and minimal defenses.",
            manufacturer_description="Lakon's super-heavy freight hauler, capable of moving enormous cargo loads."
        )
        
        # Anaconda
        ships["anaconda"] = ShipSpecification(
            name="anaconda",
            display_name="Anaconda",
            manufacturer=Manufacturer.FAULCON_DELACY,
            ship_class=ShipClass.LARGE,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.EXPLORER, ShipRole.TRADER, ShipRole.COMBAT],
            base_cost=146969451,
            insurance_cost=7348473,
            dimensions=ShipDimensions(length=152.4, width=61.8, height=32.3),
            crew_seats=3,
            fighter_hangar_capacity=1,
            hardpoints=HardpointLoadout(large=3, medium=2, small=2, utility=8),
            internal_slots=InternalSlots(class_8=1, class_6=2, class_5=3, class_4=1, class_3=3, class_2=2),
            performance=ShipPerformance(
                max_speed=183, boost_speed=240, base_jump_range=9.41, max_jump_range=82.59,
                base_shield_strength=350, hull_mass=400, hull_integrity=945,
                fuel_capacity=32, power_plant_capacity=8
            ),
            image_filename="anaconda.png",
            description="The ultimate exploration and combat vessel. Exceptional jump range and firepower.",
            manufacturer_description="Faulcon DeLacy's flagship vessel, the pinnacle of spacefaring technology."
        )
        
        # Federal Corvette
        ships["federal-corvette"] = ShipSpecification(
            name="federal-corvette",
            display_name="Federal Corvette",
            manufacturer=Manufacturer.CORE_DYNAMICS,
            ship_class=ShipClass.LARGE,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.FIGHTER],
            base_cost=187969451,
            insurance_cost=9398473,
            dimensions=ShipDimensions(length=167.8, width=87.6, height=32.8),
            crew_seats=3,
            fighter_hangar_capacity=2,
            hardpoints=HardpointLoadout(large=2, medium=1, small=4, utility=8),
            internal_slots=InternalSlots(class_7=1, class_6=2, class_5=2, class_4=3, class_3=2, class_2=2),
            performance=ShipPerformance(
                max_speed=200, boost_speed=260, base_jump_range=6.19, max_jump_range=26.52,
                base_shield_strength=555, hull_mass=900, hull_integrity=666,
                fuel_capacity=32, power_plant_capacity=8
            ),
            image_filename="federal-corvette.png",
            description="The Federation's premier warship. Devastating firepower and dual fighter capability.",
            manufacturer_description="Core Dynamics' ultimate expression of Federal military supremacy."
        )
        
        # Imperial Cutter
        ships["imperial-cutter"] = ShipSpecification(
            name="imperial-cutter",
            display_name="Imperial Cutter",
            manufacturer=Manufacturer.GUTAMAYA,
            ship_class=ShipClass.LARGE,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.TRADER, ShipRole.COMBAT],
            base_cost=208969451,
            insurance_cost=10448473,
            dimensions=ShipDimensions(length=192.6, width=111.3, height=33.4),
            crew_seats=3,
            fighter_hangar_capacity=1,
            hardpoints=HardpointLoadout(large=2, medium=1, small=4, utility=8),
            internal_slots=InternalSlots(class_8=1, class_6=2, class_5=3, class_4=2, class_3=2, class_2=2),
            performance=ShipPerformance(
                max_speed=200, boost_speed=320, base_jump_range=7.49, max_jump_range=40.37,
                base_shield_strength=562, hull_mass=1100, hull_integrity=720,
                fuel_capacity=32, power_plant_capacity=8
            ),
            image_filename="imperial-cutter.png",
            description="The Empire's flagship vessel. Combines massive cargo capacity with devastating firepower.",
            manufacturer_description="Gutamaya's masterpiece, the ultimate expression of Imperial power and luxury."
        )
        
        # MORE SPECIALIZED SHIPS
        
        # Asp Scout
        ships["asp-scout"] = ShipSpecification(
            name="asp-scout",
            display_name="Asp Scout",
            manufacturer=Manufacturer.LAKON,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.EXPLORER],
            base_cost=3961154,
            insurance_cost=198058,
            dimensions=ShipDimensions(length=43.0, width=39.4, height=8.4),
            crew_seats=2,
            hardpoints=HardpointLoadout(medium=2, small=2, utility=4),
            internal_slots=InternalSlots(class_4=1, class_3=3, class_2=4, class_1=2),
            performance=ShipPerformance(
                max_speed=220, boost_speed=300, base_jump_range=8.30, max_jump_range=32.55,
                base_shield_strength=120, hull_mass=150, hull_integrity=180,
                fuel_capacity=8, power_plant_capacity=4
            ),
            image_filename="asp-scout.png",
            description="A combat-focused version of the Asp design. More maneuverable than the Explorer.",
            manufacturer_description="Lakon's military variant of the beloved Asp series, built for reconnaissance and combat."
        )
        
        # Diamondback Scout
        ships["diamondback-scout"] = ShipSpecification(
            name="diamondback-scout",
            display_name="Diamondback Scout",
            manufacturer=Manufacturer.LAKON,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.EXPLORER],
            base_cost=564330,
            insurance_cost=28217,
            dimensions=ShipDimensions(length=37.4, width=31.1, height=7.5),
            crew_seats=1,
            hardpoints=HardpointLoadout(medium=2, small=2, utility=4),
            internal_slots=InternalSlots(class_4=1, class_3=2, class_2=4, class_1=2),
            performance=ShipPerformance(
                max_speed=280, boost_speed=380, base_jump_range=10.36, max_jump_range=43.99,
                base_shield_strength=120, hull_mass=170, hull_integrity=210,
                fuel_capacity=8, power_plant_capacity=4
            ),
            image_filename="diamondback-scout.png",
            description="A nimble reconnaissance vessel with excellent jump range and heat efficiency.",
            manufacturer_description="Lakon's specialist scout ship, designed for long-range reconnaissance missions."
        )
        
        # Diamondback Explorer
        ships["diamondback-explorer"] = ShipSpecification(
            name="diamondback-explorer",
            display_name="Diamondback Explorer",
            manufacturer=Manufacturer.LAKON,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.EXPLORER,
            secondary_roles=[ShipRole.MULTIPURPOSE],
            base_cost=1894760,
            insurance_cost=94738,
            dimensions=ShipDimensions(length=37.4, width=31.1, height=7.5),
            crew_seats=1,
            hardpoints=HardpointLoadout(medium=2, small=2, utility=4),
            internal_slots=InternalSlots(class_5=1, class_4=1, class_3=2, class_2=4, class_1=2),
            performance=ShipPerformance(
                max_speed=260, boost_speed=340, base_jump_range=10.98, max_jump_range=56.61,
                base_shield_strength=150, hull_mass=260, hull_integrity=270,
                fuel_capacity=16, power_plant_capacity=5
            ),
            image_filename="diamondback-explorer.png",
            description="An excellent exploration vessel with superb heat efficiency and good jump range.",
            manufacturer_description="Lakon's dedicated exploration platform, engineered for deep space missions."
        )
        
        # Imperial Courier
        ships["imperial-courier"] = ShipSpecification(
            name="imperial-courier",
            display_name="Imperial Courier",
            manufacturer=Manufacturer.GUTAMAYA,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.COMBAT],
            base_cost=2542931,
            insurance_cost=127147,
            dimensions=ShipDimensions(length=35.0, width=24.0, height=7.0),
            crew_seats=1,
            hardpoints=HardpointLoadout(medium=2, small=1, utility=4),
            internal_slots=InternalSlots(class_3=2, class_2=4, class_1=4),
            performance=ShipPerformance(
                max_speed=280, boost_speed=380, base_jump_range=7.65, max_jump_range=35.64,
                base_shield_strength=200, hull_mass=35, hull_integrity=105,
                fuel_capacity=4, power_plant_capacity=4
            ),
            image_filename="imperial-courier.png",
            description="A fast, elegant Imperial vessel with exceptional shields for its size.",
            manufacturer_description="Gutamaya's courier ship, combining Imperial luxury with practical performance."
        )
        
        # Viper MK IV
        ships["viper-mk-iv"] = ShipSpecification(
            name="viper-mk-iv",
            display_name="Viper MK IV",
            manufacturer=Manufacturer.FAULCON_DELACY,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.MULTIPURPOSE],
            base_cost=437931,
            insurance_cost=21897,
            dimensions=ShipDimensions(length=29.7, width=24.2, height=8.1),
            crew_seats=1,
            hardpoints=HardpointLoadout(medium=2, small=2, utility=4),
            internal_slots=InternalSlots(class_4=1, class_3=2, class_2=4, class_1=2),
            performance=ShipPerformance(
                max_speed=270, boost_speed=340, base_jump_range=7.56, max_jump_range=31.08,
                base_shield_strength=150, hull_mass=190, hull_integrity=240,
                fuel_capacity=8, power_plant_capacity=5
            ),
            image_filename="viper-mk-iv.png",
            description="An improved Viper with better armor and internals, though slightly slower.",
            manufacturer_description="Faulcon DeLacy's enhanced interceptor, trading some speed for versatility."
        )
        
        # Cobra MK IV
        ships["cobra-mk-iv"] = ShipSpecification(
            name="cobra-mk-iv",
            display_name="Cobra MK IV",
            manufacturer=Manufacturer.FAULCON_DELACY,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.TRADER],
            base_cost=779718,
            insurance_cost=38986,
            dimensions=ShipDimensions(length=27.1, width=44.0, height=7.3),
            crew_seats=2,
            hardpoints=HardpointLoadout(medium=2, small=2, utility=4),
            internal_slots=InternalSlots(class_5=1, class_4=2, class_3=2, class_2=4),
            performance=ShipPerformance(
                max_speed=200, boost_speed=300, base_jump_range=8.30, max_jump_range=31.76,
                base_shield_strength=180, hull_mass=210, hull_integrity=360,
                fuel_capacity=8, power_plant_capacity=6
            ),
            image_filename="cobra-mk-iv.png",
            description="A more cargo-focused variant of the Cobra with additional internal space.",
            manufacturer_description="Faulcon DeLacy's enhanced Cobra, optimized for extended trading missions."
        )
        
        # PASSENGER AND LUXURY SHIPS
        
        # Dolphin
        ships["dolphin"] = ShipSpecification(
            name="dolphin",
            display_name="Dolphin",
            manufacturer=Manufacturer.SAUD_KRUGER,
            ship_class=ShipClass.SMALL,
            primary_role=ShipRole.PASSENGER,
            secondary_roles=[ShipRole.EXPLORER],
            base_cost=1337154,
            insurance_cost=66858,
            dimensions=ShipDimensions(length=59.7, width=19.3, height=9.6),
            crew_seats=1,
            hardpoints=HardpointLoadout(small=2, utility=2),
            internal_slots=InternalSlots(class_5=1, class_4=2, class_3=1, class_2=4, class_1=2),
            performance=ShipPerformance(
                max_speed=250, boost_speed=350, base_jump_range=9.64, max_jump_range=42.16,
                base_shield_strength=90, hull_mass=140, hull_integrity=210,
                fuel_capacity=8, power_plant_capacity=4
            ),
            image_filename="dolphin.png",
            description="A luxury passenger vessel with excellent heat efficiency and range.",
            manufacturer_description="Saud Kruger's entry-level luxury transport, perfect for VIP passengers."
        )
        
        # Orca
        ships["orca"] = ShipSpecification(
            name="orca",
            display_name="Orca",
            manufacturer=Manufacturer.SAUD_KRUGER,
            ship_class=ShipClass.LARGE,
            primary_role=ShipRole.PASSENGER,
            secondary_roles=[ShipRole.EXPLORER],
            base_cost=48154205,
            insurance_cost=2407710,
            dimensions=ShipDimensions(length=115.7, width=34.4, height=17.5),
            crew_seats=1,
            hardpoints=HardpointLoadout(small=3, utility=4),
            internal_slots=InternalSlots(class_6=1, class_5=2, class_4=3, class_3=2, class_2=2),
            performance=ShipPerformance(
                max_speed=300, boost_speed=380, base_jump_range=9.64, max_jump_range=35.03,
                base_shield_strength=200, hull_mass=290, hull_integrity=525,
                fuel_capacity=16, power_plant_capacity=6
            ),
            image_filename="orca.png",
            description="A prestigious passenger liner combining luxury with surprising speed and agility.",
            manufacturer_description="Saud Kruger's mid-range luxury liner, offering style and performance."
        )
        
        # Beluga Liner
        ships["beluga"] = ShipSpecification(
            name="beluga",
            display_name="Beluga Liner",
            manufacturer=Manufacturer.SAUD_KRUGER,
            ship_class=ShipClass.LARGE,
            primary_role=ShipRole.PASSENGER,
            secondary_roles=[],
            base_cost=84532252,
            insurance_cost=4226613,
            dimensions=ShipDimensions(length=209.7, width=88.1, height=25.6),
            crew_seats=3,
            hardpoints=HardpointLoadout(large=1, medium=2, utility=8),
            internal_slots=InternalSlots(class_7=1, class_6=2, class_5=2, class_4=2, class_3=2, class_2=2),
            performance=ShipPerformance(
                max_speed=200, boost_speed=280, base_jump_range=8.17, max_jump_range=36.73,
                base_shield_strength=280, hull_mass=950, hull_integrity=900,
                fuel_capacity=32, power_plant_capacity=7
            ),
            image_filename="beluga-liner.png",
            description="The ultimate luxury passenger transport, capable of carrying hundreds of passengers.",
            manufacturer_description="Saud Kruger's flagship liner, the epitome of passenger transport luxury."
        )
        
        # ALLIANCE SHIPS
        
        # Alliance Chieftain
        ships["alliance-chieftain"] = ShipSpecification(
            name="alliance-chieftain",
            display_name="Alliance Chieftain",
            manufacturer=Manufacturer.ALLIANCE,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.FIGHTER],
            base_cost=19382252,
            insurance_cost=969113,
            dimensions=ShipDimensions(length=66.0, width=47.4, height=12.4),
            crew_seats=3,
            hardpoints=HardpointLoadout(large=3, medium=0, small=0, utility=4),
            internal_slots=InternalSlots(class_6=1, class_5=1, class_4=2, class_3=3, class_2=2, class_1=2),
            performance=ShipPerformance(
                max_speed=230, boost_speed=300, base_jump_range=7.56, max_jump_range=28.95,
                base_shield_strength=200, hull_mass=400, hull_integrity=450,
                fuel_capacity=16, power_plant_capacity=6
            ),
            image_filename="alliance-chieftain.png",
            description="A dedicated combat ship with three large hardpoints and excellent maneuverability.",
            manufacturer_description="Alliance Shipyard's premier combat vessel, designed to counter Thargoid threats."
        )
        
        # Alliance Challenger
        ships["alliance-challenger"] = ShipSpecification(
            name="alliance-challenger",
            display_name="Alliance Challenger",
            manufacturer=Manufacturer.ALLIANCE,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.MULTIPURPOSE],
            base_cost=30482252,
            insurance_cost=1524113,
            dimensions=ShipDimensions(length=66.0, width=47.4, height=12.4),
            crew_seats=3,
            fighter_hangar_capacity=1,
            hardpoints=HardpointLoadout(large=2, medium=1, small=0, utility=4),
            internal_slots=InternalSlots(class_6=1, class_5=2, class_4=2, class_3=2, class_2=2, class_1=2),
            performance=ShipPerformance(
                max_speed=210, boost_speed=280, base_jump_range=7.20, max_jump_range=25.19,
                base_shield_strength=250, hull_mass=450, hull_integrity=540,
                fuel_capacity=16, power_plant_capacity=7
            ),
            image_filename="alliance-challenger.png",
            description="A heavily armed variant of the Chieftain with fighter deployment capability.",
            manufacturer_description="Alliance Shipyard's enhanced combat platform, featuring integrated fighter support."
        )
        
        # Alliance Crusader
        ships["alliance-crusader"] = ShipSpecification(
            name="alliance-crusader",
            display_name="Alliance Crusader",
            manufacturer=Manufacturer.ALLIANCE,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.EXPLORER, ShipRole.TRADER],
            base_cost=22482252,
            insurance_cost=1124113,
            dimensions=ShipDimensions(length=66.0, width=47.4, height=12.4),
            crew_seats=3,
            hardpoints=HardpointLoadout(large=2, medium=1, small=0, utility=4),
            internal_slots=InternalSlots(class_6=2, class_5=1, class_4=2, class_3=2, class_2=2, class_1=2),
            performance=ShipPerformance(
                max_speed=200, boost_speed=280, base_jump_range=8.61, max_jump_range=33.11,
                base_shield_strength=200, hull_mass=500, hull_integrity=400,
                fuel_capacity=32, power_plant_capacity=6
            ),
            image_filename="alliance-crusader.png",
            description="A multipurpose variant of the Chieftain with enhanced exploration capabilities.",
            manufacturer_description="Alliance Shipyard's versatile platform, combining combat readiness with exploration range."
        )
        
        # ADDITIONAL SHIPS
        
        # Type-10 Defender
        ships["type-10"] = ShipSpecification(
            name="type-10",
            display_name="Type-10 Defender",
            manufacturer=Manufacturer.LAKON,
            ship_class=ShipClass.LARGE,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.MINER],
            base_cost=124555842,
            insurance_cost=6227792,
            dimensions=ShipDimensions(length=117.4, width=115.3, height=33.1),
            crew_seats=3,
            fighter_hangar_capacity=2,
            hardpoints=HardpointLoadout(large=4, medium=2, small=3, utility=8),
            internal_slots=InternalSlots(class_8=1, class_6=2, class_5=3, class_4=2, class_3=2, class_2=2),
            performance=ShipPerformance(
                max_speed=179, boost_speed=219, base_jump_range=6.19, max_jump_range=20.12,
                base_shield_strength=450, hull_mass=1200, hull_integrity=1350,
                fuel_capacity=32, power_plant_capacity=8
            ),
            image_filename="type-10-defender.png",
            description="A combat-modified Type-9 with massive firepower and dual fighter capability.",
            manufacturer_description="Lakon's defensive platform, engineered to protect mining operations and trade routes."
        )
        
        # Mamba
        ships["mamba"] = ShipSpecification(
            name="mamba",
            display_name="Mamba",
            manufacturer=Manufacturer.ZORGON_PETERSON,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.COMBAT,
            secondary_roles=[ShipRole.FIGHTER],
            base_cost=56567040,
            insurance_cost=2828352,
            dimensions=ShipDimensions(length=73.6, width=35.8, height=11.9),
            crew_seats=1,
            hardpoints=HardpointLoadout(large=1, medium=4, utility=2),
            internal_slots=InternalSlots(class_4=2, class_3=2, class_2=2, class_1=4),
            performance=ShipPerformance(
                max_speed=316, boost_speed=387, base_jump_range=6.94, max_jump_range=21.29,
                base_shield_strength=180, hull_mass=250, hull_integrity=280,
                fuel_capacity=8, power_plant_capacity=5
            ),
            image_filename="mamba.png",
            description="A racing-inspired combat ship with blistering speed and lethal firepower.",
            manufacturer_description="Zorgon Peterson's speed demon, where racing heritage meets combat lethality."
        )
        
        # Krait MK II
        ships["krait-mk-ii"] = ShipSpecification(
            name="krait-mk-ii",
            display_name="Krait MK II",
            manufacturer=Manufacturer.FAULCON_DELACY,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.MULTIPURPOSE,
            secondary_roles=[ShipRole.COMBAT, ShipRole.EXPLORER],
            base_cost=45814205,
            insurance_cost=2290710,
            dimensions=ShipDimensions(length=61.8, width=46.3, height=11.2),
            crew_seats=3,
            fighter_hangar_capacity=1,
            hardpoints=HardpointLoadout(large=2, medium=3, utility=4),
            internal_slots=InternalSlots(class_6=1, class_5=2, class_4=2, class_3=2, class_2=2),
            performance=ShipPerformance(
                max_speed=240, boost_speed=330, base_jump_range=8.56, max_jump_range=60.26,
                base_shield_strength=260, hull_mass=320, hull_integrity=405,
                fuel_capacity=16, power_plant_capacity=6
            ),
            image_filename="krait-mk-ii.png",
            description="A versatile medium ship with excellent combat capabilities and fighter deployment.",
            manufacturer_description="Faulcon DeLacy's modernized classic, combining firepower with versatility."
        )
        
        # Krait Phantom
        ships["krait-phantom"] = ShipSpecification(
            name="krait-phantom",
            display_name="Krait Phantom",
            manufacturer=Manufacturer.FAULCON_DELACY,
            ship_class=ShipClass.MEDIUM,
            primary_role=ShipRole.EXPLORER,
            secondary_roles=[ShipRole.MULTIPURPOSE],
            base_cost=37472252,
            insurance_cost=1873613,
            dimensions=ShipDimensions(length=61.8, width=46.3, height=11.2),
            crew_seats=3,
            hardpoints=HardpointLoadout(large=2, medium=3, utility=4),
            internal_slots=InternalSlots(class_6=1, class_5=2, class_4=3, class_3=2, class_2=2),
            performance=ShipPerformance(
                max_speed=250, boost_speed=340, base_jump_range=9.78, max_jump_range=65.20,
                base_shield_strength=200, hull_mass=270, hull_integrity=315,
                fuel_capacity=16, power_plant_capacity=6
            ),
            image_filename="krait-phantom.png",
            description="An exploration-focused Krait variant with enhanced jump range and internals.",
            manufacturer_description="Faulcon DeLacy's exploration specialist, optimized for deep space missions."
        )
        
        return ships
    
    def _build_indices(self):
        """Build lookup indices for efficient searching"""
        self.by_class = {}
        self.by_role = {}
        self.by_manufacturer = {}
        self.by_cost_range = {}
        
        for ship in self.ships.values():
            # Index by class
            if ship.ship_class not in self.by_class:
                self.by_class[ship.ship_class] = []
            self.by_class[ship.ship_class].append(ship)
            
            # Index by primary role
            if ship.primary_role not in self.by_role:
                self.by_role[ship.primary_role] = []
            self.by_role[ship.primary_role].append(ship)
            
            # Index by manufacturer
            if ship.manufacturer not in self.by_manufacturer:
                self.by_manufacturer[ship.manufacturer] = []
            self.by_manufacturer[ship.manufacturer].append(ship)
            
            # Index by cost range
            if ship.base_cost < 1000000:
                cost_range = "budget"
            elif ship.base_cost < 10000000:
                cost_range = "mid_range"
            elif ship.base_cost < 50000000:
                cost_range = "expensive"
            else:
                cost_range = "premium"
            
            if cost_range not in self.by_cost_range:
                self.by_cost_range[cost_range] = []
            self.by_cost_range[cost_range].append(ship)
    
    def get_ship(self, ship_key: str) -> Optional[ShipSpecification]:
        """Get ship by key"""
        return self.ships.get(ship_key)
    
    def get_all_ships(self) -> List[ShipSpecification]:
        """Get all ships sorted by name"""
        return sorted(self.ships.values(), key=lambda s: s.display_name)
    
    def get_ships_by_class(self, ship_class: ShipClass) -> List[ShipSpecification]:
        """Get ships by class"""
        return self.by_class.get(ship_class, [])
    
    def get_ships_by_role(self, role: ShipRole) -> List[ShipSpecification]:
        """Get ships by role"""
        return self.by_role.get(role, [])
    
    def get_ships_by_manufacturer(self, manufacturer: Manufacturer) -> List[ShipSpecification]:
        """Get ships by manufacturer"""
        return self.by_manufacturer.get(manufacturer, [])
    
    def get_ships_by_cost_range(self, cost_range: str) -> List[ShipSpecification]:
        """Get ships by cost range (budget, mid_range, expensive, premium)"""
        return self.by_cost_range.get(cost_range, [])
    
    def search_ships(self, **criteria) -> List[ShipSpecification]:
        """Search ships by multiple criteria"""
        results = list(self.ships.values())
        
        if 'name_contains' in criteria:
            name_filter = criteria['name_contains'].lower()
            results = [s for s in results if name_filter in s.display_name.lower()]
        
        if 'ship_class' in criteria:
            results = [s for s in results if s.ship_class == criteria['ship_class']]
        
        if 'primary_role' in criteria:
            results = [s for s in results if s.primary_role == criteria['primary_role']]
        
        if 'manufacturer' in criteria:
            results = [s for s in results if s.manufacturer == criteria['manufacturer']]
        
        if 'max_cost' in criteria:
            results = [s for s in results if s.base_cost <= criteria['max_cost']]
        
        if 'min_jump_range' in criteria:
            results = [s for s in results if s.performance.max_jump_range >= criteria['min_jump_range']]
        
        if 'min_cargo' in criteria:
            results = [s for s in results if s.internal_slots.max_cargo_capacity >= criteria['min_cargo']]
        
        return sorted(results, key=lambda s: s.display_name)
    
    def get_comparison_data(self, ship_keys: List[str]) -> Dict[str, Any]:
        """Get comparison data for multiple ships"""
        ships = [self.get_ship(key) for key in ship_keys if self.get_ship(key)]
        
        if not ships:
            return {}
        
        comparison = {
            "ships": [ship.to_display_dict() for ship in ships],
            "stats": {}
        }
        
        # Compare key statistics
        stats = [
            "base_cost", "hull_mass", "max_speed", "boost_speed", 
            "base_jump_range", "max_jump_range", "base_shield_strength",
            "firepower_rating"
        ]
        
        for stat in stats:
            values = []
            for ship in ships:
                if stat == "firepower_rating":
                    values.append(ship.firepower_rating)
                else:
                    values.append(getattr(ship.performance, stat, 0))
            
            comparison["stats"][stat] = {
                "values": values,
                "min": min(values),
                "max": max(values),
                "best_ship": ships[values.index(max(values))].display_name if stat != "base_cost" else ships[values.index(min(values))].display_name
            }
        
        return comparison
    
    def get_ship_count(self) -> int:
        """Get total number of ships in database"""
        return len(self.ships)
    
    def get_available_images(self, base_assets_dir: str = "/home/tclar/Desktop/EliteDangerous/EliteDangerousCompanion/Assets") -> Dict[str, str]:
        """Get mapping of ship keys to available image paths"""
        available = {}
        for key, ship in self.ships.items():
            image_path = ship.get_image_path(base_assets_dir)
            if os.path.exists(image_path):
                available[key] = image_path
        return available


# Global database instance
_ship_database = None

def get_ship_database() -> EliteShipDatabase:
    """Get global ship database instance"""
    global _ship_database
    if _ship_database is None:
        _ship_database = EliteShipDatabase()
    return _ship_database


# Convenience functions
def get_ship(ship_key: str) -> Optional[ShipSpecification]:
    """Get ship specification by key"""
    return get_ship_database().get_ship(ship_key)

def get_all_ships() -> List[ShipSpecification]:
    """Get all available ships"""
    return get_ship_database().get_all_ships()

def search_ships(**criteria) -> List[ShipSpecification]:
    """Search ships by criteria"""
    return get_ship_database().search_ships(**criteria)


# Export main classes and functions
__all__ = [
    'ShipClass', 'ShipRole', 'Manufacturer', 'HardpointLoadout', 'InternalSlots',
    'ShipDimensions', 'ShipPerformance', 'ShipSpecification', 'EliteShipDatabase',
    'get_ship_database', 'get_ship', 'get_all_ships', 'search_ships'
]