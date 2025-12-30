'use client'

import { useEffect, useState, useRef, useMemo } from 'react'
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
  const hasRedirected = useRef(false)

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

  // Calculate duration once using useMemo - randomized between 1.5s - 3.5s
  const duration = useMemo(() => {
    return 1500 + Math.random() * 2000
  }, [])

  // Maximum safety timeout - absolute guarantee (5s max)
  const SAFETY_TIMEOUT = 5000

  useEffect(() => {
    let cancelled = false

    // Validate redirect URL
    if (!redirectUrl || redirectUrl.trim() === '') {
      console.error('Invalid redirect URL')
      alert('We couldn\'t open the partner site. Please try again or choose another partner.')
      return
    }

    // Fire-and-forget redirect function - Opens in NEW TAB for non-disruptive UX
    const performRedirect = () => {
      if (cancelled || hasRedirected.current) return
      
      hasRedirected.current = true
      
      try {
        // Call completion callback first (fire-and-forget)
        if (onRedirectComplete) {
          try {
            onRedirectComplete()
          } catch (err) {
            console.warn('Redirect callback error (non-blocking):', err)
          }
        }

        // Perform the actual redirect - ALWAYS open in new tab for user trust
        console.log('Opening partner site in new tab:', redirectUrl)
        window.open(redirectUrl, '_blank', 'noopener,noreferrer')
      } catch (error) {
        console.error('Redirect error:', error)
        // Last resort - try again with new tab
        try {
          window.open(redirectUrl, '_blank', 'noopener,noreferrer')
        } catch (finalError) {
          console.error('Final redirect attempt failed:', finalError)
          alert('Unable to open partner site. Please try again.')
        }
      }
    }

    // Progress bar animation
    const progressInterval = setInterval(() => {
      if (cancelled) return
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
      if (cancelled) return
      setCurrentMessageIndex((prev) => (prev + 1) % messages.length)
    }, 800)

    // Primary redirect timeout (after animation duration)
    const redirectTimeout = setTimeout(performRedirect, duration)

    // SAFETY NET: Absolute maximum timeout - guarantees redirect even if everything else fails
    const safetyTimeout = setTimeout(() => {
      if (!hasRedirected.current) {
        console.warn('Safety timeout triggered - forcing redirect')
        performRedirect()
      }
    }, SAFETY_TIMEOUT)

    // Cleanup function
    return () => {
      cancelled = true
      clearInterval(progressInterval)
      clearInterval(messageInterval)
      clearTimeout(redirectTimeout)
      clearTimeout(safetyTimeout)
    }
  }, [redirectUrl, duration, messages.length, onRedirectComplete])

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
