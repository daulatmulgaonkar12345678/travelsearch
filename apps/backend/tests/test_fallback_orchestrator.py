"""
Unit tests for Universal Fallback Orchestrator
"""

import pytest
from app.services.fallback_orchestrator import FallbackOrchestrator
from app.services.flight_validator import haversine_distance


@pytest.fixture
def airport_data():
    """Sample airport dataset"""
    return {
        # India
        "PNQ": {"iata": "PNQ", "city": "Pune", "country": "IN", "lat": 18.5821, "lon": 73.9197},
        "BOM": {"iata": "BOM", "city": "Mumbai", "country": "IN", "lat": 19.0887, "lon": 72.8678},
        "DEL": {"iata": "DEL", "city": "Delhi", "country": "IN", "lat": 28.5562, "lon": 77.1000},
        "HYD": {"iata": "HYD", "city": "Hyderabad", "country": "IN", "lat": 17.2403, "lon": 78.4294},
        "NMI": {"iata": "NMI", "city": "Navi Mumbai", "country": "IN", "lat": 19.1886, "lon": 73.0206},
        
        # Europe
        "AMS": {"iata": "AMS", "city": "Amsterdam", "country": "NL", "lat": 52.3105, "lon": 4.7683},
        "CDG": {"iata": "CDG", "city": "Paris", "country": "FR", "lat": 49.0097, "lon": 2.5479},
        "LHR": {"iata": "LHR", "city": "London", "country": "GB", "lat": 51.4700, "lon": -0.4543},
        
        # Middle East
        "DXB": {"iata": "DXB", "city": "Dubai", "country": "AE", "lat": 25.2532, "lon": 55.3657},
        
        # Greece
        "AOK": {"iata": "AOK", "city": "Karpathos", "country": "GR", "lat": 35.4214, "lon": 27.1460},
        "ATH": {"iata": "ATH", "city": "Athens", "country": "GR", "lat": 37.9364, "lon": 23.9444},
    }


@pytest.fixture
def orchestrator(airport_data):
    """Fallback orchestrator instance"""
    return FallbackOrchestrator(airport_data)


def test_calculate_route_distance(orchestrator):
    """Test distance calculation between airports"""
    # PNQ to AMS (approximately 6970 km great-circle)
    distance = orchestrator.calculate_route_distance("PNQ", "AMS")
    assert distance is not None
    assert 6900 < distance < 7100, f"Expected ~6970km, got {distance}km"
    
    # BOM to DEL (approximately 1150 km)
    distance = orchestrator.calculate_route_distance("BOM", "DEL")
    assert distance is not None
    assert 1100 < distance < 1200, f"Expected ~1150km, got {distance}km"


def test_requires_stop_long_haul(orchestrator):
    """Test that long-haul routes (>3500km) require stops"""
    # PNQ → AMS (~6300 km)
    assert orchestrator.requires_stop("PNQ", "AMS") is True
    
    # PNQ → CDG (~6500 km)
    assert orchestrator.requires_stop("PNQ", "CDG") is True
    
    # PNQ → DXB (~1900 km)
    assert orchestrator.requires_stop("PNQ", "DXB") is False
    
    # NMI → DXB (~1900 km)
    assert orchestrator.requires_stop("NMI", "DXB") is False


def test_requires_stop_short_haul(orchestrator):
    """Test that short-haul routes (<3500km) don't require stops"""
    # BOM → DEL (~1150 km)
    assert orchestrator.requires_stop("BOM", "DEL") is False
    
    # PNQ → BOM (~120 km)
    assert orchestrator.requires_stop("PNQ", "BOM") is False


def test_get_airport_country(orchestrator):
    """Test country code extraction"""
    assert orchestrator.get_airport_country("PNQ") == "IN"
    assert orchestrator.get_airport_country("BOM") == "IN"
    assert orchestrator.get_airport_country("AMS") == "NL"
    assert orchestrator.get_airport_country("CDG") == "FR"
    assert orchestrator.get_airport_country("DXB") == "AE"
    assert orchestrator.get_airport_country("INVALID") is None


@pytest.mark.asyncio
async def test_build_expanded_origin_list_india(orchestrator, monkeypatch):
    """Test expanded origin list for Indian airport"""
    # Mock get_nearby_airports to return nearby airports
    async def mock_nearby(iata, radius_km, limit):
        if iata == "PNQ":
            return ["NMI", "BOM"]
        return []
    
    monkeypatch.setattr(orchestrator, "get_nearby_airports", mock_nearby)
    
    # Test PNQ expansion (should include PNQ, nearby, and Indian hubs)
    expanded = await orchestrator.build_expanded_origin_list("PNQ", limit_nearby=2, limit_hubs=3)
    
    assert "PNQ" in expanded, "Should include original origin"
    assert "NMI" in expanded or "BOM" in expanded, "Should include nearby airports"
    assert "DEL" in expanded or "HYD" in expanded, "Should include Indian hubs"
    assert len(expanded) >= 3, "Should have at least 3 origins"
    assert expanded[0] == "PNQ", "Original should be first"


@pytest.mark.asyncio
async def test_build_expanded_origin_list_no_duplicates(orchestrator, monkeypatch):
    """Test that expanded list has no duplicates"""
    # Mock get_nearby_airports to return BOM (which is also a hub)
    async def mock_nearby(iata, radius_km, limit):
        if iata == "PNQ":
            return ["BOM"]  # BOM is both nearby and a hub
        return []
    
    monkeypatch.setattr(orchestrator, "get_nearby_airports", mock_nearby)
    
    expanded = await orchestrator.build_expanded_origin_list("PNQ", limit_nearby=2, limit_hubs=3)
    
    # Check no duplicates
    assert len(expanded) == len(set(expanded)), "Should not have duplicate airports"
    assert expanded.count("BOM") == 1, "BOM should appear only once"


@pytest.mark.asyncio
async def test_build_expanded_origin_list_limit_respected(orchestrator, monkeypatch):
    """Test that limits are respected"""
    # Mock get_nearby_airports to return many airports
    async def mock_nearby(iata, radius_km, limit):
        if iata == "PNQ":
            return ["NMI", "BOM", "HYD", "DEL"][:limit]
        return []
    
    monkeypatch.setattr(orchestrator, "get_nearby_airports", mock_nearby)
    
    expanded = await orchestrator.build_expanded_origin_list("PNQ", limit_nearby=2, limit_hubs=2)
    
    # Should be: PNQ + 2 nearby + up to 2 hubs (excluding overlaps)
    assert len(expanded) <= 5, f"Should respect limits, got {len(expanded)}: {expanded}"


def test_log_fallback_activation(orchestrator, caplog):
    """Test fallback activation logging"""
    import logging
    caplog.set_level(logging.INFO)
    
    orchestrator.log_fallback_activation(
        original_origin="PNQ",
        destination="AMS",
        expanded_origins=["PNQ", "BOM", "DEL"],
        route_distance=6300.0,
        requires_stop=True
    )
    
    # Check log contains key information
    assert "ACTIVATED" in caplog.text
    assert "PNQ" in caplog.text
    assert "AMS" in caplog.text
    assert "6300" in caplog.text
    assert "requires_stop: True" in caplog.text.lower()


# Integration test scenarios (test actual routes)

def test_route_pnq_to_ams_distance(airport_data):
    """Test PNQ → AMS route distance"""
    pnq = airport_data["PNQ"]
    ams = airport_data["AMS"]
    
    distance = haversine_distance(
        pnq['lat'], pnq['lon'],
        ams['lat'], ams['lon']
    )
    
    # PNQ to AMS is approximately 6300 km
    assert 6200 < distance < 6500, f"PNQ→AMS distance should be ~6300km, got {distance}km"


def test_route_pnq_to_cdg_distance(airport_data):
    """Test PNQ → CDG route distance"""
    pnq = airport_data["PNQ"]
    cdg = airport_data["CDG"]
    
    distance = haversine_distance(
        pnq['lat'], pnq['lon'],
        cdg['lat'], cdg['lon']
    )
    
    # PNQ to CDG is approximately 6500 km
    assert 6400 < distance < 6700, f"PNQ→CDG distance should be ~6500km, got {distance}km"


def test_route_pnq_to_dxb_distance(airport_data):
    """Test PNQ → DXB route distance"""
    pnq = airport_data["PNQ"]
    dxb = airport_data["DXB"]
    
    distance = haversine_distance(
        pnq['lat'], pnq['lon'],
        dxb['lat'], dxb['lon']
    )
    
    # PNQ to DXB is approximately 1900 km
    assert 1800 < distance < 2000, f"PNQ→DXB distance should be ~1900km, got {distance}km"


def test_route_bom_to_del_distance(airport_data):
    """Test BOM → DEL route distance (control case)"""
    bom = airport_data["BOM"]
    del_airport = airport_data["DEL"]
    
    distance = haversine_distance(
        bom['lat'], bom['lon'],
        del_airport['lat'], del_airport['lon']
    )
    
    # BOM to DEL is approximately 1150 km
    assert 1100 < distance < 1200, f"BOM→DEL distance should be ~1150km, got {distance}km"


def test_route_hyd_to_aok_requires_hub(orchestrator):
    """Test HYD → AOK (Karpathos) - likely needs hub connection"""
    # This route should require a stop (via major hub like ATH or DEL/BOM)
    distance = orchestrator.calculate_route_distance("HYD", "AOK")
    
    # HYD to AOK is approximately 4500-5000 km
    assert distance is not None
    assert distance > 3500, f"HYD→AOK should be long-haul (>3500km), got {distance}km"
    assert orchestrator.requires_stop("HYD", "AOK") is True


def test_route_nmi_to_dxb(orchestrator):
    """Test NMI → DXB route"""
    distance = orchestrator.calculate_route_distance("NMI", "DXB")
    
    # NMI to DXB is approximately 1900 km (similar to BOM-DXB)
    assert distance is not None
    assert 1800 < distance < 2100, f"NMI→DXB should be ~1900km, got {distance}km"
    assert orchestrator.requires_stop("NMI", "DXB") is False, "NMI→DXB is short enough for direct"
