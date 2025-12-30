'use client'

/**
 * BusCard - Mobile-First Result Card
 * ===================================
 * 
 * MOBILE-FIRST DESIGN:
 * - Stacked layout on mobile (flex-col)
 * - No horizontal overflow
 * - Large tap targets (min 44px)
 * - Readable text on 360px screens
 * 
 * SERVICE THEMING:
 * - Uses warm clay accent (#C47A4A)
 * - Subtle card tint on hover/select
 * 
 * BOOKING FLOW:
 * - Clicking "Book" navigates to /buses/vendors page with search context
 * - User selects vendor on vendors page
 * - Consistent UX across all services (Flights, Hotels, Buses, Trains)
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Bus,
  ChevronDown,
  ChevronUp,
  Clock,
  Wifi,
  BatteryCharging,
  Snowflake,
  Users,
  ExternalLink,
} from 'lucide-react'
import LikelyStops from './LikelyStops'

interface BusOffer {
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
  operator_name: string
  operator_type: string
  bus_type: string
  bus_type_label: string
  is_ac: boolean
  is_sleeper: boolean
  has_charging_point: boolean
  has_wifi: boolean
  frequency: string | null
  departure_window: string | null
  stops_count: number
  intermediate_stops: string[]
}

interface BusCardProps {
  offer: BusOffer
  index?: number
  departureDate?: string // YYYY-MM-DD format for vendor page
}

// Button label mapping
const getPartnerButtonLabel = (partnerName: string): string => {
  const labels: Record<string, string> = {
    'redBus': 'redBus',
    'Paytm Bus': 'Paytm',
    'AbhiBus': 'AbhiBus',
    'MSRTC Official': 'MSRTC',
  }
  return labels[partnerName] || partnerName
}

export default function BusCard({ offer, index = 0, departureDate }: BusCardProps) {
  const router = useRouter()
  const [showDetails, setShowDetails] = useState(false)
  const [showFareTooltip, setShowFareTooltip] = useState(false)

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
    if (hours > 48 || hours < 0.25) return null
    
    const h = Math.floor(diffMs / (1000 * 60 * 60))
    const m = Math.round((diffMs % (1000 * 60 * 60)) / (1000 * 60))
    
    return `${h}h ${m}m`
  }

  // Navigate to vendors page for booking
  const handleBookClick = () => {
    // Get departure date from offer or prop
    const date = departureDate || new Date().toISOString().split('T')[0]
    
    const params = new URLSearchParams({
      origin: offer.from_city,
      destination: offer.to_city,
      departure_date: date,
      price: offer.avg_price.toString(),
      currency: offer.currency || 'INR',
      operator: offer.operator_name || '',
      bus_type: offer.bus_type_label || '',
    })
    
    router.push(`/buses/vendors?${params.toString()}`)
  }

  const sortedPartners = [...offer.booking_partners].sort((a, b) => a.priority - b.priority)
  const isEstimatedResult = offer.provider === 'state_network' || offer.operator_name === 'Multiple Operators'
  const staggerClass = `animate-stagger-${Math.min(index + 1, 8)}`
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
        {/* === HEADER: Operator + Bus Type === */}
        <div className="p-4 pb-3 border-b border-[#F3EFEA]">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              {/* Icon */}
              <div className="w-10 h-10 bg-[#F9EDE6] rounded-lg flex items-center justify-center flex-shrink-0">
                {isEstimatedResult ? (
                  <Users className="h-5 w-5 text-[#C47A4A]" />
                ) : (
                  <Bus className="h-5 w-5 text-[#C47A4A]" />
                )}
              </div>
              
              {/* Operator Info */}
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-[#2B2B2B] text-sm sm:text-base truncate">
                  {isEstimatedResult ? 'Multiple Operators' : offer.operator_name}
                </p>
                <p className="text-xs sm:text-sm text-[#6B6B6B] truncate">
                  {offer.bus_type_label}
                </p>
              </div>
            </div>
            
            {/* Amenities Badges */}
            {!offer.is_fallback && (
              <div className="flex flex-wrap gap-1.5 flex-shrink-0">
                {offer.is_ac && (
                  <span className="flex items-center gap-1 px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded-full">
                    <Snowflake className="h-3 w-3" /> AC
                  </span>
                )}
                {offer.is_sleeper && (
                  <span className="px-2 py-0.5 text-xs bg-purple-50 text-purple-700 rounded-full">
                    Sleeper
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* === TIME & ROUTE SECTION (MOBILE OPTIMIZED) === */}
        {!offer.is_fallback && (
          <div className="p-4">
            {/* Time Row - Horizontal on all screens */}
            <div className="flex items-center justify-between mb-3">
              {/* Departure */}
              <div className="text-left">
                <p className="text-xl sm:text-2xl font-bold text-[#2B2B2B]">
                  {formatTime(offer.departure_time)}
                </p>
                <p className="text-xs sm:text-sm text-[#6B6B6B] truncate max-w-[100px] sm:max-w-none">
                  {offer.from_city}
                </p>
              </div>
              
              {/* Duration */}
              <div className="flex flex-col items-center px-2 sm:px-4 flex-1">
                {duration && (
                  <div className="flex items-center gap-1 text-xs sm:text-sm text-[#6B6B6B] mb-1">
                    <Clock className="h-3 w-3" />
                    <span>{duration}</span>
                  </div>
                )}
                <div className="w-full max-w-[120px] h-0.5 bg-[#E6E1D8] relative">
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-[#C47A4A] rounded-full" />
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-[#C47A4A] rounded-full" />
                </div>
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
                <p className="text-xs sm:text-sm text-[#6B6B6B] truncate max-w-[100px] sm:max-w-none">
                  {offer.to_city}
                </p>
              </div>
            </div>
            
            {/* Station names - stacked on mobile */}
            <div className="flex justify-between text-xs text-[#9CA3AF] px-1">
              <span className="truncate max-w-[45%]">{offer.from_station_name}</span>
              <span className="truncate max-w-[45%] text-right">{offer.to_station_name}</span>
            </div>
          </div>
        )}

        {/* === FALLBACK MESSAGE === */}
        {offer.is_fallback && (
          <div className="mx-4 my-3 p-3 bg-[#F3EFEA] border border-[#E6E1D8] rounded-lg">
            <div className="flex items-start gap-2">
              <Bus className="h-4 w-4 text-[#C47A4A] flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-[#2B2B2B] text-sm">Buses available on this route</p>
                <p className="text-xs text-[#6B6B6B] mt-0.5">
                  Live schedules shown on booking partner sites.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* === PRICE + AMENITIES === */}
        <div className="px-4 py-3 bg-[#FAFAF8] border-t border-[#F3EFEA]">
          <div className="flex items-center justify-between">
            {/* Price */}
            <div>
              <div className="flex items-baseline gap-1">
                <span 
                  className="text-xl sm:text-2xl font-bold text-[#2E7D32] cursor-help"
                  onMouseEnter={() => setShowFareTooltip(true)}
                  onMouseLeave={() => setShowFareTooltip(false)}
                >
                  ₹{Math.round(offer.avg_price).toLocaleString('en-IN')}
                </span>
                <span className="text-xs sm:text-sm text-[#6B6B6B]">/ seat</span>
              </div>
              <p className="text-xs text-[#9CA3AF]">
                {isEstimatedResult ? 'Estimated fare' : 'Starting from'}
              </p>
            </div>
            
            {/* Additional amenities */}
            {!offer.is_fallback && (offer.has_wifi || offer.has_charging_point) && (
              <div className="flex gap-2">
                {offer.has_wifi && (
                  <Wifi className="h-4 w-4 text-[#6B6B6B]" title="WiFi Available" />
                )}
                {offer.has_charging_point && (
                  <BatteryCharging className="h-4 w-4 text-[#6B6B6B]" title="Charging Available" />
                )}
              </div>
            )}
          </div>
          
          {/* Fare Tooltip */}
          {showFareTooltip && (
            <div className="absolute left-4 mt-2 z-10 w-56 p-3 bg-[#2B2B2B] text-white text-xs rounded-lg shadow-lg">
              <p>Estimated based on typical services.</p>
              <p className="mt-1 text-[#9CA3AF]">Final price shown on partner site.</p>
            </div>
          )}
        </div>

        {/* === EXPAND DETAILS === */}
        {!offer.is_fallback && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="w-full px-4 py-2 flex items-center justify-center gap-1 text-sm text-[#C47A4A] hover:bg-[#F9EDE6] transition"
          >
            {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {showDetails ? 'Hide details' : 'Show details'}
          </button>
        )}

        {/* === EXPANDED DETAILS === */}
        {showDetails && !offer.is_fallback && (
          <div className="px-4 pb-3 space-y-2 text-sm text-[#6B6B6B] border-t border-[#F3EFEA] pt-3">
            <div>Operator: {offer.operator_type === 'government' ? 'Government RTC' : 'Private'}</div>
            {offer.frequency && <div>Frequency: {offer.frequency}</div>}
            {offer.departure_window && <div>Departures: {offer.departure_window}</div>}
          </div>
        )}

        {/* === LIKELY STOPS === */}
        {!offer.is_fallback && (
          <div className="px-4">
            <LikelyStops fromCity={offer.from_city} toCity={offer.to_city} />
          </div>
        )}

        {/* === VIEW BUSES BUTTON (Navigates to Vendors Page) === */}
        <div className="p-4 bg-[#F3EFEA] border-t border-[#E6E1D8]">
          <button
            onClick={handleBookClick}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold rounded-lg bg-[#C47A4A] hover:bg-[#B06A3A] text-white transition-all duration-200 min-h-[44px]"
          >
            <ExternalLink className="h-4 w-4" />
            View Buses
          </button>
          
          <p className="mt-3 text-xs text-[#9CA3AF] text-center">
            Compare on redBus, Paytm Bus & MakeMyTrip
          </p>
        </div>
      </div>
    </>
  )
}
