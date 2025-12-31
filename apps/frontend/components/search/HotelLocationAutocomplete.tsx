"use client"

/**
 * HotelLocationAutocomplete - Smart Search with City/Area/Hotel Types
 * 
 * FEATURES:
 * - Unified search for cities, areas, and specific hotels
 * - Type-specific icons (City 🏙️, Area 📍, Hotel 🏨)
 * - Full object storage for validation
 * - Matches SearchBarV3 selection-based pattern
 * 
 * STATE:
 * - selectedDestination: full destination object with type
 * - query: display text (for typing)
 * - When selected: input locked to selection label
 * - When user edits: selection cleared
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { MapPin, Check, AlertCircle, Building2, MapPinned, Hotel } from 'lucide-react'
import { apiFetch } from '@/lib/api'

// Destination types
export type HotelDestinationType = 'CITY' | 'AREA' | 'HOTEL'

// Full destination object - single source of truth
export interface HotelDestination {
  id: string
  type: HotelDestinationType
  label: string
  city: string
  country: string
  // Type-specific fields
  areaName?: string     // For AREA type
  hotelName?: string    // For HOTEL type
  hotelId?: string      // For HOTEL type
  latitude?: number
  longitude?: number
}

// Legacy HotelCity interface for backwards compatibility
export interface HotelCity {
  city: string
  country: string
  display: string
  countryCode?: string
  latitude?: number
  longitude?: number
}

// API response types
interface SmartSearchResult {
  id: string
  type: HotelDestinationType
  label: string
  city: string
  country: string
  area_name?: string
  hotel_name?: string
  hotel_id?: string
  latitude?: number
  longitude?: number
}

interface SmartSearchResponse {
  query: string
  count: number
  results: SmartSearchResult[]
  source: string
}

interface HotelLocationAutocompleteProps {
  value: HotelCity | HotelDestination | null
  onChange: (destination: HotelDestination | null) => void  // Changed: Now passes full HotelDestination
  placeholder?: string
  label?: string
  testId?: string
  disabled?: boolean
}

// Convert SmartSearchResult to HotelDestination
function toHotelDestination(result: SmartSearchResult): HotelDestination {
  return {
    id: result.id,
    type: result.type,
    label: result.label,
    city: result.city,
    country: result.country,
    areaName: result.area_name,
    hotelName: result.hotel_name,
    hotelId: result.hotel_id,
    latitude: result.latitude,
    longitude: result.longitude,
  }
}

// Convert HotelDestination to legacy HotelCity for backwards compatibility
function toHotelCity(dest: HotelDestination): HotelCity {
  return {
    city: dest.city,
    country: dest.country,
    display: dest.label,
    latitude: dest.latitude,
    longitude: dest.longitude,
  }
}

// Get icon component based on type
function TypeIcon({ type, className }: { type: HotelDestinationType; className?: string }) {
  switch (type) {
    case 'CITY':
      return <Building2 className={className || "h-5 w-5 text-blue-600"} />
    case 'AREA':
      return <MapPinned className={className || "h-5 w-5 text-green-600"} />
    case 'HOTEL':
      return <Hotel className={className || "h-5 w-5 text-purple-600"} />
    default:
      return <MapPin className={className || "h-5 w-5 text-gray-600"} />
  }
}

// Get background color based on type
function getTypeBgColor(type: HotelDestinationType): string {
  switch (type) {
    case 'CITY': return 'bg-blue-100'
    case 'AREA': return 'bg-green-100'
    case 'HOTEL': return 'bg-purple-100'
    default: return 'bg-gray-100'
  }
}

// Get type label
function getTypeLabel(type: HotelDestinationType): string {
  switch (type) {
    case 'CITY': return 'City'
    case 'AREA': return 'Area'
    case 'HOTEL': return 'Hotel'
    default: return type
  }
}

export default function HotelLocationAutocomplete({
  value,
  onChange,
  placeholder = "City, area, or hotel name",
  label = "Destination",
  testId = "hotel-city-input",
  disabled = false,
}: HotelLocationAutocompleteProps) {
  // Determine display value from legacy or new format
  const displayValue = value 
    ? ('display' in value ? value.display : (value as HotelDestination).label)
    : ''
  
  const [query, setQuery] = useState(displayValue)
  const [suggestions, setSuggestions] = useState<HotelDestination[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isLoading, setIsLoading] = useState(false)
  const [hasError, setHasError] = useState(false)
  
  const wrapperRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)
  const lastQueryRef = useRef<string>('')

  // Sync query with selected value
  useEffect(() => {
    if (value) {
      const display = 'display' in value ? value.display : (value as HotelDestination).label
      setQuery(display)
    }
  }, [value])

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
        if (!value) {
          setQuery('')
        } else {
          const display = 'display' in value ? value.display : (value as HotelDestination).label
          setQuery(display)
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [value])

  /**
   * Fetch suggestions using Smart Search API
   */
  const fetchSuggestions = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSuggestions([])
      return
    }

    lastQueryRef.current = searchQuery
    setIsLoading(true)
    setHasError(false)
    
    try {
      // Use new Smart Search API
      const url = `/api/hotels/smart-search?query=${encodeURIComponent(searchQuery)}&limit=10`
      const response = await apiFetch(url)
      
      if (lastQueryRef.current !== searchQuery) {
        return // Stale response
      }
      
      if (response.ok) {
        const data: SmartSearchResponse = await response.json()
        const destinations = data.results.map(toHotelDestination)
        setSuggestions(destinations)
      } else {
        // Fallback to legacy city API
        console.warn('[HotelAutocomplete] Smart search failed, falling back to cities API')
        const fallbackUrl = `/api/cities?query=${encodeURIComponent(searchQuery)}&limit=10`
        const fallbackResponse = await apiFetch(fallbackUrl)
        
        if (fallbackResponse.ok) {
          const fallbackData = await fallbackResponse.json()
          const rawResults = fallbackData.results || fallbackData || []
          
          const destinations: HotelDestination[] = rawResults.map((item: any) => ({
            id: `CITY_${(item.city || item.label?.split(',')[0] || '').toUpperCase().replace(/\s+/g, '_')}`,
            type: 'CITY' as HotelDestinationType,
            label: item.label || `${item.city}, ${item.country}`,
            city: item.city || item.label?.split(',')[0] || '',
            country: item.country || 'Unknown',
            latitude: item.latitude,
            longitude: item.longitude,
          }))
          
          setSuggestions(destinations)
        } else {
          setSuggestions([])
          setHasError(true)
        }
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error)
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

    if (value) {
      onChange(null)
    }

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(newValue)
    }, 300)
  }

  /**
   * Handle destination selection
   */
  const handleSelectDestination = (dest: HotelDestination) => {
    setQuery(dest.label)
    setShowDropdown(false)
    setSuggestions([])
    // Convert to legacy HotelCity format for backwards compatibility
    onChange(toHotelCity(dest))
  }

  /**
   * Keyboard navigation
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown || suggestions.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => prev < suggestions.length - 1 ? prev + 1 : prev)
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1)
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSelectDestination(suggestions[selectedIndex])
        }
        break
      case 'Escape':
        setShowDropdown(false)
        break
    }
  }

  const handleFocus = () => {
    if (query.length >= 2 && !value) {
      setShowDropdown(true)
      fetchSuggestions(query)
    }
  }

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
        
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          </div>
        )}
        
        {isValid && !isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-blue-600">
            <Check className="h-5 w-5" />
          </div>
        )}
      </div>

      {showValidationHint && (
        <p className="mt-1 text-xs text-amber-600 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Please select from the dropdown
        </p>
      )}

      {/* Smart Search Dropdown with Type Icons */}
      {showDropdown && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-96 overflow-y-auto animate-dropdown-open">
          <div className="sticky top-0 bg-gray-50 px-4 py-2 border-b border-gray-200">
            <span className="text-xs text-gray-600 font-medium">
              Search by city, area, or hotel name
            </span>
          </div>
          {suggestions.map((dest, index) => (
            <button
              key={dest.id}
              type="button"
              onClick={() => handleSelectDestination(dest)}
              className={`w-full px-4 py-3 text-left transition-colors border-b border-gray-100 last:border-b-0 last:rounded-b-xl ${
                index === selectedIndex 
                  ? 'bg-blue-50 ring-2 ring-inset ring-blue-500' 
                  : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-3">
                {/* Type-specific icon */}
                <div className={`flex-shrink-0 w-10 h-10 ${getTypeBgColor(dest.type)} rounded-lg flex items-center justify-center`}>
                  <TypeIcon type={dest.type} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 truncate">
                      {dest.type === 'HOTEL' ? dest.hotelName : 
                       dest.type === 'AREA' ? dest.areaName : 
                       dest.city}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      dest.type === 'CITY' ? 'bg-blue-100 text-blue-700' :
                      dest.type === 'AREA' ? 'bg-green-100 text-green-700' :
                      'bg-purple-100 text-purple-700'
                    }`}>
                      {getTypeLabel(dest.type)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {dest.type === 'HOTEL' && dest.areaName 
                      ? `${dest.areaName}, ${dest.city}` 
                      : dest.type === 'AREA'
                      ? dest.city
                      : dest.country}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {showDropdown && query.length >= 2 && suggestions.length === 0 && !isLoading && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg p-4">
          <div className="text-center text-gray-500 text-sm">
            {hasError 
              ? 'Failed to load suggestions. Please try again.' 
              : `No results found for "${query}"`
            }
          </div>
        </div>
      )}
    </div>
  )
}
