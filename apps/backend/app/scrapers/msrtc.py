"""
MSRTC Timetable Scraper
========================

Production-safe scraper for Maharashtra State Road Transport Corporation
publicly available timetable data.

Source: https://msrtc.maharashtra.gov.in/GeneralPages/Timetabel.aspx

DISCLAIMER:
-----------
This scraper is for READ-ONLY access to publicly available schedule data.
- NO booking automation
- NO payment processing  
- NO CAPTCHA bypassing
- NO authentication bypass
- Rate-limited to respect server resources

The data collected is for reference purposes only.
Always verify schedules on the official MSRTC website before travel.

Author: TravelSearch Team
License: Internal use only
"""

import asyncio
import logging
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from urllib.parse import urljoin
import unicodedata

import httpx
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

MSRTC_BASE_URL = "https://msrtc.maharashtra.gov.in"
MSRTC_TIMETABLE_URL = f"{MSRTC_BASE_URL}/GeneralPages/Timetabel.aspx"

# Rate limiting: minimum seconds between requests
RATE_LIMIT_SECONDS = 2.0

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0

# Maximum retries for failed requests
MAX_RETRIES = 3

# Cache duration for stops (24 hours)
STOPS_CACHE_DURATION = timedelta(hours=24)

# User agent - be transparent about what we are
USER_AGENT = (
    "TravelSearch-Bot/1.0 "
    "(+https://travelsearch.example.com/bot; "
    "timetable-reference-only; "
    "contact@travelsearch.example.com)"
)

# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class MSRTCStop:
    """
    Represents a bus stop from MSRTC dropdown.
    
    Stores both original Marathi name and normalized search key.
    """
    # Original value from dropdown (usually numeric ID or code)
    value: str
    
    # Display name in Marathi (original, untranslated)
    name_marathi: str
    
    # Normalized name for search (lowercase, ASCII-safe)
    name_normalized: str
    
    # English transliteration (if available)
    name_english: Optional[str] = None
    
    # Stop type: 'major' (district HQ) or 'minor'
    stop_type: str = "minor"
    
    # District/region (if extractable)
    district: Optional[str] = None
    
    # When this stop was last scraped
    scraped_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        result = asdict(self)
        if result.get('scraped_at'):
            result['scraped_at'] = result['scraped_at'].isoformat()
        return result
    
    @property
    def search_key(self) -> str:
        """Generate unique search key for deduplication."""
        return hashlib.md5(
            f"{self.value}:{self.name_marathi}".encode('utf-8')
        ).hexdigest()[:16]


@dataclass
class MSRTCSchedule:
    """
    Represents a single bus schedule entry from timetable.
    """
    # Route info
    origin: str
    destination: str
    
    # Bus/service identification
    bus_number: Optional[str] = None
    service_type: Optional[str] = None  # Express, Ordinary, Shivneri, etc.
    
    # Timing
    departure_time: Optional[str] = None  # HH:MM format
    arrival_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    
    # Route details
    via_stops: List[str] = field(default_factory=list)
    distance_km: Optional[int] = None
    
    # Fare (if available) - in INR
    fare: Optional[float] = None
    fare_type: Optional[str] = None  # Ordinary, Reserved, etc.
    
    # Frequency
    frequency: Optional[str] = None  # Daily, Weekdays, etc.
    days_of_operation: List[str] = field(default_factory=list)
    
    # Metadata
    scraped_at: Optional[datetime] = None
    source_url: Optional[str] = None
    
    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        result = asdict(self)
        if result.get('scraped_at'):
            result['scraped_at'] = result['scraped_at'].isoformat()
        return result


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_marathi_text(text: str) -> str:
    """
    Normalize Marathi/Devanagari text for search.
    
    - Converts to lowercase (where applicable)
    - Removes diacritics for ASCII-safe comparison
    - Strips extra whitespace
    - Preserves original Unicode for display
    
    Args:
        text: Original Marathi text
        
    Returns:
        Normalized ASCII-safe search string
    """
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Normalize Unicode (NFC form)
    text = unicodedata.normalize('NFC', text)
    
    # Create ASCII-safe version for search
    # Remove combining characters (diacritics)
    ascii_safe = unicodedata.normalize('NFKD', text)
    ascii_safe = ''.join(
        c for c in ascii_safe 
        if not unicodedata.combining(c)
    )
    
    # Lowercase and remove extra spaces
    ascii_safe = ' '.join(ascii_safe.lower().split())
    
    # Remove special characters but keep alphanumeric and spaces
    ascii_safe = re.sub(r'[^\w\s]', '', ascii_safe, flags=re.UNICODE)
    
    return ascii_safe


def transliterate_marathi_to_english(marathi_text: str) -> Optional[str]:
    """
    Basic transliteration of common Marathi place names to English.
    
    This is a simplified mapping - not a full transliteration system.
    Returns None if no mapping found.
    """
    # Common city/town name mappings
    MARATHI_TO_ENGLISH = {
        "मुंबई": "Mumbai",
        "पुणे": "Pune",
        "नागपूर": "Nagpur",
        "नाशिक": "Nashik",
        "औरंगाबाद": "Aurangabad",
        "सोलापूर": "Solapur",
        "कोल्हापूर": "Kolhapur",
        "अमरावती": "Amravati",
        "सांगली": "Sangli",
        "जळगाव": "Jalgaon",
        "अकोला": "Akola",
        "लातूर": "Latur",
        "धुळे": "Dhule",
        "अहमदनगर": "Ahmednagar",
        "चंद्रपूर": "Chandrapur",
        "परभणी": "Parbhani",
        "जालना": "Jalna",
        "भंडारा": "Bhandara",
        "यवतमाळ": "Yavatmal",
        "वर्धा": "Wardha",
        "ठाणे": "Thane",
        "रत्नागिरी": "Ratnagiri",
        "सिंधुदुर्ग": "Sindhudurg",
        "सातारा": "Satara",
        "रायगड": "Raigad",
        "पालघर": "Palghar",
        "गडचिरोली": "Gadchiroli",
        "गोंदिया": "Gondia",
        "वाशिम": "Washim",
        "हिंगोली": "Hingoli",
        "नांदेड": "Nanded",
        "उस्मानाबाद": "Osmanabad",
        "बीड": "Beed",
        "बुलडाणा": "Buldhana",
    }
    
    return MARATHI_TO_ENGLISH.get(marathi_text.strip())


# ============================================================
# MAIN SCRAPER CLASS
# ============================================================

class MSRTCScraper:
    """
    Production-safe scraper for MSRTC timetable data.
    
    Features:
    - Rate limiting to respect server resources
    - Proper error handling and retries
    - UTF-8/Marathi text handling
    - Caching to minimize requests
    - Async operation for efficiency
    
    Usage:
        scraper = MSRTCScraper()
        stops = await scraper.get_all_stops()
        schedules = await scraper.get_timetable("Mumbai", "Pune")
    """
    
    def __init__(
        self,
        rate_limit: float = RATE_LIMIT_SECONDS,
        timeout: float = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Initialize scraper with rate limiting.
        
        Args:
            rate_limit: Minimum seconds between requests
            timeout: Request timeout in seconds
            max_retries: Maximum retries for failed requests
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._last_request_time: Optional[datetime] = None
        self._stops_cache: Optional[List[MSRTCStop]] = None
        self._stops_cache_time: Optional[datetime] = None
        self._viewstate_cache: Optional[Dict[str, str]] = None
        
        # HTTP client with proper headers
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._init_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_client()
    
    async def _init_client(self):
        """Initialize HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,mr;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                },
                follow_redirects=True,
            )
    
    async def _close_client(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _rate_limit_wait(self):
        """
        Enforce rate limiting between requests.
        
        Waits if necessary to maintain minimum time between requests.
        """
        if self._last_request_time:
            elapsed = (datetime.utcnow() - self._last_request_time).total_seconds()
            if elapsed < self.rate_limit:
                wait_time = self.rate_limit - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        self._last_request_time = datetime.utcnow()
    
    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        retry_count: int = 0,
    ) -> Optional[str]:
        """
        Make HTTP request with rate limiting and retry logic.
        
        Args:
            method: HTTP method ('GET' or 'POST')
            url: Request URL
            data: POST data (optional)
            retry_count: Current retry attempt
            
        Returns:
            Response text or None if failed
        """
        await self._init_client()
        await self._rate_limit_wait()
        
        try:
            if method.upper() == 'GET':
                response = await self._client.get(url)
            else:
                response = await self._client.post(url, data=data)
            
            response.raise_for_status()
            
            # Ensure UTF-8 decoding
            return response.text
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            if retry_count < self.max_retries:
                wait_time = (retry_count + 1) * 2  # Exponential backoff
                await asyncio.sleep(wait_time)
                return await self._make_request(method, url, data, retry_count + 1)
            return None
            
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            if retry_count < self.max_retries:
                wait_time = (retry_count + 1) * 2
                await asyncio.sleep(wait_time)
                return await self._make_request(method, url, data, retry_count + 1)
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None
    
    def _parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """
        Parse HTML with proper encoding.
        
        Args:
            html: Raw HTML string
            
        Returns:
            BeautifulSoup object or None
        """
        if not html:
            return None
        
        try:
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            return None
    
    def _extract_viewstate(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract ASP.NET ViewState and related hidden fields.
        
        Required for form POST submissions.
        
        Args:
            soup: Parsed HTML
            
        Returns:
            Dictionary of hidden form fields
        """
        viewstate_fields = {}
        
        # Common ASP.NET hidden fields
        field_names = [
            '__VIEWSTATE',
            '__VIEWSTATEGENERATOR',
            '__EVENTVALIDATION',
            '__EVENTTARGET',
            '__EVENTARGUMENT',
        ]
        
        for field_name in field_names:
            field = soup.find('input', {'name': field_name})
            if field and field.get('value'):
                viewstate_fields[field_name] = field['value']
        
        return viewstate_fields
    
    def _extract_dropdown_options(
        self,
        soup: BeautifulSoup,
        dropdown_id: str,
    ) -> List[Tuple[str, str]]:
        """
        Extract options from a dropdown/select element.
        
        Args:
            soup: Parsed HTML
            dropdown_id: ID of the select element
            
        Returns:
            List of (value, text) tuples
        """
        options = []
        
        select = soup.find('select', {'id': dropdown_id})
        if not select:
            # Try by name
            select = soup.find('select', {'name': dropdown_id})
        
        if not select:
            logger.warning(f"Dropdown not found: {dropdown_id}")
            return options
        
        for option in select.find_all('option'):
            value = option.get('value', '')
            text = option.get_text(strip=True)
            
            # Skip empty or placeholder options
            if value and text and value != '0' and text != '--Select--':
                options.append((value, text))
        
        return options
    
    async def get_all_stops(self, force_refresh: bool = False) -> List[MSRTCStop]:
        """
        Get all bus stops from MSRTC timetable page dropdowns.
        
        Extracts both origin and destination stops, deduplicates,
        and returns a comprehensive list.
        
        Args:
            force_refresh: Bypass cache and fetch fresh data
            
        Returns:
            List of MSRTCStop objects
        """
        # Check cache
        if not force_refresh and self._stops_cache:
            cache_age = datetime.utcnow() - self._stops_cache_time
            if cache_age < STOPS_CACHE_DURATION:
                logger.debug("Using cached stops")
                return self._stops_cache
        
        logger.info("Fetching MSRTC stops from timetable page")
        
        # Fetch timetable page
        html = await self._make_request('GET', MSRTC_TIMETABLE_URL)
        if not html:
            logger.error("Failed to fetch timetable page")
            return []
        
        soup = self._parse_html(html)
        if not soup:
            return []
        
        # Cache viewstate for later form submissions
        self._viewstate_cache = self._extract_viewstate(soup)
        
        # Common dropdown IDs on MSRTC timetable page
        # These may need adjustment based on actual page structure
        dropdown_ids = [
            'ddlFromStation',
            'ddlToStation',
            'ctl00$ContentPlaceHolder1$ddlFromStation',
            'ctl00$ContentPlaceHolder1$ddlToStation',
            'ddlSource',
            'ddlDestination',
        ]
        
        all_options = []
        found_dropdowns = set()
        
        for dropdown_id in dropdown_ids:
            options = self._extract_dropdown_options(soup, dropdown_id)
            if options:
                found_dropdowns.add(dropdown_id)
                all_options.extend(options)
        
        if not all_options:
            logger.warning("No dropdown options found - page structure may have changed")
            # Try to find any select elements
            selects = soup.find_all('select')
            for select in selects:
                select_id = select.get('id', select.get('name', 'unknown'))
                logger.debug(f"Found select: {select_id}")
        
        # Deduplicate and create MSRTCStop objects
        seen_keys = set()
        stops = []
        
        for value, text in all_options:
            # Create stop object
            stop = MSRTCStop(
                value=value,
                name_marathi=text,
                name_normalized=normalize_marathi_text(text),
                name_english=transliterate_marathi_to_english(text),
                stop_type='major' if transliterate_marathi_to_english(text) else 'minor',
            )
            
            # Deduplicate
            if stop.search_key not in seen_keys:
                seen_keys.add(stop.search_key)
                stops.append(stop)
        
        # Sort by normalized name
        stops.sort(key=lambda s: s.name_normalized)
        
        # Update cache
        self._stops_cache = stops
        self._stops_cache_time = datetime.utcnow()
        
        logger.info(f"Found {len(stops)} unique stops from {len(found_dropdowns)} dropdowns")
        return stops
    
    async def get_timetable(
        self,
        origin: str,
        destination: str,
    ) -> List[MSRTCSchedule]:
        """
        Get bus timetable between two stops.
        
        Submits form to MSRTC timetable page and parses results.
        
        Args:
            origin: Origin stop (Marathi or English name)
            destination: Destination stop (Marathi or English name)
            
        Returns:
            List of MSRTCSchedule objects
        """
        logger.info(f"Fetching timetable: {origin} → {destination}")
        
        # Ensure we have stops and viewstate
        if not self._viewstate_cache:
            await self.get_all_stops()
        
        if not self._viewstate_cache:
            logger.error("Failed to get viewstate for form submission")
            return []
        
        # Find matching stop values
        stops = self._stops_cache or []
        
        origin_stop = self._find_stop(stops, origin)
        dest_stop = self._find_stop(stops, destination)
        
        if not origin_stop:
            logger.warning(f"Origin stop not found: {origin}")
            return []
        
        if not dest_stop:
            logger.warning(f"Destination stop not found: {destination}")
            return []
        
        # Prepare form data
        form_data = {
            **self._viewstate_cache,
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            # These field names may need adjustment
            'ctl00$ContentPlaceHolder1$ddlFromStation': origin_stop.value,
            'ctl00$ContentPlaceHolder1$ddlToStation': dest_stop.value,
            'ctl00$ContentPlaceHolder1$btnSearch': 'Search',
        }
        
        # Submit form
        html = await self._make_request('POST', MSRTC_TIMETABLE_URL, data=form_data)
        if not html:
            logger.error("Failed to submit timetable search")
            return []
        
        # Parse results
        soup = self._parse_html(html)
        if not soup:
            return []
        
        # Update viewstate for subsequent requests
        self._viewstate_cache = self._extract_viewstate(soup)
        
        # Find and parse timetable table
        schedules = self._parse_timetable_table(
            soup,
            origin_stop.name_marathi,
            dest_stop.name_marathi,
        )
        
        logger.info(f"Found {len(schedules)} schedules for {origin} → {destination}")
        return schedules
    
    def _find_stop(
        self,
        stops: List[MSRTCStop],
        query: str,
    ) -> Optional[MSRTCStop]:
        """
        Find a stop by name (Marathi, English, or normalized).
        
        Args:
            stops: List of MSRTCStop objects
            query: Search query
            
        Returns:
            Matching MSRTCStop or None
        """
        query_normalized = normalize_marathi_text(query)
        query_lower = query.lower().strip()
        
        # Exact match first
        for stop in stops:
            if stop.name_marathi == query:
                return stop
            if stop.name_english and stop.name_english.lower() == query_lower:
                return stop
        
        # Normalized match
        for stop in stops:
            if stop.name_normalized == query_normalized:
                return stop
        
        # Partial match
        for stop in stops:
            if query_normalized in stop.name_normalized:
                return stop
            if stop.name_english and query_lower in stop.name_english.lower():
                return stop
        
        return None
    
    def _parse_timetable_table(
        self,
        soup: BeautifulSoup,
        origin: str,
        destination: str,
    ) -> List[MSRTCSchedule]:
        """
        Parse timetable table from search results.
        
        Args:
            soup: Parsed HTML
            origin: Origin stop name
            destination: Destination stop name
            
        Returns:
            List of MSRTCSchedule objects
        """
        schedules = []
        
        # Try to find timetable table by common patterns
        table = None
        
        # Try by ID
        table_ids = [
            'gvTimetable',
            'GridView1',
            'ctl00_ContentPlaceHolder1_gvTimetable',
            'tblTimetable',
        ]
        
        for table_id in table_ids:
            table = soup.find('table', {'id': table_id})
            if table:
                break
        
        # Try by class
        if not table:
            table = soup.find('table', {'class': re.compile(r'grid|timetable|schedule', re.I)})
        
        # Fallback: find any table with schedule-like content
        if not table:
            tables = soup.find_all('table')
            for t in tables:
                text = t.get_text().lower()
                if any(kw in text for kw in ['departure', 'arrival', 'time', 'bus', 'निघण्याची', 'पोहोचण्याची']):
                    table = t
                    break
        
        if not table:
            logger.warning("Timetable table not found - page structure may have changed")
            # Return fallback message schedule
            return [self._create_fallback_schedule(origin, destination)]
        
        # Parse table rows
        rows = table.find_all('tr')
        if len(rows) < 2:
            logger.warning("Timetable table has no data rows")
            return [self._create_fallback_schedule(origin, destination)]
        
        # Try to detect header row
        header_row = rows[0]
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        # Map headers to indices
        col_map = self._detect_column_mapping(headers)
        
        # Parse data rows
        for row in rows[1:]:
            cells = row.find_all('td')
            if not cells:
                continue
            
            schedule = self._parse_table_row(cells, col_map, origin, destination)
            if schedule:
                schedules.append(schedule)
        
        return schedules
    
    def _detect_column_mapping(self, headers: List[str]) -> Dict[str, int]:
        """
        Detect column indices from headers.
        
        Args:
            headers: List of header texts (lowercase)
            
        Returns:
            Dictionary mapping field names to column indices
        """
        col_map = {}
        
        patterns = {
            'bus_number': ['bus', 'no', 'number', 'बस'],
            'service_type': ['type', 'service', 'प्रकार'],
            'departure_time': ['departure', 'depart', 'from', 'निघण्याची', 'सुटण्याची'],
            'arrival_time': ['arrival', 'arrive', 'to', 'पोहोचण्याची'],
            'via': ['via', 'route', 'मार्ग'],
            'fare': ['fare', 'price', 'amount', 'भाडे', 'किंमत'],
            'distance': ['km', 'distance', 'अंतर'],
            'duration': ['duration', 'time', 'hrs', 'वेळ'],
        }
        
        for idx, header in enumerate(headers):
            for field, keywords in patterns.items():
                if any(kw in header for kw in keywords):
                    if field not in col_map:  # First match wins
                        col_map[field] = idx
        
        return col_map
    
    def _parse_table_row(
        self,
        cells: List[Tag],
        col_map: Dict[str, int],
        origin: str,
        destination: str,
    ) -> Optional[MSRTCSchedule]:
        """
        Parse a single table row into MSRTCSchedule.
        
        Args:
            cells: List of td elements
            col_map: Column index mapping
            origin: Origin stop name
            destination: Destination stop name
            
        Returns:
            MSRTCSchedule or None if invalid
        """
        def get_cell(field: str) -> str:
            idx = col_map.get(field)
            if idx is not None and idx < len(cells):
                return cells[idx].get_text(strip=True)
            return ''
        
        departure_time = get_cell('departure_time')
        arrival_time = get_cell('arrival_time')
        
        # Must have at least departure time
        if not departure_time:
            return None
        
        # Parse duration
        duration_minutes = None
        duration_text = get_cell('duration')
        if duration_text:
            duration_minutes = self._parse_duration(duration_text)
        
        # Parse fare
        fare = None
        fare_text = get_cell('fare')
        if fare_text:
            fare = self._parse_fare(fare_text)
        
        # Parse via stops
        via_stops = []
        via_text = get_cell('via')
        if via_text:
            via_stops = [s.strip() for s in re.split(r'[,/\-]', via_text) if s.strip()]
        
        return MSRTCSchedule(
            origin=origin,
            destination=destination,
            bus_number=get_cell('bus_number') or None,
            service_type=get_cell('service_type') or None,
            departure_time=self._normalize_time(departure_time),
            arrival_time=self._normalize_time(arrival_time) if arrival_time else None,
            duration_minutes=duration_minutes,
            via_stops=via_stops,
            fare=fare,
            source_url=MSRTC_TIMETABLE_URL,
        )
    
    def _normalize_time(self, time_str: str) -> Optional[str]:
        """
        Normalize time string to HH:MM format.
        
        Args:
            time_str: Raw time string
            
        Returns:
            Normalized time or None
        """
        if not time_str:
            return None
        
        # Clean up
        time_str = re.sub(r'[^\d:apmAPM]', '', time_str)
        
        # Try common formats
        patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',
            r'(\d{1,2})\.(\d{2})\s*(am|pm)?',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, time_str, re.IGNORECASE)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                meridiem = match.group(3) if len(match.groups()) > 2 else None
                
                if meridiem:
                    if meridiem.lower() == 'pm' and hour != 12:
                        hour += 12
                    elif meridiem.lower() == 'am' and hour == 12:
                        hour = 0
                
                return f"{hour:02d}:{minute:02d}"
        
        return time_str
    
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """
        Parse duration string to minutes.
        
        Args:
            duration_str: Duration string (e.g., "2:30", "2.5 hrs", "150 min")
            
        Returns:
            Duration in minutes or None
        """
        if not duration_str:
            return None
        
        # Hours and minutes format
        match = re.match(r'(\d+)[:\.](\d+)', duration_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return hours * 60 + minutes
        
        # Hours only
        match = re.match(r'(\d+\.?\d*)\s*(?:hr|hour)', duration_str, re.IGNORECASE)
        if match:
            return int(float(match.group(1)) * 60)
        
        # Minutes only
        match = re.match(r'(\d+)\s*(?:min)', duration_str, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        return None
    
    def _parse_fare(self, fare_str: str) -> Optional[float]:
        """
        Parse fare string to float.
        
        Args:
            fare_str: Fare string (e.g., "₹250", "Rs. 250", "250/-")
            
        Returns:
            Fare amount or None
        """
        if not fare_str:
            return None
        
        # Remove currency symbols and extract number
        match = re.search(r'([\d,]+\.?\d*)', fare_str.replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        return None
    
    def _create_fallback_schedule(
        self,
        origin: str,
        destination: str,
    ) -> MSRTCSchedule:
        """
        Create a fallback schedule when table parsing fails.
        
        Args:
            origin: Origin stop name
            destination: Destination stop name
            
        Returns:
            Fallback MSRTCSchedule with redirect info
        """
        return MSRTCSchedule(
            origin=origin,
            destination=destination,
            service_type="CHECK_OFFICIAL_SITE",
            source_url=MSRTC_TIMETABLE_URL,
        )


# ============================================================
# DATABASE INTEGRATION
# ============================================================

async def save_stops_to_db(stops: List[MSRTCStop], db) -> int:
    """
    Save MSRTC stops to MongoDB.
    
    Uses upsert to avoid duplicates.
    
    Args:
        stops: List of MSRTCStop objects
        db: Motor database instance
        
    Returns:
        Number of stops saved/updated
    """
    if not stops:
        return 0
    
    collection = db.msrtc_stops
    count = 0
    
    for stop in stops:
        result = await collection.update_one(
            {"search_key": stop.search_key},
            {"$set": stop.to_dict()},
            upsert=True,
        )
        if result.upserted_id or result.modified_count:
            count += 1
    
    return count


async def save_schedules_to_db(schedules: List[MSRTCSchedule], db) -> int:
    """
    Save MSRTC schedules to MongoDB.
    
    Args:
        schedules: List of MSRTCSchedule objects
        db: Motor database instance
        
    Returns:
        Number of schedules saved
    """
    if not schedules:
        return 0
    
    collection = db.msrtc_schedules
    
    # Create unique key for each schedule
    docs = []
    for schedule in schedules:
        doc = schedule.to_dict()
        doc['_search_key'] = hashlib.md5(
            f"{schedule.origin}:{schedule.destination}:{schedule.departure_time}:{schedule.bus_number}".encode()
        ).hexdigest()[:16]
        docs.append(doc)
    
    # Bulk upsert
    from pymongo import UpdateOne
    operations = [
        UpdateOne(
            {"_search_key": doc['_search_key']},
            {"$set": doc},
            upsert=True,
        )
        for doc in docs
    ]
    
    result = await collection.bulk_write(operations)
    return result.upserted_count + result.modified_count


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

async def scrape_msrtc_stops() -> List[MSRTCStop]:
    """
    Convenience function to scrape all MSRTC stops.
    
    Returns:
        List of MSRTCStop objects
    """
    async with MSRTCScraper() as scraper:
        return await scraper.get_all_stops()


async def scrape_msrtc_timetable(
    origin: str,
    destination: str,
) -> List[MSRTCSchedule]:
    """
    Convenience function to scrape timetable for a route.
    
    Args:
        origin: Origin city/stop
        destination: Destination city/stop
        
    Returns:
        List of MSRTCSchedule objects
    """
    async with MSRTCScraper() as scraper:
        return await scraper.get_timetable(origin, destination)


# ============================================================
# CLI INTERFACE (for testing)
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        logging.basicConfig(level=logging.INFO)
        
        print("MSRTC Timetable Scraper")
        print("=" * 40)
        print("DISCLAIMER: This tool only reads publicly")
        print("available schedule data. No booking automation.")
        print("=" * 40)
        print()
        
        async with MSRTCScraper() as scraper:
            # Get all stops
            print("Fetching stops...")
            stops = await scraper.get_all_stops()
            print(f"Found {len(stops)} stops")
            
            # Show first 10
            print("\nFirst 10 stops:")
            for stop in stops[:10]:
                eng = f" ({stop.name_english})" if stop.name_english else ""
                print(f"  - {stop.name_marathi}{eng}")
            
            # Test timetable if arguments provided
            if len(sys.argv) >= 3:
                origin = sys.argv[1]
                destination = sys.argv[2]
                
                print(f"\nFetching timetable: {origin} → {destination}")
                schedules = await scraper.get_timetable(origin, destination)
                
                print(f"Found {len(schedules)} schedules:")
                for sch in schedules[:5]:
                    print(f"  - {sch.departure_time or 'N/A'} → {sch.arrival_time or 'N/A'}")
                    if sch.fare:
                        print(f"    Fare: ₹{sch.fare}")
    
    asyncio.run(main())
