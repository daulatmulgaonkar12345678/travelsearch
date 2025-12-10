"use client"

import { useState, useEffect, useRef } from 'react'
import { Plane, MapPin, AlertCircle } from 'lucide-react'
import { API_ENDPOINTS, apiFetch } from '@/lib/config'
import Fuse from 'fuse.js'

interface Airport {
  iata: string
  name: string
  city: string
  country: string
}

interface AirportAutocompleteProps {
  value: string
  onChange: (value: string, airport?: Airport) => void
  placeholder?: string
  label?: string
  testId?: string
}

// Local fallback search using Fuse.js
let airportDataCache: Airport[] | null = null
let fuseInstance: Fuse<Airport> | null = null

async function loadLocalAirportData(): Promise<Airport[]> {
  if (airportDataCache) return airportDataCache
  
  try {
    const response = await fetch('/data/airports-full.json')
    const data = await response.json()
    airportDataCache = data
    return data
  } catch (error) {
    console.error('Failed to load local airport data:', error)
    return []
  }
}

async function searchLocalAirports(query: string): Promise<Airport[]> {
  if (!fuseInstance) {
    const data = await loadLocalAirportData()
    fuseInstance = new Fuse(data, {
      keys: ['iata', 'city', 'name', 'country'],
      threshold: 0.3,
      distance: 100,
    })
  }
  
  const results = fuseInstance.search(query)
  return results.slice(0, 10).map(r => r.item)
}

export default function AirportAutocomplete({
  value,
  onChange,
  placeholder = "City or airport",
  label = "Location",
  testId = "airport-input"
}: AirportAutocompleteProps) {
  const [query, setQuery] = useState(value)
  const [suggestions, setSuggestions] = useState<Airport[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isLoading, setIsLoading] = useState(false)
  const [errorState, setErrorState] = useState<'none' | 'server_error' | 'no_results'>('none')
  const [usingFallback, setUsingFallback] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    setQuery(value)
  }, [value])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const fetchSuggestions = async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSuggestions([])
      return
    }

    setIsLoading(true)
    try {
      const url = `${API_ENDPOINTS.airports}?query=${encodeURIComponent(searchQuery)}&limit=10`
      const response = await apiFetch(url)
      
      if (response.ok) {
        const data = await response.json()
        // Extract results array from API response
        const results = data.results || []
        setSuggestions(results)
      } else {
        console.error(`Airport search failed: ${response.status} ${response.statusText}`)
        setSuggestions([])
      }
    } catch (error) {
      console.error('Failed to fetch airports:', error)
      setSuggestions([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setQuery(newValue)
    setSelectedIndex(-1)
    setShowSuggestions(true)

    // Debounce API calls
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(newValue)
    }, 300)

    // Update parent with raw text
    onChange(newValue)
  }

  const handleSelectAirport = (airport: Airport) => {
    const displayValue = `${airport.city}, ${airport.country}`
    setQuery(displayValue)
    setShowSuggestions(false)
    onChange(airport.iata, airport)
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
          handleSelectAirport(suggestions[selectedIndex])
        }
        break
      case 'Escape':
        setShowSuggestions(false)
        break
    }
  }

  return (
    <div ref={wrapperRef} className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div className="relative">
        <Plane className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          data-testid={testId}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && setShowSuggestions(true)}
          placeholder={placeholder}
          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          autoComplete="off"
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          </div>
        )}
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto">
          <div className="sticky top-0 bg-gray-50 px-4 py-2 border-b border-gray-200 flex items-center justify-between">
            <span className="text-xs text-gray-600 font-medium">Search Results</span>
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
              Internal dataset
            </span>
          </div>
          {suggestions.map((airport, index) => (
            <button
              key={airport.iata}
              type="button"
              onClick={() => handleSelectAirport(airport)}
              className={`w-full px-4 py-3 text-left hover:bg-blue-50 last:rounded-b-xl transition-colors border-b border-gray-100 last:border-b-0 ${
                index === selectedIndex ? 'bg-blue-50 ring-2 ring-inset ring-blue-500' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-sm">{airport.iata}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">
                    {airport.city}, {airport.country}
                  </div>
                  <div className="text-sm text-gray-500 truncate">
                    {airport.name}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {showSuggestions && query.length >= 2 && suggestions.length === 0 && !isLoading && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg p-4 text-center text-gray-500 text-sm">
          No airports found
        </div>
      )}
    </div>
  )
}
