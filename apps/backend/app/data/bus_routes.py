"""Static Bus Route Data

Popular bus routes with government RTC and estimated data.
All fares are AVERAGE/ESTIMATED based on distance.

Data Source: State RTC published schedules, industry standards
Fare Calculation: Distance-based using industry averages

"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class BusRoute:
    """Bus route information"""
    route_id: str
    
    # Route details
    origin_city: str
    origin_stop: str  # Primary bus stop/terminal
    destination_city: str
    destination_stop: str
    
    distance_km: int
    
    # Operators serving this route
    operators: List[Dict] = field(default_factory=list)  # [{name, type, bus_types}]
    
    # Schedule info
    frequency: str = "Multiple services daily"  # "Hourly", "Every 30 mins", etc.
    first_departure: str = "05:00"  # First bus time
    last_departure: str = "23:00"   # Last bus time
    
    # Duration estimates
    avg_duration_minutes: int = 0
    
    # Average fares by bus type
    fares: Dict[str, int] = field(default_factory=dict)  # {"ordinary": 300, "ac_seater": 600}


# ========================================
# POPULAR BUS ROUTES DATA
# ========================================

BUS_ROUTES: Dict[str, BusRoute] = {
    # ========================================
    # DELHI NCR ROUTES
    # ========================================
    "DEL-JAI": BusRoute(
        route_id="DEL-JAI",
        origin_city="Delhi",
        origin_stop="ISBT Kashmere Gate",
        destination_city="Jaipur",
        destination_stop="Sindhi Camp Bus Stand",
        distance_km=280,
        operators=[
            {"name": "RSRTC", "type": "government", "bus_types": ["ordinary", "deluxe", "volvo"]},
            {"name": "DTC", "type": "government", "bus_types": ["ordinary"]},
        ],
        frequency="Every 30 minutes",
        first_departure="05:00",
        last_departure="23:30",
        avg_duration_minutes=330,  # 5.5 hours
        fares={"ordinary": 350, "deluxe": 550, "ac_seater": 750, "volvo": 900}
    ),
    
    "DEL-AGR": BusRoute(
        route_id="DEL-AGR",
        origin_city="Delhi",
        origin_stop="ISBT Anand Vihar",
        destination_city="Agra",
        destination_stop="ISBT Agra",
        distance_km=233,
        operators=[
            {"name": "UPSRTC", "type": "government", "bus_types": ["ordinary", "deluxe", "ac_seater"]},
        ],
        frequency="Every 20 minutes",
        first_departure="04:30",
        last_departure="23:00",
        avg_duration_minutes=270,  # 4.5 hours
        fares={"ordinary": 280, "deluxe": 450, "ac_seater": 600}
    ),
    
    "DEL-CHD": BusRoute(
        route_id="DEL-CHD",
        origin_city="Delhi",
        origin_stop="ISBT Kashmere Gate",
        destination_city="Chandigarh",
        destination_stop="ISBT Sector 43",
        distance_km=250,
        operators=[
            {"name": "Haryana Roadways", "type": "government", "bus_types": ["ordinary", "volvo"]},
            {"name": "PRTC", "type": "government", "bus_types": ["ordinary", "volvo"]},
        ],
        frequency="Every 15 minutes",
        first_departure="04:00",
        last_departure="23:30",
        avg_duration_minutes=300,  # 5 hours
        fares={"ordinary": 320, "deluxe": 500, "volvo": 850}
    ),
    
    # ========================================
    # MUMBAI - PUNE - GOA CORRIDOR
    # ========================================
    "MUM-PUN": BusRoute(
        route_id="MUM-PUN",
        origin_city="Mumbai",
        origin_stop="Dadar Bus Depot",
        destination_city="Pune",
        destination_stop="Swargate Bus Stand",
        distance_km=150,
        operators=[
            {"name": "MSRTC", "type": "government", "bus_types": ["ordinary", "semi_deluxe", "volvo"]},
            {"name": "Neeta Travels", "type": "private", "bus_types": ["ac_seater", "ac_sleeper"]},
            {"name": "VRL Travels", "type": "private", "bus_types": ["volvo", "multi_axle"]},
        ],
        frequency="Every 10 minutes",
        first_departure="04:00",
        last_departure="00:00",
        avg_duration_minutes=210,  # 3.5 hours
        fares={
            "ordinary": 220,
            "semi_deluxe": 320,
            "ac_seater": 500,
            "non_ac_sleeper": 450,
            "ac_sleeper": 700,
            "volvo": 550,
            "multi_axle": 850
        }
    ),
    
    "MUM-GOA": BusRoute(
        route_id="MUM-GOA",
        origin_city="Mumbai",
        origin_stop="Dadar Bus Depot",
        destination_city="Goa",
        destination_stop="Panaji Bus Stand",
        distance_km=590,
        operators=[
            {"name": "Neeta Travels", "type": "private", "bus_types": ["ac_sleeper", "volvo"]},
            {"name": "Paulo Travels", "type": "private", "bus_types": ["ac_sleeper", "multi_axle"]},
            {"name": "KSRTC", "type": "government", "bus_types": ["ac_seater", "non_ac_sleeper"]},
        ],
        frequency="Multiple departures (evening)",
        first_departure="17:00",
        last_departure="23:00",
        avg_duration_minutes=720,  # 12 hours (overnight)
        fares={
            "ac_seater": 1100,
            "non_ac_sleeper": 900,
            "ac_sleeper": 1500,
            "volvo": 1800,
            "multi_axle": 2200
        }
    ),
    
    "PUN-GOA": BusRoute(
        route_id="PUN-GOA",
        origin_city="Pune",
        origin_stop="Swargate Bus Stand",
        destination_city="Goa",
        destination_stop="Panaji Bus Stand",
        distance_km=450,
        operators=[
            {"name": "MSRTC", "type": "government", "bus_types": ["ordinary", "semi_deluxe"]},
            {"name": "VRL Travels", "type": "private", "bus_types": ["ac_sleeper", "volvo"]},
        ],
        frequency="Multiple services daily",
        first_departure="06:00",
        last_departure="23:00",
        avg_duration_minutes=540,  # 9 hours
        fares={
            "ordinary": 650,
            "semi_deluxe": 850,
            "ac_sleeper": 1100,
            "volvo": 1400
        }
    ),
    
    # ========================================
    # BANGALORE - CHENNAI - HYDERABAD CORRIDOR
    # ========================================
    "BLR-CHE": BusRoute(
        route_id="BLR-CHE",
        origin_city="Bangalore",
        origin_stop="Kempegowda Bus Station (Majestic)",
        destination_city="Chennai",
        destination_stop="Chennai Mofussil Bus Terminus (CMBT)",
        distance_km=350,
        operators=[
            {"name": "KSRTC", "type": "government", "bus_types": ["ordinary", "airavat", "flybus"]},
            {"name": "SETC", "type": "government", "bus_types": ["ordinary", "ac_seater"]},
            {"name": "SRS Travels", "type": "private", "bus_types": ["volvo", "ac_sleeper"]},
        ],
        frequency="Every 30 minutes",
        first_departure="05:00",
        last_departure="23:30",
        avg_duration_minutes=390,  # 6.5 hours
        fares={"ordinary": 450, "airavat": 800, "ac_seater": 700, "volvo": 1000}
    ),
    
    "BLR-HYD": BusRoute(
        route_id="BLR-HYD",
        origin_city="Bangalore",
        origin_stop="Kempegowda Bus Station (Majestic)",
        destination_city="Hyderabad",
        destination_stop="MGBS (Mahatma Gandhi Bus Station)",
        distance_km=575,
        operators=[
            {"name": "KSRTC", "type": "government", "bus_types": ["airavat", "corona"]},
            {"name": "TSRTC", "type": "government", "bus_types": ["garuda", "super_luxury"]},
            {"name": "Orange Travels", "type": "private", "bus_types": ["volvo", "ac_sleeper"]},
        ],
        frequency="Multiple services daily",
        first_departure="06:00",
        last_departure="23:00",
        avg_duration_minutes=540,  # 9 hours
        fares={"ordinary": 600, "ac_seater": 900, "airavat": 1100, "volvo": 1300, "ac_sleeper": 1400}
    ),
    
    "CHE-HYD": BusRoute(
        route_id="CHE-HYD",
        origin_city="Chennai",
        origin_stop="Chennai Mofussil Bus Terminus (CMBT)",
        destination_city="Hyderabad",
        destination_stop="MGBS (Mahatma Gandhi Bus Station)",
        distance_km=630,
        operators=[
            {"name": "TSRTC", "type": "government", "bus_types": ["garuda", "super_luxury"]},
            {"name": "SETC", "type": "government", "bus_types": ["ac_seater", "sleeper"]},
        ],
        frequency="Multiple services daily",
        first_departure="17:00",
        last_departure="22:00",
        avg_duration_minutes=660,  # 11 hours (mostly overnight)
        fares={"ordinary": 650, "ac_seater": 950, "sleeper": 1000, "ac_sleeper": 1300}
    ),
    
    # ========================================
    # AHMEDABAD - GUJARAT ROUTES
    # ========================================
    "AMD-MUM": BusRoute(
        route_id="AMD-MUM",
        origin_city="Ahmedabad",
        origin_stop="Ahmedabad Central Bus Station",
        destination_city="Mumbai",
        destination_stop="Borivali Bus Depot",
        distance_km=530,
        operators=[
            {"name": "GSRTC", "type": "government", "bus_types": ["ordinary", "volvo"]},
            {"name": "Eagle Travels", "type": "private", "bus_types": ["ac_sleeper", "volvo"]},
        ],
        frequency="Hourly",
        first_departure="05:00",
        last_departure="23:30",
        avg_duration_minutes=540,  # 9 hours
        fares={"ordinary": 500, "ac_seater": 850, "volvo": 1100, "ac_sleeper": 1300}
    ),
    
    # ========================================
    # SOUTH INDIA ROUTES
    # ========================================
    "BLR-MYS": BusRoute(
        route_id="BLR-MYS",
        origin_city="Bangalore",
        origin_stop="Kempegowda Bus Station (Majestic)",
        destination_city="Mysore",
        destination_stop="Mysore Bus Stand",
        distance_km=145,
        operators=[
            {"name": "KSRTC", "type": "government", "bus_types": ["ordinary", "rajahamsa", "airavat"]},
        ],
        frequency="Every 15 minutes",
        first_departure="04:30",
        last_departure="23:00",
        avg_duration_minutes=180,  # 3 hours
        fares={"ordinary": 150, "rajahamsa": 300, "airavat": 450}
    ),
    
    "BLR-COI": BusRoute(
        route_id="BLR-COI",
        origin_city="Bangalore",
        origin_stop="Kempegowda Bus Station (Majestic)",
        destination_city="Coimbatore",
        destination_stop="Gandhipuram Bus Stand",
        distance_km=365,
        operators=[
            {"name": "KSRTC", "type": "government", "bus_types": ["airavat", "corona"]},
            {"name": "SETC", "type": "government", "bus_types": ["ac_seater"]},
        ],
        frequency="Multiple services daily",
        first_departure="06:00",
        last_departure="22:00",
        avg_duration_minutes=420,  # 7 hours
        fares={"ordinary": 400, "ac_seater": 650, "airavat": 800}
    ),
}


# Distance-based fare calculation (when exact route not in database)
DISTANCE_FARE_SLABS = {
    # Distance range: {bus_type: fare_per_km}
    (0, 100): {"ordinary": 0.80, "deluxe": 1.50, "ac_seater": 2.50, "ac_sleeper": 3.50, "volvo": 4.00},
    (101, 300): {"ordinary": 0.75, "deluxe": 1.40, "ac_seater": 2.30, "ac_sleeper": 3.20, "volvo": 3.70},
    (301, 500): {"ordinary": 0.70, "deluxe": 1.30, "ac_seater": 2.10, "ac_sleeper": 3.00, "volvo": 3.50},
    (501, 1000): {"ordinary": 0.65, "deluxe": 1.20, "ac_seater": 2.00, "ac_sleeper": 2.80, "volvo": 3.30},
}


def calculate_average_fare(distance_km: int, bus_type: str) -> int:
    """Calculate average fare based on distance and bus type"""
    for (min_dist, max_dist), rates in DISTANCE_FARE_SLABS.items():
        if min_dist <= distance_km <= max_dist:
            rate = rates.get(bus_type, 1.00)  # Default to deluxe rate
            return int(distance_km * rate)
    
    # For very long distances
    rate = DISTANCE_FARE_SLABS[(501, 1000)].get(bus_type, 0.65)
    return int(distance_km * rate)


def get_bus_route(origin: str, destination: str) -> Optional[BusRoute]:
    """Get bus route data for origin-destination pair"""
    # Normalize city names to route keys
    city_map = {
        "delhi": "DEL", "new delhi": "DEL",
        "mumbai": "MUM", "bombay": "MUM",
        "bangalore": "BLR", "bengaluru": "BLR",
        "chennai": "CHE", "madras": "CHE",
        "hyderabad": "HYD",
        "pune": "PUN",
        "goa": "GOA", "panaji": "GOA",
        "jaipur": "JAI",
        "agra": "AGR",
        "chandigarh": "CHD",
        "ahmedabad": "AMD",
        "mysore": "MYS", "mysuru": "MYS",
        "coimbatore": "COI",
    }
    
    origin_code = city_map.get(origin.lower(), origin.upper()[:3])
    dest_code = city_map.get(destination.lower(), destination.upper()[:3])
    
    route_key = f"{origin_code}-{dest_code}"
    return BUS_ROUTES.get(route_key)


# Approximate distances between cities (km) for fare calculation
CITY_DISTANCES: Dict[str, Dict[str, int]] = {
    "DEL": {"JAI": 280, "AGR": 233, "CHD": 250, "LKO": 555, "VAR": 820},
    "MUM": {"PUN": 150, "GOA": 590, "AMD": 530, "NAG": 840},
    "BLR": {"CHE": 350, "HYD": 575, "MYS": 145, "COI": 365, "GOA": 560},
    "CHE": {"BLR": 350, "HYD": 630, "COI": 505, "MAD": 450},
    "HYD": {"BLR": 575, "CHE": 630, "MUM": 710, "VIJ": 275},
    "PUN": {"MUM": 150, "GOA": 450, "BLR": 840, "HYD": 560},
    "AMD": {"MUM": 530, "JAI": 660, "IND": 400, "SUK": 410},
}


def get_distance(origin: str, destination: str) -> Optional[int]:
    """Get approximate distance between two cities"""
    city_map = {
        "delhi": "DEL", "mumbai": "MUM", "bangalore": "BLR",
        "chennai": "CHE", "hyderabad": "HYD", "pune": "PUN",
        "ahmedabad": "AMD", "jaipur": "JAI", "goa": "GOA",
    }
    
    origin_code = city_map.get(origin.lower(), origin.upper()[:3])
    dest_code = city_map.get(destination.lower(), destination.upper()[:3])
    
    if origin_code in CITY_DISTANCES and dest_code in CITY_DISTANCES[origin_code]:
        return CITY_DISTANCES[origin_code][dest_code]
    
    if dest_code in CITY_DISTANCES and origin_code in CITY_DISTANCES[dest_code]:
        return CITY_DISTANCES[dest_code][origin_code]
    
    return None
