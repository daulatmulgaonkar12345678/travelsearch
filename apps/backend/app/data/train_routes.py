"""Static Train Route Data

Popular train routes with official timetable data.
All fares are AVERAGE/ESTIMATED based on distance.

Data Source: Indian Railways public timetable
Fare Calculation: Distance-based using official fare slabs
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import time


@dataclass
class TrainSchedule:
    """Train schedule for a route"""
    train_number: str
    train_name: str
    train_type: str  # Rajdhani, Shatabdi, Express, Mail, etc.
    
    departure_station: str  # Station code
    arrival_station: str
    departure_time: str  # "HH:MM"
    arrival_time: str
    duration_minutes: int
    
    distance_km: int
    days_of_operation: List[str]  # ["Mon", "Tue", ...] or ["Daily"]
    
    # Average fares by class (based on distance slabs)
    fares: Dict[str, int] = field(default_factory=dict)  # {"SL": 450, "3A": 1200, ...}
    
    stops_count: int = 0
    intermediate_stops: List[str] = field(default_factory=list)
    has_pantry: bool = False


# ========================================
# POPULAR TRAIN ROUTES DATA
# ========================================
# Routes organized by corridor

TRAIN_ROUTES: Dict[str, List[TrainSchedule]] = {
    # ========================================
    # DELHI - MUMBAI CORRIDOR
    # ========================================
    "NDLS-CSMT": [
        TrainSchedule(
            train_number="12951",
            train_name="Mumbai Rajdhani",
            train_type="Rajdhani",
            departure_station="NDLS",
            arrival_station="CSMT",
            departure_time="16:55",
            arrival_time="08:35",
            duration_minutes=940,  # 15h 40m
            distance_km=1384,
            days_of_operation=["Daily"],
            fares={"3A": 2545, "2A": 3685, "1A": 6225},
            stops_count=4,
            intermediate_stops=["KOTA", "RTM", "BRC", "ST"],
            has_pantry=True
        ),
        TrainSchedule(
            train_number="12952",
            train_name="Mumbai Rajdhani",
            train_type="Rajdhani",
            departure_station="NDLS",
            arrival_station="BCT",
            departure_time="16:25",
            arrival_time="08:15",
            duration_minutes=950,
            distance_km=1386,
            days_of_operation=["Daily"],
            fares={"3A": 2545, "2A": 3685, "1A": 6225},
            stops_count=5,
            has_pantry=True
        ),
        TrainSchedule(
            train_number="12137",
            train_name="Punjab Mail",
            train_type="Mail/Express",
            departure_station="NDLS",
            arrival_station="CSMT",
            departure_time="19:20",
            arrival_time="19:35",
            duration_minutes=1455,  # 24h 15m
            distance_km=1386,
            days_of_operation=["Daily"],
            fares={"SL": 575, "3A": 1525, "2A": 2200, "1A": 3700},
            stops_count=15,
            has_pantry=True
        ),
    ],
    
    "CSMT-NDLS": [
        TrainSchedule(
            train_number="12952",
            train_name="Mumbai Rajdhani",
            train_type="Rajdhani",
            departure_station="CSMT",
            arrival_station="NDLS",
            departure_time="17:00",
            arrival_time="08:35",
            duration_minutes=935,
            distance_km=1384,
            days_of_operation=["Daily"],
            fares={"3A": 2545, "2A": 3685, "1A": 6225},
            stops_count=4,
            has_pantry=True
        ),
    ],
    
    # ========================================
    # DELHI - BANGALORE CORRIDOR
    # ========================================
    "NDLS-SBC": [
        TrainSchedule(
            train_number="22691",
            train_name="Rajdhani Express",
            train_type="Rajdhani",
            departure_station="NDLS",
            arrival_station="SBC",
            departure_time="20:50",
            arrival_time="06:10",
            duration_minutes=2000,  # 33h 20m
            distance_km=2444,
            days_of_operation=["Mon", "Tue", "Sat"],
            fares={"3A": 3430, "2A": 4970, "1A": 8365},
            stops_count=6,
            has_pantry=True
        ),
        TrainSchedule(
            train_number="12627",
            train_name="Karnataka Express",
            train_type="Superfast",
            departure_station="NDLS",
            arrival_station="SBC",
            departure_time="21:55",
            arrival_time="06:40",
            duration_minutes=2445,  # 40h 45m
            distance_km=2444,
            days_of_operation=["Daily"],
            fares={"SL": 845, "3A": 2245, "2A": 3280, "1A": 5500},
            stops_count=18,
            has_pantry=True
        ),
    ],
    
    "SBC-NDLS": [
        TrainSchedule(
            train_number="22692",
            train_name="Rajdhani Express",
            train_type="Rajdhani",
            departure_station="SBC",
            arrival_station="NDLS",
            departure_time="20:00",
            arrival_time="06:55",
            duration_minutes=2035,
            distance_km=2444,
            days_of_operation=["Wed", "Fri", "Sun"],
            fares={"3A": 3430, "2A": 4970, "1A": 8365},
            stops_count=6,
            has_pantry=True
        ),
    ],
    
    # ========================================
    # DELHI - CHENNAI CORRIDOR  
    # ========================================
    "NDLS-MAS": [
        TrainSchedule(
            train_number="12621",
            train_name="Tamil Nadu Express",
            train_type="Superfast",
            departure_station="NDLS",
            arrival_station="MAS",
            departure_time="22:30",
            arrival_time="07:05",
            duration_minutes=1955,  # 32h 35m
            distance_km=2180,
            days_of_operation=["Daily"],
            fares={"SL": 755, "3A": 2005, "2A": 2895, "1A": 4900},
            stops_count=12,
            has_pantry=True
        ),
        TrainSchedule(
            train_number="12433",
            train_name="Chennai Rajdhani",
            train_type="Rajdhani",
            departure_station="HNZM",
            arrival_station="MAS",
            departure_time="15:55",
            arrival_time="20:05",
            duration_minutes=1690,  # 28h 10m
            distance_km=2182,
            days_of_operation=["Wed", "Fri"],
            fares={"3A": 3150, "2A": 4565, "1A": 7680},
            stops_count=5,
            has_pantry=True
        ),
    ],
    
    # ========================================
    # DELHI - KOLKATA CORRIDOR
    # ========================================
    "NDLS-HWH": [
        TrainSchedule(
            train_number="12301",
            train_name="Howrah Rajdhani",
            train_type="Rajdhani",
            departure_station="NDLS",
            arrival_station="HWH",
            departure_time="16:55",
            arrival_time="09:55",
            duration_minutes=1020,  # 17h
            distance_km=1447,
            days_of_operation=["Daily"],
            fares={"3A": 2090, "2A": 3015, "1A": 5065},
            stops_count=3,
            has_pantry=True
        ),
        TrainSchedule(
            train_number="12305",
            train_name="Howrah Rajdhani (Via Patna)",
            train_type="Rajdhani",
            departure_station="NDLS",
            arrival_station="HWH",
            departure_time="17:00",
            arrival_time="10:05",
            duration_minutes=1025,
            distance_km=1531,
            days_of_operation=["Mon", "Tue", "Wed", "Thu", "Sat", "Sun"],
            fares={"3A": 2180, "2A": 3150, "1A": 5290},
            stops_count=5,
            has_pantry=True
        ),
    ],
    
    # ========================================
    # MUMBAI - BANGALORE CORRIDOR
    # ========================================
    "CSMT-SBC": [
        TrainSchedule(
            train_number="11301",
            train_name="Udyan Express",
            train_type="Express",
            departure_station="CSMT",
            arrival_station="SBC",
            departure_time="08:05",
            arrival_time="08:00",
            duration_minutes=1435,  # 23h 55m
            distance_km=1153,
            days_of_operation=["Daily"],
            fares={"SL": 485, "3A": 1285, "2A": 1855, "1A": 3130},
            stops_count=20,
            has_pantry=True
        ),
    ],
    
    # ========================================
    # MUMBAI - PUNE CORRIDOR (Short distance)
    # ========================================
    "CSMT-PUNE": [
        TrainSchedule(
            train_number="12127",
            train_name="Intercity Express",
            train_type="Superfast",
            departure_station="CSMT",
            arrival_station="PUNE",
            departure_time="06:45",
            arrival_time="10:15",
            duration_minutes=210,  # 3h 30m
            distance_km=192,
            days_of_operation=["Daily"],
            fares={"CC": 340, "2S": 115},
            stops_count=4,
            has_pantry=False
        ),
        TrainSchedule(
            train_number="12123",
            train_name="Deccan Queen",
            train_type="Superfast",
            departure_station="CSMT",
            arrival_station="PUNE",
            departure_time="17:10",
            arrival_time="20:25",
            duration_minutes=195,  # 3h 15m
            distance_km=192,
            days_of_operation=["Daily"],
            fares={"CC": 355, "2S": 115},
            stops_count=3,
            has_pantry=True
        ),
    ],
    
    # ========================================
    # BANGALORE - CHENNAI CORRIDOR
    # ========================================
    "SBC-MAS": [
        TrainSchedule(
            train_number="12007",
            train_name="Shatabdi Express",
            train_type="Shatabdi",
            departure_station="SBC",
            arrival_station="MAS",
            departure_time="06:00",
            arrival_time="10:50",
            duration_minutes=290,  # 4h 50m
            distance_km=362,
            days_of_operation=["Daily"],
            fares={"CC": 615, "EC": 1255},
            stops_count=1,
            has_pantry=True
        ),
        TrainSchedule(
            train_number="12639",
            train_name="Brindavan Express",
            train_type="Superfast",
            departure_station="SBC",
            arrival_station="MAS",
            departure_time="07:50",
            arrival_time="13:00",
            duration_minutes=310,
            distance_km=362,
            days_of_operation=["Daily"],
            fares={"2S": 145, "CC": 535},
            stops_count=6,
            has_pantry=False
        ),
    ],
    
    # ========================================
    # HYDERABAD - BANGALORE CORRIDOR
    # ========================================
    "SC-SBC": [
        TrainSchedule(
            train_number="12785",
            train_name="Rayalaseema Express",
            train_type="Superfast",
            departure_station="SC",
            arrival_station="SBC",
            departure_time="17:55",
            arrival_time="06:45",
            duration_minutes=770,  # 12h 50m
            distance_km=575,
            days_of_operation=["Daily"],
            fares={"SL": 295, "3A": 780, "2A": 1130},
            stops_count=10,
            has_pantry=True
        ),
    ],
    
    # ========================================
    # DELHI - JAIPUR CORRIDOR
    # ========================================
    "NDLS-JP": [
        TrainSchedule(
            train_number="12015",
            train_name="Ajmer Shatabdi",
            train_type="Shatabdi",
            departure_station="NDLS",
            arrival_station="JP",
            departure_time="06:05",
            arrival_time="10:40",
            duration_minutes=275,  # 4h 35m
            distance_km=308,
            days_of_operation=["Daily"],
            fares={"CC": 785, "EC": 1575},
            stops_count=1,
            has_pantry=True
        ),
        TrainSchedule(
            train_number="12413",
            train_name="Jaipur SF Express",
            train_type="Superfast",
            departure_station="NDLS",
            arrival_station="JP",
            departure_time="18:10",
            arrival_time="22:40",
            duration_minutes=270,
            distance_km=308,
            days_of_operation=["Daily"],
            fares={"SL": 220, "3A": 580, "2A": 835},
            stops_count=2,
            has_pantry=False
        ),
    ],
    
    # ========================================
    # DELHI - GOA CORRIDOR
    # ========================================
    "NDLS-MAO": [
        TrainSchedule(
            train_number="12779",
            train_name="Goa Express",
            train_type="Superfast",
            departure_station="HNZM",
            arrival_station="MAO",
            departure_time="15:00",
            arrival_time="17:20",
            duration_minutes=1580,  # 26h 20m
            distance_km=1915,
            days_of_operation=["Daily"],
            fares={"SL": 660, "3A": 1755, "2A": 2530, "1A": 4260},
            stops_count=15,
            has_pantry=True
        ),
    ],
}


# Distance-based fare calculation (when exact route not in database)
DISTANCE_FARE_SLABS = {
    # Distance range: {class: base_fare_per_km}
    (0, 300): {"SL": 0.50, "3A": 1.25, "2A": 1.80, "1A": 3.00, "CC": 1.50, "2S": 0.35},
    (301, 500): {"SL": 0.48, "3A": 1.20, "2A": 1.75, "1A": 2.90, "CC": 1.45, "2S": 0.32},
    (501, 1000): {"SL": 0.45, "3A": 1.15, "2A": 1.65, "1A": 2.80, "CC": 1.40, "2S": 0.30},
    (1001, 2000): {"SL": 0.42, "3A": 1.10, "2A": 1.55, "1A": 2.60, "CC": 1.35, "2S": 0.28},
    (2001, 5000): {"SL": 0.40, "3A": 1.05, "2A": 1.50, "1A": 2.50, "CC": 1.30, "2S": 0.26},
}


def calculate_average_fare(distance_km: int, train_class: str) -> int:
    """Calculate average fare based on distance and class"""
    for (min_dist, max_dist), rates in DISTANCE_FARE_SLABS.items():
        if min_dist <= distance_km <= max_dist:
            rate = rates.get(train_class, 0.50)  # Default to SL rate
            return int(distance_km * rate)
    
    # For very long distances, use the highest slab
    rate = DISTANCE_FARE_SLABS[(2001, 5000)].get(train_class, 0.40)
    return int(distance_km * rate)


def get_trains_for_route(origin: str, destination: str) -> Optional[List[TrainSchedule]]:
    """Get trains for a specific route"""
    route_key = f"{origin.upper()}-{destination.upper()}"
    return TRAIN_ROUTES.get(route_key)


# Approximate distances between major cities (km) for fare calculation
CITY_DISTANCES: Dict[str, Dict[str, int]] = {
    "NDLS": {"CSMT": 1384, "BCT": 1386, "SBC": 2444, "MAS": 2180, "HWH": 1447, "SC": 1676, "JP": 308, "MAO": 1915, "ADI": 941},
    "CSMT": {"NDLS": 1384, "SBC": 1153, "PUNE": 192, "SC": 711, "MAS": 1279, "ADI": 492, "MAO": 587},
    "SBC": {"NDLS": 2444, "CSMT": 1153, "MAS": 362, "SC": 575, "HWH": 1871, "ERS": 566},
    "MAS": {"NDLS": 2180, "CSMT": 1279, "SBC": 362, "SC": 793, "HWH": 1659, "TVC": 773},
    "HWH": {"NDLS": 1447, "CSMT": 1968, "SBC": 1871, "MAS": 1659, "PNBE": 545},
    "SC": {"NDLS": 1676, "CSMT": 711, "SBC": 575, "MAS": 793, "VSKP": 530},
}


def get_distance(origin: str, destination: str) -> Optional[int]:
    """Get distance between two stations"""
    origin = origin.upper()
    destination = destination.upper()
    
    if origin in CITY_DISTANCES and destination in CITY_DISTANCES[origin]:
        return CITY_DISTANCES[origin][destination]
    
    if destination in CITY_DISTANCES and origin in CITY_DISTANCES[destination]:
        return CITY_DISTANCES[destination][origin]
    
    return None
