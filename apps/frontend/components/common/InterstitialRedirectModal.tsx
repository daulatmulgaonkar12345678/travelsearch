'use client'

import { useEffect, useState } from 'react'
import { ExternalLink, X } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

interface InterstitialRedirectModalProps {
  isOpen: boolean
  provider: string
  price: number
  currency: string
  redirectUrl: string
  onClose: () => void
  countdownSeconds?: number
}

export default function InterstitialRedirectModal({
  isOpen,
  provider,
  price,
  currency,
  redirectUrl,
  onClose,
  countdownSeconds = 3
}: InterstitialRedirectModalProps) {
  const [countdown, setCountdown] = useState(countdownSeconds)
  const [redirecting, setRedirecting] = useState(false)

  useEffect(() => {
    if (!isOpen) {
      setCountdown(countdownSeconds)
      setRedirecting(false)
      return
    }

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          setRedirecting(true)
          // Redirect after countdown
          setTimeout(() => {
            window.location.href = redirectUrl
          }, 500)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [isOpen, redirectUrl, countdownSeconds])

  if (!isOpen) return null

  const handleManualRedirect = () => {
    setRedirecting(true)
    window.open(redirectUrl, '_blank')
  }

  return (
    <div
      data-testid="interstitial-modal"
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="interstitial-title"
    >
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 relative animate-scale-in">
        {/* Close Button */}
        <button
          data-testid="close-interstitial"
          onClick={onClose}
          className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-lg transition-colors"
          aria-label="Close modal"
        >
          <X className="h-5 w-5 text-gray-500" />
        </button>

        {/* Icon */}
        <div className="flex justify-center mb-6">
          <div className="h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center">
            <ExternalLink className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        {/* Content */}
        <div className="text-center">
          <h2 id="interstitial-title" className="text-2xl font-bold text-gray-900 mb-2">
            Redirecting to {provider}
          </h2>
          <p className="text-gray-600 mb-6">
            You're being redirected to complete your booking
          </p>

          {/* Price Summary */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="text-sm text-gray-600 mb-1">Total Price</div>
            <div className="text-3xl font-bold text-gray-900">
              {formatCurrency(price, currency)}
            </div>
          </div>

          {/* Countdown or Redirecting */}
          {redirecting ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="text-gray-700 font-medium">Redirecting...</span>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-4xl font-bold text-blue-600" aria-live="polite">
                {countdown}
              </div>
              <p className="text-sm text-gray-500">
                Redirecting in {countdown} second{countdown !== 1 ? 's' : ''}...
              </p>
            </div>
          )}

          {/* Manual Redirect Fallback */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-3">
              Not redirecting automatically?
            </p>
            <button
              data-testid="manual-redirect"
              onClick={handleManualRedirect}
              className="text-blue-600 hover:text-blue-700 font-medium text-sm underline"
            >
              Click here to open link
            </button>
          </div>

          {/* Transparency Note */}
          <div className="mt-6 p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-gray-600">
              <strong>100% Transparent:</strong> We never add fees. The price shown is what you'll pay on {provider}.
            </p>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes scale-in {
          from {
            transform: scale(0.9);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }
        .animate-scale-in {
          animation: scale-in 0.2s ease-out;
        }
      `}</style>
    </div>
  )
}
