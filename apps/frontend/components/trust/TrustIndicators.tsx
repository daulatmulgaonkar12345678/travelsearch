/**
 * Trust Indicators - Horizontal row on results page
 * Staggered animation entrance
 */

'use client'

import { useEffect, useState } from 'react'
import { Check } from 'lucide-react'

const indicators = [
  'Transparent pricing',
  'No hidden fees',
  'Secure partner booking'
]

export default function TrustIndicators() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div className="flex flex-wrap items-center gap-4 md:gap-6 py-3 mb-4">
      {indicators.map((text, index) => (
        <div
          key={text}
          className={`
            flex items-center gap-1.5 text-sm text-gray-600
            transition-all duration-300 ease-out
            ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1'}
          `}
          style={{
            transitionDelay: `${index * 70}ms`,
            transitionProperty: 'opacity, transform',
          }}
        >
          <Check className="h-4 w-4 text-green-600 flex-shrink-0" />
          <span>{text}</span>
        </div>
      ))}
    </div>
  )
}
