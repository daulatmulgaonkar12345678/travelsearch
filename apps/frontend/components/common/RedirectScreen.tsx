'use client'

import { useEffect, useState } from 'react'
import { Plane, Building2, Lock } from 'lucide-react'

interface RedirectScreenProps {
  vendor: {
    name: string
    logo?: string
  }
  redirectUrl: string
  type: 'flight' | 'hotel'
  contextInfo?: {
    route?: string // "PNQ → DEL"
    hotelName?: string // "JW Marriott Pune"
  }
  onRedirectComplete?: () => void
}

export default function RedirectScreen({
  vendor,
  redirectUrl,
  type,
  contextInfo,
  onRedirectComplete
}: RedirectScreenProps) {
  const [progress, setProgress] = useState(0)
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)

  // Rotating messages based on type
  const flightMessages = [
    'Checking seat availability and final price…',
    'Confirming prices…',
    'Verifying seat options…',
    'Securing your redirect…',
  ]

  const hotelMessages = [
    'Checking room availability…',
    'Comparing final rates…',
    'Verifying booking options…',
    'Securing your redirect…',
  ]

  const messages = type === 'flight' ? flightMessages : hotelMessages

  // Randomized duration (1.5s - 3.5s)
  const duration = 1500 + Math.random() * 2000 + Math.random() * 600 - 300

  useEffect(() => {
    // Progress bar animation
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + (100 / (duration / 50))
      })
    }, 50)

    // Message rotation (every 800ms)
    const messageInterval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % messages.length)
    }, 800)

    // Redirect after duration completes
    const redirectTimeout = setTimeout(() => {
      try {
        window.location.href = redirectUrl
        onRedirectComplete?.()
      } catch (error) {
        console.error('Redirect error:', error)
        // Still try direct navigation
        window.location.href = redirectUrl
      }
    }, duration)

    return () => {
      clearInterval(progressInterval)
      clearInterval(messageInterval)
      clearTimeout(redirectTimeout)
    }
  }, [duration, redirectUrl, onRedirectComplete, messages.length])

  return (
    <div className="fixed inset-0 bg-white z-50 flex items-center justify-center">
      <div className="max-w-md w-full px-6 text-center">
        {/* Context Info */}
        {contextInfo && (
          <div className="text-sm text-gray-600 mb-8">
            {type === 'flight' && contextInfo.route && (
              <div className="font-semibold text-lg text-gray-900">{contextInfo.route}</div>
            )}
            {type === 'hotel' && contextInfo.hotelName && (
              <div className="font-semibold text-lg text-gray-900">{contextInfo.hotelName}</div>
            )}
          </div>
        )}

        {/* Animation Icon */}
        <div className="mb-8 flex justify-center">
          {type === 'flight' ? (
            <div className="animate-plane-redirect">
              <Plane className="h-16 w-16 text-blue-600" style={{ transform: 'rotate(90deg)' }} />
            </div>
          ) : (
            <div className="animate-pulse-subtle">
              <Building2 className="h-16 w-16 text-blue-600" />
            </div>
          )}
        </div>

        <style jsx>{`
          @keyframes plane-redirect {
            0%, 100% {
              transform: translateX(-10px) rotate(90deg);
              opacity: 0.8;
            }
            50% {
              transform: translateX(10px) rotate(90deg);
              opacity: 1;
            }
          }

          .animate-plane-redirect {
            animation: plane-redirect 1.5s ease-in-out infinite;
          }

          @keyframes pulse-subtle {
            0%, 100% {
              transform: scale(1);
              opacity: 1;
            }
            50% {
              transform: scale(1.05);
              opacity: 0.9;
            }
          }

          .animate-pulse-subtle {
            animation: pulse-subtle 2s ease-in-out infinite;
          }
        `}</style>

        {/* Main Message */}
        <div className="mb-6">
          <p className="text-gray-600 text-sm mb-3">We're taking you to</p>
          
          {/* Vendor Logo or Name */}
          {vendor.logo ? (
            <div className="flex justify-center mb-2">
              <img 
                src={vendor.logo} 
                alt={vendor.name}
                className="h-12 object-contain"
              />
            </div>
          ) : (
            <h2 className="text-3xl font-bold text-blue-600 mb-2">
              {vendor.name}
            </h2>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-100 ease-linear"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Rotating Status Message */}
        <div className="mb-6 min-h-[24px]">
          <p className="text-sm text-gray-700 animate-fade-in">
            {messages[currentMessageIndex]}
          </p>
        </div>

        {/* Trust Message */}
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
          <Lock className="h-4 w-4 text-green-600" />
          <span>Secure redirection</span>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Prices will be confirmed on the partner website
        </p>
      </div>
    </div>
  )
}
