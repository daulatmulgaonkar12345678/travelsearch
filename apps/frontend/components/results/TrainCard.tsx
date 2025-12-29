'use client'

import { useState, useCallback } from 'react'
import {
  Train,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Clock,
  MapPin,
  Utensils,
  Info,
  AlertCircle,
} from 'lucide-react'
import RedirectTransition from '@/components/loading/RedirectTransition'
import { validatePartnerUrl, logInvalidRedirect } from '@/lib/deepLinkValidator'

interface TrainOffer {
  offer_id: string
  mode: string
  provider: string
  from_station: string
  from_city: string
  from_station_name: string
  to_station: string
  to_city: string
  to_station_name: string
  departure_time: string
  arrival_time: string
  duration_minutes: number
  avg_price: number
  currency: string
  price_label: string
  price_disclaimer: string
  distance_km: number | null
  booking_partners: Array<{
    name: string
    url: string
    priority: number
    is_official?: boolean
  }>
  is_fallback: boolean
  train_number: string
  train_name: string
  train_type: string | null
  days_of_operation: string[]
  frequency: string | null
  stops_count: number
  intermediate_stops: string[]
  // VARIANT-LEVEL: This card is for ONE class
  selected_class?: string | null  // "SL", "3A", "2A", etc.
  selected_class_display?: string | null  // "Sleeper", "AC 3-Tier", etc.
  available_classes: Array<{ class: string; avg_fare: number }>
  has_pantry: boolean
}

interface TrainCardProps {
  offer: TrainOffer
  index?: number  // For stagger animation
}

export default function TrainCard({ offer, index = 0 }: TrainCardProps) {
  const [showDetails, setShowDetails] = useState(false)
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [showRedirectTransition, setShowRedirectTransition] = useState(false)
  const [pendingRedirectUrl, setPendingRedirectUrl] = useState<string | null>(null)
  const [redirectError, setRedirectError] = useState<string | null>(null)

  // Calculate stagger class (max 8 levels)
  const staggerClass = `animate-stagger-${Math.min(index + 1, 8)}`

  const formatTime = (iso: string) => {
    if (!iso || iso === '0001-01-01T00:00:00') return '--:--'
    return new Date(iso).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  }

  /**
   * STRICT DURATION GUARD
   * 
   * Duration must ONLY be shown when we have REAL times.
   * NO fallbacks, NO estimates, NO defaults.
   * 
   * PRODUCT PRINCIPLE: "Wrong time destroys trust faster than missing time ever will"
   * 
   * Returns null if duration cannot be computed safely.
   */
  const computeSafeDuration = (departure: string, arrival: string): string | null => {
    // Guard 1: Check for missing times
    if (!departure || !arrival) {
      console.warn("[Duration] Hidden: Missing times", { departure, arrival })
      return null
    }
    
    // Guard 2: Check for invalid placeholder times
    const invalidTimes = ['0001-01-01T00:00:00', '0001-01-01', '1970-01-01']
    if (invalidTimes.some(t => departure.includes(t) || arrival.includes(t))) {
      console.warn("[Duration] Hidden: Invalid placeholder times", { departure, arrival })
      return null
    }
    
    const depTime = new Date(departure)
    const arrTime = new Date(arrival)
    
    // Guard 3: Check for invalid dates
    if (isNaN(depTime.getTime()) || isNaN(arrTime.getTime())) {
      console.warn("[Duration] Hidden: Invalid date parsing", { departure, arrival })
      return null
    }
    
    // Guard 4: Check if arrival equals departure (signals unknown arrival)
    if (depTime.getTime() === arrTime.getTime()) {
      console.warn("[Duration] Hidden: Arrival equals departure (unknown)", { departure, arrival })
      return null
    }
    
    // Calculate duration with next-day handling
    let diffMs = arrTime.getTime() - depTime.getTime()
    
    // Handle multi-day journeys (trains can take 24+ hours)
    if (diffMs < 0) {
      diffMs += 24 * 60 * 60 * 1000 // Add 24 hours for overnight
    }
    
    // Guard 5: Sanity check - reject unrealistic durations (> 72 hours for trains or < 15 mins)
    const hours = diffMs / (1000 * 60 * 60)
    if (hours > 72 || hours < 0.25) {
      console.warn("[Duration] Hidden: Unrealistic duration", { hours, departure, arrival })
      return null
    }
    
    const h = Math.floor(diffMs / (1000 * 60 * 60))
    const m = Math.round((diffMs % (1000 * 60 * 60)) / (1000 * 60))
    
    return `${h}h ${m}m`
  }

  const handleBookingClick = (partner: TrainOffer['booking_partners'][0]) => {
    // MANDATORY: Validate URL before redirect
    const validation = validatePartnerUrl(partner.url)
    
    if (!validation.isValid) {
      logInvalidRedirect(partner.name, partner.url, validation.error || 'Unknown error')
      setRedirectError(`We couldn't open ${partner.name}. Please try another option.`)
      setTimeout(() => setRedirectError(null), 5000)
      return
    }
    
    setRedirecting(partner.name)
    setPendingRedirectUrl(partner.url)
    setShowRedirectTransition(true)
  }

  const handleRedirectComplete = useCallback(() => {
    if (pendingRedirectUrl) {
      window.open(pendingRedirectUrl, '_blank')
    }
    setShowRedirectTransition(false)
    setRedirecting(null)
    setPendingRedirectUrl(null)
  }, [pendingRedirectUrl])

  // Sort booking partners by priority
  const sortedPartners = [...offer.booking_partners].sort((a, b) => a.priority - b.priority)
  
  // Get the class for this card
  const cardClass = offer.selected_class_display || offer.selected_class || 
                    (offer.available_classes?.[0]?.class) || ''

  return (
    <>
      {/* Pre-redirect transition overlay */}
      <RedirectTransition
        mode="train"
        partnerName={redirecting || ''}
        isVisible={showRedirectTransition}
        onComplete={handleRedirectComplete}
        duration={500}
      />
      
      <div className={`relative bg-white border rounded-lg shadow-sm hover:shadow-md transition-all duration-200 animate-card-in opacity-0 ${staggerClass}`}>
        {/* Fallback Badge */}
        {offer.is_fallback && (
          <div className="absolute top-3 right-3">
            <span className="px-2 py-1 text-xs font-medium bg-amber-100 text-amber-700 rounded-full">
              Redirect Only
            </span>
          </div>
        )}

      <div className="p-4">
        {/* Train Info Header - WITH CLASS BADGE */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Train className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">
                {offer.train_name}
                {!offer.is_fallback && (
                  <span className="ml-2 text-sm font-normal text-gray-500">#{offer.train_number}</span>
                )}
              </p>
              {offer.train_type && (
                <p className="text-sm text-gray-500">{offer.train_type}</p>
              )}
            </div>
          </div>
          
          {/* CLASS BADGE - Prominent for variant-level */}
          {cardClass && !offer.is_fallback && (
            <span className="px-3 py-1 text-sm font-semibold bg-blue-100 text-blue-700 rounded-full">
              {cardClass}
            </span>
          )}
        </div>

        {/* Route & Time */}
        {!offer.is_fallback && (
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <p className="text-2xl font-bold text-gray-900">{formatTime(offer.departure_time)}</p>
              <p className="text-sm text-gray-600">{offer.from_station}</p>
              <p className="text-xs text-gray-400">{offer.from_city}</p>
            </div>
            
            <div className="flex-1 flex flex-col items-center px-4">
              {/* Duration - ONLY show if computeSafeDuration returns a value */}
              {computeSafeDuration(offer.departure_time, offer.arrival_time) && (
                <p className="text-sm text-gray-500">{computeSafeDuration(offer.departure_time, offer.arrival_time)}</p>
              )}
              <div className="w-full h-0.5 bg-gray-200 my-1 relative">
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full" />
                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full" />
              </div>
              <p className="text-xs text-gray-400">
                {offer.stops_count === 0 ? 'Direct' : `${offer.stops_count} stop${offer.stops_count > 1 ? 's' : ''}`}
              </p>
            </div>
            
            <div className="flex-1 text-right">
              {/* Arrival time - ONLY show if different from departure (known arrival) */}
              {computeSafeDuration(offer.departure_time, offer.arrival_time) ? (
                <p className="text-2xl font-bold text-gray-900">{formatTime(offer.arrival_time)}</p>
              ) : (
                <p className="text-lg text-gray-400">Arr. varies</p>
              )}
              <p className="text-sm text-gray-600">{offer.to_station}</p>
              <p className="text-xs text-gray-400">{offer.to_city}</p>
            </div>
          </div>
        )}

        {/* Fallback Message */}
        {offer.is_fallback && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex gap-2">
              <Info className="h-5 w-5 text-amber-600 flex-shrink-0" />
              <p className="text-sm text-amber-800">
                This route is not in our database. Check our booking partners for live schedules and availability.
              </p>
            </div>
          </div>
        )}

        {/* Price - THIS IS THE PRICE FOR THIS CLASS ONLY */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-green-600">
                ₹{Math.round(offer.avg_price).toLocaleString('en-IN')}
              </span>
              <span className="text-sm text-gray-500">/ person</span>
            </div>
            <p className="text-xs text-gray-400">{offer.price_label}</p>
          </div>
          
          {/* Amenities */}
          {!offer.is_fallback && offer.has_pantry && (
            <div className="flex items-center gap-1 text-gray-500">
              <Utensils className="h-4 w-4" />
              <span className="text-xs">Pantry</span>
            </div>
          )}
        </div>

        {/* Expand Details Button */}
        {!offer.is_fallback && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 mb-4"
          >
            {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {showDetails ? 'Hide details' : 'Show details'}
          </button>
        )}

        {/* Expanded Details */}
        {showDetails && !offer.is_fallback && (
          <div className="border-t pt-4 mb-4 space-y-3">
            {offer.frequency && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="h-4 w-4" />
                <span>Runs: {offer.frequency}</span>
              </div>
            )}
            {offer.days_of_operation.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>Days: {offer.days_of_operation.join(', ')}</span>
              </div>
            )}
            {offer.distance_km && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <MapPin className="h-4 w-4" />
                <span>Distance: {offer.distance_km} km</span>
              </div>
            )}
          </div>
        )}

        {/* Booking Partners */}
        <div className="border-t pt-4">
          <p className="text-xs text-gray-500 mb-2">Check availability:</p>
          
          {/* Redirect Error Fallback UI */}
          {redirectError && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{redirectError}</p>
            </div>
          )}
          
          <div className="flex flex-wrap gap-2">
            {sortedPartners.map(partner => (
              <button
                key={partner.name}
                onClick={() => handleBookingClick(partner)}
                disabled={redirecting === partner.name}
                className={`flex items-center gap-1 px-3 py-2 text-sm rounded-lg transition ${
                  partner.is_official
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                } disabled:opacity-50`}
              >
                {redirecting === partner.name ? (
                  'Redirecting...'
                ) : (
                  <>
                    {partner.name}
                    {partner.is_official && <span className="text-xs">(Official)</span>}
                    <ExternalLink className="h-3 w-3" />
                  </>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <p className="mt-3 text-xs text-gray-400">{offer.price_disclaimer}</p>
      </div>
    </div>
    </>
  )
}
