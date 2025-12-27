"""MSRTC Seed Data - Phase 1 Routes

Pre-populated data for high-traffic Maharashtra routes.
Includes Marathi names stored as UTF-8 with normalized keys.

Phase 1 Routes:
- Pune ↔ Mumbai
- Pune ↔ Nashik  
- Mumbai ↔ Kolhapur
- Pune ↔ Kolhapur
- Pune ↔ Aurangabad
- Mumbai ↔ Pune (reverse)

Data Source: MSRTC published schedules and industry knowledge
"""

from typing import Dict, List
from dataclasses import dataclass, field


# ============================================================
# MSRTC STOPS - Major Maharashtra Bus Stations
# ============================================================

MSRTC_STOPS: List[Dict] = [
    # Major Cities - Phase 1
    {
        "value": "PUNE",
        "name_marathi": "पुणे",
        "name_english": "Pune",
        "name_normalized": "pune",
        "stop_type": "major",
        "district": "Pune",
        "station_name": "पुणे स्वारगेट बस स्थानक",
        "station_name_english": "Pune Swargate Bus Stand",
    },
    {
        "value": "PUNE_SL",
        "name_marathi": "पुणे शिवाजीनगर",
        "name_english": "Pune Shivajinagar",
        "name_normalized": "pune shivajinagar",
        "stop_type": "major",
        "district": "Pune",
        "station_name": "पुणे शिवाजीनगर बस स्थानक",
        "station_name_english": "Pune Shivajinagar Bus Stand",
    },
    {
        "value": "MUMBAI",
        "name_marathi": "मुंबई",
        "name_english": "Mumbai",
        "name_normalized": "mumbai",
        "stop_type": "major",
        "district": "Mumbai",
        "station_name": "मुंबई सेंट्रल बस स्थानक",
        "station_name_english": "Mumbai Central Bus Stand",
    },
    {
        "value": "MUMBAI_DR",
        "name_marathi": "मुंबई दादर",
        "name_english": "Mumbai Dadar",
        "name_normalized": "mumbai dadar",
        "stop_type": "major",
        "district": "Mumbai",
        "station_name": "दादर (टर्मिनस)",
        "station_name_english": "Dadar (Terminus)",
    },
    {
        "value": "NASHIK",
        "name_marathi": "नाशिक",
        "name_english": "Nashik",
        "name_normalized": "nashik",
        "stop_type": "major",
        "district": "Nashik",
        "station_name": "नाशिक मध्यवर्ती बस स्थानक",
        "station_name_english": "Nashik Central Bus Stand",
    },
    {
        "value": "KOLHAPUR",
        "name_marathi": "कोल्हापूर",
        "name_english": "Kolhapur",
        "name_normalized": "kolhapur",
        "stop_type": "major",
        "district": "Kolhapur",
        "station_name": "कोल्हापूर मध्यवर्ती बस स्थानक",
        "station_name_english": "Kolhapur Central Bus Stand",
    },
    {
        "value": "AURANGABAD",
        "name_marathi": "औरंगाबाद",
        "name_english": "Aurangabad",
        "name_normalized": "aurangabad",
        "stop_type": "major",
        "district": "Aurangabad",
        "station_name": "औरंगाबाद मध्यवर्ती बस स्थानक",
        "station_name_english": "Aurangabad Central Bus Stand",
    },
    
    # Additional Major Cities for Phase 2
    {
        "value": "NAGPUR",
        "name_marathi": "नागपूर",
        "name_english": "Nagpur",
        "name_normalized": "nagpur",
        "stop_type": "major",
        "district": "Nagpur",
        "station_name": "नागपूर बस स्थानक",
        "station_name_english": "Nagpur Bus Stand",
    },
    {
        "value": "SOLAPUR",
        "name_marathi": "सोलापूर",
        "name_english": "Solapur",
        "name_normalized": "solapur",
        "stop_type": "major",
        "district": "Solapur",
        "station_name": "सोलापूर बस स्थानक",
        "station_name_english": "Solapur Bus Stand",
    },
    {
        "value": "SATARA",
        "name_marathi": "सातारा",
        "name_english": "Satara",
        "name_normalized": "satara",
        "stop_type": "major",
        "district": "Satara",
        "station_name": "सातारा बस स्थानक",
        "station_name_english": "Satara Bus Stand",
    },
    {
        "value": "SANGLI",
        "name_marathi": "सांगली",
        "name_english": "Sangli",
        "name_normalized": "sangli",
        "stop_type": "major",
        "district": "Sangli",
        "station_name": "सांगली बस स्थानक",
        "station_name_english": "Sangli Bus Stand",
    },
    {
        "value": "AHMEDNAGAR",
        "name_marathi": "अहमदनगर",
        "name_english": "Ahmednagar",
        "name_normalized": "ahmednagar",
        "stop_type": "major",
        "district": "Ahmednagar",
        "station_name": "अहमदनगर बस स्थानक",
        "station_name_english": "Ahmednagar Bus Stand",
    },
    {
        "value": "THANE",
        "name_marathi": "ठाणे",
        "name_english": "Thane",
        "name_normalized": "thane",
        "stop_type": "major",
        "district": "Thane",
        "station_name": "ठाणे बस स्थानक",
        "station_name_english": "Thane Bus Stand",
    },
    {
        "value": "PANVEL",
        "name_marathi": "पनवेल",
        "name_english": "Panvel",
        "name_normalized": "panvel",
        "stop_type": "major",
        "district": "Raigad",
        "station_name": "पनवेल बस स्थानक",
        "station_name_english": "Panvel Bus Stand",
    },
    {
        "value": "LONAVALA",
        "name_marathi": "लोणावळा",
        "name_english": "Lonavala",
        "name_normalized": "lonavala",
        "stop_type": "minor",
        "district": "Pune",
        "station_name": "लोणावळा बस स्थानक",
        "station_name_english": "Lonavala Bus Stand",
    },
    {
        "value": "SHIRDI",
        "name_marathi": "शिर्डी",
        "name_english": "Shirdi",
        "name_normalized": "shirdi",
        "stop_type": "major",
        "district": "Ahmednagar",
        "station_name": "शिर्डी बस स्थानक",
        "station_name_english": "Shirdi Bus Stand",
    },
    {
        "value": "MAHABALESHWAR",
        "name_marathi": "महाबळेश्वर",
        "name_english": "Mahabaleshwar",
        "name_normalized": "mahabaleshwar",
        "stop_type": "minor",
        "district": "Satara",
        "station_name": "महाबळेश्वर बस स्थानक",
        "station_name_english": "Mahabaleshwar Bus Stand",
    },
]


# ============================================================
# MSRTC BUS TYPES
# ============================================================

MSRTC_BUS_TYPES = {
    "ST": {
        "name_marathi": "साधी",
        "name_english": "Ordinary (ST)",
        "is_ac": False,
        "is_sleeper": False,
        "fare_multiplier": 1.0,
    },
    "SEMI_LUX": {
        "name_marathi": "निमलक्झरी",
        "name_english": "Semi-Luxury",
        "is_ac": False,
        "is_sleeper": False,
        "fare_multiplier": 1.3,
    },
    "ASIAD": {
        "name_marathi": "आशियाड",
        "name_english": "Asiad (AC)",
        "is_ac": True,
        "is_sleeper": False,
        "fare_multiplier": 1.8,
    },
    "SHIVNERI": {
        "name_marathi": "शिवनेरी",
        "name_english": "Shivneri (Premium AC)",
        "is_ac": True,
        "is_sleeper": False,
        "fare_multiplier": 2.2,
    },
    "SHIVSHAHI": {
        "name_marathi": "शिवशाही",
        "name_english": "Shivshahi (AC Sleeper)",
        "is_ac": True,
        "is_sleeper": True,
        "fare_multiplier": 2.0,
    },
    "ASHWAMEDH": {
        "name_marathi": "अश्वमेध",
        "name_english": "Ashwamedh (Multi-Axle AC)",
        "is_ac": True,
        "is_sleeper": True,
        "fare_multiplier": 2.5,
    },
}


# ============================================================
# PHASE 1 ROUTES - High Traffic MH Routes
# ============================================================

@dataclass
class MSRTCRoute:
    """MSRTC Route Definition"""
    route_id: str
    origin_code: str
    origin_marathi: str
    origin_english: str
    origin_station: str
    destination_code: str
    destination_marathi: str
    destination_english: str
    destination_station: str
    distance_km: int
    base_fare: int  # Ordinary ST fare
    avg_duration_minutes: int
    frequency: str
    first_departure: str
    last_departure: str
    bus_types: List[str] = field(default_factory=list)
    via_stops: List[str] = field(default_factory=list)


MSRTC_PHASE1_ROUTES: List[MSRTCRoute] = [
    # ========================================
    # PUNE ↔ MUMBAI (Most frequent route)
    # ========================================
    MSRTCRoute(
        route_id="MSRTC-PUNE-MUM",
        origin_code="PUNE",
        origin_marathi="पुणे",
        origin_english="Pune",
        origin_station="पुणे स्वारगेट बस स्थानक",
        destination_code="MUMBAI",
        destination_marathi="मुंबई",
        destination_english="Mumbai",
        destination_station="मुंबई सेंट्रल बस स्थानक",
        distance_km=150,
        base_fare=280,  # ST ordinary fare
        avg_duration_minutes=210,  # 3.5 hours
        frequency="Every 15 minutes",
        first_departure="04:00",
        last_departure="23:30",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVNERI", "SHIVSHAHI"],
        via_stops=["लोणावळा", "खंडाला", "पनवेल"],
    ),
    MSRTCRoute(
        route_id="MSRTC-MUM-PUNE",
        origin_code="MUMBAI",
        origin_marathi="मुंबई",
        origin_english="Mumbai",
        origin_station="मुंबई सेंट्रल बस स्थानक",
        destination_code="PUNE",
        destination_marathi="पुणे",
        destination_english="Pune",
        destination_station="पुणे स्वारगेट बस स्थानक",
        distance_km=150,
        base_fare=280,
        avg_duration_minutes=210,
        frequency="Every 15 minutes",
        first_departure="04:00",
        last_departure="23:30",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVNERI", "SHIVSHAHI"],
        via_stops=["पनवेल", "खंडाला", "लोणावळा"],
    ),
    
    # ========================================
    # PUNE ↔ NASHIK
    # ========================================
    MSRTCRoute(
        route_id="MSRTC-PUNE-NSK",
        origin_code="PUNE",
        origin_marathi="पुणे",
        origin_english="Pune",
        origin_station="पुणे शिवाजीनगर बस स्थानक",
        destination_code="NASHIK",
        destination_marathi="नाशिक",
        destination_english="Nashik",
        destination_station="नाशिक मध्यवर्ती बस स्थानक",
        distance_km=212,
        base_fare=350,
        avg_duration_minutes=300,  # 5 hours
        frequency="Every 30 minutes",
        first_departure="05:00",
        last_departure="22:00",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVNERI"],
        via_stops=["अहमदनगर", "संगमनेर", "शिर्डी"],
    ),
    MSRTCRoute(
        route_id="MSRTC-NSK-PUNE",
        origin_code="NASHIK",
        origin_marathi="नाशिक",
        origin_english="Nashik",
        origin_station="नाशिक मध्यवर्ती बस स्थानक",
        destination_code="PUNE",
        destination_marathi="पुणे",
        destination_english="Pune",
        destination_station="पुणे शिवाजीनगर बस स्थानक",
        distance_km=212,
        base_fare=350,
        avg_duration_minutes=300,
        frequency="Every 30 minutes",
        first_departure="05:00",
        last_departure="22:00",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVNERI"],
        via_stops=["शिर्डी", "संगमनेर", "अहमदनगर"],
    ),
    
    # ========================================
    # MUMBAI ↔ KOLHAPUR
    # ========================================
    MSRTCRoute(
        route_id="MSRTC-MUM-KOP",
        origin_code="MUMBAI",
        origin_marathi="मुंबई",
        origin_english="Mumbai",
        origin_station="मुंबई सेंट्रल बस स्थानक",
        destination_code="KOLHAPUR",
        destination_marathi="कोल्हापूर",
        destination_english="Kolhapur",
        destination_station="कोल्हापूर मध्यवर्ती बस स्थानक",
        distance_km=400,
        base_fare=650,
        avg_duration_minutes=480,  # 8 hours
        frequency="Every hour",
        first_departure="05:00",
        last_departure="23:00",
        bus_types=["ST", "SEMI_LUX", "SHIVSHAHI", "ASHWAMEDH"],
        via_stops=["पुणे", "सातारा", "कराड", "सांगली"],
    ),
    MSRTCRoute(
        route_id="MSRTC-KOP-MUM",
        origin_code="KOLHAPUR",
        origin_marathi="कोल्हापूर",
        origin_english="Kolhapur",
        origin_station="कोल्हापूर मध्यवर्ती बस स्थानक",
        destination_code="MUMBAI",
        destination_marathi="मुंबई",
        destination_english="Mumbai",
        destination_station="मुंबई सेंट्रल बस स्थानक",
        distance_km=400,
        base_fare=650,
        avg_duration_minutes=480,
        frequency="Every hour",
        first_departure="05:00",
        last_departure="23:00",
        bus_types=["ST", "SEMI_LUX", "SHIVSHAHI", "ASHWAMEDH"],
        via_stops=["सांगली", "कराड", "सातारा", "पुणे"],
    ),
    
    # ========================================
    # PUNE ↔ KOLHAPUR
    # ========================================
    MSRTCRoute(
        route_id="MSRTC-PUNE-KOP",
        origin_code="PUNE",
        origin_marathi="पुणे",
        origin_english="Pune",
        origin_station="पुणे स्वारगेट बस स्थानक",
        destination_code="KOLHAPUR",
        destination_marathi="कोल्हापूर",
        destination_english="Kolhapur",
        destination_station="कोल्हापूर मध्यवर्ती बस स्थानक",
        distance_km=250,
        base_fare=420,
        avg_duration_minutes=300,  # 5 hours
        frequency="Every 30 minutes",
        first_departure="05:00",
        last_departure="22:30",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVSHAHI"],
        via_stops=["सातारा", "कराड", "सांगली"],
    ),
    MSRTCRoute(
        route_id="MSRTC-KOP-PUNE",
        origin_code="KOLHAPUR",
        origin_marathi="कोल्हापूर",
        origin_english="Kolhapur",
        origin_station="कोल्हापूर मध्यवर्ती बस स्थानक",
        destination_code="PUNE",
        destination_marathi="पुणे",
        destination_english="Pune",
        destination_station="पुणे स्वारगेट बस स्थानक",
        distance_km=250,
        base_fare=420,
        avg_duration_minutes=300,
        frequency="Every 30 minutes",
        first_departure="05:00",
        last_departure="22:30",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVSHAHI"],
        via_stops=["सांगली", "कराड", "सातारा"],
    ),
    
    # ========================================
    # PUNE ↔ AURANGABAD
    # ========================================
    MSRTCRoute(
        route_id="MSRTC-PUNE-AUR",
        origin_code="PUNE",
        origin_marathi="पुणे",
        origin_english="Pune",
        origin_station="पुणे शिवाजीनगर बस स्थानक",
        destination_code="AURANGABAD",
        destination_marathi="औरंगाबाद",
        destination_english="Aurangabad",
        destination_station="औरंगाबाद मध्यवर्ती बस स्थानक",
        distance_km=235,
        base_fare=380,
        avg_duration_minutes=330,  # 5.5 hours
        frequency="Every 45 minutes",
        first_departure="05:30",
        last_departure="21:00",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVNERI"],
        via_stops=["अहमदनगर"],
    ),
    MSRTCRoute(
        route_id="MSRTC-AUR-PUNE",
        origin_code="AURANGABAD",
        origin_marathi="औरंगाबाद",
        origin_english="Aurangabad",
        origin_station="औरंगाबाद मध्यवर्ती बस स्थानक",
        destination_code="PUNE",
        destination_marathi="पुणे",
        destination_english="Pune",
        destination_station="पुणे शिवाजीनगर बस स्थानक",
        distance_km=235,
        base_fare=380,
        avg_duration_minutes=330,
        frequency="Every 45 minutes",
        first_departure="05:30",
        last_departure="21:00",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVNERI"],
        via_stops=["अहमदनगर"],
    ),
]


# ============================================================
# PHASE 2 ROUTES - District HQ Connections
# ============================================================

MSRTC_PHASE2_ROUTES: List[MSRTCRoute] = [
    # Mumbai ↔ Nagpur
    MSRTCRoute(
        route_id="MSRTC-MUM-NGP",
        origin_code="MUMBAI",
        origin_marathi="मुंबई",
        origin_english="Mumbai",
        origin_station="मुंबई सेंट्रल बस स्थानक",
        destination_code="NAGPUR",
        destination_marathi="नागपूर",
        destination_english="Nagpur",
        destination_station="नागपूर बस स्थानक",
        distance_km=840,
        base_fare=1100,
        avg_duration_minutes=900,  # 15 hours
        frequency="Multiple daily (evening)",
        first_departure="17:00",
        last_departure="21:00",
        bus_types=["SEMI_LUX", "SHIVSHAHI", "ASHWAMEDH"],
        via_stops=["पुणे", "औरंगाबाद", "अकोला"],
    ),
    
    # Pune ↔ Shirdi
    MSRTCRoute(
        route_id="MSRTC-PUNE-SHRD",
        origin_code="PUNE",
        origin_marathi="पुणे",
        origin_english="Pune",
        origin_station="पुणे शिवाजीनगर बस स्थानक",
        destination_code="SHIRDI",
        destination_marathi="शिर्डी",
        destination_english="Shirdi",
        destination_station="शिर्डी बस स्थानक",
        distance_km=185,
        base_fare=300,
        avg_duration_minutes=270,  # 4.5 hours
        frequency="Every hour",
        first_departure="04:30",
        last_departure="20:00",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVNERI"],
        via_stops=["अहमदनगर"],
    ),
    
    # Mumbai ↔ Shirdi
    MSRTCRoute(
        route_id="MSRTC-MUM-SHRD",
        origin_code="MUMBAI",
        origin_marathi="मुंबई",
        origin_english="Mumbai",
        origin_station="दादर (टर्मिनस)",
        destination_code="SHIRDI",
        destination_marathi="शिर्डी",
        destination_english="Shirdi",
        destination_station="शिर्डी बस स्थानक",
        distance_km=250,
        base_fare=450,
        avg_duration_minutes=330,  # 5.5 hours
        frequency="Every 30 minutes",
        first_departure="04:00",
        last_departure="21:00",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVNERI"],
        via_stops=["ठाणे", "नाशिक"],
    ),
    
    # Mumbai ↔ Nashik
    MSRTCRoute(
        route_id="MSRTC-MUM-NSK",
        origin_code="MUMBAI",
        origin_marathi="मुंबई",
        origin_english="Mumbai",
        origin_station="मुंबई सेंट्रल बस स्थानक",
        destination_code="NASHIK",
        destination_marathi="नाशिक",
        destination_english="Nashik",
        destination_station="नाशिक मध्यवर्ती बस स्थानक",
        distance_km=167,
        base_fare=280,
        avg_duration_minutes=240,  # 4 hours
        frequency="Every 20 minutes",
        first_departure="04:30",
        last_departure="23:00",
        bus_types=["ST", "SEMI_LUX", "ASIAD", "SHIVNERI"],
        via_stops=["ठाणे", "कसारा", "इगतपुरी"],
    ),
]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def get_msrtc_route(origin: str, destination: str) -> MSRTCRoute | None:
    """Find MSRTC route by origin and destination.
    
    Searches both Phase 1 and Phase 2 routes.
    Accepts Marathi, English, or code.
    """
    origin_lower = origin.lower().strip()
    dest_lower = destination.lower().strip()
    
    all_routes = MSRTC_PHASE1_ROUTES + MSRTC_PHASE2_ROUTES
    
    for route in all_routes:
        # Check origin match
        origin_match = (
            route.origin_code.lower() == origin_lower or
            route.origin_english.lower() == origin_lower or
            route.origin_marathi == origin
        )
        
        # Check destination match
        dest_match = (
            route.destination_code.lower() == dest_lower or
            route.destination_english.lower() == dest_lower or
            route.destination_marathi == destination
        )
        
        if origin_match and dest_match:
            return route
    
    return None


def get_msrtc_stop(query: str) -> Dict | None:
    """Find MSRTC stop by query (Marathi, English, or normalized)."""
    query_lower = query.lower().strip()
    
    for stop in MSRTC_STOPS:
        if (
            stop["value"].lower() == query_lower or
            stop["name_english"].lower() == query_lower or
            stop["name_normalized"] == query_lower or
            stop["name_marathi"] == query
        ):
            return stop
    
    return None


def calculate_msrtc_fare(base_fare: int, bus_type: str) -> int:
    """Calculate fare for a specific bus type."""
    config = MSRTC_BUS_TYPES.get(bus_type, MSRTC_BUS_TYPES["ST"])
    return int(base_fare * config["fare_multiplier"])


def get_all_msrtc_stops() -> List[Dict]:
    """Get all MSRTC stops."""
    return MSRTC_STOPS.copy()


def get_all_msrtc_routes() -> List[MSRTCRoute]:
    """Get all MSRTC routes (Phase 1 + Phase 2)."""
    return MSRTC_PHASE1_ROUTES + MSRTC_PHASE2_ROUTES
