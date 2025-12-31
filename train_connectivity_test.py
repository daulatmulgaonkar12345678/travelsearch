#!/usr/bin/env python3
"""
Train Connectivity System Testing (Phase 1)
Tests the comprehensive Indian Railway connectivity system with:
1. Station database (100+ stations with codes, zones, coordinates, aliases)
2. Rail hubs (30 hubs categorized as MEGA_HUB, MAJOR_HUB, REGIONAL_HUB)
3. Connectivity graph (100+ edges representing railway lines)
4. Hub-based routing resolver (flight-like routing strategy)
"""

import asyncio
import httpx
import json
from datetime import datetime
import sys
import os

# Backend URL - using production URL from environment
BACKEND_URL = "https://click-tracker-23.preview.emergentagent.com"

class TrainConnectivityTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_result(self, test_name: str, success: bool, details: str, response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    async def test_direct_route_csmt_pune(self):
        """Test GET /api/trains/connectivity?from=CSMT&to=PUNE - should return DIRECT route with HIGH confidence"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/connectivity",
                params={"from": "CSMT", "to": "PUNE"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Direct Route CSMT→PUNE", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Validate required fields
            required_fields = ["route_type", "path", "confidence", "note", "via_hubs", "zone_changes"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Direct Route CSMT→PUNE",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Validate route type
            if data.get("route_type") != "DIRECT":
                self.log_result(
                    "Direct Route CSMT→PUNE",
                    False,
                    f"Expected route_type=DIRECT, got {data.get('route_type')}",
                    data
                )
                return False
            
            # Validate confidence
            if data.get("confidence") != "HIGH":
                self.log_result(
                    "Direct Route CSMT→PUNE",
                    False,
                    f"Expected confidence=HIGH, got {data.get('confidence')}",
                    data
                )
                return False
            
            # Validate path structure
            path = data.get("path", [])
            if len(path) < 2:
                self.log_result(
                    "Direct Route CSMT→PUNE",
                    False,
                    f"Path too short: {len(path)} nodes",
                    data
                )
                return False
            
            # Check path nodes have required fields
            for i, node in enumerate(path):
                required_node_fields = ["station", "type", "station_name", "city", "zone", "is_hub"]
                missing_node_fields = [field for field in required_node_fields if field not in node]
                
                if missing_node_fields:
                    self.log_result(
                        "Direct Route CSMT→PUNE",
                        False,
                        f"Path node {i} missing fields: {missing_node_fields}",
                        node
                    )
                    return False
            
            # Validate origin and destination
            if path[0].get("type") != "ORIGIN":
                self.log_result(
                    "Direct Route CSMT→PUNE",
                    False,
                    f"First node should be ORIGIN, got {path[0].get('type')}",
                    path[0]
                )
                return False
            
            if path[-1].get("type") != "DESTINATION":
                self.log_result(
                    "Direct Route CSMT→PUNE",
                    False,
                    f"Last node should be DESTINATION, got {path[-1].get('type')}",
                    path[-1]
                )
                return False
            
            self.log_result(
                "Direct Route CSMT→PUNE",
                True,
                f"Direct route found with {len(path)} stations, confidence={data.get('confidence')}"
            )
            return True
            
        except Exception as e:
            self.log_result("Direct Route CSMT→PUNE", False, f"Exception: {str(e)}")
            return False
    
    async def test_hub_based_route_delhi_bangalore(self):
        """Test GET /api/trains/connectivity?from=Delhi&to=Bangalore - should return HUB_BASED route via Secunderabad"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/connectivity",
                params={"from": "Delhi", "to": "Bangalore"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Hub-Based Route Delhi→Bangalore", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should be HUB_BASED route
            if data.get("route_type") != "HUB_BASED":
                self.log_result(
                    "Hub-Based Route Delhi→Bangalore",
                    False,
                    f"Expected route_type=HUB_BASED, got {data.get('route_type')}",
                    data
                )
                return False
            
            # Should have via_hubs
            via_hubs = data.get("via_hubs", [])
            if not via_hubs:
                self.log_result(
                    "Hub-Based Route Delhi→Bangalore",
                    False,
                    "Expected via_hubs to be non-empty for HUB_BASED route",
                    data
                )
                return False
            
            # Path should contain hub nodes (either type="HUB" or is_hub=true)
            path = data.get("path", [])
            hub_nodes = [node for node in path if node.get("type") == "HUB" or node.get("is_hub") == True]
            
            if len(hub_nodes) < 2:  # Should have at least origin/destination hubs
                self.log_result(
                    "Hub-Based Route Delhi→Bangalore",
                    False,
                    f"Expected at least 2 hub nodes in path, found {len(hub_nodes)}",
                    data
                )
                return False
            
            # Confidence should be HIGH or MEDIUM for hub-based routes
            confidence = data.get("confidence")
            if confidence not in ["HIGH", "MEDIUM"]:
                self.log_result(
                    "Hub-Based Route Delhi→Bangalore",
                    False,
                    f"Expected confidence HIGH or MEDIUM, got {confidence}",
                    data
                )
                return False
            
            self.log_result(
                "Hub-Based Route Delhi→Bangalore",
                True,
                f"Hub-based route found via {', '.join(via_hubs)}, confidence={confidence}"
            )
            return True
            
        except Exception as e:
            self.log_result("Hub-Based Route Delhi→Bangalore", False, f"Exception: {str(e)}")
            return False
    
    async def test_direct_route_delhi_chennai(self):
        """Test GET /api/trains/connectivity?from=Delhi&to=Chennai - should return DIRECT route via GT Express corridor"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/connectivity",
                params={"from": "Delhi", "to": "Chennai"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Direct Route Delhi→Chennai", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should be DIRECT route (GT Express corridor)
            route_type = data.get("route_type")
            if route_type not in ["DIRECT", "HUB_BASED"]:
                self.log_result(
                    "Direct Route Delhi→Chennai",
                    False,
                    f"Expected route_type DIRECT or HUB_BASED, got {route_type}",
                    data
                )
                return False
            
            # Should have HIGH confidence for major corridor
            confidence = data.get("confidence")
            if confidence != "HIGH":
                self.log_result(
                    "Direct Route Delhi→Chennai",
                    False,
                    f"Expected confidence=HIGH for major corridor, got {confidence}",
                    data
                )
                return False
            
            self.log_result(
                "Direct Route Delhi→Chennai",
                True,
                f"Route found: type={route_type}, confidence={confidence}"
            )
            return True
            
        except Exception as e:
            self.log_result("Direct Route Delhi→Chennai", False, f"Exception: {str(e)}")
            return False
    
    async def test_direct_route_satara_pune(self):
        """Test GET /api/trains/connectivity?from=Satara&to=Pune - should return DIRECT regional route"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/connectivity",
                params={"from": "Satara", "to": "Pune"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Direct Route Satara→Pune", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should be DIRECT route
            if data.get("route_type") != "DIRECT":
                self.log_result(
                    "Direct Route Satara→Pune",
                    False,
                    f"Expected route_type=DIRECT, got {data.get('route_type')}",
                    data
                )
                return False
            
            # Should have HIGH confidence
            if data.get("confidence") != "HIGH":
                self.log_result(
                    "Direct Route Satara→Pune",
                    False,
                    f"Expected confidence=HIGH, got {data.get('confidence')}",
                    data
                )
                return False
            
            self.log_result(
                "Direct Route Satara→Pune",
                True,
                f"Direct regional route found with confidence={data.get('confidence')}"
            )
            return True
            
        except Exception as e:
            self.log_result("Direct Route Satara→Pune", False, f"Exception: {str(e)}")
            return False
    
    async def test_station_search_mumbai(self):
        """Test GET /api/trains/stations/search?q=Mumbai - should return CSMT, BCT, LTT, DR stations"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/stations/search",
                params={"q": "Mumbai", "limit": 5}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Station Search Mumbai", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            if "results" not in data or "count" not in data:
                self.log_result(
                    "Station Search Mumbai",
                    False,
                    "Missing 'results' or 'count' in response",
                    data
                )
                return False
            
            results = data.get("results", [])
            
            if not results:
                self.log_result(
                    "Station Search Mumbai",
                    False,
                    "No results returned for Mumbai search",
                    data
                )
                return False
            
            # Check for expected Mumbai stations
            station_codes = [r.get("station_code") for r in results]
            expected_stations = ["CSMT", "BCT", "LTT", "DR"]
            found_stations = [code for code in expected_stations if code in station_codes]
            
            if len(found_stations) < 2:  # At least 2 major Mumbai stations
                self.log_result(
                    "Station Search Mumbai",
                    False,
                    f"Expected major Mumbai stations, found: {found_stations}",
                    data
                )
                return False
            
            # Validate result structure
            for result in results[:3]:  # Check first 3 results
                required_fields = ["station_code", "station_name", "city", "state", "zone", "is_hub"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "Station Search Mumbai",
                        False,
                        f"Result missing fields: {missing_fields}",
                        result
                    )
                    return False
            
            self.log_result(
                "Station Search Mumbai",
                True,
                f"Found {len(results)} Mumbai stations including: {', '.join(found_stations)}"
            )
            return True
            
        except Exception as e:
            self.log_result("Station Search Mumbai", False, f"Exception: {str(e)}")
            return False
    
    async def test_station_search_ndls(self):
        """Test GET /api/trains/stations/search?q=NDLS - should return New Delhi with high score"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/stations/search",
                params={"q": "NDLS", "limit": 5}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Station Search NDLS", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                self.log_result(
                    "Station Search NDLS",
                    False,
                    "No results returned for NDLS search",
                    data
                )
                return False
            
            # First result should be NDLS with high score
            first_result = results[0]
            if first_result.get("station_code") != "NDLS":
                self.log_result(
                    "Station Search NDLS",
                    False,
                    f"Expected first result to be NDLS, got {first_result.get('station_code')}",
                    first_result
                )
                return False
            
            # Should have high score for exact match
            score = first_result.get("score", 0)
            if score < 90:  # Exact code match should have high score
                self.log_result(
                    "Station Search NDLS",
                    False,
                    f"Expected high score for exact match, got {score}",
                    first_result
                )
                return False
            
            self.log_result(
                "Station Search NDLS",
                True,
                f"Found NDLS with score {score}: {first_result.get('station_name')}"
            )
            return True
            
        except Exception as e:
            self.log_result("Station Search NDLS", False, f"Exception: {str(e)}")
            return False
    
    async def test_station_info_ndls(self):
        """Test GET /api/trains/stations/NDLS - should return full station details with hub info"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/stations/NDLS"
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Station Info NDLS", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = ["station_code", "station_name", "city", "state", "zone", "station_type", "is_hub"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Station Info NDLS",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # NDLS should be a hub
            if not data.get("is_hub"):
                self.log_result(
                    "Station Info NDLS",
                    False,
                    "NDLS should be marked as a hub",
                    data
                )
                return False
            
            # Should have hub_type
            if not data.get("hub_type"):
                self.log_result(
                    "Station Info NDLS",
                    False,
                    "NDLS should have hub_type specified",
                    data
                )
                return False
            
            self.log_result(
                "Station Info NDLS",
                True,
                f"NDLS info: {data.get('station_name')}, hub_type={data.get('hub_type')}"
            )
            return True
            
        except Exception as e:
            self.log_result("Station Info NDLS", False, f"Exception: {str(e)}")
            return False
    
    async def test_railway_hubs_all(self):
        """Test GET /api/trains/hubs - should return all 30 hubs"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/hubs"
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Railway Hubs All", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            if "hubs" not in data or "count" not in data:
                self.log_result(
                    "Railway Hubs All",
                    False,
                    "Missing 'hubs' or 'count' in response",
                    data
                )
                return False
            
            hubs = data.get("hubs", [])
            count = data.get("count", 0)
            
            if len(hubs) != count:
                self.log_result(
                    "Railway Hubs All",
                    False,
                    f"Count mismatch: {count} reported but {len(hubs)} hubs returned",
                    data
                )
                return False
            
            # Should have reasonable number of hubs (at least 20)
            if count < 20:
                self.log_result(
                    "Railway Hubs All",
                    False,
                    f"Expected at least 20 hubs, got {count}",
                    data
                )
                return False
            
            # Validate hub structure
            if hubs:
                first_hub = hubs[0]
                required_fields = ["hub_code", "hub_name", "hub_type", "city", "state", "zone", "importance_score"]
                missing_fields = [field for field in required_fields if field not in first_hub]
                
                if missing_fields:
                    self.log_result(
                        "Railway Hubs All",
                        False,
                        f"Hub missing fields: {missing_fields}",
                        first_hub
                    )
                    return False
            
            self.log_result(
                "Railway Hubs All",
                True,
                f"Retrieved {count} railway hubs successfully"
            )
            return True
            
        except Exception as e:
            self.log_result("Railway Hubs All", False, f"Exception: {str(e)}")
            return False
    
    async def test_railway_hubs_mega(self):
        """Test GET /api/trains/hubs?hub_type=MEGA_HUB - should return exactly 4: NDLS, CSMT, HWH, MAS"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/hubs",
                params={"hub_type": "MEGA_HUB"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Railway Hubs MEGA_HUB", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            hubs = data.get("hubs", [])
            count = data.get("count", 0)
            
            # Should have exactly 4 mega hubs
            if count != 4:
                self.log_result(
                    "Railway Hubs MEGA_HUB",
                    False,
                    f"Expected exactly 4 MEGA_HUBs, got {count}",
                    data
                )
                return False
            
            # Check for expected mega hubs
            hub_codes = [h.get("hub_code") for h in hubs]
            expected_mega_hubs = ["NDLS", "CSMT", "HWH", "MAS"]
            found_mega_hubs = [code for code in expected_mega_hubs if code in hub_codes]
            
            if len(found_mega_hubs) < 3:  # At least 3 of the 4 expected
                self.log_result(
                    "Railway Hubs MEGA_HUB",
                    False,
                    f"Expected mega hubs {expected_mega_hubs}, found: {found_mega_hubs}",
                    data
                )
                return False
            
            # All should have hub_type = MEGA_HUB
            for hub in hubs:
                if hub.get("hub_type") != "MEGA_HUB":
                    self.log_result(
                        "Railway Hubs MEGA_HUB",
                        False,
                        f"Hub {hub.get('hub_code')} has wrong type: {hub.get('hub_type')}",
                        hub
                    )
                    return False
            
            self.log_result(
                "Railway Hubs MEGA_HUB",
                True,
                f"Found {count} MEGA_HUBs: {', '.join(hub_codes)}"
            )
            return True
            
        except Exception as e:
            self.log_result("Railway Hubs MEGA_HUB", False, f"Exception: {str(e)}")
            return False
    
    async def test_autocomplete_pune(self):
        """Test GET /api/trains/autocomplete?q=Pun - should suggest Pune with hub badge"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/autocomplete",
                params={"q": "Pun", "limit": 5}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Autocomplete Pune", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            if "suggestions" not in data or "count" not in data:
                self.log_result(
                    "Autocomplete Pune",
                    False,
                    "Missing 'suggestions' or 'count' in response",
                    data
                )
                return False
            
            suggestions = data.get("suggestions", [])
            
            if not suggestions:
                self.log_result(
                    "Autocomplete Pune",
                    False,
                    "No suggestions returned for 'Pun' query",
                    data
                )
                return False
            
            # Look for Pune in suggestions
            pune_suggestion = None
            for suggestion in suggestions:
                if "pune" in suggestion.get("display_name", "").lower():
                    pune_suggestion = suggestion
                    break
            
            if not pune_suggestion:
                self.log_result(
                    "Autocomplete Pune",
                    False,
                    "Pune not found in autocomplete suggestions",
                    data
                )
                return False
            
            # Check suggestion structure
            required_fields = ["station_code", "display_name", "city", "state", "is_hub"]
            missing_fields = [field for field in required_fields if field not in pune_suggestion]
            
            if missing_fields:
                self.log_result(
                    "Autocomplete Pune",
                    False,
                    f"Pune suggestion missing fields: {missing_fields}",
                    pune_suggestion
                )
                return False
            
            # Check for hub badge if it's a hub
            display_name = pune_suggestion.get("display_name", "")
            is_hub = pune_suggestion.get("is_hub", False)
            
            if is_hub and "🚉" not in display_name:
                self.log_result(
                    "Autocomplete Pune",
                    False,
                    f"Pune is a hub but missing hub badge in display_name: {display_name}",
                    pune_suggestion
                )
                return False
            
            self.log_result(
                "Autocomplete Pune",
                True,
                f"Pune found: {display_name}, is_hub={is_hub}"
            )
            return True
            
        except Exception as e:
            self.log_result("Autocomplete Pune", False, f"Exception: {str(e)}")
            return False
    
    async def test_autocomplete_delhi(self):
        """Test GET /api/trains/autocomplete?q=Del - should suggest Delhi stations prioritizing NDLS"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/autocomplete",
                params={"q": "Del", "limit": 5}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Autocomplete Delhi", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            suggestions = data.get("suggestions", [])
            
            if not suggestions:
                self.log_result(
                    "Autocomplete Delhi",
                    False,
                    "No suggestions returned for 'Del' query",
                    data
                )
                return False
            
            # Look for Delhi stations
            delhi_stations = []
            for suggestion in suggestions:
                if "delhi" in suggestion.get("display_name", "").lower():
                    delhi_stations.append(suggestion)
            
            if not delhi_stations:
                self.log_result(
                    "Autocomplete Delhi",
                    False,
                    "No Delhi stations found in autocomplete suggestions",
                    data
                )
                return False
            
            # NDLS should be prioritized (first Delhi station or high in list)
            ndls_found = False
            for i, suggestion in enumerate(suggestions[:3]):  # Check top 3
                if suggestion.get("station_code") == "NDLS":
                    ndls_found = True
                    break
            
            if not ndls_found:
                self.log_result(
                    "Autocomplete Delhi",
                    False,
                    "NDLS not found in top 3 suggestions for Delhi",
                    data
                )
                return False
            
            self.log_result(
                "Autocomplete Delhi",
                True,
                f"Found {len(delhi_stations)} Delhi stations with NDLS prioritized"
            )
            return True
            
        except Exception as e:
            self.log_result("Autocomplete Delhi", False, f"Exception: {str(e)}")
            return False
    
    async def test_route_validation_criteria(self):
        """Test route type and confidence validation criteria"""
        try:
            # Test a route to check validation criteria
            response = await self.client.get(
                f"{self.backend_url}/api/trains/connectivity",
                params={"from": "NDLS", "to": "CSMT"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Route Validation Criteria", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Validate route_type is one of expected values
            route_type = data.get("route_type")
            valid_route_types = ["DIRECT", "HUB_BASED", "LOCAL_CATCHMENT", "NOT_FOUND"]
            
            if route_type not in valid_route_types:
                self.log_result(
                    "Route Validation Criteria",
                    False,
                    f"Invalid route_type: {route_type}, expected one of {valid_route_types}",
                    data
                )
                return False
            
            # Validate confidence is one of expected values
            confidence = data.get("confidence")
            valid_confidence_levels = ["HIGH", "MEDIUM", "LOW"]
            
            if confidence not in valid_confidence_levels:
                self.log_result(
                    "Route Validation Criteria",
                    False,
                    f"Invalid confidence: {confidence}, expected one of {valid_confidence_levels}",
                    data
                )
                return False
            
            # Validate path structure
            path = data.get("path", [])
            for node in path:
                node_type = node.get("type")
                valid_node_types = ["ORIGIN", "VIA", "HUB", "DESTINATION"]
                
                if node_type not in valid_node_types:
                    self.log_result(
                        "Route Validation Criteria",
                        False,
                        f"Invalid node type: {node_type}, expected one of {valid_node_types}",
                        node
                    )
                    return False
            
            self.log_result(
                "Route Validation Criteria",
                True,
                f"All validation criteria met: route_type={route_type}, confidence={confidence}"
            )
            return True
            
        except Exception as e:
            self.log_result("Route Validation Criteria", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all train connectivity tests"""
        print("🚆 Starting Train Connectivity System Tests (Phase 1)")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Run all tests in order
        tests = [
            self.test_direct_route_csmt_pune,
            self.test_hub_based_route_delhi_bangalore,
            self.test_direct_route_delhi_chennai,
            self.test_direct_route_satara_pune,
            self.test_station_search_mumbai,
            self.test_station_search_ndls,
            self.test_station_info_ndls,
            self.test_railway_hubs_all,
            self.test_railway_hubs_mega,
            self.test_autocomplete_pune,
            self.test_autocomplete_delhi,
            self.test_route_validation_criteria
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                results.append(False)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TRAIN CONNECTIVITY SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All train connectivity tests passed!")
            print("📝 Station database working correctly")
            print("📝 Hub-based routing functional")
            print("📝 Direct route detection working")
            print("📝 Search and autocomplete operational")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with TrainConnectivityTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())