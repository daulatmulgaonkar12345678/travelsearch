"use client"

/**
 * HotelLocationAutocomplete - Controlled Selection Autocomplete
 * 
 * PRINCIPLES:
 * - Autocomplete is SELECTION, not typing
 * - Selected city is stored as structured object
 * - Free-text submission NOT allowed
 * - Matches Flights/Trains/Buses behavior
 * 
 * STATE:
 * - selectedCity: full city object or null
 * - query: display text (for typing)
 * - When city selected: input locked to city name
 * - When user edits: selection cleared
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { MapPin, Check, AlertCircle } from 'lucide-react'
import { apiFetch } from '@/lib/api'

// Structured city object - single source of truth
export interface HotelCity {
  city: string
  country: string
  display: string
  countryCode?: string
  latitude?: number
  longitude?: number
}

interface HotelLocationAutocompleteProps {
  value: HotelCity | null  // Selected city object (NOT string)
  onChange: (city: HotelCity | null) => void
  placeholder?: string
  label?: string
  testId?: string
  disabled?: boolean
}

export default function HotelLocationAutocomplete({
  value,
  onChange,
  placeholder = "City, area, or hotel name",
  label = "Destination",
  testId = "hotel-city-input",
  disabled = false,
}: HotelLocationAutocompleteProps) {
  // Query is the text shown in input
  const [query, setQuery] = useState(value?.display || '')
  const [suggestions, setSuggestions] = useState<HotelCity[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isLoading, setIsLoading] = useState(false)
  const [hasError, setHasError] = useState(false)
  
  const wrapperRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)
  const lastQueryRef = useRef<string>('')  // Track last query to ignore stale responses

  // Sync query with selected value
  useEffect(() => {
    if (value) {
      setQuery(value.display)
    }
  }, [value])

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
        // If user clicked away without selecting, reset to last valid selection
        if (!value) {
          setQuery('')
        } else {
          setQuery(value.display)
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [value])

  /**
   * Fetch city suggestions with debouncing and stale response handling
   */
  const fetchSuggestions = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSuggestions([])
      return
    }

    // Store current query to detect stale responses
    lastQueryRef.current = searchQuery
    
    setIsLoading(true)
    setHasError(false)
    
    try {
      const url = `/api/cities?query=${encodeURIComponent(searchQuery)}&limit=10`
      const response = await apiFetch(url)
      
      // Ignore response if query has changed (stale)
      if (lastQueryRef.current !== searchQuery) {
        return
      }
      
      if (response.ok) {
        const data = await response.json()
        
        // Handle API response format: { results: [...] }
        const rawResults = data.results || data || []
        
        // Map to HotelCity structure
        const cities: HotelCity[] = rawResults.map((item: any) => ({
          city: item.city || item.label?.split(',')[0] || '',
          country: item.country || 'Unknown',
          display: item.label || `${item.city}, ${item.country}`,
          countryCode: item.country,
          latitude: item.latitude,
          longitude: item.longitude,
        }))
        
        setSuggestions(cities)
      } else {
        console.error(`City search failed: ${response.status}`)
        setSuggestions([])
        setHasError(true)
      }
    } catch (error) {
      console.error('Failed to fetch cities:', error)
      setSuggestions([])
      setHasError(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Handle input change - clears selection when user types
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setQuery(newValue)
    setSelectedIndex(-1)
    setShowDropdown(true)

    // IMPORTANT: Clear selection when user types (editing after selection)
    if (value) {
      onChange(null)
    }

    // Debounce API calls (300ms)
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(newValue)
    }, 300)
  }

  /**
   * Handle city selection - locks input to selected city
   */
  const handleSelectCity = (city: HotelCity) => {
    setQuery(city.display)
    setShowDropdown(false)
    setSuggestions([])
    onChange(city)  // Pass full city object
  }

  /**
   * Keyboard navigation
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
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
          handleSelectCity(suggestions[selectedIndex])
        }
        break
      case 'Escape':
        setShowDropdown(false)
        break
    }
  }

  /**
   * Handle focus - show dropdown if there's a query
   */
  const handleFocus = () => {
    if (query.length >= 2 && !value) {
      setShowDropdown(true)
      fetchSuggestions(query)
    }
  }

  // Validation state
  const isValid = value !== null
  const showValidationHint = query.length >= 2 && !value && !showDropdown

  return (
    <div ref={wrapperRef} className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      )}
      <div className="relative">
        <MapPin className={`absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 ${
          isValid ? 'text-blue-600' : 'text-gray-400'
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
          autoComplete="off"
          className={`w-full pl-10 pr-10 py-3 border rounded-xl search-input-animated focus:ring-2 focus:border-transparent transition-colors ${
            isValid 
              ? 'border-blue-500 focus:ring-blue-500 bg-blue-50' 
              : 'border-gray-300 focus:ring-blue-500'
          } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
        />
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          </div>
        )}
        
        {/* Valid checkmark */}
        {isValid && !isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-blue-600">
            <Check className="h-5 w-5" />
          </div>
        )}
      </div>

      {/* Validation hint - must select from dropdown */}
      {showValidationHint && (
        <p className="mt-1 text-xs text-amber-600 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Please select a city from the dropdown
        </p>
      )}

      {/* Dropdown */}
      {showDropdown && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto">
          <div className="sticky top-0 bg-gray-50 px-4 py-2 border-b border-gray-200">
            <span className="text-xs text-gray-600 font-medium">
              Select a destination
            </span>
          </div>
          {suggestions.map((city, index) => (
            <button
              key={`${city.city}-${city.country}-${index}`}
              type="button"
              onClick={() => handleSelectCity(city)}
              className={`w-full px-4 py-3 text-left transition-colors border-b border-gray-100 last:border-b-0 last:rounded-b-xl ${
                index === selectedIndex 
                  ? 'bg-blue-50 ring-2 ring-inset ring-blue-500' 
                  : 'hover:bg-blue-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0 w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <MapPin className="h-5 w-5 text-green-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">
                    {city.city}
                  </div>
                  <div className="text-sm text-gray-500">
                    {city.country}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No results */}
      {showDropdown && query.length >= 2 && suggestions.length === 0 && !isLoading && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg p-4">
          <div className="text-center text-gray-500 text-sm">
            {hasError 
              ? 'Failed to load suggestions. Please try again.' 
              : `No cities found for "${query}"`
            }
          </div>
        </div>
      )}
    </div>
  )
}
