'use client'

import { useState } from 'react'
import { Plane, Clock, ChevronDown, ChevronUp, ExternalLink, Lock, Shield } from 'lucide-react'
import { FlightOffer, Segment } from './ResultCard'
import { FLIGHT_VENDORS } from '@/lib/vendors'
import { API_BASE_URL } from '@/lib/config'
import PriceDisplay from '@/components/ui/PriceDisplay'

interface EnhancedFlightCardProps {
  offer: FlightOffer
  badge?: 'best' | 'cheapest' | 'fastest'
  searchParams?: URLSearchParams
}

export default function EnhancedFlightCard({ offer, badge, searchParams }: EnhancedFlightCardProps) {
  const [showVendors, setShowVendors] = useState(false)
  const [redirecting, setRedirecting] = useState<string | null>(null)

  const firstSegment = offer.segments[0]
  const lastSegment = offer.segments[offer.segments.length - 1]

  const formatTime = (isoDate: string) => {
    const date = new Date(isoDate)
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
  }

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  const getDayOffset = (dep: string, arr: string) => {
    const depDate = new Date(dep)
    const arrDate = new Date(arr)
    const dayDiff = Math.floor((arrDate.getTime() - depDate.getTime()) / (1000 * 60 * 60 * 24))
    return dayDiff > 0 ? `+${dayDiff}` : null
  }

  const dayOffset = getDayOffset(firstSegment.departure_time, lastSegment.arrival_time)

  const badgeConfig = {
    best: { label: 'Best value', bg: 'bg-blue-100', textColor: 'text-blue-700', borderColor: 'border-blue-200' },
    cheapest: { label: 'Cheapest', bg: 'bg-green-100', textColor: 'text-green-700', borderColor: 'border-green-200' },
    fastest: { label: 'Fastest', bg: 'bg-gray-100', textColor: 'text-gray-700', borderColor: 'border-gray-200' },
  }

  const handleVendorClick = async (vendorId: string) => {
    if (vendorId !== 'aviasales') {
      alert(`${vendorId} integration coming soon!`)
      return
    }

    try {
      setRedirecting(vendorId)

      const redirectParams = new URLSearchParams({
        origin: firstSegment.departure_airport,
        destination: lastSegment.arrival_airport,
        depart: new Date(firstSegment.departure_time).toISOString().split('T')[0],
        adults: searchParams?.get('adults') || '1',
        children: searchParams?.get('children') || '0',
        infants: searchParams?.get('infants') || '0',
      })

      const returnDate = searchParams?.get('return_date')
      if (returnDate) {
        redirectParams.set('return', returnDate)
      }

      const redirectUrl = `${API_BASE_URL}/api/redirect/aviasales?${redirectParams.toString()}`
      window.open(redirectUrl, '_blank')
    } catch (error) {
      console.error('Redirect error:', error)
      alert('Failed to redirect. Please try again.')
    } finally {
      setRedirecting(null)
    }
  }

  const getViaText = () => {
    if (offer.stops === 0) return 'Non-stop'
    if (offer.stops === 1) {
      const viaAirport = offer.segments[0].arrival_airport
      return `via ${viaAirport}`
    }
    return `${offer.stops} stops`
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all">
      {/* Badge */}
      {badge && (
        <div className={`${badgeConfig[badge].bg} ${badgeConfig[badge].textColor} px-3 py-1 text-xs font-semibold inline-block rounded-tl-lg`}>
          {badgeConfig[badge].label}
        </div>
      )}

      <div className="p-4">
        {/* Main Flight Info - Single Line */}
        <div className="flex items-center justify-between gap-4">
          {/* Left: Airline */}
          <div className="flex items-center space-x-3 min-w-0 flex-shrink-0">
            <div className="h-10 w-10 bg-gray-100 rounded flex items-center justify-center">
              <Plane className="h-5 w-5 text-gray-600" />
            </div>
            <div className="min-w-0">
              <div className="font-semibold text-gray-900 text-sm truncate">
                {firstSegment.carrier_name}
              </div>
            </div>
          </div>

          {/* Center: Route & Time */}
          <div className="flex items-center space-x-4 flex-1 min-w-0">
            <div className="text-center flex-shrink-0">
              <div className="text-xl font-bold text-gray-900">
                {formatTime(firstSegment.departure_time)}
              </div>
              <div className="text-xs text-gray-600">
                {firstSegment.departure_airport}
              </div>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-center space-x-2">
                <div className="flex-1 border-t border-gray-300 relative">
                  {offer.stops > 0 && (
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white">
                      <div className="h-2 w-2 rounded-full bg-gray-400"></div>
                    </div>
                  )}
                </div>
              </div>
              <div className="text-center mt-1">
                <div className="text-xs text-gray-600">
                  {formatDuration(offer.total_duration_minutes)} · {getViaText()}
                </div>
              </div>
            </div>

            <div className="text-center flex-shrink-0">
              <div className="text-xl font-bold text-gray-900">
                {formatTime(lastSegment.arrival_time)}
                {dayOffset && <span className="text-xs text-red-600 ml-1">{dayOffset}</span>}
              </div>
              <div className="text-xs text-gray-600">
                {lastSegment.arrival_airport}
              </div>
            </div>
          </div>

          {/* Right: Price & Action */}
          <div className="text-right flex-shrink-0">
            <PriceDisplay 
              price={offer.price}
              currency={offer.currency}
              size="md"
              showTrustLabel={true}
              className="mb-2"
            />
            <button
              onClick={() => setShowVendors(!showVendors)}
              className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold text-sm flex items-center space-x-2"
            >
              <span>Select</span>
              {showVendors ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Vendor Selection Panel */}
        {showVendors && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-1">Choose your booking site</h4>
                <p className="text-xs text-gray-600">
                  You'll be redirected to complete your booking securely on the partner's website
                </p>
              </div>
              <div className="flex items-center space-x-1 text-xs text-gray-600 whitespace-nowrap ml-4">
                <Lock className="h-3 w-3" />
                <span>Secure redirection</span>
              </div>
            </div>
            <div className="space-y-2">
              {FLIGHT_VENDORS.map((vendor) => {
                const isActive = vendor.type === 'real'
                const isRedirecting = redirecting === vendor.id

                return (
                  <button
                    key={vendor.id}
                    onClick={() => handleVendorClick(vendor.id)}
                    disabled={!isActive || isRedirecting}
                    className={`
                      w-full p-3 rounded-lg border-2 transition-all text-left flex items-center justify-between
                      ${
                        isActive
                          ? 'border-blue-500 bg-blue-50 hover:bg-blue-100 cursor-pointer'
                          : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                      }
                    `}
                  >
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <div className="font-semibold text-gray-900 text-sm">{vendor.name}</div>
                        {isActive && (
                          <span className="inline-flex items-center space-x-1 text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full border border-green-200">
                            <Shield className="h-3 w-3" />
                            <span>Official partner</span>
                          </span>
                        )}
                      </div>
                      {vendor.description && (
                        <div className="text-xs text-gray-600 mt-0.5">{vendor.description}</div>
                      )}
                    </div>

                    <div className="flex items-center space-x-3">
                      {isActive && (
                        <PriceDisplay 
                          price={offer.price}
                          currency={offer.currency}
                          size="sm"
                          showTrustLabel={true}
                        />
                      )}

                      {isActive ? (
                        <ExternalLink className="h-5 w-5 text-blue-600" />
                      ) : (
                        <span className="text-xs font-semibold text-gray-500 px-2 py-1 bg-gray-200 rounded">
                          Coming Soon
                        </span>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
