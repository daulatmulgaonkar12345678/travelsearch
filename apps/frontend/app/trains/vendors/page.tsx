'use client'

import { Suspense, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import { Train, ArrowRight, Loader2, ExternalLink, Calendar, Check, AlertCircle } from 'lucide-react'
import { 
  getVendorsForService, 
  getPrimaryVendor,
  buildTrainDeepLink, 
  buildTrackedRedirectUrl,
  type TrainDeepLinkParams 
} from '@/lib/affiliate'
import RedirectScreen from '@/components/common/RedirectScreen'
import ModifySearchButton from '@/components/search/ModifySearchButton'

// Train-specific vendors only - Ixigo is PRIMARY
const TRAIN_VENDORS = getVendorsForService('trains')
const PRIMARY_VENDOR = getPrimaryVendor('trains')

function TrainVendorsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [redirectUrl, setRedirectUrl] = useState<string>('')
  const [showRedirectScreen, setShowRedirectScreen] = useState(false)
  const [selectedVendor, setSelectedVendor] = useState<string>(PRIMARY_VENDOR?.id || 'ixigo_trains')

  // Get search details from URL params
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const originCity = searchParams.get('origin_city') || origin
  const destinationCity = searchParams.get('destination_city') || destination
  const departureDate = searchParams.get('departure_date') || ''
  const price = searchParams.get('price') || '0'
  const currency = searchParams.get('currency') || 'INR'
  const trainName = searchParams.get('train_name') || ''
  const trainNumber = searchParams.get('train_number') || ''

  const handleVendorClick = async (vendorId: string) => {
    try {
      setRedirecting(vendorId)

      // Build deep link for selected vendor with validation
      const params: TrainDeepLinkParams = {
        fromStation: origin,
        toStation: destination,
        fromCity: originCity,
        toCity: destinationCity,
        date: departureDate,
      }

      const result = buildTrainDeepLink(vendorId, params)
      
      // BLOCK redirect if validation failed
      if (!result.url) {
        alert(`Cannot redirect: ${result.error}`)
        setRedirecting(null)
        return
      }

      // Build tracked redirect URL (logs click via /api/redirect)
      const trackedUrl = buildTrackedRedirectUrl({
        service: 'train',
        vendor: vendorId,
        targetUrl: result.url,
        origin,
        destination,
        date: departureDate,
        price: parseFloat(price),
      })

      // Show redirect screen with tracked URL
      setRedirectUrl(trackedUrl)
      setShowRedirectScreen(true)
    } catch (error) {
      console.error('Redirect error:', error)
      alert('Failed to redirect to vendor. Please try again.')
      setRedirecting(null)
    }
  }

  // Show redirect screen
  if (showRedirectScreen && redirectUrl) {
    const vendor = TRAIN_VENDORS.find(v => v.id === redirecting)
    return (
      <RedirectScreen
        vendor={{
          name: vendor?.name || 'Partner',
          logo: vendor?.logo
        }}
        redirectUrl={redirectUrl}
        type="train"
        contextInfo={{
          route: `${originCity} → ${destinationCity}`
        }}
        onRedirectComplete={() => {
          setShowRedirectScreen(false)
          setRedirecting(null)
        }}
      />
    )
  }

  if (!origin || !destination || !departureDate) {
    return (
      <div className="min-h-screen bg-[#FAF9F6]">
        <Navigation />
        <div className="max-w-2xl mx-auto text-center py-12 px-4">
          <Train className="w-16 h-16 text-[#7A8B5C] mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-[#1A1A1A] mb-2">Missing Train Details</h3>
          <p className="text-[#6B6B6B] mb-4">Unable to load train search information.</p>
          <button
            onClick={() => router.push('/?tab=trains')}
            className="px-6 py-3 bg-[#7A8B5C] text-white rounded-lg hover:bg-[#697A4C] transition-colors"
          >
            Search Trains
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#FAF9F6]">
      <Navigation />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Train Search Summary with Modify Search */}
        <div className="bg-white rounded-xl border border-[#E6E1D8] p-6 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4 flex-1">
              <div className="w-12 h-12 bg-[#EEF1E8] rounded-lg flex items-center justify-center">
                <Train className="w-6 h-6 text-[#7A8B5C]" />
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
                </div>
                
                {parseFloat(price) > 0 && (
                  <div className="mt-3">
                    <span className="text-lg font-semibold text-[#7A8B5C]">
                      {currency} {parseFloat(price).toLocaleString()}
                    </span>
                    <span className="text-xs text-[#6B6B6B] ml-2">(estimated)</span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Modify Search Button */}
            <ModifySearchButton 
              service="trains"
              searchParams={{
                origin_city: originCity,
                destination_city: destinationCity,
                departure_date: departureDate,
              }}
              variant="compact"
            />
          </div>
        </div>

        {/* Vendor Selection */}
        <div className="bg-white rounded-xl border border-[#E6E1D8] p-6">
          <h2 className="text-lg font-semibold text-[#1A1A1A] mb-4">
            Choose Train Availability Partner
          </h2>
          <p className="text-sm text-[#6B6B6B] mb-6">
            Select a partner to check seat availability. Login, CAPTCHA, and booking will happen on their site.
          </p>

          {/* Vendor List */}
          <div className="space-y-3 mb-6">
            {TRAIN_VENDORS.map((vendor) => (
              <button
                key={vendor.id}
                onClick={() => setSelectedVendor(vendor.id)}
                className={`w-full p-4 rounded-lg border-2 transition-all flex items-center justify-between ${
                  selectedVendor === vendor.id
                    ? 'border-[#7A8B5C] bg-[#EEF1E8]'
                    : 'border-[#E6E1D8] hover:border-[#7A8B5C]/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    selectedVendor === vendor.id ? 'bg-[#7A8B5C]' : 'bg-gray-100'
                  }`}>
                    <Train className={`w-5 h-5 ${selectedVendor === vendor.id ? 'text-white' : 'text-gray-500'}`} />
                  </div>
                  <span className="font-medium text-[#1A1A1A]">{vendor.name}</span>
                </div>
                {selectedVendor === vendor.id && (
                  <Check className="w-5 h-5 text-[#7A8B5C]" />
                )}
              </button>
            ))}
          </div>

          {/* Check Availability Button - NOT "Book Now" */}
          <button
            onClick={() => handleVendorClick(selectedVendor)}
            disabled={redirecting !== null}
            className="w-full py-4 bg-[#7A8B5C] text-white rounded-lg font-semibold hover:bg-[#697A4C] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {redirecting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Redirecting...
              </>
            ) : (
              <>
                <ExternalLink className="w-5 h-5" />
                Check availability on {TRAIN_VENDORS.find(v => v.id === selectedVendor)?.name}
              </>
            )}
          </button>

          {/* Pricing Disclaimer */}
          <div className="flex items-start gap-2 mt-4 p-3 bg-[#F9F7F4] rounded-lg">
            <AlertCircle className="w-4 h-4 text-[#6B6B6B] flex-shrink-0 mt-0.5" />
            <p className="text-xs text-[#6B6B6B]">
              Final price is shown on partner website. Prices may vary based on availability and booking time.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function TrainVendorsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#FAF9F6] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#7A8B5C]" />
      </div>
    }>
      <TrainVendorsContent />
    </Suspense>
  )
}
