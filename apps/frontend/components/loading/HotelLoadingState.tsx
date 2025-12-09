'use client'

import { useState, useEffect } from 'react'
import { Building2, Lock } from 'lucide-react'

interface HotelLoadingStateProps {
  city?: string
}

export default function HotelLoadingState({ city }: HotelLoadingStateProps) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)

  const messages = [
    '🏨 Finding best stays…',
    '🛏️ Comparing hotel prices…',
    '⭐ Checking top-rated properties…',
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % messages.length)
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-[600px] flex flex-col items-center justify-center px-4 py-12">
      {/* City Display */}
      {city && (
        <div className="text-center mb-8">
          <div className="text-2xl font-semibold text-gray-900">
            Searching in {city}
          </div>
        </div>
      )}

      {/* Animated Hotel Icon */}
      <div className="relative mb-12">
        <div className="animate-bounce-subtle">
          <Building2 className="h-16 w-16 text-blue-600" />
        </div>

        <style jsx>{`
          @keyframes bounce-subtle {
            0%, 100% {
              transform: translateY(0);
              opacity: 1;
            }
            50% {
              transform: translateY(-10px);
              opacity: 0.8;
            }
          }

          .animate-bounce-subtle {
            animation: bounce-subtle 2s ease-in-out infinite;
          }
        `}</style>
      </div>

      {/* Rotating Status Text */}
      <div className="text-center mb-12">
        <div className="text-lg font-medium text-gray-700 h-8 flex items-center justify-center transition-opacity duration-300">
          {messages[currentMessageIndex]}
        </div>
      </div>

      {/* Trust Message */}
      <div className="flex items-start space-x-2 text-sm text-gray-600 max-w-md text-center mb-12">
        <Lock className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />
        <div>
          <div className="font-medium text-gray-700">Prices shown are final and include taxes</div>
          <div className="text-gray-500 mt-1">We redirect you securely to official partners</div>
        </div>
      </div>

      {/* Skeleton Hotel Cards */}
      <div className="w-full max-w-4xl space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-white rounded-lg border border-gray-200 overflow-hidden animate-pulse"
          >
            <div className="flex">
              {/* Image skeleton */}
              <div className="w-48 h-48 bg-gray-200 flex-shrink-0"></div>

              {/* Content skeleton */}
              <div className="flex-1 p-4 space-y-3">
                <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                <div className="flex items-center justify-between mt-4">
                  <div className="h-4 bg-gray-200 rounded w-24"></div>
                  <div className="h-8 bg-gray-200 rounded w-32"></div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
