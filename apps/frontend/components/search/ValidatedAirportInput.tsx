/**
 * Enhanced Airport Autocomplete with Strict Validation
 * Google Flights style - must select from list
 */

import { useState, useEffect, useRef } from 'react'
import { Plane, MapPin, Loader2, X, AlertCircle } from 'lucide-react'
import { apiFetch } from '@/lib/api'

interface Airport {
  iata: string
  name: string
  city: string
  country: string
  iso_country?: string
}

interface ValidatedAirportInputProps {
  value: Airport | null
  onChange: (airport: Airport | null) => void
  placeholder: string
  label?: string
  error?: string
  onValidationChange?: (isValid: boolean) => void
}

export default function ValidatedAirportInput({
  value,
  onChange,
  placeholder,
  label,
  error: externalError,
  onValidationChange,
}: ValidatedAirportInputProps) {
  const [inputValue, setInputValue] = useState('')
  const [suggestions, setSuggestions] = useState<Airport[]>([])
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [internalError, setInternalError] = useState('')
  const [touched, setTouched] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const debounceTimerRef = useRef<NodeJS.Timeout>()

  const error = externalError || internalError

  useEffect(() => {
    // Update input display when value changes externally
    if (value) {
      setInputValue(formatAirportDisplay(value))
      setInternalError('')
      onValidationChange?.(true)
    } else if (touched && inputValue) {
      setInternalError('Please select a valid airport')
      onValidationChange?.(false)
    }
  }, [value])

  useEffect(() => {
    // Click outside handler
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const formatAirportDisplay = (airport: Airport) => {
    return `${airport.city} (${airport.iata})`
  }

  const searchAirports = async (query: string) => {
    if (query.length < 2) {
      setSuggestions([])
      return
    }

    setLoading(true)
    try {
      const response = await apiFetch(`/api/airports?query=${encodeURIComponent(query)}&limit=8`)
      if (response.ok) {
        const data = await response.json()
        setSuggestions(data.results || [])
        setShowDropdown(true)
      }
    } catch (err) {
      console.error('Airport search error:', err)
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setTouched(true)
    setInternalError('')

    // Clear selected airport if user types after selection
    if (value) {
      onChange(null)
      onValidationChange?.(false)
    }

    // Debounce search
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    debounceTimerRef.current = setTimeout(() => {
      searchAirports(newValue)
    }, 300)
  }

  const handleSelectAirport = (airport: Airport) => {
    onChange(airport)
    setInputValue(formatAirportDisplay(airport))
    setShowDropdown(false)
    setSuggestions([])
    setInternalError('')
    setTouched(true)
    onValidationChange?.(true)
  }

  const handleBlur = () => {
    setTouched(true)
    
    // Delay to allow click/mousedown on dropdown
    setTimeout(() => {
      if (!value && inputValue) {
        // Invalid input - clear it
        setInputValue('')
        setInternalError('Please select a valid airport from the list')
        onValidationChange?.(false)
      }
      setShowDropdown(false)
    }, 300)
  }

  const handleClear = () => {
    setInputValue('')
    onChange(null)
    setSuggestions([])
    setInternalError('')
    setTouched(false)
    onValidationChange?.(false)
    inputRef.current?.focus()
  }

  const handleFocus = () => {
    if (suggestions.length > 0) {
      setShowDropdown(true)
    }
  }

  return (
    <div className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      
      <div className="relative">
        <Plane className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          placeholder={placeholder}
          className={`w-full pl-10 pr-10 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 transition-colors ${
            error
              ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
              : value
              ? 'border-green-300 bg-green-50'
              : 'border-gray-300 focus:border-blue-500'
          }`}
          autoComplete="off"
        />

        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center space-x-1">
          {loading && <Loader2 className="h-4 w-4 animate-spin text-gray-400" />}
          {value && !loading && (
            <button
              onClick={handleClear}
              className="p-1 hover:bg-gray-100 rounded-full transition-colors"
              type="button"
            >
              <X className="h-4 w-4 text-gray-400" />
            </button>
          )}
        </div>
      </div>

      {/* Dropdown */}
      {showDropdown && suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto"
        >
          {suggestions.map((airport) => (
            <button
              key={airport.iata}
              onMouseDown={(e) => {
                e.preventDefault() // Prevent input blur
                handleSelectAirport(airport)
              }}
              className="w-full px-4 py-3 text-left hover:bg-blue-50 transition-colors flex items-start space-x-3 border-b border-gray-100 last:border-0"
              type="button"
            >
              <MapPin className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-gray-900">
                  {airport.city} ({airport.iata})
                </div>
                <div className="text-sm text-gray-600 truncate">
                  {airport.name}
                </div>
                <div className="text-xs text-gray-500">
                  {airport.country}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Error Message */}
      {error && touched && (
        <div className="mt-1 flex items-center space-x-1 text-sm text-red-600">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Hint */}
      {!error && !value && touched && inputValue && (
        <div className="mt-1 text-sm text-gray-500">
          Select an airport from the dropdown
        </div>
      )}
    </div>
  )
}
