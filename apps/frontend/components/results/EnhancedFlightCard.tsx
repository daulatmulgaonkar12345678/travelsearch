'use client'

import { useState } from 'react'
import { Plane, ChevronDown, ChevronUp, ExternalLink, Lock, Shield } from 'lucide-react'
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

export default function EnhancedFlightCard({ offer, badge, searchParams }: EnhancedFlightCardProps) {
  const [showVendors, setShowVendors] = useState(false)
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [redirectUrl, setRedirectUrl] = useState('')
  const [showRedirectScreen, setShowRedirectScreen] = useState(false)

  const first = offer.segments[0]
  const last = offer.segments[offer.segments.length - 1]

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })

  const handleVendorClick = async (vendorId: string) => {
    if (vendorId !== 'aviasales') return alert('Coming soon')

    const url = buildAviasalesFlightUrl({
      origin: first.departure_airport,
      destination: last.arrival_airport,
      departDate: first.departure_time.split('T')[0],
      returnDate: searchParams?.get('return_date') || undefined,
      adults: Number(searchParams?.get('adults') || 1),
      children: Number(searchParams?.get('children') || 0),
      infants: Number(searchParams?.get('infants') || 0),
    })

    logAffiliateClick('aviasales', `${first.departure_airport}-${last.arrival_airport}`, offer.offer_id, offer.price).catch(() => {})
    setRedirectUrl(url)
    setShowRedirectScreen(true)
  }

  if (showRedirectScreen) {
    const vendor = FLIGHT_VENDORS.find(v => v.id === redirecting)
    if (!vendor) return null

    return (
      <RedirectScreen
        vendor={{ name: vendor.name, logo: vendor.logo }}
        redirectUrl={redirectUrl}
        type="flight"
        contextInfo={{ route: `${first.departure_airport} → ${last.arrival_airport}` }}
        onRedirectComplete={() => {
          setShowRedirectScreen(false)
          setRedirecting(null)
        }}
      />
    )
  }

  return (
    <div className="bg-white border rounded-lg hover:shadow-md transition">

      {/* BADGE */}
      {badge && (
        <div className="px-3 py-1 text-xs font-semibold bg-blue-100 text-blue-700 inline-block rounded-br-lg">
          {badge.toUpperCase()}
        </div>
      )}

      <div className="p-4 space-y-4">

        {/* MOBILE FIRST LAYOUT */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

          {/* Airline */}
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-gray-100 rounded flex items-center justify-center">
              <Plane className="h-5 w-5 text-gray-600" />
            </div>
            <div className="font-semibold text-sm text-gray-900">
              {first.carrier_name}
            </div>
          </div>

          {/* TIMES */}
          <div className="flex items-center justify-between sm:justify-center gap-6 text-center">
            <div>
              <div className="text-lg font-bold">{formatTime(first.departure_time)}</div>
              <div className="text-xs text-gray-600">{first.departure_airport}</div>
            </div>

            <div className="text-xs text-gray-600 whitespace-nowrap">
              {formatDuration(offer.total_duration_minutes)} <br />
              {offer.stops === 0 ? 'Non-stop' : `${offer.stops} stop(s)`}
            </div>

            <div>
              <div className="text-lg font-bold">{formatTime(last.arrival_time)}</div>
              <div className="text-xs text-gray-600">{last.arrival_airport}</div>
            </div>
          </div>

          {/* PRICE + CTA */}
          <div className="flex flex-col items-stretch sm:items-end gap-2">
            <PriceDisplay price={offer.price} currency={offer.currency} />
            <button
              onClick={() => setShowVendors(!showVendors)}
              className="w-full sm:w-auto px-5 py-2 bg-blue-600 text-white rounded-lg font-semibold flex items-center justify-center gap-2"
            >
              Select {showVendors ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>
        </div>

        {/* VENDORS */}
        {showVendors && (
          <div className="pt-4 border-t space-y-2">
            {FLIGHT_VENDORS.map(v => (
              <button
                key={v.id}
                onClick={() => handleVendorClick(v.id)}
                disabled={v.type !== 'real'}
                className={`w-full p-3 border rounded-lg flex justify-between items-center ${
                  v.type === 'real'
                    ? 'bg-blue-50 border-blue-400'
                    : 'bg-gray-100 opacity-60 cursor-not-allowed'
                }`}
              >
                <div>
                  <div className="font-semibold">{v.name}</div>
                  <div className="text-xs text-gray-600">{v.description}</div>
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
    </div>
  )
}
