"""Shared transport models for Trains and Buses

Base models that trains and buses extend.
Follows same patterns as flight.py for UI consistency.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class TransportMode(str, Enum):
    """Transport mode types"""
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"


class BaseTransportOffer(BaseModel):
    """Base offer model shared across all transport types"""
    offer_id: str
    mode: TransportMode
    provider: str  # Data source identifier
    
    # Route info
    from_station: str  # Station/Stop code
    from_city: str
    from_station_name: str
    to_station: str
    to_city: str
    to_station_name: str
    
    # Timing
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    
    # Pricing - ALWAYS average/estimated, never live
    avg_price: float
    currency: str = "INR"
    price_label: str = "Average Fare"  # Always display this
    price_disclaimer: str = "Average fare shown for reference. Actual price may vary on booking site."
    
    # Distance
    distance_km: Optional[float] = None
    
    # Redirect booking (no direct booking)
    booking_partners: List[dict] = Field(default_factory=list)  # [{name, url, priority}]
    
    # Status
    is_fallback: bool = False  # True if route data not available, showing redirect only
    

class TrainClass(str, Enum):
    """Indian Railways coach classes"""
    SL = "SL"  # Sleeper
    _3A = "3A"  # AC 3-Tier
    _2A = "2A"  # AC 2-Tier
    _1A = "1A"  # AC First Class
    CC = "CC"  # AC Chair Car
    EC = "EC"  # Executive Chair Car
    _2S = "2S"  # Second Sitting
    GN = "GN"  # General


class TrainOffer(BaseTransportOffer):
    """Train offer with Indian Railways specific fields"""
    mode: TransportMode = TransportMode.TRAIN
    
    # Train info
    train_number: str
    train_name: str
    train_type: Optional[str] = None  # Rajdhani, Shatabdi, Duronto, etc.
    
    # Schedule
    days_of_operation: List[str] = Field(default_factory=list)  # ["Mon", "Wed", "Fri"]
    frequency: Optional[str] = None  # "Daily", "Tri-weekly", etc.
    
    # Stops (intermediate)
    stops_count: int = 0
    intermediate_stops: List[str] = Field(default_factory=list)  # Station codes
    
    # Classes available with average fares
    available_classes: List[dict] = Field(default_factory=list)  # [{class: "SL", avg_fare: 450}]
    
    # Pantry/Food
    has_pantry: bool = False
    

class BusType(str, Enum):
    """Bus types"""
    ORDINARY = "ordinary"
    SEMI_DELUXE = "semi_deluxe"
    DELUXE = "deluxe"
    AC_SEATER = "ac_seater"
    AC_SLEEPER = "ac_sleeper"
    NON_AC_SLEEPER = "non_ac_sleeper"
    VOLVO = "volvo"
    MULTI_AXLE = "multi_axle"


class BusOffer(BaseTransportOffer):
    """Bus offer with RTC/private bus specific fields"""
    mode: TransportMode = TransportMode.BUS
    
    # Operator info
    operator_name: str  # KSRTC, MSRTC, redBus partner, etc.
    operator_type: Literal["government", "private"] = "government"
    
    # Bus type
    bus_type: BusType = BusType.ORDINARY
    bus_type_label: str = "Ordinary"  # Human readable
    
    # Amenities
    is_ac: bool = False
    is_sleeper: bool = False
    has_charging_point: bool = False
    has_wifi: bool = False
    
    # Schedule
    frequency: Optional[str] = None  # "Every 30 mins", "4 services daily"
    departure_window: Optional[str] = None  # "06:00 - 22:00" if exact time unknown
    
    # Stops
    stops_count: int = 0
    intermediate_stops: List[str] = Field(default_factory=list)


# ========================================
# SEARCH REQUEST/RESPONSE MODELS
# ========================================

class TrainSearchRequest(BaseModel):
    """Train search parameters"""
    origin: str  # Station code or city name
    destination: str
    departure_date: str  # YYYY-MM-DD
    
    # Optional filters
    train_class: Optional[str] = None  # SL, 3A, 2A, etc.
    train_type: Optional[str] = None  # Rajdhani, Shatabdi
    
    passengers: int = 1


class TrainSearchResponse(BaseModel):
    """Train search response"""
    offers: List[TrainOffer]
    search_id: str
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Route metadata
    origin_city: str
    destination_city: str
    distance_km: Optional[float] = None
    
    # Fallback info
    is_fallback: bool = False
    fallback_message: Optional[str] = None


class BusSearchRequest(BaseModel):
    """Bus search parameters"""
    origin: str  # City or bus stop
    destination: str
    departure_date: str  # YYYY-MM-DD
    
    # Optional filters
    bus_type: Optional[str] = None
    ac_only: bool = False
    sleeper_only: bool = False
    
    passengers: int = 1


class BusSearchResponse(BaseModel):
    """Bus search response"""
    offers: List[BusOffer]
    search_id: str
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Route metadata
    origin_city: str
    destination_city: str
    distance_km: Optional[float] = None
    
    # Fallback info
    is_fallback: bool = False
    fallback_message: Optional[str] = None
