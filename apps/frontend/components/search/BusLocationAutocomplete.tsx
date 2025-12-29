'use client'

/**
 * BusLocationAutocomplete - ID-Based Selection Only
 * ==================================================
 * 
 * CRITICAL ARCHITECTURE RULES:
 * 1. User selection = STRICT, ID-based, immutable
 * 2. Route intelligence = FLEXIBLE, corridor-based, POST-selection only
 * 3. These two layers must NEVER mix
 * 
 * FORBIDDEN BEHAVIORS:
 * - ❌ DO NOT resolve from text
 * - ❌ DO NOT fallback to origin when destination not selected
 * - ❌ DO NOT guess nearest city
 * - ❌ DO NOT use corridor logic during selection
 * - ❌ DO NOT allow search without dropdown selection
 * 
 * This component ensures user intent is PRESERVED EXACTLY.
 * "Satara → Karad" MUST stay "Satara → Karad", never "Satara → Satara"
 */

import { useState, useEffect, useRef } from 'react'
import { Bus, MapPin, AlertCircle, Check, Loader2 } from 'lucide-react'
import { apiFetch } from '@/lib/api'

// ============================================================
// STRICT PLACE OBJECT - ID IS THE SOURCE OF TRUTH
// ============================================================
export interface BusPlace {
  place_id: string       // UNIQUE - The ONLY source of truth
  name: string           // Display name (English) - stop or city name
  name_local?: string    // Marathi name (optional)
  type: 'CITY' | 'STOP' | 'TOURIST'  // Place type
  district: string       // District name
  state: string          // State (Maharashtra for MSRTC)
  operator?: string      // Operator (e.g., MSRTC)
  is_depot?: boolean     // Is this a depot/search surface stop
  // CRITICAL: City info for booking partner URLs
  // redBus only supports CITY → CITY searches, never STOP → STOP
  cityName: string       // Parent city name (used for redBus URLs)
  cityId?: string        // City ID (for future use)
  // Tourist destination fields
  is_tourist?: boolean
  destination_type?: string  // HILL_STATION, RELIGIOUS, HERITAGE, BEACH, RESORT
  description?: string
}

interface BusLocationAutocompleteProps {
  value: string                    // Display text
  selectedPlace: BusPlace | null   // STRICT: Selected place object with ID
  onChange: (text: string, place: BusPlace | null) => void
  placeholder?: string
  label: string
  testId?: string
  disabled?: boolean
  otherPlaceId?: string | null     // The other field's place_id (to prevent same selection)
}

export default function BusLocationAutocomplete({
  value,
  selectedPlace,
  onChange,
  placeholder = 'Select city (e.g., Pune)',
  label,
  testId = 'bus-location',
  disabled = false,
  otherPlaceId = null,
}: BusLocationAutocompleteProps) {
  const [query, setQuery] = useState(value)
  const [suggestions, setSuggestions] = useState<BusPlace[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isLoading, setIsLoading] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Sync query with external value
  useEffect(() => {
    setQuery(value)
  }, [value])

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  /**
   * Fetch suggestions from backend API
   * 
   * IMPORTANT: These are SUGGESTIONS only.
   * User MUST select from dropdown to set a valid place.
   */
  const fetchSuggestions = async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSuggestions([])
      return
    }

    setIsLoading(true)
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || ''
      const response = await fetch(
        `${apiBase}/api/autocomplete/bus?q=${encodeURIComponent(searchQuery)}&mode=bus&limit=15`
      )
      
      if (response.ok) {
        const data = await response.json()
        
        // Convert API response to BusPlace format
        // IMPORTANT: Use label_en (stop name) as the primary name, not city name
        // This ensures "Karad Bus Stand" shows as "Karad", not "Satara"
        // BUT: cityName is ALWAYS the parent city for redBus URLs
        const busPlaces: BusPlace[] = data.results.map((r: any) => {
          // For tourist destinations, use the destination name directly
          if (r.type === 'tourist_destination') {
            return {
              place_id: r.id,
              name: r.label_en || r.city,
              name_local: r.city_local || '',
              type: 'TOURIST' as const,
              district: r.city,
              state: r.state || 'Maharashtra',
              operator: undefined,
              is_depot: false,
              // CRITICAL: cityName for booking URLs - use parent city, not destination
              cityName: r.cityName || r.city,
              cityId: r.cityId,
              is_tourist: true,
              destination_type: r.destination_type,
              description: r.description,
            }
          }
          
          // label_en format: "Karad Bus Stand" -> extract first part as name
          // For cities without label_en, use city name
          const labelEn = r.label_en || ''
          const stopName = labelEn 
            ? labelEn.replace(/ Bus Stand$/i, '')
                     .replace(/ Depot$/i, '')
                     .replace(/ ST Stand$/i, '')
                     .replace(/ CBS$/i, '')
                     .trim()
            : r.city
          
          return {
            place_id: r.id,              // THIS IS THE KEY - place_id from backend
            name: stopName,              // Stop name (e.g., "Karad" not "Satara")
            name_local: r.label || '',   // Marathi name (e.g., "कराड बस स्थानक")
            type: r.type === 'bus_stop' ? 'STOP' : 'CITY',
            district: r.city,            // District/parent city (for display)
            state: r.state || 'Maharashtra',
            operator: r.operator || undefined,
            is_depot: r.is_search_surface || false,
            // CRITICAL: cityName for booking partner URLs
            // redBus only supports CITY → CITY, not STOP → STOP
            cityName: r.cityName || r.city,  // Parent city for URLs
            cityId: r.cityId,
          }
        })
        
        // Filter out the "other" place if it's already selected
        // This prevents selecting same city for both origin AND destination
        const filteredPlaces = otherPlaceId 
          ? busPlaces.filter(p => p.place_id !== otherPlaceId)
          : busPlaces
        
        setSuggestions(filteredPlaces)
      } else {
        setSuggestions([])
      }
    } catch (error) {
      console.error('Bus autocomplete fetch error:', error)
      setSuggestions([])
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Handle input change
   * 
   * CRITICAL: When user types, we CLEAR the selectedPlace.
   * User MUST re-select from dropdown to have a valid place.
   * 
   * This prevents text-based resolution which causes bugs like
   * "Satara → Karad" becoming "Satara → Satara"
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setQuery(newValue)
    setSelectedIndex(-1)
    setShowSuggestions(true)

    // CRITICAL: Clear selected place when user types
    // This forces user to select from dropdown again
    if (selectedPlace) {
      onChange(newValue, null) // place_id is now NULL
    }

    // Debounce search
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(newValue)
    }, 150)
  }

  /**
   * Handle dropdown selection
   * 
   * CRITICAL: This is the ONLY way to set a valid place.
   * The place_id from this selection is the source of truth.
   */
  const handleSelectPlace = (place: BusPlace) => {
    const displayValue = place.name_local 
      ? `${place.name} (${place.name_local})`
      : place.name
    
    setQuery(displayValue)
    setShowSuggestions(false)
    
    // CRITICAL: Set the place with its place_id
    // This place_id will be used in the search API call
    onChange(displayValue, place)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1)
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSelectPlace(suggestions[selectedIndex])
        }
        break
      case 'Escape':
        setShowSuggestions(false)
        break
    }
  }

  const handleFocus = () => {
    if (query.length >= 2) {
      setShowSuggestions(true)
      fetchSuggestions(query)
    }
  }

  // Validation state
  const isValid = selectedPlace !== null
  const showValidationHint = query.length >= 2 && !selectedPlace && !showSuggestions

  return (
    <div ref={wrapperRef} className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div className="relative">
        <Bus className={`absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 ${
          isValid ? 'text-orange-600' : 'text-gray-400'
        }`} />
        <input
          ref={inputRef}
          data-testid={testId}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder={placeholder}
          disabled={disabled}
          className={`w-full pl-10 pr-10 py-3 border rounded-xl search-input-animated focus:ring-2 focus:border-transparent transition-colors ${
            isValid 
              ? 'border-orange-500 focus:ring-orange-500 bg-orange-50' 
              : 'border-gray-300 focus:ring-blue-500'
          } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          autoComplete="off"
        />
        {/* Loading indicator */}
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <Loader2 className="h-4 w-4 animate-spin text-orange-600" />
          </div>
        )}
        {/* Valid checkmark */}
        {isValid && !isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-orange-600">
            <Check className="h-5 w-5" />
          </div>
        )}
      </div>

      {/* Validation hint - CRITICAL for user awareness */}
      {showValidationHint && (
        <p className="mt-1 text-xs text-amber-600 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Please select a city from the dropdown
        </p>
      )}

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto animate-dropdown-open">
          <div className="sticky top-0 bg-gray-50 px-4 py-2 border-b border-gray-200">
            <span className="text-xs text-gray-600 font-medium">
              Select a bus stop or city
            </span>
          </div>
          {suggestions.map((place, index) => (
            <button
              key={place.place_id}
              type="button"
              onClick={() => handleSelectPlace(place)}
              className={`w-full px-4 py-3 text-left transition-colors border-b border-gray-100 last:border-b-0 last:rounded-b-xl ${
                index === selectedIndex 
                  ? 'bg-orange-50 ring-2 ring-inset ring-orange-500' 
                  : 'hover:bg-orange-50'
              }`}
            >
              <div className="flex items-center gap-3">
                {/* Icon/Badge */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                  place.type === 'TOURIST' ? 'bg-purple-100' :
                  place.type === 'STOP' && place.is_depot ? 'bg-green-100' :
                  place.type === 'STOP' ? 'bg-orange-100' :
                  'bg-gray-100'
                }`}>
                  {place.type === 'TOURIST' ? (
                    <span className="text-lg">
                      {place.destination_type === 'HILL_STATION' ? '🏔️' :
                       place.destination_type === 'RELIGIOUS' ? '🛕' :
                       place.destination_type === 'HERITAGE' ? '🏛️' :
                       place.destination_type === 'BEACH' ? '🏖️' :
                       place.destination_type === 'RESORT' ? '🏨' : '📍'}
                    </span>
                  ) : place.type === 'STOP' ? (
                    <span className={`text-lg ${place.is_depot ? 'text-green-600' : 'text-orange-600'}`}>
                      🚌
                    </span>
                  ) : (
                    <MapPin className="h-5 w-5 text-gray-600" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate flex items-center gap-2">
                    {place.name}
                    {place.type === 'TOURIST' && (
                      <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">
                        {place.destination_type?.replace('_', ' ').toLowerCase()}
                      </span>
                    )}
                    {place.is_depot && (
                      <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                        Depot
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-500 truncate">
                    {place.type === 'TOURIST' && place.description ? (
                      <span>{place.description}</span>
                    ) : (
                      <>
                        {place.name_local && (
                          <span className="mr-2">{place.name_local}</span>
                        )}
                        <span className="text-gray-400">
                          {place.district !== place.name && `${place.district}, `}{place.state}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No results */}
      {showSuggestions && query.length >= 2 && suggestions.length === 0 && !isLoading && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg p-4">
          <div className="text-center text-gray-500 text-sm">
            No cities found for "{query}"
          </div>
        </div>
      )}
    </div>
  )
}
