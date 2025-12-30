'use client'

/**
 * BusLocationAutocomplete - ID-Based Selection Only
 * ==================================================
 * 
 * Uses shared useAutocomplete hook for:
 * - State machine (IDLE | LOADING | HAS_RESULTS | NO_RESULTS)
 * - Race condition prevention
 * - Response normalization
 * - Credit-saving debounce
 * 
 * CRITICAL RULES:
 * - User MUST select from dropdown
 * - Typing alone is NOT a valid selection
 * - Validation is DECOUPLED from autocomplete UI
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { Bus, MapPin, AlertCircle, Check, Loader2 } from 'lucide-react'
import { useAutocomplete } from '@/hooks/useAutocomplete'

// ============================================================
// STRICT PLACE OBJECT - ID IS THE SOURCE OF TRUTH
// ============================================================
export interface BusPlace {
  place_id: string
  name: string
  name_local?: string
  type: 'CITY' | 'STOP' | 'TOURIST'
  district: string
  state: string
  operator?: string
  is_depot?: boolean
  /** For UI styling only - makes item appear faded if false. NEVER filter by this. */
  is_search_surface?: boolean
  cityName: string
  cityId?: string
  is_tourist?: boolean
  destination_type?: string
  description?: string
}

interface BusLocationAutocompleteProps {
  value: string
  selectedPlace: BusPlace | null
  onChange: (text: string, place: BusPlace | null) => void
  placeholder?: string
  label: string
  testId?: string
  disabled?: boolean
  otherPlaceId?: string | null
}

/**
 * Transform raw API result to BusPlace
 */
/**
 * Transform raw API result to BusPlace
 * 
 * CRITICAL: Do NOT filter by is_search_surface here.
 * All valid results must be included. is_search_surface is only
 * used for UI styling (faded appearance for non-primary stops).
 */
function transformToBusPlace(raw: unknown): BusPlace {
  const r = raw as Record<string, any>
  
  if (r.type === 'tourist_destination') {
    return {
      place_id: r.id || r.place_id || `tourist_${r.city}`,
      name: r.label_en || r.name || r.city || '',
      name_local: r.city_local || r.label || '',
      type: 'TOURIST',
      district: r.city || r.district || '',
      state: r.state || 'Maharashtra',
      operator: undefined,
      is_depot: false,
      // is_search_surface is for UI styling only (faded vs prominent)
      is_search_surface: r.is_search_surface !== false,
      cityName: r.cityName || r.city || '',
      cityId: r.cityId,
      is_tourist: true,
      destination_type: r.destination_type,
      description: r.description,
    }
  }
  
  const labelEn = r.label_en || r.name || ''
  const stopName = labelEn 
    ? labelEn
        .replace(/ Bus Stand$/i, '')
        .replace(/ Depot$/i, '')
        .replace(/ ST Stand$/i, '')
        .replace(/ CBS$/i, '')
        .trim()
    : r.city || ''
  
  // Determine if this is a depot/main stand (is_depot) - separate from is_search_surface
  // is_depot: true means it's a main bus depot/stand (show "Depot" badge)
  // is_search_surface: for UI styling only (prominent vs faded)
  const isDepot = r.is_depot === true || (r.type === 'bus_stop' && r.stop_role === 'DEPOT')
  
  return {
    place_id: r.id || r.place_id || `place_${stopName}`,
    name: stopName,
    name_local: r.label || r.name_local || '',
    type: r.type === 'bus_stop' ? 'STOP' : 'CITY',
    district: r.city || r.district || '',
    state: r.state || 'Maharashtra',
    operator: r.operator || undefined,
    is_depot: isDepot,
    // is_search_surface is for UI styling only - NOT for filtering
    is_search_surface: r.is_search_surface !== false,
    cityName: r.cityName || r.city || '',
    cityId: r.cityId,
  }
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
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  
  const wrapperRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Shared autocomplete hook
  const {
    state,
    results: allResults,
    isLoading,
    search,
    clear,
    shouldShowNoResults,
  } = useAutocomplete<BusPlace>({
    endpoint: '/api/autocomplete/bus',
    minQueryLength: 2,
    debounceMs: 400,
    limit: 15,
    transform: transformToBusPlace,
    extraParams: { mode: 'bus' },
  })

  // Filter out the other selected place
  const suggestions = otherPlaceId 
    ? allResults.filter(p => p.place_id !== otherPlaceId)
    : allResults

  // Sync query with external value
  useEffect(() => {
    setQuery(value)
  }, [value])

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Handle input change
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setQuery(newValue)
    setSelectedIndex(-1)
    setShowDropdown(true)

    // Clear selection when user types
    if (selectedPlace) {
      onChange(newValue, null)
    }

    // Trigger search via hook
    search(newValue)
  }, [selectedPlace, onChange, search])

  // Handle dropdown selection
  const handleSelectPlace = useCallback((place: BusPlace) => {
    const displayValue = place.name_local 
      ? `${place.name} (${place.name_local})`
      : place.name
    
    setQuery(displayValue)
    setShowDropdown(false)
    onChange(displayValue, place)
  }, [onChange])

  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown || suggestions.length === 0) return

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
        setShowDropdown(false)
        break
    }
  }, [showDropdown, suggestions, selectedIndex, handleSelectPlace])

  // Handle focus
  const handleFocus = useCallback(() => {
    if (query.length >= 2) {
      setShowDropdown(true)
      search(query)
    }
  }, [query, search])

  // Cleanup on unmount
  useEffect(() => {
    return () => clear()
  }, [clear])

  // Validation state (DECOUPLED from autocomplete)
  const isValid = selectedPlace !== null
  const showValidationHint = query.length >= 2 && !selectedPlace && !showDropdown

  // Empty state check via hook
  const showNoResults = showDropdown && shouldShowNoResults(query)

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

      {/* Validation hint - DECOUPLED from autocomplete */}
      {showValidationHint && (
        <p className="mt-1 text-xs text-amber-600 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Please select a city from the dropdown
        </p>
      )}

      {/* Suggestions dropdown - only show when HAS_RESULTS */}
      {showDropdown && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto animate-dropdown-open">
          <div className="sticky top-0 bg-gray-50 px-4 py-2 border-b border-gray-200">
            <span className="text-xs text-gray-600 font-medium">
              Select a bus stop or city
            </span>
          </div>
          {suggestions.map((place, index) => {
            // is_search_surface is for UI styling only (faded vs prominent)
            // NEVER filter/hide results based on this value
            const isFaded = place.is_search_surface === false
            
            return (
            <button
              key={place.place_id}
              type="button"
              onClick={() => handleSelectPlace(place)}
              className={`w-full px-4 py-3 text-left transition-colors border-b border-gray-100 last:border-b-0 last:rounded-b-xl ${
                index === selectedIndex 
                  ? 'bg-orange-50 ring-2 ring-inset ring-orange-500' 
                  : 'hover:bg-orange-50'
              } ${isFaded ? 'opacity-75' : ''}`}
            >
              <div className="flex items-center gap-3">
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
                  <div className={`font-medium truncate flex items-center gap-2 ${isFaded ? 'text-gray-600' : 'text-gray-900'}`}>
                    {place.name}
                    {place.type === 'TOURIST' && (
                      <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">
                        {place.destination_type?.replace('_', ' ').toLowerCase()}
                      </span>
                    )}
                    {place.is_depot && place.type === 'STOP' && (
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

      {/* No results - ONLY via state machine */}
      {showNoResults && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg p-4">
          <div className="text-center text-gray-500 text-sm">
            No cities found for "{query}"
          </div>
        </div>
      )}
    </div>
  )
}
