'use client'

import { Suspense, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import { Plane, ArrowRight, Loader2, ExternalLink, Calendar, Users, Check, AlertCircle } from 'lucide-react'
import { 
  getVendorsForService, 
  getPrimaryVendor,
  buildFlightDeepLink, 
  logAffiliateClick,
  type FlightDeepLinkParams 
} from '@/lib/affiliate'
import RedirectScreen from '@/components/common/RedirectScreen'
import ModifySearchButton from '@/components/search/ModifySearchButton'

// Flight-specific vendors only
const FLIGHT_VENDORS = getVendorsForService('flights')
const PRIMARY_VENDOR = getPrimaryVendor('flights')

function FlightVendorsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [redirectUrl, setRedirectUrl] = useState<string>('')
  const [showRedirectScreen, setShowRedirectScreen] = useState(false)
  // Use primary vendor as default
  const [selectedVendor, setSelectedVendor] = useState<string>(PRIMARY_VENDOR?.id || 'skyscanner')

  // Get search params
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const departureDate = searchParams.get('departure_date') || ''
  const returnDate = searchParams.get('return_date') || ''
  const price = searchParams.get('price') || '0'
  const currency = searchParams.get('currency') || 'INR'
  const adults = searchParams.get('adults') || '1'
  const children = searchParams.get('children') || '0'
  const infants = searchParams.get('infants') || '0'

  const handleVendorClick = async (vendorId: string) => {
    try {
      setRedirecting(vendorId)

      // Build deep link for selected vendor with validation
      const params: FlightDeepLinkParams = {
        origin,
        destination,
        departDate: departureDate,
        returnDate: returnDate || undefined,
        adults: parseInt(adults, 10),
        children: parseInt(children, 10),
        infants: parseInt(infants, 10),
      }

      const result = buildFlightDeepLink(vendorId, params)
      
      // BLOCK redirect if validation failed
      if (!result.url) {
        alert(`Cannot redirect: ${result.error}`)
        setRedirecting(null)
        return
      }

      // Log click asynchronously (fire-and-forget)
      logAffiliateClick(
        vendorId,
        `${origin}-${destination}`,
        `${origin}-${destination}-${departureDate}`,
        parseFloat(price)
      ).catch(() => {})

      // Show redirect screen
      setRedirectUrl(result.url)
      setShowRedirectScreen(true)
    } catch (error) {
      console.error('Redirect error:', error)
      alert('Failed to redirect to vendor. Please try again.')
      setRedirecting(null)
    }
  }

  // Show redirect screen
  if (showRedirectScreen && redirectUrl) {
    const vendor = FLIGHT_VENDORS.find(v => v.id === redirecting)
    return (
      <RedirectScreen
        vendor={{
          name: vendor?.name || 'Partner',
          logo: vendor?.logo
        }}
        redirectUrl={redirectUrl}
        type="flight"
        contextInfo={{
          route: `${origin} → ${destination}`
        }}
        onRedirectComplete={() => {
          setShowRedirectScreen(false)
          setRedirecting(null)
        }}
      />
    )
  }

  if (!origin || !destination) {
    return (
      <div className="min-h-screen bg-[#F5F1EB]">
        <Navigation />
        <div className="max-w-2xl mx-auto text-center py-12 px-4">
          <Plane className="w-16 h-16 text-blue-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-[#1A1A1A] mb-2">Missing Flight Details</h3>
          <p className="text-[#6B6B6B] mb-4">Unable to load flight information.</p>
          <button
            onClick={() => router.push('/?tab=flights')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Search Flights
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F5F1EB]">
      <Navigation />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Flight Summary with Modify Search */}
        <div className="bg-white rounded-xl border border-[#E6E1D8] p-6 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4 flex-1">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Plane className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xl font-semibold text-[#1A1A1A]">{origin}</span>
                  <ArrowRight className="w-5 h-5 text-[#6B6B6B]" />
                  <span className="text-xl font-semibold text-[#1A1A1A]">{destination}</span>
                </div>
                
                <div className="flex items-center gap-4 mt-2 text-sm text-[#6B6B6B]">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    <span>{departureDate}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    <span>{adults} adult{parseInt(adults) > 1 ? 's' : ''}</span>
                  </div>
                </div>
                
                {/* Estimated Price - same for all vendors */}
                {parseFloat(price) > 0 && (
                  <div className="mt-3">
                    <span className="text-lg font-semibold text-blue-600">
                      {currency} {parseFloat(price).toLocaleString()}
                    </span>
                    <span className="text-xs text-[#6B6B6B] ml-2">(estimated)</span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Modify Search Button */}
            <ModifySearchButton 
              service="flights"
              searchParams={{
                origin,
                destination,
                departure_date: departureDate,
                return_date: returnDate,
                adults,
                children,
                infants,
              }}
              variant="compact"
            />
          </div>
        </div>

        {/* Vendor Selection */}
        <div className="bg-white rounded-xl border border-[#E6E1D8] p-6">
          <h2 className="text-lg font-semibold text-[#1A1A1A] mb-4">
            Choose Flight Search Partner
          </h2>
          <p className="text-sm text-[#6B6B6B] mb-6">
            Select a partner to view available flights. You&apos;ll see flight results and can book on their site.
          </p>

          {/* Vendor List */}
          <div className="space-y-3 mb-6">
            {FLIGHT_VENDORS.map((vendor) => (
              <button
                key={vendor.id}
                onClick={() => setSelectedVendor(vendor.id)}
                className={`w-full p-4 rounded-lg border-2 transition-all flex items-center justify-between ${
                  selectedVendor === vendor.id
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-[#E6E1D8] hover:border-blue-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    selectedVendor === vendor.id ? 'bg-blue-600' : 'bg-gray-100'
                  }`}>
                    <Plane className={`w-5 h-5 ${selectedVendor === vendor.id ? 'text-white' : 'text-gray-500'}`} />
                  </div>
                  <span className="font-medium text-[#1A1A1A]">{vendor.name}</span>
                </div>
                {selectedVendor === vendor.id && (
                  <Check className="w-5 h-5 text-blue-600" />
                )}
              </button>
            ))}
          </div>

          {/* View Flights Button - vendor-specific label */}
          <button
            onClick={() => handleVendorClick(selectedVendor)}
            disabled={redirecting !== null}
            className="w-full py-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {redirecting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Redirecting...
              </>
            ) : (
              <>
                <ExternalLink className="w-5 h-5" />
                View flights on {FLIGHT_VENDORS.find(v => v.id === selectedVendor)?.name}
              </>
            )}
          </button>

          <p className="text-xs text-[#6B6B6B] text-center mt-4">
            You&apos;ll be redirected to the partner website to complete your booking.
          </p>
        </div>
      </div>
    </div>
  )
}

export default function FlightVendorsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#F5F1EB] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    }>
      <FlightVendorsContent />
    </Suspense>
  )
}
