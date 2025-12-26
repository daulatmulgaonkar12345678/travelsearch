"""
Track Price Service
===================
Background service for monitoring saved flight searches and sending
price drop alerts via email.

Features:
1. Daily background checks for saved searches
2. Compare current prices with last checked prices
3. Send email alerts only on meaningful price drops (configurable threshold)
4. Update last_checked_price after each check
5. Track notification history

Integration:
- Uses Resend for email delivery
- Integrates with Aviasales/Amadeus for current prices
- Stores state in MongoDB (saved_searches collection)
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import resend

from app.db.mongodb import get_db
from app.core.config import settings
from app.models.flight import FlightSearchRequest

logger = logging.getLogger(__name__)

# Configure Resend
resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# Price drop threshold - only alert if price drops by this percentage or more
PRICE_DROP_THRESHOLD_PERCENT = 5.0  # 5% price drop
MIN_PRICE_DROP_AMOUNT = 500  # Minimum ₹500 drop to trigger alert


class TrackPriceService:
    """
    Service for tracking prices and sending alerts.
    """
    
    def __init__(self):
        self.db = None
    
    async def _get_db(self):
        """Get database connection."""
        if self.db is None:
            self.db = get_db()
        return self.db
    
    async def get_active_saved_searches(self) -> List[Dict]:
        """
        Get all active saved searches that need price checking.
        """
        db = await self._get_db()
        
        # Get searches where:
        # - is_active = True
        # - departure_date is in the future
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        searches = await db.saved_searches.find(
            {
                "is_active": True,
                "search.departure_date": {"$gte": today}
            },
            {"_id": 0}
        ).to_list(1000)
        
        logger.info(f"[TrackPrice] Found {len(searches)} active searches to check")
        return searches
    
    async def fetch_current_price(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        cabin_class: str = "economy"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch current live price for a route.
        Returns the minimum price and provider info.
        """
        try:
            # Import here to avoid circular imports
            from app.services.aviasales_orchestrator import aviasales_first_orchestrator
            
            request = FlightSearchRequest(
                origin=origin.upper(),
                destination=destination.upper(),
                departure_date=departure_date,
                adults=adults,
                cabin_class=cabin_class,
                trip_type="oneway"
            )
            
            result = await aviasales_first_orchestrator.search(request)
            
            offers = result.get("offers", []) or result.get("flights", [])
            
            if not offers:
                logger.info(f"[TrackPrice] No offers found for {origin}-{destination}")
                return None
            
            # Get minimum price
            min_price = min(o.get("price", float('inf')) for o in offers)
            currency = offers[0].get("currency", "INR")
            
            return {
                "price": min_price,
                "currency": currency,
                "offer_count": len(offers),
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TrackPrice] Error fetching price for {origin}-{destination}: {e}")
            return None
    
    def should_send_alert(
        self,
        last_price: float,
        current_price: float,
        currency: str = "INR"
    ) -> tuple[bool, float, float]:
        """
        Determine if a price drop is significant enough to send an alert.
        
        Returns:
            (should_alert, price_drop_amount, price_drop_percent)
        """
        if current_price >= last_price:
            return False, 0, 0
        
        price_drop = last_price - current_price
        price_drop_percent = (price_drop / last_price) * 100
        
        # Check if drop meets thresholds
        meets_percentage = price_drop_percent >= PRICE_DROP_THRESHOLD_PERCENT
        meets_minimum = price_drop >= MIN_PRICE_DROP_AMOUNT
        
        should_alert = meets_percentage and meets_minimum
        
        logger.info(
            f"[TrackPrice] Price analysis: "
            f"{last_price} -> {current_price} ({currency}), "
            f"Drop: {price_drop} ({price_drop_percent:.1f}%), "
            f"Alert: {should_alert}"
        )
        
        return should_alert, price_drop, price_drop_percent
    
    async def send_price_alert_email(
        self,
        email: str,
        origin: str,
        destination: str,
        departure_date: str,
        last_price: float,
        current_price: float,
        price_drop: float,
        currency: str = "INR"
    ) -> bool:
        """
        Send price drop alert email via Resend.
        """
        if not resend.api_key:
            logger.warning("[TrackPrice] Resend API key not configured")
            return False
        
        # Format prices
        currency_symbol = "₹" if currency == "INR" else "$"
        
        # Build email HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">💰 Price Drop Alert!</h1>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border: 1px solid #e9ecef;">
                <h2 style="color: #333; margin-top: 0;">
                    {origin} → {destination}
                </h2>
                <p style="color: #666; font-size: 14px;">
                    Departure: {departure_date}
                </p>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <p style="color: #155724; margin: 0; font-size: 18px;">
                        <strong>Price dropped by {currency_symbol}{price_drop:,.0f}!</strong>
                    </p>
                    <p style="color: #155724; margin: 10px 0 0 0;">
                        <span style="text-decoration: line-through;">{currency_symbol}{last_price:,.0f}</span>
                        →
                        <strong style="font-size: 24px;">{currency_symbol}{current_price:,.0f}</strong>
                    </p>
                </div>
                
                <a href="https://travelsearch.app/flights/results?origin={origin}&destination={destination}&departure_date={departure_date}&adults=1&cabin_class=economy&trip_type=oneway" 
                   style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    View Flights
                </a>
                
                <p style="color: #999; font-size: 12px; margin-top: 30px;">
                    You're receiving this because you saved a search for this route.
                    <br>Prices are sourced from our travel partners and may change.
                </p>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; border-radius: 0 0 12px 12px; text-align: center;">
                <p style="margin: 0; font-size: 12px;">
                    TravelSearch • Find Your Perfect Journey
                </p>
            </div>
        </body>
        </html>
        """
        
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"💰 Price Drop: {origin} to {destination} now {currency_symbol}{current_price:,.0f}",
            "html": html_content
        }
        
        try:
            # Run sync SDK in thread to keep non-blocking
            result = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"[TrackPrice] Email sent to {email}: {result.get('id')}")
            return True
        except Exception as e:
            logger.error(f"[TrackPrice] Failed to send email to {email}: {e}")
            return False
    
    async def update_saved_search(
        self,
        search_id: str,
        current_price: float,
        current_currency: str,
        alert_sent: bool = False
    ):
        """
        Update saved search with latest price check info.
        """
        db = await self._get_db()
        
        update_data = {
            "last_checked_price": current_price,
            "last_checked_currency": current_currency,
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if alert_sent:
            update_data["last_notified_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.saved_searches.update_one(
            {"id": search_id},
            {
                "$set": update_data,
                "$inc": {"notification_count": 1 if alert_sent else 0}
            }
        )
        
        logger.info(f"[TrackPrice] Updated search {search_id}")
    
    async def check_all_saved_searches(self) -> Dict[str, Any]:
        """
        Main job: Check all active saved searches for price drops.
        This should be called periodically (e.g., daily via cron).
        """
        logger.info("[TrackPrice] Starting price check job")
        
        results = {
            "checked": 0,
            "alerts_sent": 0,
            "price_drops": 0,
            "no_change": 0,
            "errors": 0,
            "skipped": 0
        }
        
        searches = await self.get_active_saved_searches()
        
        for search in searches:
            try:
                search_params = search.get("search", {})
                search_id = search.get("id")
                email = search.get("email")
                
                # Get current price (live API call)
                price_data = await self.fetch_current_price(
                    origin=search_params.get("origin"),
                    destination=search_params.get("destination"),
                    departure_date=search_params.get("departure_date"),
                    adults=search_params.get("adults", 1),
                    cabin_class=search_params.get("cabin_class", "economy")
                )
                
                if not price_data:
                    results["skipped"] += 1
                    continue
                
                current_price = price_data["price"]
                current_currency = price_data["currency"]
                
                # Use last_checked_price if available, otherwise use last_known_price from save
                last_price = search.get("last_checked_price") or search.get("last_known_price")
                
                results["checked"] += 1
                
                if last_price is None:
                    # First check - just store the price
                    await self.update_saved_search(
                        search_id, current_price, current_currency
                    )
                    continue
                
                # Check if price dropped
                should_alert, price_drop, drop_percent = self.should_send_alert(
                    last_price, current_price, current_currency
                )
                
                if should_alert:
                    results["price_drops"] += 1
                    
                    # Send alert email
                    email_sent = await self.send_price_alert_email(
                        email=email,
                        origin=search_params.get("origin"),
                        destination=search_params.get("destination"),
                        departure_date=search_params.get("departure_date"),
                        last_price=last_price,
                        current_price=current_price,
                        price_drop=price_drop,
                        currency=current_currency
                    )
                    
                    if email_sent:
                        results["alerts_sent"] += 1
                else:
                    results["no_change"] += 1
                
                # Update saved search with new price
                await self.update_saved_search(
                    search_id, current_price, current_currency,
                    alert_sent=should_alert
                )
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"[TrackPrice] Error checking search {search.get('id')}: {e}")
                results["errors"] += 1
        
        logger.info(f"[TrackPrice] Job complete: {results}")
        return results


# Singleton instance
track_price_service = TrackPriceService()
