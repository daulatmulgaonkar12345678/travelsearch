'use client'

/**
 * BusSearchForm - Strict ID-Based Bus Search
 * ==========================================
 * 
 * ARCHITECTURE PRINCIPLE:
 * - User selection = STRICT, ID-based, immutable
 * - Route intelligence = FLEXIBLE, corridor-based, POST-selection only
 * - These two layers must NEVER mix
 * 
 * GUARD RULES:
 * 1. Search button DISABLED unless BOTH origin AND destination have place_id
 * 2. place_id is the ONLY source of truth - never resolve from text
 * 3. If origin === destination → BLOCK search
 * 4. Show clear error messages to guide user
 * 
 * This prevents the "Satara → Karad" becoming "Satara → Satara" bug.
 */

import { useState, useEffect } from 'react'
import { Calendar, Users, AlertCircle } from 'lucide-react'
import BusLocationAutocomplete, { BusPlace } from './BusLocationAutocomplete'

interface BusSearchFormProps {
  initialOrigin?: string
  initialDestination?: string
  initialDate?: string
  initialPassengers?: number
  initialBusType?: string
  onSearch?: (params: BusSearchParams) => void
}

export interface BusSearchParams {
  origin_place_id: string
  origin_name: string
  destination_place_id: string
  destination_name: string
  departure_date: string
  passengers: number
  bus_type?: string
}

export default function BusSearchForm({
  initialOrigin = '',
  initialDestination = '',
  initialDate,
  initialPassengers = 1,
  initialBusType = '',
  onSearch,
}: BusSearchFormProps) {
  // ============================================================
  // STATE - place_id IS THE SOURCE OF TRUTH
  // ============================================================
  
  // Origin
  const [originText, setOriginText] = useState(initialOrigin)
  const [originPlace, setOriginPlace] = useState<BusPlace | null>(null)
  
  // Destination
  const [destinationText, setDestinationText] = useState(initialDestination)
  const [destinationPlace, setDestinationPlace] = useState<BusPlace | null>(null)
  
  // Other fields
  const [busDate, setBusDate] = useState(initialDate || getTomorrowDate())
  const [busPassengers, setBusPassengers] = useState(initialPassengers)
  const [busType, setBusType] = useState(initialBusType)

  // ============================================================
  // VALIDATION - STRICT RULES
  // ============================================================
  
  /**
   * CRITICAL VALIDATION:
   * - Both origin AND destination MUST have valid place_id
   * - place_id must be different (can't search same place)
   * 
   * This prevents:
   * - Text-based resolution
   * - Fallback to origin
   * - Same city origin/destination
   */
  const originValid = originPlace !== null && originPlace.place_id !== ''
  const destinationValid = destinationPlace !== null && destinationPlace.place_id !== ''
  
  const isSamePlace = originPlace?.place_id === destinationPlace?.place_id && 
                      originPlace !== null && destinationPlace !== null
  
  const searchEnabled = originValid && destinationValid && !isSamePlace

  /**
   * Get the specific reason search is disabled
   * This helps users understand what they need to do
   */
  const getDisabledReason = (): string | null => {
    if (!originValid && !destinationValid) {
      return 'Select origin and destination from the dropdown'
    }
    if (!originValid) {
      return 'Select origin city from the dropdown'
    }
    if (!destinationValid) {
      return 'Select destination city from the dropdown'
    }
    if (isSamePlace) {
      return 'Origin and destination cannot be the same'
    }
    return null
  }

  const disabledReason = getDisabledReason()

  // ============================================================
  // HANDLERS
  // ============================================================

  const handleOriginChange = (text: string, place: BusPlace | null) => {
    setOriginText(text)
    setOriginPlace(place)
  }

  const handleDestinationChange = (text: string, place: BusPlace | null) => {
    setDestinationText(text)
    setDestinationPlace(place)
  }

  /**
   * Handle search submission
   * 
   * CRITICAL: Only proceeds if BOTH places have valid place_id
   * Uses place_id for API call, NOT text
   */
  const handleSearch = () => {
    // Double-check validation (belt and suspenders)
    if (!originPlace || !destinationPlace) {
      alert('Please select origin and destination from the dropdown')
      return
    }
    
    if (originPlace.place_id === destinationPlace.place_id) {
      alert('Origin and destination cannot be the same')
      return
    }
    
    // Validate date
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const searchDate = new Date(busDate)
    
    if (searchDate < today) {
      alert('Date cannot be in the past')
      return
    }

    // If callback provided, use it
    if (onSearch) {
      onSearch({
        origin_place_id: originPlace.place_id,
        origin_name: originPlace.name,
        destination_place_id: destinationPlace.place_id,
        destination_name: destinationPlace.name,
        departure_date: busDate,
        passengers: busPassengers,
        bus_type: busType || undefined,
      })
      return
    }

    // Default: Navigate to results page
    // CRITICAL: We pass the city NAME here for the backend
    // The backend normalizes it, but we've validated via place_id
    const params = new URLSearchParams({
      origin: originPlace.name,
      destination: destinationPlace.name,
      departure_date: busDate,
      passengers: busPassengers.toString(),
    })
    
    if (busType) {
      params.append('bus_type', busType)
    }
    
    window.location.href = `/buses/results?${params}`
  }

  return (
    <div className="space-y-4">
      {/* Origin/Destination Row */}
      <div className="grid md:grid-cols-2 gap-4">
        <BusLocationAutocomplete
          value={originText}
          selectedPlace={originPlace}
          onChange={handleOriginChange}
          label="From"
          testId="bus-origin"
          placeholder="Select city (e.g., Satara)"
          otherPlaceId={destinationPlace?.place_id || null}
        />
        <BusLocationAutocomplete
          value={destinationText}
          selectedPlace={destinationPlace}
          onChange={handleDestinationChange}
          label="To"
          testId="bus-destination"
          placeholder="Select city (e.g., Karad)"
          otherPlaceId={originPlace?.place_id || null}
        />
      </div>
      
      {/* Same place error */}
      {isSamePlace && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
          <p className="text-sm text-red-700">
            Origin and destination cannot be the same. Please select different cities.
          </p>
        </div>
      )}
      
      {/* Date, Type, Passengers Row */}
      <div className="grid md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="date"
              data-testid="bus-date"
              value={busDate}
              min={getTodayDate()}
              onChange={(e) => setBusDate(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Bus Type</label>
          <select
            data-testid="bus-type"
            value={busType}
            onChange={(e) => setBusType(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          >
            <option value="">All Types</option>
            <option value="non_ac">Non-AC</option>
            <option value="ac_seater">AC Seater</option>
            <option value="ac_sleeper">AC Sleeper</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Passengers</label>
          <div className="relative">
            <Users className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <select
              data-testid="bus-passengers"
              value={busPassengers}
              onChange={(e) => setBusPassengers(Number(e.target.value))}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            >
              {[1, 2, 3, 4, 5, 6].map(n => (
                <option key={n} value={n}>{n} Passenger{n > 1 ? 's' : ''}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      {/* Info Note */}
      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-sm text-amber-800">
          <strong>Note:</strong> Fares shown are average/estimated. We&apos;ll redirect you to redBus, AbhiBus, or Paytm for live availability & booking.
        </p>
      </div>
      
      {/* Search Button */}
      <div className="relative">
        <button
          data-testid="bus-search-button"
          onClick={handleSearch}
          disabled={!searchEnabled}
          className={`w-full font-semibold py-4 px-6 rounded-xl transition-colors shadow-lg ${
            searchEnabled
              ? 'bg-orange-600 hover:bg-orange-700 text-white hover:shadow-xl'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
          title={disabledReason || undefined}
        >
          Search Buses
        </button>
        {!searchEnabled && disabledReason && (
          <p className="text-center text-xs text-gray-500 mt-2 flex items-center justify-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {disabledReason}
          </p>
        )}
      </div>
    </div>
  )
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function getTodayDate(): string {
  return new Date().toISOString().split('T')[0]
}

function getTomorrowDate(): string {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return tomorrow.toISOString().split('T')[0]
}
