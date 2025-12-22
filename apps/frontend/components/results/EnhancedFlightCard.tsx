'use client'

import { useState } from 'react'
import { Plane, ChevronDown, ChevronUp, ExternalLink, Lock, Shield } from 'lucide-react'
import { useSwipeable } from 'react-swipeable'
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

  const firstSegment = offer.segments[0]
  const lastSegment = offer.segments[offer.segments.length - 1]

  /* ✅ Swipe ONLY for flight info (NOT buttons) */
  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => {},
    onSwipedRight: () => {},
    trackTouch: true,
    preventScrollOnSwipe: true,
  })

  const handleVendorClick = async (vendorId: string) => {
    if (vendorId !== 'aviasales') {
      alert(`${vendorId} integration coming soon!`)
      return
    }

    try {
      setRedirecting(vendorId)

      const departDate = new Date(firstSegment.departure_time).toISOString().split('T')[0]
      const returnDate = searchParams?.get('return_date')

      const finalUrl = buildAviasalesFlightUrl({
        origin: firstSegment.departure_airport,
        destination: lastSegment.arrival_airport,
        departDate,
        returnDate: returnDate || undefined,
        adults: parseInt(searchParams?.get('adults') || '1', 10),
        children: parseInt(searchParams?.get('children') || '0', 10),
        infants: parseInt(searchParams?.get('infants') || '0', 10),
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
      alert('Redirect failed. Please try again.')
      setRedirecting(null)
    }
  }

  const selectedVendor = FLIGHT_VENDORS.find(v => v.id === redirecting)

  /* ✅ Redirect screen */
  if (showRedirectScreen && selectedVendor) {
    return (
      <RedirectScreen
        vendor={{ name: selectedVendor.name, logo: selectedVendor.logo }}
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
    <div className="bg-white rounded-lg border border-gray-200 hover:shadow-md transition">

      {/* 🔹 Flight Info (Swipe Enabled) */}
      <div {...swipeHandlers} className="p-4 touch-pan-y">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-gray-100 rounded flex items-center justify-center">
              <Plane className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <div className="font-semibold text-sm">{firstSegment.carrier_name}</div>
              <div className="text-xs text-gray-500">
                {formatDuration(offer.total_duration_minutes)} · {offer.stops === 0 ? 'Non-stop' : `${offer.stops} stops`}
              </div>
            </div>
          </div>

          <PriceDisplay
            price={offer.price}
            currency={offer.currency}
            size="md"
            showTrustLabel
          />
        </div>
      </div>

      {/* 🔹 Action Area (NO swipe here) */}
      <div className="px-4 pb-4">
        <button
          type="button"
          onClick={() => setShowVendors(!showVendors)}
          className="w-full mt-2 py-2 bg-blue-600 text-white rounded-lg font-semibold flex items-center justify-center gap-2"
        >
          Select
          {showVendors ? <ChevronUp /> : <ChevronDown />}
        </button>

        {showVendors && (
          <div className="mt-4 space-y-2">
            {FLIGHT_VENDORS.map(vendor => {
              const isActive = vendor.type === 'real'
              return (
                <button
                  key={vendor.id}
                  type="button"
                  disabled={!isActive}
                  onClick={() => handleVendorClick(vendor.id)}
                  className={`w-full p-3 rounded-lg border flex justify-between items-center ${
                    isActive
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-gray-100 opacity-60'
                  }`}
                >
                  <div>
                    <div className="font-semibold">{vendor.name}</div>
                    <div className="text-xs text-gray-600">{vendor.description}</div>
                  </div>
                  {isActive ? <ExternalLink /> : <Lock />}
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
