/**
 * Save Search Feature
 * localStorage-based (last 3 searches)
 */

'use client'

import { useState, useEffect } from 'react'

interface SaveSearchProps {
  searchParams: {
    origin: string
    destination: string
    departureDate: string
    returnDate?: string
    tripType?: string
  }
}

export default function SaveSearch({ searchParams }: SaveSearchProps) {
  const [isSaved, setIsSaved] = useState(false)
  const [showFeedback, setShowFeedback] = useState(false)

  useEffect(() => {
    // Check if this search is already saved
    const saved = localStorage.getItem('saved_searches') || '[]'
    const searches = JSON.parse(saved)
    const exists = searches.some((s: any) => 
      s.origin === searchParams.origin && 
      s.destination === searchParams.destination &&
      s.departureDate === searchParams.departureDate
    )
    setIsSaved(exists)
  }, [searchParams])

  const handleSave = () => {
    const saved = localStorage.getItem('saved_searches') || '[]'
    let searches = JSON.parse(saved)

    if (isSaved) {
      // Remove
      searches = searches.filter((s: any) => 
        !(s.origin === searchParams.origin && 
          s.destination === searchParams.destination &&
          s.departureDate === searchParams.departureDate)
      )
      setIsSaved(false)
    } else {
      // Add (keep only last 3)
      searches.unshift({
        ...searchParams,
        savedAt: new Date().toISOString()
      })
      searches = searches.slice(0, 3)
      setIsSaved(true)
      setShowFeedback(true)
      setTimeout(() => setShowFeedback(false), 2000)
    }

    localStorage.setItem('saved_searches', JSON.stringify(searches))
  }

  return (
    <div className="relative">
      <button
        onClick={handleSave}
        className={`
          flex items-center gap-2 px-4 py-2 text-sm rounded-lg 
          transition-all duration-200
          active:scale-[0.98]
          ${isSaved 
            ? 'text-blue-700 bg-blue-50 hover:bg-blue-100' 
            : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
          }
        `}
        style={{
          transitionProperty: 'background-color, color, transform',
        }}
      >
        <span>{isSaved ? '✓ Saved' : 'Save search'}</span>
      </button>

      {/* Success feedback */}
      {showFeedback && (
        <div
          className="absolute top-full left-0 mt-2 px-3 py-1.5 bg-gray-50 text-gray-700 text-xs rounded-lg shadow-sm border border-gray-200 whitespace-nowrap animate-[fadeInUp_0.2s_ease-out]"
        >
          Search saved
        </div>
      )}

      <style jsx>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
