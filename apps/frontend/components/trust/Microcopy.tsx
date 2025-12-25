/**
 * UX Microcopy Components
 * Small, informative text near key actions
 */

'use client'

/**
 * Below search button: "Free to use • No signup required"
 */
export function SearchButtonMicrocopy() {
  return (
    <p className="text-xs text-gray-500 text-center mt-2 transition-opacity duration-200 hover:opacity-80">
      Free to use • No signup required
    </p>
  )
}

/**
 * Near booking/select button: Provider redirect notice
 */
export function BookingRedirectMicrocopy() {
  return (
    <p className="text-xs text-gray-500 mt-1.5 transition-opacity duration-200">
      You'll complete booking on the provider's website
    </p>
  )
}

/**
 * Above results: Price comparison notice
 */
export function PriceComparisonNotice() {
  return (
    <div className="mb-4 animate-[fadeIn_0.3s_ease-out]">
      <p className="text-sm text-gray-600">
        Prices may vary by provider. Compare duration, stops, and total cost before booking.
      </p>
    </div>
  )
}

/**
 * Below results: Platform explanation
 */
export function PlatformExplanation() {
  return (
    <div 
      className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200 animate-[fadeIn_0.3s_ease-out]"
      style={{ animationDelay: '150ms' }}
    >
      <p className="text-sm text-gray-700 leading-relaxed">
        TravelSearch compares flight options across multiple booking platforms. When you select 
        a flight, you'll be redirected to the provider's website to complete your booking securely.
      </p>
    </div>
  )
}
