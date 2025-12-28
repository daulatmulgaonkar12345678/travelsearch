"use client"

/**
 * TrainStationAutocomplete - STATION-FIRST ARCHITECTURE
 * 
 * 🔴 CONTRACT (NON-NEGOTIABLE):
 * - Only station codes (CSMT, PUNE) or _ALL tokens (MUMBAI_ALL) are valid
 * - Raw city names (Mumbai, Pune) are NEVER valid inputs
 * - User MUST select from dropdown - free text is disabled
 * 
 * This component:
 * 1. Fetches from /api/trains/autocomplete which returns station-first format
 * 2. Shows "City (All Stations) ⭐" first, then individual stations
 * 3. Stores the `value` field (e.g., "MUMBAI_ALL" or "CSMT") for API submission
 * 4. Never allows raw city name submission
 */

import { useState, useEffect, useRef } from 'react'
import { Train, AlertCircle, Star, Building2 } from 'lucide-react'

// Type for dropdown options from backend
export interface TrainStationOption {
  value: string        // "MUMBAI_ALL" or "CSMT" - THIS is what we submit
  label: string        // "Mumbai (All Stations) ⭐" or "CSMT – Chhatrapati Shivaji Maharaj Terminus"
  type: "city_all" | "station"
  city?: string
  station_count?: number  // Only for city_all
  is_major?: boolean      // Only for stations
  is_recommended?: boolean
}

interface TrainStationAutocompleteProps {
  value: TrainStationOption | null  // The selected option
  onChange: (option: TrainStationOption | null) => void
  placeholder?: string
  label?: string
  testId?: string
  disabled?: boolean
}

export default function TrainStationAutocomplete({
  value,
  onChange,
  placeholder = "Station or City (All Stations)",
  label = "Station",
  testId = "train-station-input",
  disabled = false,
}: TrainStationAutocompleteProps) {
  const [query, setQuery] = useState(value?.label || '')
  const [suggestions, setSuggestions] = useState<TrainStationOption[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isLoading, setIsLoading] = useState(false)
  const [hasError, setHasError] = useState(false)
  
  const wrapperRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)

  // Sync query with value
  useEffect(() => {
    if (value) {
      setQuery(value.label)
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
          setQuery(value.label)
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [value])

  /**
   * Fetch suggestions from backend /api/trains/autocomplete
   * Backend returns station-first format with CITY_ALL options
   */
  const fetchSuggestions = async (searchQuery: string) => {
    if (searchQuery.length < 1) {
      setSuggestions([])
      return
    }

    setIsLoading(true)
    setHasError(false)
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || ''
      const response = await fetch(
        `${apiBase}/api/trains/autocomplete?q=${encodeURIComponent(searchQuery)}&limit=10`
      )
      
      if (!response.ok) {
        throw new Error('Failed to fetch suggestions')
      }
      
      const data = await response.json()
      
      // Map backend response to TrainStationOption
      const options: TrainStationOption[] = data.results.map((r: any) => ({
        value: r.value,
        label: r.label,
        type: r.type,
        city: r.city,
        station_count: r.station_count,
        is_major: r.is_major,
        is_recommended: r.is_recommended,
      }))
      
      setSuggestions(options)
    } catch (error) {
      console.error('Train autocomplete error:', error)
      setHasError(true)
      setSuggestions([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setQuery(newValue)
    setSelectedIndex(-1)
    setShowDropdown(true)

    // Clear selection when user types (they need to re-select)
    if (value) {
      onChange(null)
    }

    // Debounce search
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(newValue)
    }, 150)
  }

  const handleSelectOption = (option: TrainStationOption) => {
    setQuery(option.label)
    setShowDropdown(false)
    onChange(option)
  }

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
          handleSelectOption(suggestions[selectedIndex])
        }
        break
      case 'Escape':
        setShowDropdown(false)
        break
    }
  }

  const handleFocus = () => {
    if (query.length >= 1) {
      setShowDropdown(true)
      fetchSuggestions(query)
    }
  }

  // Validation: is a valid option selected?
  const isValid = value !== null
  const showValidationHint = query.length >= 2 && !value && !showDropdown

  return (
    <div ref={wrapperRef} className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div className="relative">
        <Train className={`absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 ${
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
          className={`w-full pl-10 pr-10 py-3 border rounded-xl focus:ring-2 focus:border-transparent transition-colors ${
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
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>

      {/* Validation hint - MUST select from dropdown */}
      {showValidationHint && (
        <p className="mt-1 text-xs text-amber-600 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Please select a station or "All Stations" from the dropdown
        </p>
      )}

      {/* Dropdown */}
      {showDropdown && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto">
          <div className="sticky top-0 bg-gray-50 px-4 py-2 border-b border-gray-200">
            <span className="text-xs text-gray-600 font-medium">
              Select a station or "All Stations"
            </span>
          </div>
          {suggestions.map((option, index) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleSelectOption(option)}
              className={`w-full px-4 py-3 text-left transition-colors border-b border-gray-100 last:border-b-0 last:rounded-b-xl ${
                index === selectedIndex 
                  ? 'bg-blue-50 ring-2 ring-inset ring-blue-500' 
                  : 'hover:bg-blue-50'
              }`}
            >
              <div className="flex items-center gap-3">
                {/* Icon - Different for city_all vs station */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                  option.type === 'city_all' 
                    ? 'bg-amber-100' 
                    : option.is_major 
                      ? 'bg-blue-100' 
                      : 'bg-gray-100'
                }`}>
                  {option.type === 'city_all' ? (
                    <Building2 className="h-5 w-5 text-amber-600" />
                  ) : (
                    <span className={`font-bold text-xs ${option.is_major ? 'text-blue-600' : 'text-gray-600'}`}>
                      {option.value}
                    </span>
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate flex items-center gap-2">
                    {option.label}
                    {option.is_recommended && (
                      <Star className="h-4 w-4 text-amber-500 fill-amber-500" />
                    )}
                  </div>
                  <div className="text-sm text-gray-500">
                    {option.type === 'city_all' ? (
                      <span>{option.station_count} stations • Select for all routes</span>
                    ) : (
                      <span>{option.city} {option.is_major ? '• Major station' : ''}</span>
                    )}
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
              : `No stations found for "${query}"`
            }
          </div>
        </div>
      )}
    </div>
  )
}
