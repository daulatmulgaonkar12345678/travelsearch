/**
 * Trust Strip - Appears below search component
 * Subtle, informative trust indicator
 */

'use client'

import { useEffect, useState } from 'react'
import { Lock } from 'lucide-react'

export default function TrustStrip() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div
      className={`
        w-full py-3 px-4 bg-blue-50 rounded-lg border border-blue-100
        transition-all duration-300 ease-out
        ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1.5'}
      `}
      style={{
        transitionProperty: 'opacity, transform',
      }}
    >
      <div className="max-w-4xl mx-auto flex items-center justify-center gap-2 text-center">
        <Lock className="h-4 w-4 text-blue-600 flex-shrink-0" />
        <p className="text-sm text-gray-700">
          Compare prices from verified travel partners. Booking completed securely on partner websites.
        </p>
      </div>
    </div>
  )
}
