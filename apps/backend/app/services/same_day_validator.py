"""
Same-Day Search Policy Validator

Enforces business rule:
- Searches for flights departing TODAY are only allowed AFTER 12:00 IST
- Before 12:00 IST, treat "today" as "tomorrow" and suggest next-day search

Timezone: Asia/Kolkata (IST = UTC+5:30)
"""

import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)

class SameDayValidator:
    """Validates and enforces same-day search policy."""
    
    CUTOFF_HOUR = 12  # 12:00 IST
    TIMEZONE = ZoneInfo("Asia/Kolkata")
    
    @classmethod
    def validate_departure_date(
        cls,
        departure_date_str: str
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Validate departure date against same-day policy.
        
        Args:
            departure_date_str: Departure date in YYYY-MM-DD format
        
        Returns:
            (is_valid: bool, suggested_date: str|None, metadata: dict)
        """
        try:
            # Parse requested date
            requested_date = datetime.strptime(departure_date_str, "%Y-%m-%d").date()
            
            # Get current time in IST
            now_ist = datetime.now(cls.TIMEZONE)
            today_ist = now_ist.date()
            
            # If not searching for today, allow
            if requested_date != today_ist:
                return True, None, {
                    "same_day_check": False,
                    "requested_date": departure_date_str
                }
            
            # Searching for today - check time
            current_hour = now_ist.hour
            
            if current_hour >= cls.CUTOFF_HOUR:
                # After cutoff - allow same-day search
                logger.info(
                    f"✅ Same-day search allowed (current IST: {now_ist.strftime('%H:%M')})"
                )
                return True, None, {
                    "same_day_check": True,
                    "same_day_allowed": True,
                    "current_ist_time": now_ist.strftime("%H:%M"),
                    "requested_date": departure_date_str
                }
            else:
                # Before cutoff - shift to tomorrow
                from datetime import timedelta
                tomorrow = today_ist + timedelta(days=1)
                suggested_date = tomorrow.strftime("%Y-%m-%d")
                
                logger.warning(
                    f"⚠️  Same-day search before {cls.CUTOFF_HOUR}:00 IST. "
                    f"Current: {now_ist.strftime('%H:%M')}. Suggesting: {suggested_date}"
                )
                
                return False, suggested_date, {
                    "same_day_check": True,
                    "same_day_allowed": False,
                    "same_day_shifted": True,
                    "current_ist_time": now_ist.strftime("%H:%M"),
                    "requested_date": departure_date_str,
                    "suggested_date": suggested_date,
                    "reason": f"Same-day searches available after {cls.CUTOFF_HOUR}:00 IST"
                }
        
        except Exception as e:
            logger.error(f"Error validating same-day policy: {e}")
            # Fail open - allow request
            return True, None, {"error": str(e)}
    
    @classmethod
    def apply_to_request(cls, request_dict: Dict) -> Tuple[Dict, Dict]:
        """
        Apply same-day policy to a flight search request.
        
        Args:
            request_dict: Flight search request as dict
        
        Returns:
            (modified_request: dict, metadata: dict)
        """
        departure_date = request_dict.get("departure_date")
        if not departure_date:
            return request_dict, {}
        
        is_valid, suggested_date, metadata = cls.validate_departure_date(departure_date)
        
        if not is_valid and suggested_date:
            # Auto-shift to suggested date
            request_dict["departure_date"] = suggested_date
            logger.info(f"🔄 Auto-shifted departure: {departure_date} → {suggested_date}")
        
        return request_dict, metadata
