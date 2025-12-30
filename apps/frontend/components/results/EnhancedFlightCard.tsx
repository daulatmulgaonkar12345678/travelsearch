'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Plane,
  ExternalLink,
  Briefcase,
  Backpack,
  MapPin,
  Clock,
  ChevronDown,   // ✅ FIX
} from 'lucide-react'

import { FlightOffer, Segment } from './ResultCard'
import { formatDuration } from '@/lib/formatters'
import PriceDisplay from '@/components/ui/PriceDisplay'

// Airline code → name map
const AIRLINE_NAMES: Record<string, string> = {
  AI: 'Air India',
  '6E': 'IndiGo',
  UK: 'Vistara',
  SG: 'SpiceJet',
  G8: 'Go First',
  I5: 'AirAsia India',
  QP: 'Akasa Air',
  IX: 'Air India Express',
}

interface EnhancedFlightCardProps {
  offer: FlightOffer
  badge?: 'best' | 'cheapest' | 'fastest'
  searchParams?: URLSearchParams
}

const BADGE_CONFIG = {
  cheapest: { label: 'Cheapest', className: 'bg-green-50 text-green-700 border-green-200' },
  fastest: { label: 'Fastest', className: 'bg-purple-50 text-purple-700 border-purple-200' },
  best: { label: 'Best', className: 'bg-blue-50 text-blue-700 border-blue-200' },
} as const

function getAirlineName(code: string, name?: string) {
  if (name && name.length > 3) return name
  return AIRLINE_NAMES[code] || name || code
}

function isOvernightFlight(dep: string, arr: string) {
  return new Date(dep).toDateString() !== new Date(arr).toDateString()
}

function formatStops(stops: number) {
  if (stops === 0) return 'Non-stop'
  if (stops === 1) return '1 stop'
  return `${stops} stops`
}

function getLayovers(segments: Segment[]) {
  if (segments.length <= 1) return []
  return segments.slice(0, -1).map((s, i) => {
    const next = segments[i + 1]
    const mins =
      (new Date(next.departure_time).getTime() -
        new Date(s.arrival_time).getTime()) /
      60000
    return { airport: s.arrival_airport, duration: Math.round(mins) }
  })
}

export default function EnhancedFlightCard({
  offer,
  badge,
  searchParams,
}: EnhancedFlightCardProps) {
  const router = useRouter()
  const [showStops, setShowStops] = useState(false)

  const first = offer.segments[0]
  const last = offer.segments[offer.segments.length - 1]
  const layovers = getLayovers(offer.segments)

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
    })

  const handleVendorClick = () => {
    const params = new URLSearchParams({
      origin: first.departure_airport,
      destination: last.arrival_airport,
      departure_date: first.departure_time.split('T')[0],
      adults: searchParams?.get('adults') || '1',
      children: searchParams?.get('children') || '0',
      infants: searchParams?.get('infants') || '0',
    })

    router.push(`/flights/vendors?${params.toString()}`)
  }

  return (
    <div className="relative bg-white border rounded-lg shadow-sm hover:shadow-md transition">
      {badge && (
        <span
          className={`absolute top-3 left-3 px-2 py-0.5 text-[11px] font-semibold rounded-md border ${BADGE_CONFIG[badge].className}`}
        >
          {BADGE_CONFIG[badge].label}
        </span>
      )}

      <div className="p-4 flex flex-col sm:flex-row gap-4">
        {/* Airline */}
        <div className="flex items-center gap-3 min-w-[140px]">
          <div className="h-10 w-10 bg-gray-100 rounded flex items-center justify-center">
            <Plane className="h-5 w-5 text-gray-600" />
          </div>
          <div className="font-semibold text-sm truncate">
            {getAirlineName(first.carrier_code, first.carrier_name)}
          </div>
        </div>

        {/* Times */}
        <div className="flex-1 flex justify-between text-sm">
          <div>
            <div className="font-bold">{formatTime(first.departure_time)}</div>
            <div className="text-xs text-gray-500">{first.departure_airport}</div>
          </div>

          <div className="text-center text-xs text-gray-500">
            <div>{formatDuration(offer.total_duration_minutes)}</div>
            {offer.stops === 0 ? (
              <span>Non-stop</span>
            ) : (
              <button
                onClick={() => setShowStops(!showStops)}
                className="inline-flex items-center gap-1 hover:text-blue-600"
              >
                {formatStops(offer.stops)}
                <ChevronDown
                  size={12}
                  className={`transition-transform ${showStops ? 'rotate-180' : ''}`}
                />
              </button>
            )}
          </div>

          <div className="text-right">
            <div className="font-bold">
              {formatTime(last.arrival_time)}
              {isOvernightFlight(first.departure_time, last.arrival_time) && (
                <span className="text-xs text-gray-400 ml-1">(+1)</span>
              )}
            </div>
            <div className="text-xs text-gray-500">{last.arrival_airport}</div>
          </div>
        </div>

        {/* Price */}
        <div className="text-right">
          <PriceDisplay price={offer.price} currency={offer.currency} />
          <button
            onClick={handleVendorClick}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded text-sm flex items-center gap-1"
          >
            View Flights <ExternalLink size={14} />
          </button>
        </div>
      </div>

      {showStops && layovers.length > 0 && (
        <div className="border-t bg-gray-50 px-4 py-3">
          {layovers.map((l, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <MapPin size={12} />
              Stop at <b>{l.airport}</b> · <Clock size={12} />
              {formatDuration(l.duration)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
