'use client'

/**
 * TrainCard - Mobile-First Result Card
 * =====================================
 * 
 * MOBILE-FIRST DESIGN:
 * - Stacked layout on mobile (flex-col)
 * - No horizontal overflow
 * - Large tap targets (min 44px)
 * - Readable text on 360px screens
 * 
 * SERVICE THEMING:
 * - Uses muted olive green accent (#7A8B5C)
 * - Subtle card tint on hover/select
 * 
 * BOOKING FLOW:
 * - Clicking "Book" navigates to /trains/vendors page with search context
 * - User selects vendor on vendors page
 * - Consistent UX across all services (Flights, Hotels, Buses, Trains)
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Train,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Clock,
  MapPin,
  Utensils,
  Info,
} from 'lucide-react'

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
  selected_class?: string | null
  selected_class_display?: string | null
  available_classes: Array<{ class: string; avg_fare: number }>
  has_pantry: boolean
}

interface TrainCardProps {
  offer: TrainOffer
  index?: number
  departureDate?: string // YYYY-MM-DD format for vendor page
}

export default function TrainCard({ offer, index = 0, departureDate }: TrainCardProps) {
  const router = useRouter()
  const [showDetails, setShowDetails] = useState(false)

  const staggerClass = `animate-stagger-${Math.min(index + 1, 8)}`

  const formatTime = (iso: string) => {
    if (!iso || iso === '0001-01-01T00:00:00') return '--:--'
    return new Date(iso).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  }

  const computeSafeDuration = (departure: string, arrival: string): string | null => {
    if (!departure || !arrival) return null
    
    const invalidTimes = ['0001-01-01T00:00:00', '0001-01-01', '1970-01-01']
    if (invalidTimes.some(t => departure.includes(t) || arrival.includes(t))) return null
    
    const depTime = new Date(departure)
    const arrTime = new Date(arrival)
    
    if (isNaN(depTime.getTime()) || isNaN(arrTime.getTime())) return null
    if (depTime.getTime() === arrTime.getTime()) return null
    
    let diffMs = arrTime.getTime() - depTime.getTime()
    if (diffMs < 0) diffMs += 24 * 60 * 60 * 1000
    
    const hours = diffMs / (1000 * 60 * 60)
    if (hours > 72 || hours < 0.25) return null
    
    const h = Math.floor(diffMs / (1000 * 60 * 60))
    const m = Math.round((diffMs % (1000 * 60 * 60)) / (1000 * 60))
    
    return `${h}h ${m}m`
  }

  // Navigate to vendors page for booking
  const handleBookClick = () => {
    // Get departure date from offer or prop
    const date = departureDate || new Date().toISOString().split('T')[0]
    
    const params = new URLSearchParams({
      origin: offer.from_station,
      destination: offer.to_station,
      origin_city: offer.from_city,
      destination_city: offer.to_city,
      departure_date: date,
      price: offer.avg_price.toString(),
      currency: offer.currency || 'INR',
      train_name: offer.train_name || '',
      train_number: offer.train_number || '',
    })
    
    router.push(`/trains/vendors?${params.toString()}`)
  }

  const sortedPartners = [...offer.booking_partners].sort((a, b) => a.priority - b.priority)
  const cardClass = offer.selected_class_display || offer.selected_class || 
                    (offer.available_classes?.[0]?.class) || ''
  const duration = computeSafeDuration(offer.departure_time, offer.arrival_time)

  return (
    <>
      {/* MOBILE-FIRST CARD */}
      <div 
        className={`
          relative bg-white border border-[#E6E1D8] rounded-xl 
          shadow-sm hover:shadow-md transition-all duration-200 
          animate-card-in opacity-0 ${staggerClass}
          overflow-hidden
        `}
      >
        {/* Fallback Badge */}
        {offer.is_fallback && (
          <div className="absolute top-3 right-3 z-10">
            <span className="px-2 py-1 text-xs font-medium bg-amber-100 text-amber-700 rounded-full">
              Redirect Only
            </span>
          </div>
        )}

        {/* === HEADER: Train Name + Number + Class === */}
        <div className="p-4 pb-3 border-b border-[#F3EFEA]">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              {/* Icon */}
              <div className="w-10 h-10 bg-[#EEF1E8] rounded-lg flex items-center justify-center flex-shrink-0">
                <Train className="h-5 w-5 text-[#7A8B5C]" />
              </div>
              
              {/* Train Info */}
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-[#2B2B2B] text-sm sm:text-base truncate">
                  {offer.train_name}
                  {!offer.is_fallback && (
                    <span className="ml-1.5 text-xs sm:text-sm font-normal text-[#6B6B6B]">
                      #{offer.train_number}
                    </span>
                  )}
                </p>
                {offer.train_type && (
                  <p className="text-xs sm:text-sm text-[#6B6B6B] truncate">
                    {offer.train_type}
                  </p>
                )}
              </div>
            </div>
            
            {/* Class Badge */}
            {cardClass && !offer.is_fallback && (
              <span className="px-2.5 py-1 text-xs sm:text-sm font-semibold bg-[#EEF1E8] text-[#7A8B5C] rounded-full flex-shrink-0">
                {cardClass}
              </span>
            )}
          </div>
        </div>

        {/* === TIME & ROUTE SECTION (MOBILE OPTIMIZED) === */}
        {!offer.is_fallback && (
          <div className="p-4">
            {/* Time Row */}
            <div className="flex items-center justify-between mb-3">
              {/* Departure */}
              <div className="text-left">
                <p className="text-xl sm:text-2xl font-bold text-[#2B2B2B]">
                  {formatTime(offer.departure_time)}
                </p>
                <p className="text-xs sm:text-sm font-medium text-[#2B2B2B] truncate max-w-[90px] sm:max-w-none">
                  {offer.from_station}
                </p>
                <p className="text-xs text-[#9CA3AF] truncate max-w-[90px] sm:max-w-none">
                  {offer.from_city}
                </p>
              </div>
              
              {/* Duration */}
              <div className="flex flex-col items-center px-2 sm:px-4 flex-1">
                {duration && (
                  <p className="text-xs sm:text-sm text-[#6B6B6B] mb-1">{duration}</p>
                )}
                <div className="w-full max-w-[100px] h-0.5 bg-[#E6E1D8] relative">
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-[#7A8B5C] rounded-full" />
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-[#7A8B5C] rounded-full" />
                </div>
                <p className="text-xs text-[#9CA3AF] mt-1">
                  {offer.stops_count === 0 ? 'Direct' : `${offer.stops_count} stop${offer.stops_count > 1 ? 's' : ''}`}
                </p>
              </div>
              
              {/* Arrival */}
              <div className="text-right">
                {duration ? (
                  <p className="text-xl sm:text-2xl font-bold text-[#2B2B2B]">
                    {formatTime(offer.arrival_time)}
                  </p>
                ) : (
                  <p className="text-base text-[#9CA3AF]">Arr. varies</p>
                )}
                <p className="text-xs sm:text-sm font-medium text-[#2B2B2B] truncate max-w-[90px] sm:max-w-none">
                  {offer.to_station}
                </p>
                <p className="text-xs text-[#9CA3AF] truncate max-w-[90px] sm:max-w-none">
                  {offer.to_city}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* === FALLBACK MESSAGE === */}
        {offer.is_fallback && (
          <div className="mx-4 my-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs sm:text-sm text-amber-800">
                Route not in our database. Check partners for live schedules.
              </p>
            </div>
          </div>
        )}

        {/* === PRICE + AMENITIES === */}
        <div className="px-4 py-3 bg-[#FAFAF8] border-t border-[#F3EFEA]">
          <div className="flex items-center justify-between">
            {/* Price */}
            <div>
              <div className="flex items-baseline gap-1">
                <span className="text-xl sm:text-2xl font-bold text-[#2E7D32]">
                  ₹{Math.round(offer.avg_price).toLocaleString('en-IN')}
                </span>
                <span className="text-xs sm:text-sm text-[#6B6B6B]">/ person</span>
              </div>
              <p className="text-xs text-[#9CA3AF]">{offer.price_label}</p>
            </div>
            
            {/* Pantry indicator */}
            {!offer.is_fallback && offer.has_pantry && (
              <div className="flex items-center gap-1 text-[#6B6B6B]">
                <Utensils className="h-4 w-4" />
                <span className="text-xs hidden sm:inline">Pantry</span>
              </div>
            )}
          </div>
        </div>

        {/* === EXPAND DETAILS === */}
        {!offer.is_fallback && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="w-full px-4 py-2 flex items-center justify-center gap-1 text-sm text-[#7A8B5C] hover:bg-[#EEF1E8] transition"
          >
            {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {showDetails ? 'Hide details' : 'Show details'}
          </button>
        )}

        {/* === EXPANDED DETAILS === */}
        {showDetails && !offer.is_fallback && (
          <div className="px-4 pb-3 space-y-2 text-sm text-[#6B6B6B] border-t border-[#F3EFEA] pt-3">
            {offer.frequency && (
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <span>Runs: {offer.frequency}</span>
              </div>
            )}
            {offer.days_of_operation.length > 0 && (
              <div>Days: {offer.days_of_operation.join(', ')}</div>
            )}
            {offer.distance_km && (
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                <span>Distance: {offer.distance_km} km</span>
              </div>
            )}
          </div>
        )}

        {/* === CHECK AVAILABILITY BUTTON (Navigates to Vendors Page) === */}
        <div className="p-4 bg-[#EEF1E8] border-t border-[#E6E1D8]">
          <button
            onClick={handleBookClick}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold rounded-lg bg-[#7A8B5C] hover:bg-[#697A4C] text-white transition-all duration-200 min-h-[44px]"
          >
            <ExternalLink className="h-4 w-4" />
            Check Availability
          </button>
          
          <p className="mt-3 text-xs text-[#9CA3AF] text-center">
            View on Paytm Trains or MakeMyTrip
          </p>
        </div>

        {/* Disclaimer */}
        <p className="px-4 py-2 text-xs text-[#9CA3AF] bg-[#FAFAF8] border-t border-[#F3EFEA]">
          {offer.price_disclaimer}
        </p>
      </div>
    </>
  )
}
