'use client'

import { Suspense, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import { Bus, ArrowRight, Loader2, ExternalLink, Calendar, Check, AlertCircle } from 'lucide-react'
import { 
  getVendorsForService, 
  getPrimaryVendor,
  buildBusDeepLink, 
  logAffiliateClick,
  type BusDeepLinkParams 
} from '@/lib/affiliate'
import RedirectScreen from '@/components/common/RedirectScreen'
import ModifySearchButton from '@/components/search/ModifySearchButton'

// Bus-specific vendors only - redBus is PRIMARY
const BUS_VENDORS = getVendorsForService('buses')
const PRIMARY_VENDOR = getPrimaryVendor('buses')

function BusVendorsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [redirectUrl, setRedirectUrl] = useState<string>('')
  const [showRedirectScreen, setShowRedirectScreen] = useState(false)
  const [selectedVendor, setSelectedVendor] = useState<string>(PRIMARY_VENDOR?.id || 'redbus')

  // Get search details from URL params
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const departureDate = searchParams.get('departure_date') || ''
  const price = searchParams.get('price') || '0'
  const currency = searchParams.get('currency') || 'INR'
  const busType = searchParams.get('bus_type') || ''
  const operator = searchParams.get('operator') || ''

  const handleVendorClick = async (vendorId: string) => {
    try {
      setRedirecting(vendorId)

      // Build deep link for selected vendor with validation
      const params: BusDeepLinkParams = {
        fromCity: origin,
        toCity: destination,
        date: departureDate,
      }

      const result = buildBusDeepLink(vendorId, params)
      
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
        `bus-${origin}-${destination}-${departureDate}`,
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
    const vendor = BUS_VENDORS.find(v => v.id === redirecting)
    return (
      <RedirectScreen
        vendor={{
          name: vendor?.name || 'Partner',
          logo: vendor?.logo
        }}
        redirectUrl={redirectUrl}
        type="bus"
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

  if (!origin || !destination || !departureDate) {
    return (
      <div className="min-h-screen bg-[#FAF9F6]">
        <Navigation />
        <div className="max-w-2xl mx-auto text-center py-12 px-4">
          <Bus className="w-16 h-16 text-[#C47A4A] mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-[#1A1A1A] mb-2">Missing Bus Details</h3>
          <p className="text-[#6B6B6B] mb-4">Unable to load bus search information.</p>
          <button
            onClick={() => router.push('/?tab=buses')}
            className="px-6 py-3 bg-[#C47A4A] text-white rounded-lg hover:bg-[#B06A3A] transition-colors"
          >
            Search Buses
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#FAF9F6]">
      <Navigation />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Bus Search Summary with Modify Search */}
        <div className="bg-white rounded-xl border border-[#E6E1D8] p-6 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4 flex-1">
              <div className="w-12 h-12 bg-[#F9EDE6] rounded-lg flex items-center justify-center">
                <Bus className="w-6 h-6 text-[#C47A4A]" />
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
                    <span className="text-lg font-semibold text-[#C47A4A]">
                      {currency} {parseFloat(price).toLocaleString()}
                    </span>
                    <span className="text-xs text-[#6B6B6B] ml-2">(estimated)</span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Modify Search Button */}
            <ModifySearchButton 
              service="buses"
              searchParams={{
                origin_city: origin,
                destination_city: destination,
                departure_date: departureDate,
              }}
              variant="compact"
            />
          </div>
        </div>

        {/* Vendor Selection */}
        <div className="bg-white rounded-xl border border-[#E6E1D8] p-6">
          <h2 className="text-lg font-semibold text-[#1A1A1A] mb-4">
            Choose Bus Search Partner
          </h2>
          <p className="text-sm text-[#6B6B6B] mb-6">
            Select a partner to view available buses. Seat selection and payment will happen on their site.
          </p>

          {/* Vendor List */}
          <div className="space-y-3 mb-6">
            {BUS_VENDORS.map((vendor) => (
              <button
                key={vendor.id}
                onClick={() => setSelectedVendor(vendor.id)}
                className={`w-full p-4 rounded-lg border-2 transition-all flex items-center justify-between ${
                  selectedVendor === vendor.id
                    ? 'border-[#C47A4A] bg-[#F9EDE6]'
                    : 'border-[#E6E1D8] hover:border-[#C47A4A]/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    selectedVendor === vendor.id ? 'bg-[#C47A4A]' : 'bg-gray-100'
                  }`}>
                    <Bus className={`w-5 h-5 ${selectedVendor === vendor.id ? 'text-white' : 'text-gray-500'}`} />
                  </div>
                  <span className="font-medium text-[#1A1A1A]">{vendor.name}</span>
                </div>
                {selectedVendor === vendor.id && (
                  <Check className="w-5 h-5 text-[#C47A4A]" />
                )}
              </button>
            ))}
          </div>

          {/* View Buses Button - NOT "Book Now" */}
          <button
            onClick={() => handleVendorClick(selectedVendor)}
            disabled={redirecting !== null}
            className="w-full py-4 bg-[#C47A4A] text-white rounded-lg font-semibold hover:bg-[#B06A3A] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {redirecting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Redirecting...
              </>
            ) : (
              <>
                <ExternalLink className="w-5 h-5" />
                View Buses on {BUS_VENDORS.find(v => v.id === selectedVendor)?.name}
              </>
            )}
          </button>

          <p className="text-xs text-[#6B6B6B] text-center mt-4">
            You&apos;ll see bus search results with your route and date prefilled.
          </p>
        </div>
      </div>
    </div>
  )
}

export default function BusVendorsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#FAF9F6] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#C47A4A]" />
      </div>
    }>
      <BusVendorsContent />
    </Suspense>
  )
}
