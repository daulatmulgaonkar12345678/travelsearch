/**
 * Save Search Button Component
 * 
 * Explicit user action to save a search for price alerts.
 * - Shows only after results load
 * - Asks for email if user is not logged in
 * - Stores in backend DB for price tracking
 * 
 * This is SEPARATE from Recent Searches (automatic localStorage).
 */

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bookmark, Check, Mail, X, Loader2 } from 'lucide-react'
import { apiFetch } from '@/lib/api'

interface SaveSearchButtonProps {
  searchParams: {
    origin: string
    destination: string
    departureDate: string
    returnDate?: string
    adults: number
    cabinClass: string
    tripType: string
  }
  lastKnownPrice?: number
  lastKnownCurrency?: string
  className?: string
}

export default function SaveSearchButton({
  searchParams,
  lastKnownPrice,
  lastKnownCurrency,
  className = ''
}: SaveSearchButtonProps) {
  const [isSaved, setIsSaved] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [email, setEmail] = useState('')
  const [emailError, setEmailError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const validateEmail = (email: string): boolean => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return re.test(email)
  }

  const handleSaveClick = () => {
    // Check if user is logged in (could check for auth token)
    const isLoggedIn = false // TODO: Check actual auth status
    
    if (!isLoggedIn) {
      setShowEmailModal(true)
    } else {
      submitSavedSearch(email)
    }
  }

  const submitSavedSearch = async (userEmail: string) => {
    if (!validateEmail(userEmail)) {
      setEmailError('Please enter a valid email address')
      return
    }

    setEmailError('')
    setIsLoading(true)

    try {
      const response = await apiFetch('/api/saved-searches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: userEmail,
          search: {
            origin: searchParams.origin,
            destination: searchParams.destination,
            departure_date: searchParams.departureDate,
            return_date: searchParams.returnDate,
            adults: searchParams.adults,
            cabin_class: searchParams.cabinClass,
            trip_type: searchParams.tripType,
          },
          last_known_price: lastKnownPrice,
          last_known_currency: lastKnownCurrency || 'INR',
        })
      })

      if (response.ok) {
        setIsSaved(true)
        setShowEmailModal(false)
        setSuccessMessage("Search saved. We'll notify you if prices change.")
        setTimeout(() => setSuccessMessage(''), 5000)
      } else {
        const error = await response.json()
        setEmailError(error.detail || 'Failed to save search')
      }
    } catch (err) {
      setEmailError('Failed to save search. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={`relative ${className}`}>
      {/* Main Save Button */}
      <motion.button
        onClick={handleSaveClick}
        disabled={isSaved || isLoading}
        whileTap={{ scale: 0.98 }}
        className={`
          flex items-center gap-2 px-4 py-2 text-sm rounded-lg
          transition-all duration-200
          ${isSaved
            ? 'text-green-700 bg-green-50 cursor-default'
            : 'text-gray-700 hover:text-blue-700 hover:bg-blue-50 border border-gray-200 hover:border-blue-300'
          }
        `}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : isSaved ? (
          <Check className="w-4 h-4" />
        ) : (
          <Bookmark className="w-4 h-4" />
        )}
        <span>{isSaved ? 'Saved' : 'Save this search'}</span>
      </motion.button>

      {/* Success Message */}
      <AnimatePresence>
        {successMessage && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="absolute top-full left-0 mt-2 px-3 py-2 bg-green-50 text-green-700 text-xs rounded-lg shadow-sm border border-green-200 whitespace-nowrap z-10"
          >
            {successMessage}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Email Modal */}
      <AnimatePresence>
        {showEmailModal && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowEmailModal(false)}
              className="fixed inset-0 bg-black/20 z-40"
            />
            
            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
              className="absolute top-full left-0 mt-2 p-4 bg-white rounded-xl shadow-lg border border-gray-200 z-50 w-72"
            >
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">Get price alerts</h4>
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              
              <p className="text-sm text-gray-600 mb-3">
                Enter your email to get notified when prices change for this route.
              </p>
              
              <div className="space-y-3">
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value)
                      setEmailError('')
                    }}
                    placeholder="your@email.com"
                    className="
                      w-full pl-10 pr-3 py-2 text-sm
                      border border-gray-200 rounded-lg
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                      placeholder:text-gray-400
                    "
                  />
                </div>
                
                {emailError && (
                  <p className="text-xs text-red-600">{emailError}</p>
                )}
                
                <button
                  onClick={() => submitSavedSearch(email)}
                  disabled={isLoading || !email}
                  className="
                    w-full py-2 px-4 text-sm font-medium
                    bg-blue-600 text-white rounded-lg
                    hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed
                    transition-colors duration-200
                    flex items-center justify-center gap-2
                  "
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    'Save & notify me'
                  )}
                </button>
                
                <p className="text-xs text-gray-500 text-center">
                  We respect your privacy. Unsubscribe anytime.
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
