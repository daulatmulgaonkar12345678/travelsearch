"use client"

/**
 * TrainRedirectCard - Clean UI for routes not in our database
 * 
 * Shows:
 * - Positive messaging (not an error!)
 * - Route title
 * - Estimated fare range by class
 * - Partner booking buttons as main CTA
 * 
 * NEVER shows:
 * - "0 trains found"
 * - Warning banners
 * - "route not in database"
 */

import { useState, useCallback } from 'react'
import { Train, ExternalLink, Clock, MapPin, Ticket, Star } from 'lucide-react'
import RedirectTransition from '@/components/loading/RedirectTransition'

interface BookingPartner {
  name: string
  url: string
  priority: number
  is_official?: boolean
  description?: string
}

interface ClassEstimate {
  class: string
  avg_fare: number
}

interface TrainRedirectCardProps {
  originCity: string
  destinationCity: string
  distanceKm: number | null
  estimatedFares: ClassEstimate[]
  bookingPartners: BookingPartner[]
  departureDate: string
}

// Class display names
const CLASS_LABELS: Record<string, string> = {
  'SL': 'Sleeper',
  '3A': 'AC 3-Tier',
  '2A': 'AC 2-Tier',
  '1A': 'AC First',
  'CC': 'Chair Car',
  '2S': 'Second Sitting',
}

export default function TrainRedirectCard({
  originCity,
  destinationCity,
  distanceKm,
  estimatedFares,
  bookingPartners,
  departureDate,
}: TrainRedirectCardProps) {
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [showRedirectTransition, setShowRedirectTransition] = useState(false)
  const [pendingRedirectUrl, setPendingRedirectUrl] = useState<string | null>(null)
  
  // Sort partners by priority
  const sortedPartners = [...bookingPartners].sort((a, b) => a.priority - b.priority)
  
  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-IN', { 
      weekday: 'short', 
      day: 'numeric', 
      month: 'short',
      year: 'numeric'
    })
  }

  const handlePartnerClick = (partner: BookingPartner, e: React.MouseEvent) => {
    e.preventDefault()
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
      
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden animate-card-in">
        {/* Header - Route Info */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-5 text-white">
          <div className="flex items-center gap-3 mb-3">
            <div className="bg-white/20 p-2 rounded-lg">
              <Train className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">
                {originCity} → {destinationCity}
              </h2>
              <p className="text-blue-100 text-sm">
                {formatDate(departureDate)}
                {distanceKm && ` • ${distanceKm} km`}
              </p>
          </div>
        </div>
      </div>
      
      {/* Positive Message */}
      <div className="px-6 py-4 bg-green-50 border-b border-green-100">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 bg-green-100 p-1.5 rounded-full">
            <Ticket className="h-4 w-4 text-green-600" />
          </div>
          <div>
            <p className="text-green-800 font-medium">
              Multiple trains operate on this route daily
            </p>
            <p className="text-green-700 text-sm mt-1">
              Check live schedules, seat availability, and final prices on booking partners below.
            </p>
          </div>
        </div>
      </div>
      
      {/* Estimated Fares by Class */}
      {estimatedFares && estimatedFares.length > 0 && (
        <div className="px-6 py-4 border-b border-gray-100">
          <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
            <MapPin className="h-4 w-4 text-gray-500" />
            Estimated Fare Range
          </h3>
          <div className="grid grid-cols-3 gap-3">
            {estimatedFares.slice(0, 3).map((fare) => (
              <div 
                key={fare.class} 
                className="bg-gray-50 rounded-lg p-3 text-center"
              >
                <span className="text-xs text-gray-500 block mb-1">
                  {CLASS_LABELS[fare.class] || fare.class}
                </span>
                <span className="text-lg font-semibold text-gray-900">
                  ₹{fare.avg_fare.toLocaleString()}
                </span>
                <span className="text-xs text-gray-400 block">approx</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            * Actual prices depend on quota, availability, and booking date
          </p>
        </div>
      )}
      
      {/* Booking Partners - Main CTA */}
      <div className="px-6 py-5">
        <h3 className="text-sm font-medium text-gray-700 mb-3">
          Book on Official Partners
        </h3>
        <div className="space-y-3">
          {sortedPartners.map((partner, index) => (
            <a
              key={partner.name}
              href={partner.url}
              onClick={(e) => handlePartnerClick(partner, e)}
              className={`flex items-center justify-between p-4 rounded-lg border transition-all cursor-pointer ${
                index === 0 
                  ? 'bg-blue-50 border-blue-200 hover:bg-blue-100 hover:border-blue-300' 
                  : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300'
              } ${redirecting === partner.name ? 'opacity-70' : ''}`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  index === 0 ? 'bg-blue-600' : 'bg-gray-600'
                }`}>
                  <span className="text-white font-bold text-sm">
                    {partner.name.charAt(0)}
                  </span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`font-medium ${index === 0 ? 'text-blue-900' : 'text-gray-900'}`}>
                      {redirecting === partner.name ? 'Redirecting...' : partner.name}
                    </span>
                    {partner.is_official && (
                      <span className="bg-green-100 text-green-700 text-xs px-1.5 py-0.5 rounded">
                        Official
                      </span>
                    )}
                    {index === 0 && (
                      <Star className="h-4 w-4 text-amber-500 fill-amber-500" />
                    )}
                  </div>
                  {partner.description && (
                    <span className="text-sm text-gray-500">{partner.description}</span>
                  )}
                </div>
              </div>
              <ExternalLink className={`h-5 w-5 ${index === 0 ? 'text-blue-600' : 'text-gray-400'}`} />
            </a>
          ))}
        </div>
      </div>
      
      {/* Footer Tip */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
        <p className="text-xs text-gray-500 text-center flex items-center justify-center gap-1">
          <Clock className="h-3 w-3" />
          IRCTC bookings open 120 days in advance at 8:00 AM IST
        </p>
      </div>
    </div>
  )
}
