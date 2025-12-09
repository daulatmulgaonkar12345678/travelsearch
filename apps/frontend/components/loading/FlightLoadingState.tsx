'use client'

import { useState, useEffect } from 'react'
import { Plane, Lock } from 'lucide-react'

interface FlightLoadingStateProps {
  origin?: string
  destination?: string
}

export default function FlightLoadingState({ origin, destination }: FlightLoadingStateProps) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)

  const messages = [
    '✈️ Searching 400+ airlines…',
    '🔍 Finding the best fares for you…',
    '🛫 Checking real-time prices…',
    '💰 Comparing prices from trusted partners…',
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % messages.length)
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-[600px] flex flex-col items-center justify-center px-4 py-12">
      {/* Route Display */}
      {origin && destination && (
        <div className="text-center mb-8">
          <div className="text-2xl font-semibold text-gray-900">
            {origin} → {destination}
          </div>
        </div>
      )}

      {/* Animated Plane Route */}
      <div className="relative w-full max-w-md mb-12">
        {/* Dotted line */}
        <div className="absolute top-1/2 left-0 right-0 border-t-2 border-dashed border-gray-300"></div>
        
        {/* Animated Plane */}
        <div className="relative w-full">
          <div className="animate-plane">
            <Plane className="h-8 w-8 text-blue-600" style={{ transform: 'rotate(90deg)' }} />
          </div>
        </div>

        <style jsx>{`
          @keyframes plane-flight {
            0% {
              left: 0%;
              transform: translateX(0);
            }
            100% {
              left: 100%;
              transform: translateX(-100%);
            }
          }

          .animate-plane {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            animation: plane-flight 3s ease-in-out infinite;
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

      {/* Skeleton Flight Cards */}
      <div className="w-full max-w-4xl space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse"
          >
            <div className="flex items-center justify-between">
              {/* Left side skeleton */}
              <div className="flex-1 space-y-3">
                <div className="h-4 bg-gray-200 rounded w-32"></div>
                <div className="h-6 bg-gray-200 rounded w-48"></div>
                <div className="h-3 bg-gray-200 rounded w-24"></div>
              </div>

              {/* Middle skeleton */}
              <div className="flex-1 text-center space-y-3">
                <div className="h-3 bg-gray-200 rounded w-20 mx-auto"></div>
                <div className="h-8 bg-gray-200 rounded w-16 mx-auto"></div>
              </div>

              {/* Right side skeleton */}
              <div className="flex-1 flex flex-col items-end space-y-3">
                <div className="h-8 bg-gray-200 rounded w-24"></div>
                <div className="h-3 bg-gray-200 rounded w-32"></div>
                <div className="h-10 bg-gray-200 rounded w-28"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
