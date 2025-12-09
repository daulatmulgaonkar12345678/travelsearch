'use client'

import { Suspense, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import { Hotel, MapPin, Star, Loader2, ExternalLink } from 'lucide-react'
import { HOTEL_VENDORS } from '@/lib/vendors'
import { API_BASE_URL } from '@/lib/config'
import RedirectScreen from '@/components/common/RedirectScreen'

function HotelVendorsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [redirectUrl, setRedirectUrl] = useState<string>('')
  const [showRedirectScreen, setShowRedirectScreen] = useState(false)

  // Get hotel details from URL params
  const hotelName = searchParams.get('hotel_name') || ''
  const city = searchParams.get('city') || ''
  const price = searchParams.get('price') || '0'
  const currency = searchParams.get('currency') || 'INR'
  const checkIn = searchParams.get('check_in') || ''
  const checkOut = searchParams.get('check_out') || ''

  const handleVendorClick = async (vendorId: string) => {
    if (vendorId !== 'aviasales') {
      alert(`${vendorId} integration coming soon!`)
      return
    }

    try {
      setRedirecting(vendorId)

      // For hotels, we'll use a simple redirect for now
      // In production, you'd build a proper hotel deep-link
      const baseUrl = 'https://aviasales.tpx.lt/eqOxwsZu'
      const params = new URLSearchParams({
        marker: '689331',
        city: city,
        checkIn: checkIn,
        checkOut: checkOut,
      })

      const finalRedirectUrl = `${baseUrl}?${params.toString()}`
      
      // Show redirect screen instead of immediate redirect
      setRedirectUrl(finalRedirectUrl)
      setShowRedirectScreen(true)
    } catch (error) {
      console.error('Redirect error:', error)
      alert('Failed to redirect to vendor. Please try again.')
      setRedirecting(null)
    }
  }

  if (!hotelName || !city) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-yellow-900 mb-2">Missing Hotel Details</h3>
          <p className="text-yellow-700 mb-4">Unable to load hotel information.</p>
          <button
            onClick={() => router.push('/hotels')}
            className="px-6 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
          >
            Back to Search
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hotel Details Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Selected Hotel</h2>
        
        <div className="mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{hotelName}</h3>
              <div className="flex items-center text-gray-600">
                <MapPin className="h-5 w-5 mr-2" />
                <span>{city}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
            <div>
              <div className="text-sm text-gray-600 mb-1">Check-in</div>
              <div className="font-semibold text-gray-900">{checkIn}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Check-out</div>
              <div className="font-semibold text-gray-900">{checkOut}</div>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Total Price</div>
              <div className="text-3xl font-bold text-gray-900">
                {currency} {parseFloat(price).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Vendor Selection */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Choose Your Booking Platform</h3>
        <p className="text-gray-600 mb-6">
          Select a vendor to complete your booking. You'll be redirected to their website.
        </p>

        <div className="space-y-3">
          {HOTEL_VENDORS.map((vendor) => {
            const isActive = vendor.type === 'real'
            const isRedirecting = redirecting === vendor.id

            return (
              <button
                key={vendor.id}
                onClick={() => handleVendorClick(vendor.id)}
                disabled={!isActive || isRedirecting}
                className={`
                  w-full p-4 rounded-lg border-2 transition-all text-left
                  ${isActive
                    ? 'border-blue-600 bg-blue-50 hover:bg-blue-100 cursor-pointer'
                    : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                  }
                  ${isRedirecting ? 'opacity-50' : ''}
                `}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div>
                        <div className="font-semibold text-gray-900">{vendor.name}</div>
                        <div className="text-sm text-gray-600">{vendor.description}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {isActive && (
                      <div className="text-right">
                        <div className="text-lg font-bold text-gray-900">
                          {currency} {parseFloat(price).toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-600">Same price</div>
                      </div>
                    )}
                    
                    {isRedirecting ? (
                      <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                    ) : isActive ? (
                      <div className="flex items-center space-x-2 text-blue-600">
                        <span className="font-semibold">Book Now</span>
                        <ExternalLink className="h-5 w-5" />
                      </div>
                    ) : (
                      <span className="text-sm font-semibold text-gray-500 px-3 py-1 bg-gray-200 rounded-full">
                        Coming Soon
                      </span>
                    )}
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-900">
            <strong>Note:</strong> You'll be redirected to the vendor's website to complete your booking. 
            Prices and availability are subject to change.
          </p>
        </div>
      </div>

      <div className="mt-6 text-center">
        <button
          onClick={() => router.back()}
          className="text-blue-600 hover:text-blue-700 font-semibold"
        >
          ← Back to Results
        </button>
      </div>
    </div>
  )
}

export default function HotelVendorsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        <Suspense fallback={
          <div className="flex items-center justify-center min-h-[400px]">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
          </div>
        }>
          <HotelVendorsContent />
        </Suspense>
      </main>
    </div>
  )
}
