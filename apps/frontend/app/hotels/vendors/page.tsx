'use client'

import { Suspense, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import { Hotel, MapPin, Star, Loader2, ExternalLink, Check } from 'lucide-react'
import { 
  getVendorsForService, 
  buildHotelDeepLink, 
  logAffiliateClick,
  type HotelDeepLinkParams 
} from '@/lib/affiliate'
import RedirectScreen from '@/components/common/RedirectScreen'

// Hotel-specific vendors
const HOTEL_VENDORS = getVendorsForService('hotels')

function HotelVendorsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [redirectUrl, setRedirectUrl] = useState<string>('')
  const [showRedirectScreen, setShowRedirectScreen] = useState(false)
  const [selectedVendor, setSelectedVendor] = useState<string>('booking')

  // Get hotel details from URL params
  const hotelName = searchParams.get('hotel_name') || ''
  const city = searchParams.get('city') || ''
  const price = searchParams.get('price') || '0'
  const currency = searchParams.get('currency') || 'INR'
  const checkIn = searchParams.get('check_in') || ''
  const checkOut = searchParams.get('check_out') || ''

  const handleVendorClick = async (vendorId: string) => {
    try {
      setRedirecting(vendorId)

      // Build deep link for selected vendor
      const params: HotelDeepLinkParams = {
        hotelName: hotelName || city,
        city,
        checkIn,
        checkOut,
        adults: 2,
        rooms: 1,
      }

      const finalRedirectUrl = buildHotelDeepLink(vendorId, params)

      // Log click asynchronously (fire-and-forget)
      logAffiliateClick(
        vendorId,
        `hotel-${city}`,
        `${hotelName}-${checkIn}`,
        parseFloat(price)
      ).catch(() => {})

      // Show redirect screen
      setRedirectUrl(finalRedirectUrl)
      setShowRedirectScreen(true)
    } catch (error) {
      console.error('Redirect error:', error)
      alert('Failed to redirect to vendor. Please try again.')
      setRedirecting(null)
    }
  }

  // Show redirect screen
  if (showRedirectScreen && redirectUrl) {
    const vendor = HOTEL_VENDORS.find(v => v.id === redirecting)
    return (
      <RedirectScreen
        vendor={{
          name: vendor?.name || 'Partner',
          logo: vendor?.logo
        }}
        redirectUrl={redirectUrl}
        type="hotel"
        contextInfo={{
          hotelName: hotelName || `Hotels in ${city}`
        }}
        onRedirectComplete={() => {
          setShowRedirectScreen(false)
          setRedirecting(null)
        }}
      />
    )
  }

  // Missing params
  if (!city || !checkIn || !checkOut) {
    return (
      <div className="min-h-screen bg-[#F5F1EB]">
        <Navigation />
        <div className="max-w-2xl mx-auto py-12 px-4 text-center">
          <Hotel className="w-16 h-16 text-yellow-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-[#1A1A1A] mb-2">Missing Hotel Information</h2>
          <p className="text-[#6B6B6B] mb-6">Please search for hotels first to view booking options.</p>
          <button
            onClick={() => router.push('/?tab=hotels')}
            className="px-6 py-3 bg-[#E6B54A] text-white rounded-lg hover:bg-[#D4A43C] transition-colors"
          >
            Search Hotels
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F5F1EB]">
      <Navigation />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Hotel Summary */}
        <div className="bg-white rounded-xl border border-[#E6E1D8] p-6 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-[#E6B54A]/10 rounded-lg flex items-center justify-center">
              <Hotel className="w-6 h-6 text-[#E6B54A]" />
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-semibold text-[#1A1A1A]">
                {hotelName || `Hotels in ${city}`}
              </h1>
              <div className="flex items-center gap-2 text-[#6B6B6B] mt-1">
                <MapPin className="w-4 h-4" />
                <span>{city}</span>
              </div>
              <div className="mt-2 text-sm text-[#6B6B6B]">
                {checkIn} → {checkOut}
              </div>
              {parseFloat(price) > 0 && (
                <div className="mt-2 text-lg font-semibold text-[#E6B54A]">
                  {currency} {parseFloat(price).toLocaleString()}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Vendor Selection */}
        <div className="bg-white rounded-xl border border-[#E6E1D8] p-6">
          <h2 className="text-lg font-semibold text-[#1A1A1A] mb-4">
            Choose Booking Partner
          </h2>
          <p className="text-sm text-[#6B6B6B] mb-6">
            Select a partner to complete your hotel booking. You&apos;ll be redirected to their site.
          </p>

          {/* Vendor Dropdown/List */}
          <div className="space-y-3 mb-6">
            {HOTEL_VENDORS.map((vendor) => (
              <button
                key={vendor.id}
                onClick={() => setSelectedVendor(vendor.id)}
                className={`w-full p-4 rounded-lg border-2 transition-all flex items-center justify-between ${
                  selectedVendor === vendor.id
                    ? 'border-[#E6B54A] bg-[#E6B54A]/5'
                    : 'border-[#E6E1D8] hover:border-[#E6B54A]/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    selectedVendor === vendor.id ? 'bg-[#E6B54A]' : 'bg-gray-100'
                  }`}>
                    <Hotel className={`w-5 h-5 ${selectedVendor === vendor.id ? 'text-white' : 'text-gray-500'}`} />
                  </div>
                  <span className="font-medium text-[#1A1A1A]">{vendor.name}</span>
                </div>
                {selectedVendor === vendor.id && (
                  <Check className="w-5 h-5 text-[#E6B54A]" />
                )}
              </button>
            ))}
          </div>

          {/* Book Button */}
          <button
            onClick={() => handleVendorClick(selectedVendor)}
            disabled={redirecting !== null}
            className="w-full py-4 bg-[#E6B54A] text-white rounded-lg font-semibold hover:bg-[#D4A43C] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {redirecting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Redirecting...
              </>
            ) : (
              <>
                <ExternalLink className="w-5 h-5" />
                Book on {HOTEL_VENDORS.find(v => v.id === selectedVendor)?.name}
              </>
            )}
          </button>

          <p className="text-xs text-[#6B6B6B] text-center mt-4">
            You&apos;ll be redirected to the partner site to complete your booking.
          </p>
        </div>
      </div>
    </div>
  )
}

export default function HotelVendorsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#F5F1EB] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#E6B54A]" />
      </div>
    }>
      <HotelVendorsContent />
    </Suspense>
  )
}
