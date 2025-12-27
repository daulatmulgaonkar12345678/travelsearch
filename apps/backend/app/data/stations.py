"""Railway Station and Bus Stop Data

Official station codes and mappings for Indian Railways and major bus stops.
Data sourced from Indian Railways public timetable.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class RailwayStation:
    """Railway station information"""
    code: str  # Station code (e.g., NDLS)
    name: str  # Full name
    city: str  # City name
    state: str
    zone: str  # Railway zone (NR, CR, WR, etc.)
    is_major: bool = False


@dataclass
class BusStop:
    """Bus stop/terminal information"""
    code: str
    name: str
    city: str
    state: str
    stop_type: str = "terminal"  # terminal, depot, stop


# ========================================
# MAJOR RAILWAY STATIONS
# ========================================
RAILWAY_STATIONS: Dict[str, RailwayStation] = {
    # Delhi NCR
    "NDLS": RailwayStation("NDLS", "New Delhi", "Delhi", "Delhi", "NR", True),
    "DEE": RailwayStation("DEE", "Delhi Sarai Rohilla", "Delhi", "Delhi", "NR", True),
    "DLI": RailwayStation("DLI", "Old Delhi", "Delhi", "Delhi", "NR", True),
    "HNZM": RailwayStation("HNZM", "Hazrat Nizamuddin", "Delhi", "Delhi", "NR", True),
    "ANVT": RailwayStation("ANVT", "Anand Vihar Terminal", "Delhi", "Delhi", "NR", True),
    
    # Mumbai
    "CSMT": RailwayStation("CSMT", "Chhatrapati Shivaji Maharaj Terminus", "Mumbai", "Maharashtra", "CR", True),
    "BCT": RailwayStation("BCT", "Mumbai Central", "Mumbai", "Maharashtra", "WR", True),
    "LTT": RailwayStation("LTT", "Lokmanya Tilak Terminus", "Mumbai", "Maharashtra", "CR", True),
    "BDTS": RailwayStation("BDTS", "Bandra Terminus", "Mumbai", "Maharashtra", "WR", True),
    
    # Bangalore
    "SBC": RailwayStation("SBC", "Bangalore City Junction", "Bangalore", "Karnataka", "SWR", True),
    "BAND": RailwayStation("BAND", "Bangalore Cantonment", "Bangalore", "Karnataka", "SWR"),
    "YPR": RailwayStation("YPR", "Yesvantpur Junction", "Bangalore", "Karnataka", "SWR", True),
    "KJM": RailwayStation("KJM", "Krishnarajapuram", "Bangalore", "Karnataka", "SWR"),
    
    # Chennai
    "MAS": RailwayStation("MAS", "Chennai Central", "Chennai", "Tamil Nadu", "SR", True),
    "MS": RailwayStation("MS", "Chennai Egmore", "Chennai", "Tamil Nadu", "SR", True),
    
    # Kolkata
    "HWH": RailwayStation("HWH", "Howrah Junction", "Kolkata", "West Bengal", "ER", True),
    "SDAH": RailwayStation("SDAH", "Sealdah", "Kolkata", "West Bengal", "ER", True),
    "KOAA": RailwayStation("KOAA", "Kolkata", "Kolkata", "West Bengal", "ER", True),
    
    # Hyderabad
    "SC": RailwayStation("SC", "Secunderabad Junction", "Hyderabad", "Telangana", "SCR", True),
    "HYB": RailwayStation("HYB", "Hyderabad Deccan", "Hyderabad", "Telangana", "SCR", True),
    
    # Ahmedabad
    "ADI": RailwayStation("ADI", "Ahmedabad Junction", "Ahmedabad", "Gujarat", "WR", True),
    
    # Pune
    "PUNE": RailwayStation("PUNE", "Pune Junction", "Pune", "Maharashtra", "CR", True),
    
    # Jaipur
    "JP": RailwayStation("JP", "Jaipur Junction", "Jaipur", "Rajasthan", "NWR", True),
    
    # Lucknow
    "LKO": RailwayStation("LKO", "Lucknow Charbagh", "Lucknow", "Uttar Pradesh", "NR", True),
    "LJN": RailwayStation("LJN", "Lucknow Junction", "Lucknow", "Uttar Pradesh", "NER", True),
    
    # Varanasi
    "BSB": RailwayStation("BSB", "Varanasi Junction", "Varanasi", "Uttar Pradesh", "NER", True),
    
    # Goa
    "MAO": RailwayStation("MAO", "Madgaon Junction", "Goa", "Goa", "SWR", True),
    "THVM": RailwayStation("THVM", "Thivim", "Goa", "Goa", "SWR"),
    "VSG": RailwayStation("VSG", "Vasco Da Gama", "Goa", "Goa", "SWR"),
    
    # Kerala
    "ERS": RailwayStation("ERS", "Ernakulam Junction", "Kochi", "Kerala", "SR", True),
    "TVC": RailwayStation("TVC", "Thiruvananthapuram Central", "Trivandrum", "Kerala", "SR", True),
    "CLT": RailwayStation("CLT", "Kozhikode", "Calicut", "Kerala", "SR", True),
    
    # Chandigarh
    "CDG": RailwayStation("CDG", "Chandigarh Junction", "Chandigarh", "Chandigarh", "NR", True),
    
    # Patna
    "PNBE": RailwayStation("PNBE", "Patna Junction", "Patna", "Bihar", "ECR", True),
    
    # Bhopal
    "BPL": RailwayStation("BPL", "Bhopal Junction", "Bhopal", "Madhya Pradesh", "WCR", True),
    
    # Nagpur
    "NGP": RailwayStation("NGP", "Nagpur Junction", "Nagpur", "Maharashtra", "CR", True),
    
    # Indore
    "INDB": RailwayStation("INDB", "Indore Junction", "Indore", "Madhya Pradesh", "WR", True),
    
    # Agra
    "AGC": RailwayStation("AGC", "Agra Cantt", "Agra", "Uttar Pradesh", "NCR", True),
    
    # Amritsar
    "ASR": RailwayStation("ASR", "Amritsar Junction", "Amritsar", "Punjab", "NR", True),
    
    # Coimbatore
    "CBE": RailwayStation("CBE", "Coimbatore Junction", "Coimbatore", "Tamil Nadu", "SR", True),
    
    # Mysore
    "MYS": RailwayStation("MYS", "Mysore Junction", "Mysore", "Karnataka", "SWR", True),
    
    # Visakhapatnam
    "VSKP": RailwayStation("VSKP", "Visakhapatnam Junction", "Visakhapatnam", "Andhra Pradesh", "ECoR", True),
}


# City to station code mapping (primary station)
CITY_TO_RAIL_STATION: Dict[str, str] = {
    "delhi": "NDLS",
    "new delhi": "NDLS",
    "mumbai": "CSMT",
    "bombay": "CSMT",
    "bangalore": "SBC",
    "bengaluru": "SBC",
    "chennai": "MAS",
    "madras": "MAS",
    "kolkata": "HWH",
    "calcutta": "HWH",
    "hyderabad": "SC",
    "ahmedabad": "ADI",
    "pune": "PUNE",
    "jaipur": "JP",
    "lucknow": "LKO",
    "varanasi": "BSB",
    "goa": "MAO",
    "kochi": "ERS",
    "cochin": "ERS",
    "trivandrum": "TVC",
    "thiruvananthapuram": "TVC",
    "chandigarh": "CDG",
    "patna": "PNBE",
    "bhopal": "BPL",
    "nagpur": "NGP",
    "indore": "INDB",
    "agra": "AGC",
    "amritsar": "ASR",
    "coimbatore": "CBE",
    "mysore": "MYS",
    "mysuru": "MYS",
    "visakhapatnam": "VSKP",
    "vizag": "VSKP",
}


# ========================================
# BUS STOPS / TERMINALS
# ========================================
BUS_STOPS: Dict[str, BusStop] = {
    # Delhi
    "DEL_ISBT_KSM": BusStop("DEL_ISBT_KSM", "ISBT Kashmere Gate", "Delhi", "Delhi", "terminal"),
    "DEL_ISBT_ANV": BusStop("DEL_ISBT_ANV", "ISBT Anand Vihar", "Delhi", "Delhi", "terminal"),
    "DEL_ISBT_SRP": BusStop("DEL_ISBT_SRP", "ISBT Sarai Kale Khan", "Delhi", "Delhi", "terminal"),
    
    # Mumbai
    "MUM_BORIVALI": BusStop("MUM_BORIVALI", "Borivali Bus Depot", "Mumbai", "Maharashtra", "depot"),
    "MUM_DADAR": BusStop("MUM_DADAR", "Dadar Bus Depot", "Mumbai", "Maharashtra", "depot"),
    "MUM_KURLA": BusStop("MUM_KURLA", "Kurla Bus Depot", "Mumbai", "Maharashtra", "depot"),
    
    # Bangalore
    "BLR_KEMPEGOWDA": BusStop("BLR_KEMPEGOWDA", "Kempegowda Bus Station (Majestic)", "Bangalore", "Karnataka", "terminal"),
    "BLR_SHANTINAGAR": BusStop("BLR_SHANTINAGAR", "Shantinagar Bus Station", "Bangalore", "Karnataka", "terminal"),
    
    # Chennai
    "CHE_CMBT": BusStop("CHE_CMBT", "Chennai Mofussil Bus Terminus (CMBT)", "Chennai", "Tamil Nadu", "terminal"),
    "CHE_KOYAMBEDU": BusStop("CHE_KOYAMBEDU", "Koyambedu Bus Stand", "Chennai", "Tamil Nadu", "terminal"),
    
    # Hyderabad
    "HYD_MGBS": BusStop("HYD_MGBS", "MGBS (Mahatma Gandhi Bus Station)", "Hyderabad", "Telangana", "terminal"),
    "HYD_JBS": BusStop("HYD_JBS", "JBS (Jubilee Bus Station)", "Hyderabad", "Telangana", "terminal"),
    
    # Pune
    "PUN_SHIVAJI": BusStop("PUN_SHIVAJI", "Shivajinagar Bus Stand", "Pune", "Maharashtra", "terminal"),
    "PUN_SWARGATE": BusStop("PUN_SWARGATE", "Swargate Bus Stand", "Pune", "Maharashtra", "terminal"),
    
    # Ahmedabad
    "AMD_CENTRAL": BusStop("AMD_CENTRAL", "Ahmedabad Central Bus Station", "Ahmedabad", "Gujarat", "terminal"),
    
    # Jaipur
    "JAI_SINDHI": BusStop("JAI_SINDHI", "Sindhi Camp Bus Stand", "Jaipur", "Rajasthan", "terminal"),
}


# City to bus stop mapping (primary terminal)
CITY_TO_BUS_STOP: Dict[str, str] = {
    "delhi": "DEL_ISBT_KSM",
    "new delhi": "DEL_ISBT_KSM",
    "mumbai": "MUM_DADAR",
    "bombay": "MUM_DADAR",
    "bangalore": "BLR_KEMPEGOWDA",
    "bengaluru": "BLR_KEMPEGOWDA",
    "chennai": "CHE_CMBT",
    "hyderabad": "HYD_MGBS",
    "pune": "PUN_SWARGATE",
    "ahmedabad": "AMD_CENTRAL",
    "jaipur": "JAI_SINDHI",
}


# ========================================
# HELPER FUNCTIONS
# ========================================

def get_railway_station(query: str) -> Optional[RailwayStation]:
    """Find railway station by code or city name"""
    query_upper = query.upper().strip()
    query_lower = query.lower().strip()
    
    # Try direct code match first
    if query_upper in RAILWAY_STATIONS:
        return RAILWAY_STATIONS[query_upper]
    
    # Try city name match
    if query_lower in CITY_TO_RAIL_STATION:
        code = CITY_TO_RAIL_STATION[query_lower]
        return RAILWAY_STATIONS.get(code)
    
    # Fuzzy match on station names
    for code, station in RAILWAY_STATIONS.items():
        if query_lower in station.name.lower() or query_lower in station.city.lower():
            return station
    
    return None


def get_bus_stop(query: str) -> Optional[BusStop]:
    """Find bus stop by code or city name"""
    query_upper = query.upper().strip()
    query_lower = query.lower().strip()
    
    # Try direct code match
    if query_upper in BUS_STOPS:
        return BUS_STOPS[query_upper]
    
    # Try city name match
    if query_lower in CITY_TO_BUS_STOP:
        code = CITY_TO_BUS_STOP[query_lower]
        return BUS_STOPS.get(code)
    
    # Fuzzy match
    for code, stop in BUS_STOPS.items():
        if query_lower in stop.name.lower() or query_lower in stop.city.lower():
            return stop
    
    return None


def get_all_railway_stations() -> List[Dict]:
    """Get all stations for autocomplete"""
    return [
        {
            "code": s.code,
            "name": s.name,
            "city": s.city,
            "state": s.state,
            "display": f"{s.name} ({s.code}) - {s.city}"
        }
        for s in RAILWAY_STATIONS.values()
    ]


def get_all_bus_stops() -> List[Dict]:
    """Get all bus stops for autocomplete"""
    return [
        {
            "code": s.code,
            "name": s.name,
            "city": s.city,
            "state": s.state,
            "display": f"{s.name} - {s.city}"
        }
        for s in BUS_STOPS.values()
    ]
