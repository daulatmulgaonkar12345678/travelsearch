/**
 * Track Price Feature
 * Lightweight email-only price tracking (localStorage)
 */

'use client'

import { useState } from 'react'

interface TrackPriceProps {
  origin: string
  destination: string
  departureDate: string
  returnDate?: string
}

export default function TrackPrice({ origin, destination, departureDate, returnDate }: TrackPriceProps) {
  const [showModal, setShowModal] = useState(false)
  const [email, setEmail] = useState('')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  const handleSave = () => {
    // Simple email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address')
      return
    }

    // Save to localStorage
    const trackData = {
      origin,
      destination,
      departureDate,
      returnDate,
      email,
      timestamp: new Date().toISOString()
    }

    const existing = localStorage.getItem('tracked_prices') || '[]'
    const tracked = JSON.parse(existing)
    tracked.push(trackData)
    localStorage.setItem('tracked_prices', JSON.stringify(tracked))

    setSaved(true)
    setTimeout(() => {
      setShowModal(false)
      setSaved(false)
      setEmail('')
    }, 1500)
  }

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-all duration-200 active:scale-[0.98]"
      >
        <span>Track price</span>
      </button>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-[fadeIn_0.2s_ease-out]">
          <div
            className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6 animate-[scaleIn_0.2s_ease-out]"
            style={{
              animation: 'scaleIn 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
            }}
          >
            {/* Close button */}
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-full transition-colors text-gray-500 text-lg leading-none"
              aria-label="Close"
            >
              ×
            </button>

            {/* Content */}
            {!saved ? (
              <>
                <div className="mb-4">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    Track price
                  </h3>
                  <p className="text-sm text-gray-600">
                    Get notified when prices change for this route.
                  </p>
                </div>

                {/* Route info */}
                <div className="mb-4 p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
                  <p className="font-medium">{origin} → {destination}</p>
                  <p className="text-xs text-gray-600 mt-1">
                    {departureDate} {returnDate && `• ${returnDate}`}
                  </p>
                </div>

                {/* Email input */}
                <div className="mb-4">
                  <label htmlFor="track-email" className="block text-sm font-medium text-gray-700 mb-1">
                    Your email
                  </label>
                  <input
                    id="track-email"
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value)
                      setError('')
                    }}
                    placeholder="email@example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                  />
                  {error && (
                    <p className="text-xs text-red-600 mt-1">{error}</p>
                  )}
                </div>

                {/* Note */}
                <p className="text-xs text-gray-500 mb-4">
                  Price tracking is stored locally. Upgrade to real notifications coming soon.
                </p>

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors active:scale-[0.98]"
                  >
                    Save
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-gray-50 rounded-full mb-4">
                  <span className="text-green-600 text-2xl">✓</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Tracking saved
                </h3>
                <p className="text-sm text-gray-600">
                  You'll be notified when prices change for this route.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </>
  )
}
