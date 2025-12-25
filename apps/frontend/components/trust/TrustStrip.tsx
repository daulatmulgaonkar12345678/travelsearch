/**
 * Trust Strip - Appears below search component
 * Subtle, informative trust indicator
 * 
 * Design rules:
 * - No icons except checks (✓)
 * - Colors: gray-50, blue-50 only
 * - Animation: translateY ≤ 8px, duration 200-300ms
 */

'use client'

import { useEffect, useState } from 'react'

export default function TrustStrip() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div
      className={`
        w-full py-3 px-4 bg-blue-50 rounded-lg border border-blue-100
        transition-all duration-250 ease-out
        ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1.5'}
      `}
      style={{
        transitionProperty: 'opacity, transform',
      }}
    >
      <div className="max-w-4xl mx-auto flex items-center justify-center gap-2 text-center">
        <span className="text-green-600 text-sm">✓</span>
        <p className="text-sm text-gray-700">
          Compare prices from verified travel partners. Booking completed securely on partner websites.
        </p>
      </div>
    </div>
  )
}
