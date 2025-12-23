'use client'

import { useState } from 'react'
import {
  Plane,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from 'lucide-react'
import { FlightOffer } from './ResultCard'
import { FLIGHT_VENDORS } from '@/lib/vendors'
import { buildAviasalesFlightUrl, logAffiliateClick } from '@/lib/affiliate'
import { formatDuration } from '@/lib/formatters'
import PriceDisplay from '@/components/ui/PriceDisplay'
import RedirectScreen from '@/components/common/RedirectScreen'

interface EnhancedFlightCardProps {
  offer: FlightOffer
  badge?: 'best' | 'cheapest' | 'fastest'
  searchParams?: URLSearchParams
}

const BADGE_CONFIG = {
  cheapest: {
    label: 'Cheapest',
    className: 'bg-green-50 text-green-700 border-green-200',
  },
  fastest: {
    label: 'Fastest',
    className: 'bg-purple-50 text-purple-700 border-purple-200',
  },
  best: {
    label: 'Best',
    className: 'bg-blue-50 text-blue-700 border-blue-200',
  },
} as const

export default function EnhancedFlightCard({
  offer,
  badge,
  searchParams,
}: EnhancedFlightCardProps) {
  const [showVendors, setShowVendors] = useState(false)
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [redirectUrl, setRedirectUrl] = useState('')
  const [showRedirectScreen, setShowRedirectScreen] = useState(false)

  const firstSegment = offer.segments[0]
  const lastSegment = offer.segments[offer.segments.length - 1]

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })

  const handleVendorClick = async (vendorId: string) => {
    if (vendorId !== 'aviasales') {
      alert(`${vendorId} integration coming soon`)
      return
    }

    try {
      setRedirecting(vendorId)

      const finalUrl = buildAviasalesFlightUrl({
        origin: firstSegment.departure_airport,
        destination: lastSegment.arrival_airport,
        departDate: firstSegment.departure_time.split('T')[0],
        returnDate: searchParams?.get('return_date') || undefined,
        adults: parseInt(searchParams?.get('adults') || '1'),
        children: parseInt(searchParams?.get('children') || '0'),
        infants: parseInt(searchParams?.get('infants') || '0'),
      })

      logAffiliateClick(
        'aviasales',
        `${firstSegment.departure_airport}-${lastSegment.arrival_airport}`,
        offer.offer_id,
        offer.price
      ).catch(() => {})

      setRedirectUrl(finalUrl)
      setShowRedirectScreen(true)
    } catch {
      setRedirecting(null)
      alert('Redirect failed')
    }
  }

  const selectedVendor = FLIGHT_VENDORS.find(v => v.id === redirecting)

  if (showRedirectScreen && selectedVendor) {
    return (
      <RedirectScreen
        vendor={{
          name: selectedVendor.name,
          logo: selectedVendor.logo,
        }}
        redirectUrl={redirectUrl}
        type="flight"
        contextInfo={{
          route: `${firstSegment.departure_airport} → ${lastSegment.arrival_airport}`,
        }}
        onRedirectComplete={() => {
          setShowRedirectScreen(false)
          setRedirecting(null)
        }}
      />
    )
  }

  return (
    <div className="relative bg-white border rounded-lg shadow-sm hover:shadow-md transition">

      {/* BADGE – TOP LEFT */}
      {badge && (
        <span
          className={`absolute top-3 left-3 px-2 py-0.5 text-[11px] font-semibold rounded-md border ${
            BADGE_CONFIG[badge].className
          }`}
        >
          {BADGE_CONFIG[badge].label}
        </span>
      )}

      {/* MAIN ROW */}
      <div className="p-4 flex flex-col sm:flex-row gap-4">

        {/* Airline */}
        <div className="flex items-center gap-3 min-w-[140px]">
          <div className="h-10 w-10 bg-gray-100 rounded flex items-center justify-center">
            <Plane className="h-5 w-5 text-gray-600" />
          </div>
          <div className="font-semibold text-sm truncate">
            {firstSegment.carrier_name}
          </div>
        </div>

        {/* Times */}
        <div className="flex-1 flex justify-between text-sm">
          <div>
            <div className="font-bold">
              {formatTime(firstSegment.departure_time)}
            </div>
            <div className="text-xs text-gray-500">
              {firstSegment.departure_airport}
            </div>
          </div>

          <div className="text-center text-xs text-gray-500">
            {formatDuration(offer.total_duration_minutes)} ·{' '}
            {offer.stops === 0
              ? 'Non-stop'
              : `${offer.stops} stop(s)`}
          </div>

          <div className="text-right">
            <div className="font-bold">
              {formatTime(lastSegment.arrival_time)}
            </div>
            <div className="text-xs text-gray-500">
              {lastSegment.arrival_airport}
            </div>
          </div>
        </div>

        {/* Price */}
        <div className="text-right">
          <PriceDisplay
            price={offer.price}
            currency={offer.currency}
          />
          <button
            onClick={() => setShowVendors(v => !v)}
            className="mt-2 w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded text-sm flex items-center justify-center gap-1"
          >
            Select
            {showVendors ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {/* VENDORS */}
      {showVendors && (
        <div className="border-t p-4 space-y-2">
          {FLIGHT_VENDORS.map(v => (
            <button
              key={v.id}
              onClick={() => handleVendorClick(v.id)}
              disabled={v.type !== 'real' || redirecting === v.id}
              className={`w-full p-3 rounded border flex justify-between items-center ${
                v.type === 'real'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-gray-100 opacity-60'
              }`}
            >
              <div>
                <div className="font-semibold">{v.name}</div>
                <div className="text-xs text-gray-500">
                  {v.description}
                </div>
              </div>

              {v.type === 'real' ? (
                <ExternalLink className="text-blue-600" />
              ) : (
                <span className="text-xs">Coming Soon</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
