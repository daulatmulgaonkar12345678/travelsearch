"""MSRTC Timetable Scrapers

This module provides read-only access to publicly available
MSRTC (Maharashtra State Road Transport Corporation) timetable data.

DISCLAIMER:
- This scraper only reads publicly available schedule information
- No booking automation or payment processing
- No CAPTCHA bypassing
- Rate-limited to respect server resources
- Data is for reference only - always check official sources

Usage:
    from app.scrapers.msrtc import MSRTCScraper
    
    scraper = MSRTCScraper()
    stops = await scraper.get_all_stops()
    timetable = await scraper.get_timetable("मुंबई", "पुणे")
"""

from .msrtc import MSRTCScraper, MSRTCStop, MSRTCSchedule

__all__ = ["MSRTCScraper", "MSRTCStop", "MSRTCSchedule"]
