"use client"

import { useState, useEffect, useRef } from 'react'
import { Plane, Train, Bus, MapPin, AlertCircle } from 'lucide-react'
import Fuse from 'fuse.js'

// Unified location structure supporting all transport modes
export interface TransportLocation {
  city_id: string           // Unique identifier
  label: string             // Display name (e.g., "Pune, Maharashtra")
  city: string              // City name
  state?: string            // State/region
  country: string           // Country
  flight_codes: string[]    // Airport IATA codes (e.g., ["PNQ"])
  rail_codes: string[]      // Railway station codes (e.g., ["PUNE", "PUNEJN"])
  bus_codes: string[]       // Bus stand codes (e.g., ["SWARGATE", "SHIVAJINAGAR"])
}

// Comprehensive India city dataset with all transport codes
const INDIA_CITIES: TransportLocation[] = [
  // Metro Cities
  { city_id: "DEL", label: "New Delhi, Delhi", city: "New Delhi", state: "Delhi", country: "India", flight_codes: ["DEL"], rail_codes: ["NDLS", "DLI", "HNZM", "NZM"], bus_codes: ["ISBT_KASHMERE", "ISBT_ANAND_VIHAR", "ISBT_SARAI_KALE_KHAN"] },
  { city_id: "MUM", label: "Mumbai, Maharashtra", city: "Mumbai", state: "Maharashtra", country: "India", flight_codes: ["BOM"], rail_codes: ["CSMT", "BCT", "LTT", "DR"], bus_codes: ["MUMBAI_CENTRAL", "DADAR", "BORIVALI"] },
  { city_id: "BLR", label: "Bangalore, Karnataka", city: "Bangalore", state: "Karnataka", country: "India", flight_codes: ["BLR"], rail_codes: ["SBC", "KSR", "YPR", "BNCE"], bus_codes: ["MAJESTIC", "KEMPEGOWDA", "SHANTINAGAR"] },
  { city_id: "CHE", label: "Chennai, Tamil Nadu", city: "Chennai", state: "Tamil Nadu", country: "India", flight_codes: ["MAA"], rail_codes: ["MAS", "MS", "MMCC", "TBM"], bus_codes: ["CMBT", "KOYAMBEDU", "GUINDY"] },
  { city_id: "HYD", label: "Hyderabad, Telangana", city: "Hyderabad", state: "Telangana", country: "India", flight_codes: ["HYD"], rail_codes: ["SC", "HYB", "NZB", "KCG"], bus_codes: ["MGBS", "JBS", "MIYAPUR"] },
  { city_id: "KOL", label: "Kolkata, West Bengal", city: "Kolkata", state: "West Bengal", country: "India", flight_codes: ["CCU"], rail_codes: ["HWH", "SDAH", "KOAA"], bus_codes: ["ESPLANADE", "KARUNAMOYEE", "HOWRAH"] },
  
  // Major Cities
  { city_id: "PUN", label: "Pune, Maharashtra", city: "Pune", state: "Maharashtra", country: "India", flight_codes: ["PNQ"], rail_codes: ["PUNE", "PNVL"], bus_codes: ["SWARGATE", "SHIVAJINAGAR", "PUNE_STATION"] },
  { city_id: "AMD", label: "Ahmedabad, Gujarat", city: "Ahmedabad", state: "Gujarat", country: "India", flight_codes: ["AMD"], rail_codes: ["ADI", "AHME"], bus_codes: ["GEETA_MANDIR", "PALDI", "RANIP"] },
  { city_id: "JAI", label: "Jaipur, Rajasthan", city: "Jaipur", state: "Rajasthan", country: "India", flight_codes: ["JAI"], rail_codes: ["JP", "JPS"], bus_codes: ["SINDHI_CAMP", "NARAYAN_SINGH"] },
  { city_id: "LKO", label: "Lucknow, Uttar Pradesh", city: "Lucknow", state: "Uttar Pradesh", country: "India", flight_codes: ["LKO"], rail_codes: ["LKO", "LJN"], bus_codes: ["ALAMBAGH", "KAISERBAGH", "CHARBAGH"] },
  { city_id: "GOA", label: "Goa", city: "Goa", state: "Goa", country: "India", flight_codes: ["GOI", "GOX"], rail_codes: ["MAO", "KRMI", "THVM"], bus_codes: ["PANAJI", "MARGAO", "MAPUSA"] },
  { city_id: "COK", label: "Kochi, Kerala", city: "Kochi", state: "Kerala", country: "India", flight_codes: ["COK"], rail_codes: ["ERS", "ERNR"], bus_codes: ["ERNAKULAM", "VYTTILA", "ALUVA"] },
  { city_id: "TRV", label: "Thiruvananthapuram, Kerala", city: "Thiruvananthapuram", state: "Kerala", country: "India", flight_codes: ["TRV"], rail_codes: ["TVC"], bus_codes: ["THAMPANOOR", "EAST_FORT"] },
  { city_id: "VNS", label: "Varanasi, Uttar Pradesh", city: "Varanasi", state: "Uttar Pradesh", country: "India", flight_codes: ["VNS"], rail_codes: ["BSB", "BCY"], bus_codes: ["CANTT", "VARANASI_JN"] },
  { city_id: "PAT", label: "Patna, Bihar", city: "Patna", state: "Bihar", country: "India", flight_codes: ["PAT"], rail_codes: ["PNBE", "PPTA", "DNR"], bus_codes: ["GANDHI_MAIDAN", "PATNA_JN"] },
  { city_id: "BPL", label: "Bhopal, Madhya Pradesh", city: "Bhopal", state: "Madhya Pradesh", country: "India", flight_codes: ["BHO"], rail_codes: ["BPL", "HBJ"], bus_codes: ["ISBT_BHOPAL", "NADRA_BUS_STAND"] },
  { city_id: "IND", label: "Indore, Madhya Pradesh", city: "Indore", state: "Madhya Pradesh", country: "India", flight_codes: ["IDR"], rail_codes: ["INDB"], bus_codes: ["SARWATE", "GANGWAL"] },
  { city_id: "NGP", label: "Nagpur, Maharashtra", city: "Nagpur", state: "Maharashtra", country: "India", flight_codes: ["NAG"], rail_codes: ["NGP"], bus_codes: ["GANESHPETH", "NAGPUR_CENTRAL"] },
  { city_id: "SUR", label: "Surat, Gujarat", city: "Surat", state: "Gujarat", country: "India", flight_codes: ["STV"], rail_codes: ["ST", "UDN"], bus_codes: ["UDHNA", "KATARGAM"] },
  { city_id: "VAD", label: "Vadodara, Gujarat", city: "Vadodara", state: "Gujarat", country: "India", flight_codes: ["BDQ"], rail_codes: ["BRC", "BDTS"], bus_codes: ["VADODARA_CENTRAL"] },
  { city_id: "VIZ", label: "Visakhapatnam, Andhra Pradesh", city: "Visakhapatnam", state: "Andhra Pradesh", country: "India", flight_codes: ["VTZ"], rail_codes: ["VSKP"], bus_codes: ["DWARAKA", "GAJUWAKA"] },
  { city_id: "VIJ", label: "Vijayawada, Andhra Pradesh", city: "Vijayawada", state: "Andhra Pradesh", country: "India", flight_codes: ["VGA"], rail_codes: ["BZA"], bus_codes: ["PANDIT_NEHRU", "VIJAYAWADA_CENTRAL"] },
  { city_id: "MYS", label: "Mysore, Karnataka", city: "Mysore", state: "Karnataka", country: "India", flight_codes: ["MYQ"], rail_codes: ["MYS"], bus_codes: ["MYSORE_CENTRAL", "SATELLITE"] },
  { city_id: "CMB", label: "Coimbatore, Tamil Nadu", city: "Coimbatore", state: "Tamil Nadu", country: "India", flight_codes: ["CJB"], rail_codes: ["CBE"], bus_codes: ["GANDHIPURAM", "UKKADAM", "SINGANALLUR"] },
  { city_id: "MAD", label: "Madurai, Tamil Nadu", city: "Madurai", state: "Tamil Nadu", country: "India", flight_codes: ["IXM"], rail_codes: ["MDU"], bus_codes: ["PERIYAR", "MATTUTHAVANI"] },
  { city_id: "TRC", label: "Tiruchirappalli, Tamil Nadu", city: "Tiruchirappalli", state: "Tamil Nadu", country: "India", flight_codes: ["TRZ"], rail_codes: ["TPJ"], bus_codes: ["CENTRAL_BUS_STAND", "CHATRAM"] },
  { city_id: "CHD", label: "Chandigarh", city: "Chandigarh", state: "Chandigarh", country: "India", flight_codes: ["IXC"], rail_codes: ["CDG"], bus_codes: ["ISBT_43", "ISBT_17"] },
  { city_id: "AGR", label: "Agra, Uttar Pradesh", city: "Agra", state: "Uttar Pradesh", country: "India", flight_codes: ["AGR"], rail_codes: ["AGC", "AF"], bus_codes: ["IDGAH", "ISBT_AGRA"] },
  { city_id: "AMR", label: "Amritsar, Punjab", city: "Amritsar", state: "Punjab", country: "India", flight_codes: ["ATQ"], rail_codes: ["ASR"], bus_codes: ["ISBT_AMRITSAR"] },
  { city_id: "DUN", label: "Dehradun, Uttarakhand", city: "Dehradun", state: "Uttarakhand", country: "India", flight_codes: ["DED"], rail_codes: ["DDN"], bus_codes: ["ISBT_DEHRADUN", "PARADE_GROUND"] },
  { city_id: "SIM", label: "Shimla, Himachal Pradesh", city: "Shimla", state: "Himachal Pradesh", country: "India", flight_codes: ["SLV"], rail_codes: ["SML"], bus_codes: ["ISBT_SHIMLA", "OLD_BUS_STAND"] },
  { city_id: "UDR", label: "Udaipur, Rajasthan", city: "Udaipur", state: "Rajasthan", country: "India", flight_codes: ["UDR"], rail_codes: ["UDZ"], bus_codes: ["UDAIPUR_CENTRAL"] },
  { city_id: "JDP", label: "Jodhpur, Rajasthan", city: "Jodhpur", state: "Rajasthan", country: "India", flight_codes: ["JDH"], rail_codes: ["JU"], bus_codes: ["PAOTA", "RAIKA_BAGH"] },
]

// Initialize Fuse.js for fuzzy search
let fuseInstance: Fuse<TransportLocation> | null = null

function getFuseInstance(): Fuse<TransportLocation> {
  if (!fuseInstance) {
    fuseInstance = new Fuse(INDIA_CITIES, {
      keys: [
        { name: 'city', weight: 2 },
        { name: 'label', weight: 1.5 },
        { name: 'state', weight: 1 },
        { name: 'city_id', weight: 1 },
        { name: 'flight_codes', weight: 0.8 },
        { name: 'rail_codes', weight: 0.8 },
        { name: 'bus_codes', weight: 0.8 },
      ],
      threshold: 0.3,
      distance: 100,
      includeScore: true,
    })
  }
  return fuseInstance
}

function searchLocations(query: string): TransportLocation[] {
  const fuse = getFuseInstance()
  const results = fuse.search(query)
  return results.slice(0, 10).map(r => r.item)
}

export type TransportMode = 'flight' | 'train' | 'bus'

interface TransportAutocompleteProps {
  value: string
  selectedLocation: TransportLocation | null
  onChange: (value: string, location: TransportLocation | null) => void
  mode: TransportMode
  placeholder?: string
  label?: string
  testId?: string
  disabled?: boolean
}

const MODE_ICONS = {
  flight: Plane,
  train: Train,
  bus: Bus,
}

const MODE_COLORS = {
  flight: 'blue',
  train: 'blue',
  bus: 'orange',
}

export default function TransportAutocomplete({
  value,
  selectedLocation,
  onChange,
  mode,
  placeholder,
  label = "Location",
  testId = "transport-input",
  disabled = false,
}: TransportAutocompleteProps) {
  const [query, setQuery] = useState(value)
  const [suggestions, setSuggestions] = useState<TransportLocation[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isLoading, setIsLoading] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const Icon = MODE_ICONS[mode]
  const color = MODE_COLORS[mode]

  // Default placeholders by mode
  const defaultPlaceholder = placeholder || (
    mode === 'flight' ? 'City or airport' :
    mode === 'train' ? 'City or station (e.g., Delhi)' :
    'City (e.g., Mumbai)'
  )

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

  /**
   * Fetch suggestions - uses backend API for bus mode, client-side for others
   */
  const fetchSuggestions = async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSuggestions([])
      return
    }

    setIsLoading(true)
    
    try {
      // For BUS mode: Use backend autocomplete API with state bias
      if (mode === 'bus') {
        // Use API base URL from environment or relative path
        const apiBase = process.env.NEXT_PUBLIC_API_BASE || ''
        const response = await fetch(
          `${apiBase}/api/autocomplete/bus?q=${encodeURIComponent(searchQuery)}&mode=bus&limit=15`
        )
        
        if (response.ok) {
          const data = await response.json()
          
          // Convert API response to TransportLocation format
          const busResults: TransportLocation[] = data.results.map((r: any) => ({
            city_id: r.id,
            label: r.label,
            city: r.city,
            state: r.state || 'India',
            country: 'India',
            flight_codes: [],
            rail_codes: [],
            bus_codes: [r.id], // Use ID as bus code
            // Extra fields for display
            _type: r.type,
            _operator: r.operator,
            _isSearchSurface: r.is_search_surface,
            _cityLocal: r.city_local,
          }))
          
          setSuggestions(busResults)
          setIsLoading(false)
          return
        }
      }
      
      // For other modes OR if bus API fails: Use client-side Fuse.js search
      setTimeout(() => {
        let results = searchLocations(searchQuery)
        
        // Filter by mode support
        results = results.filter(loc => {
          if (mode === 'flight') return loc.flight_codes.length > 0
          if (mode === 'train') return loc.rail_codes.length > 0
          if (mode === 'bus') return loc.bus_codes.length > 0
          return true
        })
        
        setSuggestions(results)
        setIsLoading(false)
      }, 100)
      
    } catch (error) {
      console.error('Autocomplete fetch error:', error)
      // Fallback to client-side search on error
      let results = searchLocations(searchQuery)
      results = results.filter(loc => {
        if (mode === 'flight') return loc.flight_codes.length > 0
        if (mode === 'train') return loc.rail_codes.length > 0
        if (mode === 'bus') return loc.bus_codes.length > 0
        return true
      })
      setSuggestions(results)
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setQuery(newValue)
    setSelectedIndex(-1)
    setShowSuggestions(true)

    // Clear selected location when user types
    if (selectedLocation) {
      onChange(newValue, null)
    }

    // Debounce search
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(newValue)
    }, 150)
  }

  const handleSelectLocation = (location: TransportLocation) => {
    const displayValue = location.label
    setQuery(displayValue)
    setShowSuggestions(false)
    onChange(displayValue, location)
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
          handleSelectLocation(suggestions[selectedIndex])
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

  // Get codes to display based on mode
  const getCodeDisplay = (location: TransportLocation) => {
    if (mode === 'flight') return location.flight_codes[0] || location.city_id
    if (mode === 'train') return location.rail_codes[0] || location.city_id
    if (mode === 'bus') return location.city_id
    return location.city_id
  }

  // Check if location supports current mode
  const getModeWarning = (location: TransportLocation) => {
    if (mode === 'flight' && location.flight_codes.length === 0) {
      return "No airport in this city"
    }
    if (mode === 'train' && location.rail_codes.length === 0) {
      return "No train station in this city"
    }
    if (mode === 'bus' && location.bus_codes.length === 0) {
      return "No bus service in this city"
    }
    return null
  }

  // Validation state
  const isValid = selectedLocation !== null
  const showValidationHint = query.length >= 2 && !selectedLocation && !showSuggestions

  return (
    <div ref={wrapperRef} className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div className="relative">
        <Icon className={`absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 ${
          isValid ? `text-${color}-600` : 'text-gray-400'
        }`} />
        <input
          ref={inputRef}
          data-testid={testId}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder={defaultPlaceholder}
          disabled={disabled}
          className={`w-full pl-10 pr-10 py-3 border rounded-xl focus:ring-2 focus:border-transparent transition-colors ${
            isValid 
              ? `border-${color}-500 focus:ring-${color}-500 bg-${color}-50` 
              : 'border-gray-300 focus:ring-blue-500'
          } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          autoComplete="off"
        />
        {/* Loading indicator */}
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className={`animate-spin rounded-full h-4 w-4 border-b-2 border-${color}-600`}></div>
          </div>
        )}
        {/* Valid checkmark */}
        {isValid && !isLoading && (
          <div className={`absolute right-3 top-1/2 -translate-y-1/2 text-${color}-600`}>
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>

      {/* Validation hint */}
      {showValidationHint && (
        <p className="mt-1 text-xs text-amber-600 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Please select a city from the dropdown
        </p>
      )}

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto">
          <div className="sticky top-0 bg-gray-50 px-4 py-2 border-b border-gray-200">
            <span className="text-xs text-gray-600 font-medium">
              {mode === 'bus' ? 'Select a bus stop or city' : 'Select a city'}
            </span>
          </div>
          {suggestions.map((location, index) => {
            const warning = getModeWarning(location)
            // For bus mode, check if this is a bus stop from API
            const isBusStop = mode === 'bus' && (location as any)._type === 'bus_stop'
            const busOperator = (location as any)._operator
            const isSearchSurface = (location as any)._isSearchSurface
            
            return (
              <button
                key={location.city_id}
                type="button"
                onClick={() => !warning && handleSelectLocation(location)}
                disabled={!!warning}
                className={`w-full px-4 py-3 text-left transition-colors border-b border-gray-100 last:border-b-0 last:rounded-b-xl ${
                  warning 
                    ? 'bg-gray-50 cursor-not-allowed opacity-60'
                    : index === selectedIndex 
                      ? 'bg-blue-50 ring-2 ring-inset ring-blue-500' 
                      : 'hover:bg-blue-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  {/* Icon/Badge - Different for bus stops vs cities */}
                  <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                    warning ? 'bg-gray-200' : 
                    isBusStop && isSearchSurface ? 'bg-green-100' :
                    isBusStop ? 'bg-orange-100' :
                    `bg-${color}-100`
                  }`}>
                    {isBusStop ? (
                      <span className={`text-lg ${isSearchSurface ? 'text-green-600' : 'text-orange-600'}`}>
                        🚌
                      </span>
                    ) : (
                      <span className={`font-bold text-sm ${warning ? 'text-gray-500' : `text-${color}-600`}`}>
                        {getCodeDisplay(location)}
                      </span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 truncate flex items-center gap-2">
                      {location.label}
                      {isSearchSurface && isBusStop && (
                        <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                          Depot
                        </span>
                      )}
                    </div>
                    {warning ? (
                      <div className="text-sm text-amber-600">{warning}</div>
                    ) : (
                      <div className="text-sm text-gray-500">
                        {mode === 'bus' && isBusStop ? (
                          <span>
                            {location.city}, {location.state}
                            {busOperator && <span className="ml-2 text-gray-400">• {busOperator}</span>}
                          </span>
                        ) : mode === 'bus' ? (
                          <span>{location.state} - All stops</span>
                        ) : mode === 'train' && location.rail_codes.length > 0 ? (
                          <span>Stations: {location.rail_codes.slice(0, 3).join(', ')}</span>
                        ) : mode === 'flight' && location.flight_codes.length > 0 ? (
                          <span>Airport: {location.flight_codes.join(', ')}</span>
                        ) : null}
                      </div>
                    )}
                  </div>
                </div>
              </button>
            )
          })}
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

// Export the location type and cities for reuse
export { INDIA_CITIES }
