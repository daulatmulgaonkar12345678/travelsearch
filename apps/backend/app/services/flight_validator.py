"""
Flight Data Validation Module

Implements universal duration and data quality checks for all flight itineraries.
Drops invalid itineraries before returning results to ensure data quality.
"""

import math
import logging
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from app.models.flight import FlightOffer, FlightSegment

logger = logging.getLogger(__name__)

# Metrics counter (in-memory for now, can be replaced with Prometheus/StatsD)
validation_metrics = {
    "total_itineraries": 0,
    "dropped_invalid_duration": 0,
    "dropped_negative_duration": 0,
    "dropped_too_fast": 0,
    "dropped_too_slow": 0,
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points using Haversine formula.
    Returns distance in kilometers.
    
    Args:
        lat1, lon1: Origin coordinates in decimal degrees
        lat2, lon2: Destination coordinates in decimal degrees
    
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers
    r = 6371
    
    return r * c


def get_airport_coordinates(iata: str, airport_data: Dict) -> Optional[Tuple[float, float]]:
    """
    Get airport coordinates from the airport dataset.
    
    Args:
        iata: Airport IATA code
        airport_data: Dictionary mapping IATA codes to airport data
    
    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    if iata not in airport_data:
        return None
    
    airport = airport_data[iata]
    lat = airport.get('lat')
    lon = airport.get('lon')
    
    if lat is None or lon is None:
        return None
    
    return (float(lat), float(lon))


def compute_segment_duration_minutes(segment: FlightSegment) -> Optional[int]:
    """
    Compute actual segment duration from timestamps.
    
    Args:
        segment: Flight segment with departure_time and arrival_time
    
    Returns:
        Duration in minutes, or None if timestamps are invalid
    """
    try:
        departure = segment.departure_time
        arrival = segment.arrival_time
        
        # Ensure we have datetime objects
        if isinstance(departure, str):
            departure = datetime.fromisoformat(departure.replace('Z', '+00:00'))
        if isinstance(arrival, str):
            arrival = datetime.fromisoformat(arrival.replace('Z', '+00:00'))
        
        # Compute duration
        duration = arrival - departure
        minutes = int(duration.total_seconds() / 60)
        
        return minutes
    except Exception as e:
        logger.warning(f"Failed to compute segment duration: {e}")
        return None


def validate_segment_duration(
    segment: FlightSegment,
    airport_data: Dict,
    provider: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate a single flight segment's duration against distance and sanity checks.
    
    Args:
        segment: Flight segment to validate
        airport_data: Airport dataset with coordinates
        provider: Provider name for logging
    
    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    # Step 1: Recompute duration from timestamps
    computed_minutes = compute_segment_duration_minutes(segment)
    
    if computed_minutes is None:
        return False, "invalid_timestamps"
    
    if computed_minutes <= 0:
        validation_metrics["dropped_negative_duration"] += 1
        logger.warning(
            f"[VALIDATION] Negative duration: {segment.departure_airport} → {segment.arrival_airport}, "
            f"provider={provider}, computed_minutes={computed_minutes}"
        )
        return False, "negative_duration"
    
    # Step 2: Get coordinates and compute distance
    origin_coords = get_airport_coordinates(segment.departure_airport, airport_data)
    dest_coords = get_airport_coordinates(segment.arrival_airport, airport_data)
    
    if not origin_coords or not dest_coords:
        # If we don't have coordinates, we can't validate distance
        # But we can still check if duration is reasonable (at least > 30 min for any flight)
        if computed_minutes < 30:
            validation_metrics["dropped_too_fast"] += 1
            logger.warning(
                f"[VALIDATION] Duration too short (no coords): {segment.departure_airport} → {segment.arrival_airport}, "
                f"provider={provider}, computed_minutes={computed_minutes}"
            )
            return False, "duration_too_short"
        # Accept if duration is reasonable even without distance check
        return True, None
    
    distance_km = haversine_distance(
        origin_coords[0], origin_coords[1],
        dest_coords[0], dest_coords[1]
    )
    
    # Step 3: Compute allowed min/max duration
    # minAllowed = max(30, distance_km * 0.004 * 60)
    # This assumes minimum average speed of ~250 km/h, with floor of 30 min
    min_allowed = max(30, distance_km * 0.004 * 60)
    
    # maxAllowed = (distance_km / 150) * 60 + 240
    # Very generous: slow flight (150 km/h) + 4 hours buffer for connections/delays
    max_allowed = (distance_km / 150) * 60 + 240
    
    # Step 4: Validate
    if computed_minutes < min_allowed:
        validation_metrics["dropped_too_fast"] += 1
        logger.warning(
            f"[VALIDATION] Duration too fast: {segment.departure_airport} → {segment.arrival_airport}, "
            f"provider={provider}, distance_km={distance_km:.1f}, "
            f"computed_minutes={computed_minutes}, min_allowed={min_allowed:.1f}, "
            f"provider_duration={segment.duration_minutes}"
        )
        return False, "duration_too_fast"
    
    if computed_minutes > max_allowed:
        validation_metrics["dropped_too_slow"] += 1
        logger.warning(
            f"[VALIDATION] Duration too slow: {segment.departure_airport} → {segment.arrival_airport}, "
            f"provider={provider}, distance_km={distance_km:.1f}, "
            f"computed_minutes={computed_minutes}, max_allowed={max_allowed:.1f}, "
            f"provider_duration={segment.duration_minutes}"
        )
        return False, "duration_too_slow"
    
    return True, None


def validate_and_fix_itinerary(
    offer: FlightOffer,
    airport_data: Dict
) -> Tuple[bool, FlightOffer]:
    """
    Validate and fix a complete flight itinerary.
    
    - Validates all segments
    - Recomputes total duration from segments
    - Returns (is_valid, updated_offer)
    
    Args:
        offer: Flight offer to validate
        airport_data: Airport dataset with coordinates
    
    Returns:
        Tuple of (is_valid, updated_offer_with_corrected_duration)
    """
    validation_metrics["total_itineraries"] += 1
    
    # Validate each segment
    total_duration = 0
    for segment in offer.segments:
        is_valid, reason = validate_segment_duration(segment, airport_data, offer.provider)
        
        if not is_valid:
            validation_metrics["dropped_invalid_duration"] += 1
            logger.info(
                f"[VALIDATION] Dropping itinerary: offer_id={offer.offer_id}, "
                f"provider={offer.provider}, reason={reason}"
            )
            return False, offer
        
        # Recompute segment duration
        computed_minutes = compute_segment_duration_minutes(segment)
        if computed_minutes:
            segment.duration_minutes = computed_minutes
            total_duration += computed_minutes
    
    # Update total duration with recomputed value
    offer.total_duration_minutes = total_duration
    
    return True, offer


def validate_flight_offers(
    offers: List[FlightOffer],
    airport_data: Dict
) -> List[FlightOffer]:
    """
    Validate and filter a list of flight offers.
    Drops invalid itineraries and returns only valid ones with corrected durations.
    
    Args:
        offers: List of flight offers to validate
        airport_data: Airport dataset with coordinates
    
    Returns:
        List of valid flight offers with recomputed durations
    """
    valid_offers = []
    
    for offer in offers:
        is_valid, updated_offer = validate_and_fix_itinerary(offer, airport_data)
        if is_valid:
            valid_offers.append(updated_offer)
    
    if len(offers) > len(valid_offers):
        dropped_count = len(offers) - len(valid_offers)
        logger.info(
            f"[VALIDATION] Filtered {dropped_count} invalid itineraries out of {len(offers)}. "
            f"Returning {len(valid_offers)} valid offers."
        )
    
    return valid_offers


def get_validation_metrics() -> Dict:
    """
    Get current validation metrics.
    
    Returns:
        Dictionary of validation metrics
    """
    return validation_metrics.copy()


def reset_validation_metrics():
    """Reset validation metrics (useful for testing)."""
    global validation_metrics
    validation_metrics = {
        "total_itineraries": 0,
        "dropped_invalid_duration": 0,
        "dropped_negative_duration": 0,
        "dropped_too_fast": 0,
        "dropped_too_slow": 0,
    }
