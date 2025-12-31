'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Plane, Hotel, Calendar, Users, Train, Bus } from 'lucide-react'
import TripTypeSelector from './TripTypeSelector'
import CabinClassSelector from './CabinClassSelector'
import AdvancedPassengerModal from './AdvancedPassengerModal'
import EnhancedHotelRoomSelector from './EnhancedHotelRoomSelector'
import DateInputs from './DateInputs'
import AirportAutocomplete from './AirportAutocomplete'
import ValidatedAirportInput from './ValidatedAirportInput'
import TransportAutocomplete, { TransportLocation } from './TransportAutocomplete'
import BusLocationAutocomplete, { BusPlace } from './BusLocationAutocomplete'
import TrainStationAutocomplete, { TrainStationOption } from './TrainStationAutocomplete'
import HotelLocationAutocomplete, { HotelCity, HotelDestination, HotelDestinationType } from './HotelLocationAutocomplete'
import { Airport, validateFlightSearch, extractIATACodes } from '@/lib/airportValidation'
import { SearchButtonMicrocopy } from '@/components/trust/Microcopy'
import { PREFILL_SEARCH_EVENT, PrefillEventData } from '@/components/seo/InternalLinks'
import { 
  getModifySearchPayload, 
  clearModifySearchPayload,
  FlightSearchPayload,
  HotelSearchPayload,
  BusSearchPayload,
  TrainSearchPayload,
  ServiceType
} from '@/lib/modifySearchStore'

type SearchType = 'flights' | 'hotels' | 'trains' | 'buses'
type TripType = 'oneway' | 'roundtrip' | 'multicity'
type CabinClass = 'economy' | 'premium_economy' | 'business' | 'first'
type RoomType = 'Standard' | 'Deluxe' | 'Suite'

interface Child {
  age: number
}

interface PassengerData {
  adults: number
  children: Child[]
  infants: number
}

interface FlightSegment {
  id: string
  origin: string
  destination: string
  date: string
}

interface Room {
  adults: number
  children: number[]
  roomType: RoomType
  ac: boolean
}

interface EnhancedHotelRoomData {
  rooms: Room[]
}

interface SearchBarV3Props {
  defaultTab?: SearchType
}

export default function SearchBarV3({ defaultTab = 'flights' }: SearchBarV3Props) {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // Ref for auto-scroll when popular cards are clicked
  const searchFormRef = useRef<HTMLDivElement>(null)
  
  // SSR-safe state initialization
  const [mounted, setMounted] = useState(false)
  
  // Get active tab from URL or default
  const getTabFromUrl = (): SearchType => {
    const tabParam = searchParams.get('tab') as SearchType | null
    if (tabParam && ['flights', 'trains', 'buses', 'hotels'].includes(tabParam)) {
      return tabParam
    }
    return defaultTab
  }
  
  const [searchType, setSearchTypeState] = useState<SearchType>(getTabFromUrl)
  
  // Sync with URL changes (browser back/forward, navigation clicks)
  useEffect(() => {
    const urlTab = getTabFromUrl()
    if (urlTab !== searchType) {
      setSearchTypeState(urlTab)
    }
  }, [searchParams]) // eslint-disable-line react-hooks/exhaustive-deps
  
  // Update URL when tab changes
  const setSearchType = (newType: SearchType) => {
    setSearchTypeState(newType)
    
    // Update URL param
    const params = new URLSearchParams()
    params.set('tab', newType)
    router.push(`/?${params.toString()}`, { scroll: false })
  }
  
  // Get deterministic default dates (SSR-safe)
  const getTodayDate = () => {
    const today = new Date()
    return today.toISOString().split('T')[0]
  }
  
  const getTomorrowDate = () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow.toISOString().split('T')[0]
  }
  
  const getDayAfterTomorrow = () => {
    const dayAfter = new Date()
    dayAfter.setDate(dayAfter.getDate() + 2)
    return dayAfter.toISOString().split('T')[0]
  }

  // Flights state with validated airports
  const [tripType, setTripType] = useState<TripType>('oneway')
  const [origin, setOrigin] = useState<Airport | null>(null)
  const [destination, setDestination] = useState<Airport | null>(null)
  const [departureDate, setDepartureDate] = useState(getTodayDate())
  const [returnDate, setReturnDate] = useState(getTomorrowDate())
  const [cabinClass, setCabinClass] = useState<CabinClass>('economy')
  const [passengers, setPassengers] = useState<PassengerData>({
    adults: 1,
    children: [],
    infants: 0,
  })
  const [multiCitySegments, setMultiCitySegments] = useState<FlightSegment[]>([
    { id: 'seg-1', origin: '', destination: '', date: getTodayDate() },
    { id: 'seg-2', origin: '', destination: '', date: getTomorrowDate() },
  ])
  const [showPassengerModal, setShowPassengerModal] = useState(false)
  
  // Validation state
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [originValid, setOriginValid] = useState(false)
  const [destinationValid, setDestinationValid] = useState(false)
  
  // Nearby airports state
  const [includeNearbyOrigin, setIncludeNearbyOrigin] = useState(false)
  const [includeNearbyDestination, setIncludeNearbyDestination] = useState(false)
  
  // Hotels state - Now stores full HotelDestination with type (CITY/AREA/HOTEL)
  const [selectedHotelDestination, setSelectedHotelDestination] = useState<HotelDestination | null>(null)
  const [checkIn, setCheckIn] = useState(getTodayDate())
  const [checkOut, setCheckOut] = useState(getTomorrowDate())
  const [hotelRooms, setHotelRooms] = useState<EnhancedHotelRoomData>({
    rooms: [{ adults: 2, children: [], roomType: 'Standard', ac: true }],
  })
  const [showRoomModal, setShowRoomModal] = useState(false)

  // Trains & Buses state - with validated locations
  // STATION-FIRST: trainOrigin/Destination store TrainStationOption with .value (e.g., "MUMBAI_ALL" or "CSMT")
  const [trainOrigin, setTrainOrigin] = useState<TrainStationOption | null>(null)
  const [trainDestination, setTrainDestination] = useState<TrainStationOption | null>(null)
  const [trainDate, setTrainDate] = useState(getTomorrowDate())
  const [trainPassengers, setTrainPassengers] = useState(1)
  const [trainClass, setTrainClass] = useState<string>('')
  
  const [busOriginText, setBusOriginText] = useState('')
  const [busOriginPlace, setBusOriginPlace] = useState<BusPlace | null>(null)
  const [busDestinationText, setBusDestinationText] = useState('')
  const [busDestinationPlace, setBusDestinationPlace] = useState<BusPlace | null>(null)
  const [busDate, setBusDate] = useState(getTomorrowDate())
  const [busPassengers, setBusPassengers] = useState(1)
  const [busType, setBusType] = useState<string>('')  // '', 'ac_seater', 'ac_sleeper', 'non_ac'

  // Validation flags for trains - STATION-FIRST: must have valid station/ALL selection
  const trainOriginValid = trainOrigin !== null
  const trainDestinationValid = trainDestination !== null
  const trainSearchEnabled = trainOriginValid && trainDestinationValid && 
    trainOrigin?.value !== trainDestination?.value
  
  // Validation flags for buses - STRICT ID-based validation
  // CRITICAL: Both origin AND destination MUST have valid place_id
  // This prevents the "Satara → Karad" becoming "Satara → Satara" bug
  const busOriginValid = busOriginPlace !== null && busOriginPlace.place_id !== ''
  const busDestinationValid = busDestinationPlace !== null && busDestinationPlace.place_id !== ''
  const busSamePlace = busOriginPlace?.place_id === busDestinationPlace?.place_id && 
                       busOriginPlace !== null && busDestinationPlace !== null
  const busSearchEnabled = busOriginValid && busDestinationValid && !busSamePlace

  // Track if we're in modify mode - prevents date sync from overwriting hydrated values
  const [isHydrating, setIsHydrating] = useState(() => {
    // Check if we're in modify mode on initial load
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      return params.get('modify') === 'true'
    }
    return false
  })

  // Synchronize dates between all modes (skip during hydration)
  useEffect(() => {
    // Skip date sync when we're hydrating from modify search
    if (isHydrating) {
      console.log('[SearchBarV3] Skipping date sync - isHydrating=true')
      return
    }
    
    // When switching modes, sync dates (but not from/to - those are mode-specific)
    if (searchType === 'flights') {
      setCheckIn(departureDate)
      setCheckOut(returnDate)
    } else if (searchType === 'hotels') {
      setDepartureDate(checkIn)
      setReturnDate(checkOut)
    } else if (searchType === 'trains') {
      // Sync train date with departure
      if (trainDate !== departureDate) {
        setTrainDate(departureDate)
      }
    } else if (searchType === 'buses') {
      // Sync bus date with departure
      if (busDate !== departureDate) {
        setBusDate(departureDate)
      }
    }
    
    // Reset mode-specific filters when switching
    if (searchType === 'trains') {
      setTrainClass('')
    } else if (searchType === 'buses') {
      setBusType('')
    }
  }, [searchType])  // Only run when searchType changes

  // Sync dates when user changes flight dates
  const handleDepartureDateChange = (date: string) => {
    setDepartureDate(date)
    setCheckIn(date)  // Sync to hotel check-in
    setTrainDate(date)  // Sync to train date
    setBusDate(date)  // Sync to bus date
  }

  const handleReturnDateChange = (date: string) => {
    setReturnDate(date)
    setCheckOut(date)  // Sync to hotel check-out
  }

  // Sync dates when user changes hotel dates
  const handleCheckInChange = (date: string) => {
    setCheckIn(date)
    setDepartureDate(date)  // Sync to flight departure
    setTrainDate(date)
    setBusDate(date)
  }

  const handleCheckOutChange = (date: string) => {
    setCheckOut(date)
    setReturnDate(date)  // Sync to flight return
  }

  // Sync dates when user changes train/bus dates
  const handleTrainDateChange = (date: string) => {
    setTrainDate(date)
    setDepartureDate(date)
    setCheckIn(date)
    setBusDate(date)
  }

  const handleBusDateChange = (date: string) => {
    setBusDate(date)
    setDepartureDate(date)
    setCheckIn(date)
    setTrainDate(date)
  }

  useEffect(() => {
    setMounted(true)
  }, [])

  /**
   * MODIFY SEARCH HYDRATION
   * 
   * When user clicks "Modify Search" on results/vendor page:
   * 1. ModifySearchButton saves search payload to localStorage
   * 2. User is navigated to /?tab={service}&modify=true
   * 3. This effect reads from localStorage and hydrates the form
   * 
   * localStorage is the SINGLE SOURCE OF TRUTH - not URL params.
   * This ensures data persists even if URL gets truncated.
   * 
   * NOTE: Payload is cleared AFTER successful form submit, not here.
   */
  useEffect(() => {
    if (!mounted) return
    
    const isModify = searchParams.get('modify') === 'true'
    const tab = searchParams.get('tab') as ServiceType | null
    
    if (!isModify || !tab) return
    
    console.log(`[SearchBarV3] Hydrating ${tab} form from localStorage`)
    
    // Set hydrating flag to prevent date sync from overwriting values
    setIsHydrating(true)
    
    // Hydrate based on service type
    switch (tab) {
      case 'flights': {
        const payload = getModifySearchPayload<FlightSearchPayload>('flights')
        if (payload) {
          // Use FULL airport objects from payload (passes validation)
          if (payload.origin && typeof payload.origin === 'object') {
            setOrigin({
              iata: payload.origin.iata,
              name: payload.origin.name,
              city: payload.origin.city,
              country: payload.origin.country,
            })
            setOriginValid(true)
          }
          if (payload.destination && typeof payload.destination === 'object') {
            setDestination({
              iata: payload.destination.iata,
              name: payload.destination.name,
              city: payload.destination.city,
              country: payload.destination.country,
            })
            setDestinationValid(true)
          }
          if (payload.departure_date) {
            setDepartureDate(payload.departure_date)
          }
          if (payload.return_date) {
            setReturnDate(payload.return_date)
            setTripType('roundtrip')
          } else {
            setTripType('oneway')
          }
          if (payload.adults) {
            setPassengers(prev => ({ ...prev, adults: payload.adults }))
          }
          if (payload.cabin_class) {
            setCabinClass(payload.cabin_class as CabinClass)
          }
          if (payload.trip_type) {
            setTripType(payload.trip_type as TripType)
          }
          // NOTE: Don't clear here - clear after successful search submit
        }
        break
      }
      
      case 'hotels': {
        const payload = getModifySearchPayload<HotelSearchPayload>('hotels')
        if (payload) {
          // Use full destination object - preserves type (CITY/AREA/HOTEL)
          if (payload.destination && typeof payload.destination === 'object') {
            setSelectedHotelDestination({
              id: payload.destination.id || `CITY_${payload.destination.city.toUpperCase()}`,
              type: (payload.destination.type as HotelDestinationType) || 'CITY',
              label: payload.destination.label,
              city: payload.destination.city,
              country: payload.destination.country,
              areaName: payload.destination.areaName,
              hotelName: payload.destination.hotelName,
              hotelId: payload.destination.hotelId,
              latitude: payload.destination.latitude,
              longitude: payload.destination.longitude,
            })
          }
          if (payload.check_in) {
            setCheckIn(payload.check_in)
          }
          if (payload.check_out) {
            setCheckOut(payload.check_out)
          }
          if (payload.adults) {
            setHotelRooms({
              rooms: [{ adults: payload.adults, children: [], roomType: 'Standard', ac: true }]
            })
          }
          // NOTE: Don't clear here - clear after successful search submit
        }
        break
      }
      
      case 'buses': {
        const payload = getModifySearchPayload<BusSearchPayload>('buses')
        if (payload) {
          if (payload.origin) {
            setBusOriginText(payload.origin)
            setBusOriginPlace({
              place_id: `modify_${payload.origin.toLowerCase().replace(/\s+/g, '_')}`,
              name: payload.origin,
              type: 'city'
            })
          }
          if (payload.destination) {
            setBusDestinationText(payload.destination)
            setBusDestinationPlace({
              place_id: `modify_${payload.destination.toLowerCase().replace(/\s+/g, '_')}`,
              name: payload.destination,
              type: 'city'
            })
          }
          if (payload.departure_date) {
            setBusDate(payload.departure_date)
          }
          if (payload.passengers) {
            setBusPassengers(payload.passengers)
          }
          if (payload.bus_type) {
            setBusType(payload.bus_type)
          }
          // NOTE: Don't clear here - clear after successful search submit
        }
        break
      }
      
      case 'trains': {
        const payload = getModifySearchPayload<TrainSearchPayload>('trains')
        if (payload) {
          // Use origin_city for display if available, otherwise use origin
          const originLabel = payload.origin_city || payload.origin
          const destLabel = payload.destination_city || payload.destination
          
          if (payload.origin) {
            setTrainOrigin({
              value: payload.origin,
              label: originLabel.includes('(All') ? originLabel : `${originLabel} (All Stations)`,
              type: payload.origin.endsWith('_ALL') ? 'city_all' : 'station'
            })
          }
          if (payload.destination) {
            setTrainDestination({
              value: payload.destination,
              label: destLabel.includes('(All') ? destLabel : `${destLabel} (All Stations)`,
              type: payload.destination.endsWith('_ALL') ? 'city_all' : 'station'
            })
          }
          if (payload.departure_date) {
            setTrainDate(payload.departure_date)
          }
          if (payload.passengers) {
            setTrainPassengers(payload.passengers)
          }
          if (payload.train_class) {
            setTrainClass(payload.train_class)
          }
          // NOTE: Don't clear here - clear after successful search submit
        }
        break
      }
    }
    
    // Clear hydrating flag after a short delay to allow state to settle
    setTimeout(() => {
      setIsHydrating(false)
    }, 100)
  }, [mounted, searchParams])

  /**
   * PREFILL EVENT LISTENER
   * 
   * PRODUCT RULE: Popular cards simulate typing — they are NOT navigation links.
   * 
   * When a popular card is clicked, it dispatches a custom event.
   * This listener updates the search form state directly (like manual typing).
   * Then scrolls to the search form so user can see the prefilled values.
   * 
   * UI Display Rules:
   * - Always display `label` (e.g., "Bangalore")
   * - Never show backend tokens like `_ALL` in UI
   * 
   * ✅ Updates form state (same as typing in input)
   * ✅ Scrolls to search form after prefill
   * ❌ Does NOT change URL
   * ❌ Does NOT trigger API call
   * ❌ Does NOT navigate
   */
  const handlePrefillEvent = useCallback((event: Event) => {
    const customEvent = event as CustomEvent<PrefillEventData>
    const data = customEvent.detail
    
    // HARD GUARD: This handler ONLY updates state, never navigates
    if (!data || !data.service) return
    
    // Switch to the appropriate tab if needed
    if (data.service !== searchType) {
      setSearchTypeState(data.service)
    }
    
    // Update form state based on service type (exactly like manual typing)
    if (data.service === 'buses' && data.origin && data.destination) {
      // BUS: Update origin and destination state
      // Use label for display, token for backend (same for buses)
      setBusOriginText(data.origin.label)
      setBusOriginPlace({
        place_id: `popular_${data.origin.token.toLowerCase().replace(/\s+/g, '_')}`,
        name: data.origin.label,
        type: 'city'
      })
      setBusDestinationText(data.destination.label)
      setBusDestinationPlace({
        place_id: `popular_${data.destination.token.toLowerCase().replace(/\s+/g, '_')}`,
        name: data.destination.label,
        type: 'city'
      })
    } else if (data.service === 'trains' && data.origin && data.destination) {
      // TRAIN: Update origin_city and destination_city state
      // Use label for UI display, token for backend API
      // TRAIN SEARCH GUARD: Ensure tokens end with _ALL
      const originToken = data.origin.token.endsWith('_ALL') 
        ? data.origin.token 
        : `${data.origin.token}_ALL`
      const destToken = data.destination.token.endsWith('_ALL') 
        ? data.destination.token 
        : `${data.destination.token}_ALL`
      
      setTrainOrigin({
        value: originToken,                           // Backend token: "BANGALORE_ALL"
        label: `${data.origin.label} (All Stations)`, // UI display: "Bangalore (All Stations)"
        type: 'city_all'
      })
      setTrainDestination({
        value: destToken,                                  // Backend token: "CHENNAI_ALL"
        label: `${data.destination.label} (All Stations)`, // UI display: "Chennai (All Stations)"
        type: 'city_all'
      })
    } else if (data.service === 'hotels' && data.city) {
      // HOTEL: Update destination state with CITY type
      // This prefills the form like manual typing - user still needs to click Search
      setSelectedHotelDestination({
        id: `CITY_${data.city.toUpperCase()}`,
        type: 'CITY',
        label: `${data.city}, India`,
        city: data.city,
        country: 'India',
      })
    }
    
    // AUTO-SCROLL: Scroll search form into view after prefill
    // This helps user see the prefilled values without manual scrolling
    if (data.scrollToForm && searchFormRef.current) {
      // Small delay to allow state update to render
      setTimeout(() => {
        searchFormRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
      }, 100)
    }
    
    // STOP HERE — no navigation, no URL mutation, no API calls
    // Dates remain untouched - user must select manually
  }, [searchType])

  // Register event listener for prefill events from popular cards
  useEffect(() => {
    if (!mounted) return
    
    window.addEventListener(PREFILL_SEARCH_EVENT, handlePrefillEvent)
    
    return () => {
      window.removeEventListener(PREFILL_SEARCH_EVENT, handlePrefillEvent)
    }
  }, [mounted, handlePrefillEvent])

  const totalPassengers = passengers.adults + passengers.children.length + passengers.infants
  const totalGuests = hotelRooms.rooms.reduce((sum, room) => sum + room.adults + room.children.length, 0)

  const validateFlightDates = (): boolean => {
    if (tripType === 'multicity') {
      // Import validation logic
      const segments = multiCitySegments.map(seg => ({
        origin: seg.origin,
        destination: seg.destination,
        date: seg.date
      }))
      
      // Check all segments filled
      for (let i = 0; i < segments.length; i++) {
        const seg = segments[i]
        if (!seg.origin || !seg.destination || !seg.date) {
          alert(`Flight ${i + 1}: Please fill all fields`)
          return false
        }
        
        // Check origin !== destination
        if (seg.origin.toUpperCase() === seg.destination.toUpperCase()) {
          alert(`Flight ${i + 1}: Origin and destination must be different`)
          return false
        }
      }
      
      // Check dates in order
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      
      for (let i = 0; i < segments.length; i++) {
        const currentDate = new Date(segments[i].date)
        
        if (i === 0 && currentDate < today) {
          alert('First flight date cannot be in the past')
          return false
        }
        
        if (i > 0) {
          const prevDate = new Date(segments[i - 1].date)
          if (currentDate <= prevDate) {
            alert(`Flight ${i + 1} must be after Flight ${i}`)
            return false
          }
        }
      }
    } else {
      // Validate one-way or round-trip
      if (!origin || !destination || !departureDate) {
        alert('Please fill all required fields')
        return false
      }
      
      // Check origin !== destination
      if (origin.toUpperCase() === destination.toUpperCase()) {
        alert('Origin and destination must be different')
        return false
      }
      
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const depDate = new Date(departureDate)
      
      if (depDate < today) {
        alert('Departure date cannot be in the past')
        return false
      }
      
      if (tripType === 'roundtrip') {
        if (!returnDate) {
          alert('Please select return date')
          return false
        }
        const retDate = new Date(returnDate)
        if (retDate <= depDate) {
          alert('Return date must be after departure date')
          return false
        }
      }
    }
    
    // Validate passengers
    const totalPassengers = passengers.adults + passengers.children.length + passengers.infants
    if (passengers.adults < 1) {
      alert('At least 1 adult is required')
      return false
    }
    if (passengers.infants > passengers.adults) {
      alert('Number of infants cannot exceed number of adults')
      return false
    }
    if (totalPassengers > 9) {
      alert('Maximum 9 passengers allowed')
      return false
    }
    
    return true
  }

  const handleFlightSearch = () => {
    // Validate using new validation function
    const validation = validateFlightSearch(
      origin,
      destination,
      departureDate,
      tripType === 'roundtrip' ? returnDate : undefined,
      tripType
    )

    if (!validation.isValid) {
      setValidationErrors(validation.errors)
      alert(validation.errors.join('\n'))
      return
    }

    // Extract IATA codes safely
    const codes = extractIATACodes(origin, destination)
    if (!codes) {
      alert('Invalid airports selected. Please select valid airports from the list.')
      return
    }

    if (tripType === 'multicity') {
      const params = new URLSearchParams({
        trip_type: 'multicity',
        cabin_class: cabinClass,
        adults: passengers.adults.toString(),
        infants: passengers.infants.toString(),
      })
      passengers.children.forEach((child, idx) => {
        params.append(`child_${idx}_age`, child.age.toString())
      })
      multiCitySegments.forEach((seg, idx) => {
        params.append(`seg_${idx}_origin`, seg.origin)
        params.append(`seg_${idx}_dest`, seg.destination)
        params.append(`seg_${idx}_date`, seg.date)
      })
      window.location.href = `/flights/results?${params}`
    } else {
      const params = new URLSearchParams({
        trip_type: tripType,
        origin: codes.origin,
        destination: codes.destination,
        departure_date: departureDate,
        cabin_class: cabinClass,
        adults: passengers.adults.toString(),
        infants: passengers.infants.toString(),
      })
      if (tripType === 'roundtrip' && returnDate) {
        params.append('return_date', returnDate)
      }
      passengers.children.forEach((child, idx) => {
        params.append(`child_${idx}_age`, child.age.toString())
      })
      // Add nearby airports flags
      if (includeNearbyOrigin) {
        params.append('include_nearby_origin', 'true')
      }
      if (includeNearbyDestination) {
        params.append('include_nearby_destination', 'true')
      }
      // Clear modify search payload on successful submit
      clearModifySearchPayload('flights')
      window.location.href = `/flights/results?${params}`
    }
  }

  const handleHotelSearch = () => {
    if (!selectedHotelDestination) {
      alert('Please select a destination from the dropdown')
      return
    }
    
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const checkInDate = new Date(checkIn)
    const checkOutDate = new Date(checkOut)
    
    if (checkInDate < today) {
      alert('Check-in date cannot be in the past')
      return
    }
    
    if (checkOutDate <= checkInDate) {
      alert('Check-out date must be after check-in date (minimum 1 night stay)')
      return
    }
    
    // Validate minimum 1 night stay
    const nightsDiff = Math.floor((checkOutDate.getTime() - checkInDate.getTime()) / (1000 * 60 * 60 * 24))
    if (nightsDiff < 1) {
      alert('Minimum stay is 1 night')
      return
    }
    
    // Validate room configuration
    for (let i = 0; i < hotelRooms.rooms.length; i++) {
      const room = hotelRooms.rooms[i]
      if (room.adults < 1) {
        alert(`Room ${i + 1}: At least 1 adult required`)
        return
      }
      
      const totalGuests = room.adults + room.children.length
      if (totalGuests > 8) {
        alert(`Room ${i + 1}: Maximum 8 guests per room`)
        return
      }
    }
    
    // Build search params based on destination TYPE (CITY/AREA/HOTEL)
    const params = new URLSearchParams({
      city: selectedHotelDestination.city,
      check_in: checkIn,
      check_out: checkOut,
      rooms: hotelRooms.rooms.length.toString(),
      // Pass search type for backend handling
      search_type: selectedHotelDestination.type,
    })
    
    // Add type-specific parameters
    if (selectedHotelDestination.type === 'AREA') {
      // AREA search - include area name and geo coordinates
      if (selectedHotelDestination.areaName) {
        params.append('area', selectedHotelDestination.areaName)
      }
      if (selectedHotelDestination.latitude && selectedHotelDestination.longitude) {
        params.append('lat', selectedHotelDestination.latitude.toString())
        params.append('lng', selectedHotelDestination.longitude.toString())
      }
    } else if (selectedHotelDestination.type === 'HOTEL') {
      // HOTEL search - include hotel ID for direct lookup
      if (selectedHotelDestination.hotelId) {
        params.append('hotel_id', selectedHotelDestination.hotelId)
      }
      if (selectedHotelDestination.hotelName) {
        params.append('hotel_name', selectedHotelDestination.hotelName)
      }
    }
    // CITY search uses only city param (default)
    
    hotelRooms.rooms.forEach((room, roomIdx) => {
      params.append(`room_${roomIdx}_adults`, room.adults.toString())
      params.append(`room_${roomIdx}_type`, room.roomType)
      params.append(`room_${roomIdx}_ac`, room.ac.toString())
      room.children.forEach((age, childIdx) => {
        params.append(`room_${roomIdx}_child_${childIdx}_age`, age.toString())
      })
    })
    // Clear modify search payload on successful submit
    clearModifySearchPayload('hotels')
    window.location.href = `/hotels/results?${params}`
  }

  const handleTrainSearch = () => {
    // STATION-FIRST: Validate station/ALL selections from dropdown
    if (!trainOrigin || !trainDestination) {
      alert('Please select origin and destination from the dropdown')
      return
    }
    
    if (trainOrigin.value === trainDestination.value) {
      alert('Origin and destination cannot be the same')
      return
    }
    
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const searchDate = new Date(trainDate)
    
    if (searchDate < today) {
      alert('Date cannot be in the past')
      return
    }
    
    // STATION-FIRST: Submit .value (station code or _ALL token)
    // Examples: "CSMT", "PUNE", "MUMBAI_ALL", "PUNE_ALL"
    const params = new URLSearchParams({
      origin: trainOrigin.value,        // e.g., "MUMBAI_ALL" or "CSMT"
      destination: trainDestination.value,  // e.g., "PUNE" or "PUNE_ALL"
      departure_date: trainDate,
      passengers: trainPassengers.toString(),
    })
    
    if (trainClass) {
      params.append('train_class', trainClass)
    }
    
    // Clear modify search payload on successful submit
    clearModifySearchPayload('trains')
    window.location.href = `/trains/results?${params}`
  }

  const handleBusSearch = () => {
    /**
     * STRICT VALIDATION - ID-Based Only
     * 
     * CRITICAL: We NEVER resolve from text.
     * Both origin and destination MUST have been selected from dropdown.
     * This prevents destination from being overwritten with origin.
     */
    
    // Guard: Must have valid place selections
    if (!busOriginPlace || !busDestinationPlace) {
      alert('Please select origin and destination from the dropdown')
      return
    }
    
    // Guard: Cannot be same place
    if (busOriginPlace.place_id === busDestinationPlace.place_id) {
      alert('Origin and destination cannot be the same')
      return
    }
    
    // Guard: Date validation
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const searchDate = new Date(busDate)
    
    if (searchDate < today) {
      alert('Date cannot be in the past')
      return
    }
    
    // Build search params using CITY NAMES for booking partner URLs
    // CRITICAL: redBus only supports CITY → CITY searches
    // Use cityName (parent city) not name (stop name)
    const params = new URLSearchParams({
      origin: busOriginPlace.cityName || busOriginPlace.name,
      destination: busDestinationPlace.cityName || busDestinationPlace.name,
      departure_date: busDate,
      passengers: busPassengers.toString(),
    })
    
    if (busType) {
      params.append('bus_type', busType)
    }
    
    // Clear modify search payload on successful submit
    clearModifySearchPayload('buses')
    window.location.href = `/buses/results?${params}`
  }

  const handleMultiCitySegmentUpdate = (id: string, field: keyof FlightSegment, value: string) => {
    setMultiCitySegments(prev =>
      prev.map(seg =>
        seg.id === id ? { ...seg, [field]: value } : seg
      )
    )
  }

  const addMultiCitySegment = () => {
    const lastSegment = multiCitySegments[multiCitySegments.length - 1]
    const lastDate = new Date(lastSegment.date || getTodayDate())
    lastDate.setDate(lastDate.getDate() + 1)
    
    setMultiCitySegments([...multiCitySegments, {
      id: `seg-${Date.now()}`,
      origin: '',
      destination: '',
      date: lastDate.toISOString().split('T')[0]
    }])
  }

  const removeMultiCitySegment = (id: string) => {
    if (multiCitySegments.length > 2) {
      setMultiCitySegments(prev => prev.filter(seg => seg.id !== id))
    }
  }

  // ONE COLOR RULE: Blue (#2563EB) is the ONLY selection indicator

  // Don't render until mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
        <div className="h-96 flex items-center justify-center">
          <div className="animate-pulse text-gray-400">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div ref={searchFormRef} className="relative">
      {/* Tab Bar Container */}
      <div className="relative flex">
        {/* Flights Tab */}
        <button
          data-testid="flights-tab"
          onClick={() => setSearchType('flights')}
          className={`relative flex-1 min-w-[100px] py-3.5 px-4 flex items-center justify-center space-x-2 font-semibold text-sm transition-all duration-200 rounded-t-xl ${
            searchType === 'flights'
              ? 'bg-white text-blue-600 z-20'
              : 'bg-transparent text-gray-400 hover:text-gray-600'
          }`}
          style={searchType === 'flights' ? {
            borderTop: '1px solid #E5E7EB',
            borderLeft: '1px solid #E5E7EB',
            borderRight: '1px solid #E5E7EB',
            borderBottom: 'none',
            marginBottom: '-1px',
          } : {}}
        >
          <Plane className="h-5 w-5" />
          <span>Flights</span>
        </button>
        
        {/* Buses Tab */}
        <button
          data-testid="buses-tab"
          onClick={() => setSearchType('buses')}
          className={`relative flex-1 min-w-[100px] py-3.5 px-4 flex items-center justify-center space-x-2 font-semibold text-sm transition-all duration-200 rounded-t-xl ${
            searchType === 'buses'
              ? 'bg-white text-blue-600 z-20'
              : 'bg-transparent text-gray-400 hover:text-gray-600'
          }`}
          style={searchType === 'buses' ? {
            borderTop: '1px solid #E5E7EB',
            borderLeft: '1px solid #E5E7EB',
            borderRight: '1px solid #E5E7EB',
            borderBottom: 'none',
            marginBottom: '-1px',
          } : {}}
        >
          <Bus className="h-5 w-5" />
          <span>Buses</span>
        </button>
        
        {/* Trains Tab */}
        <button
          data-testid="trains-tab"
          onClick={() => setSearchType('trains')}
          className={`relative flex-1 min-w-[100px] py-3.5 px-4 flex items-center justify-center space-x-2 font-semibold text-sm transition-all duration-200 rounded-t-xl ${
            searchType === 'trains'
              ? 'bg-white text-blue-600 z-20'
              : 'bg-transparent text-gray-400 hover:text-gray-600'
          }`}
          style={searchType === 'trains' ? {
            borderTop: '1px solid #E5E7EB',
            borderLeft: '1px solid #E5E7EB',
            borderRight: '1px solid #E5E7EB',
            borderBottom: 'none',
            marginBottom: '-1px',
          } : {}}
        >
          <Train className="h-5 w-5" />
          <span>Trains</span>
        </button>
        
        {/* Hotels Tab */}
        <button
          data-testid="hotels-tab"
          onClick={() => setSearchType('hotels')}
          className={`relative flex-1 min-w-[100px] py-3.5 px-4 flex items-center justify-center space-x-2 font-semibold text-sm transition-all duration-200 rounded-t-xl ${
            searchType === 'hotels'
              ? 'bg-white text-blue-600 z-20'
              : 'bg-transparent text-gray-400 hover:text-gray-600'
          }`}
          style={searchType === 'hotels' ? {
            borderTop: '1px solid #E5E7EB',
            borderLeft: '1px solid #E5E7EB',
            borderRight: '1px solid #E5E7EB',
            borderBottom: 'none',
            marginBottom: '-1px',
          } : {}}
        >
          <Hotel className="h-5 w-5" />
          <span>Hotels</span>
        </button>
      </div>

      {/* Card Body - White background with border */}
      <div className="relative bg-white rounded-b-2xl shadow-lg border border-gray-200 z-10">
        {/* Search Form */}
        <div className="p-6 animate-tab-content" key={searchType}>
          {searchType === 'flights' ? (
            <div className="space-y-4">
              <TripTypeSelector value={tripType} onChange={setTripType} />

            {/* Cabin Class - ALWAYS VISIBLE for all trip types */}
            <CabinClassSelector value={cabinClass} onChange={setCabinClass} />

            {tripType === 'multicity' ? (
              <div className="space-y-4">
                {multiCitySegments.map((segment, index) => (
                  <div key={segment.id} className="border border-gray-200 rounded-xl p-4 bg-gray-50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-[#374151]">Flight {index + 1}</span>
                      {multiCitySegments.length > 2 && (
                        <button
                          type="button"
                          onClick={() => removeMultiCitySegment(segment.id)}
                          className="text-red-500 hover:text-red-700 text-sm"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                    <div className="grid md:grid-cols-3 gap-3">
                      <AirportAutocomplete
                        value={segment.origin}
                        onChange={(val) => handleMultiCitySegmentUpdate(segment.id, 'origin', val)}
                        label="From"
                        placeholder="Origin"
                        testId={`origin-${index}`}
                      />
                      <AirportAutocomplete
                        value={segment.destination}
                        onChange={(val) => handleMultiCitySegmentUpdate(segment.id, 'destination', val)}
                        label="To"
                        placeholder="Destination"
                        testId={`destination-${index}`}
                      />
                      <div>
                        <label className="block text-sm font-medium text-[#374151] mb-2">Date</label>
                        <div className="relative">
                          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-[#9CA3AF]" />
                          <input
                            type="date"
                            value={segment.date}
                            min={index === 0 ? getTodayDate() : multiCitySegments[index - 1]?.date}
                            onChange={(e) => handleMultiCitySegmentUpdate(segment.id, 'date', e.target.value)}
                            className="w-full pl-10 pr-4 py-3 border border-[#E6ECEA] rounded-xl focus:ring-2 focus:ring-[#5F8D7E] focus:border-transparent"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addMultiCitySegment}
                  className="w-full py-2 px-4 border-2 border-dashed border-[#E6ECEA] rounded-xl text-[#6B7280] hover:border-[#5F8D7E] hover:text-[#5F8D7E] transition-colors"
                >
                  + Add Another Flight
                </button>
              </div>
            ) : (
              <>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <ValidatedAirportInput
                      value={origin}
                      onChange={(airport) => {
                        setOrigin(airport)
                        setValidationErrors([])
                      }}
                      label="From"
                      placeholder="Origin city or airport"
                      onValidationChange={setOriginValid}
                    />
                    {/* Nearby airports toggle for origin */}
                    <div className="mt-2 flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="nearby-origin"
                        checked={includeNearbyOrigin}
                        onChange={(e) => setIncludeNearbyOrigin(e.target.checked)}
                        disabled={!origin}
                        data-testid="nearby-origin-checkbox"
                        className="h-4 w-4 text-[#5F8D7E] focus:ring-2 focus:ring-[#5F8D7E] border-[#E6ECEA] rounded disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                      <label 
                        htmlFor="nearby-origin" 
                        className={`text-sm select-none ${!origin ? 'text-[#9CA3AF]' : 'text-[#374151] cursor-pointer'}`}
                      >
                        Add nearby airports (within 250 km)
                      </label>
                    </div>
                  </div>
                  
                  <div>
                    <ValidatedAirportInput
                      value={destination}
                      onChange={(airport) => {
                        setDestination(airport)
                        setValidationErrors([])
                      }}
                      label="To"
                      placeholder="Destination city or airport"
                      onValidationChange={setDestinationValid}
                    />
                    {/* Nearby airports toggle for destination */}
                    <div className="mt-2 flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="nearby-destination"
                        checked={includeNearbyDestination}
                        onChange={(e) => setIncludeNearbyDestination(e.target.checked)}
                        disabled={!destination}
                        data-testid="nearby-destination-checkbox"
                        className="h-4 w-4 text-[#5F8D7E] focus:ring-2 focus:ring-[#5F8D7E] border-[#E6ECEA] rounded disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                      <label 
                        htmlFor="nearby-destination" 
                        className={`text-sm select-none ${!destination ? 'text-[#9CA3AF]' : 'text-[#374151] cursor-pointer'}`}
                      >
                        Add nearby airports (within 250 km)
                      </label>
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[#374151] mb-2">Departure</label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-[#9CA3AF]" />
                      <input
                        data-testid="departure-date-input"
                        type="date"
                        value={departureDate}
                        min={getTodayDate()}
                        onChange={(e) => handleDepartureDateChange(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-[#E6ECEA] rounded-xl focus:ring-2 focus:ring-[#5F8D7E] focus:border-transparent"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#374151] mb-2">
                      Return {tripType === 'oneway' && '(N/A)'}
                    </label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-[#9CA3AF]" />
                      <input
                        data-testid="return-date-input"
                        type="date"
                        value={returnDate}
                        min={departureDate}
                        onChange={(e) => handleReturnDateChange(e.target.value)}
                        disabled={tripType === 'oneway'}
                        className="w-full pl-10 pr-4 py-3 border border-[#E6ECEA] rounded-xl focus:ring-2 focus:ring-[#5F8D7E] focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-[#374151] mb-2">Passengers</label>
              <button
                data-testid="passenger-selector"
                onClick={() => setShowPassengerModal(true)}
                className="w-full px-4 py-3 border border-[#E6ECEA] rounded-xl text-left flex items-center justify-between hover:border-[#5F8D7E] focus:ring-2 focus:ring-[#5F8D7E] focus:border-transparent"
              >
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-[#9CA3AF]" />
                  <span>
                    {totalPassengers} passenger{totalPassengers !== 1 ? 's' : ''} • {cabinClass.replace('_', ' ')}
                  </span>
                </div>
              </button>
            </div>
          </div>
        ) : searchType === 'trains' ? (
          /* Train Search Form - STATION-FIRST ARCHITECTURE */
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <TrainStationAutocomplete
                value={trainOrigin}
                onChange={setTrainOrigin}
                label="From"
                testId="train-origin"
                placeholder="Station or City (All Stations)"
              />
              <TrainStationAutocomplete
                value={trainDestination}
                onChange={setTrainDestination}
                label="To"
                testId="train-destination"
                placeholder="Station or City (All Stations)"
              />
            </div>
            
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-[#374151] mb-2">Date</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-[#9CA3AF]" />
                  <input
                    type="date"
                    data-testid="train-date"
                    value={trainDate}
                    min={getTodayDate()}
                    onChange={(e) => handleTrainDateChange(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-[#E6ECEA] rounded-xl focus:ring-2 focus:ring-[#5F8D7E] focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#374151] mb-2">Class (Optional)</label>
                <select
                  data-testid="train-class"
                  value={trainClass}
                  onChange={(e) => setTrainClass(e.target.value)}
                  className="w-full px-4 py-3 border border-[#E6ECEA] rounded-xl focus:ring-2 focus:ring-[#5F8D7E] focus:border-transparent"
                >
                  <option value="">All Classes</option>
                  <option value="SL">Sleeper (SL)</option>
                  <option value="3A">AC 3-Tier (3A)</option>
                  <option value="2A">AC 2-Tier (2A)</option>
                  <option value="1A">AC First (1A)</option>
                  <option value="CC">Chair Car (CC)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#374151] mb-2">Passengers</label>
                <div className="relative">
                  <Users className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-[#9CA3AF]" />
                  <select
                    data-testid="train-passengers"
                    value={trainPassengers}
                    onChange={(e) => setTrainPassengers(Number(e.target.value))}
                    className="w-full pl-10 pr-4 py-3 border border-[#E6ECEA] rounded-xl focus:ring-2 focus:ring-[#5F8D7E] focus:border-transparent"
                  >
                    {[1, 2, 3, 4, 5, 6].map(n => (
                      <option key={n} value={n}>{n} Passenger{n > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            <div className="p-3 bg-[#EEF1E8] border border-[#D4DBC9] rounded-lg">
              <p className="text-sm text-[#4A5A3A]">
                <strong>Note:</strong> Fares shown are average/estimated. We&apos;ll redirect you to IRCTC, ixigo, or Paytm for live availability & booking.
              </p>
            </div>
          </div>
        ) : searchType === 'buses' ? (
          /* Bus Search Form - STRICT ID-Based Selection */
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <BusLocationAutocomplete
                value={busOriginText}
                selectedPlace={busOriginPlace}
                onChange={(text, place) => {
                  setBusOriginText(text)
                  setBusOriginPlace(place)
                }}
                label="From"
                testId="bus-origin"
                placeholder="Select city (e.g., Satara)"
                otherPlaceId={busDestinationPlace?.place_id || null}
              />
              <BusLocationAutocomplete
                value={busDestinationText}
                selectedPlace={busDestinationPlace}
                onChange={(text, place) => {
                  setBusDestinationText(text)
                  setBusDestinationPlace(place)
                }}
                label="To"
                testId="bus-destination"
                placeholder="Select city (e.g., Karad)"
                otherPlaceId={busOriginPlace?.place_id || null}
              />
            </div>
            
            {/* Same place error - STRICT GUARD */}
            {busSamePlace && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                <svg className="h-4 w-4 text-red-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-700">
                  Origin and destination cannot be the same. Please select different cities.
                </p>
              </div>
            )}
            
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-[#374151] mb-2">Date</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-[#9CA3AF]" />
                  <input
                    type="date"
                    data-testid="bus-date"
                    value={busDate}
                    min={getTodayDate()}
                    onChange={(e) => handleBusDateChange(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-[#E6ECEA] rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#374151] mb-2">Bus Type</label>
                <select
                  data-testid="bus-type"
                  value={busType}
                  onChange={(e) => setBusType(e.target.value)}
                  className="w-full px-4 py-3 border border-[#E6ECEA] rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                >
                  <option value="">All Types</option>
                  <option value="non_ac">Non-AC</option>
                  <option value="ac_seater">AC Seater</option>
                  <option value="ac_sleeper">AC Sleeper</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#374151] mb-2">Passengers</label>
                <div className="relative">
                  <Users className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-[#9CA3AF]" />
                  <select
                    data-testid="bus-passengers"
                    value={busPassengers}
                    onChange={(e) => setBusPassengers(Number(e.target.value))}
                    className="w-full pl-10 pr-4 py-3 border border-[#E6ECEA] rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  >
                    {[1, 2, 3, 4, 5, 6].map(n => (
                      <option key={n} value={n}>{n} Passenger{n > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            <div className="p-3 bg-[#F9EDE6] border border-[#E5C9B5] rounded-lg">
              <p className="text-sm text-[#8B5A2B]">
                <strong>Note:</strong> Fares shown are average/estimated. We&apos;ll redirect you to redBus, AbhiBus, or Paytm for live availability & booking.
              </p>
            </div>
          </div>
        ) : (
          /* Hotel Search Form - Controlled Selection */
          // <div className="space-y-4">
          //   <div>
          //     <HotelLocationAutocomplete
          //       value={selectedHotelDestination}
          //       onChange={setSelectedHotelDestination}
          //       label="Destination"
          //       placeholder="City, area"
          //       testId="hotel-city-input"
          //     />
          //   </div>

            <div className="grid md:grid-cols-3 gap-4">
              <DateInputs
                checkIn={checkIn}
                checkOut={checkOut}
                onChange={({ checkIn: ci, checkOut: co }) => {
                  handleCheckInChange(ci)
                  handleCheckOutChange(co)
                }}
              />
              <div>
                <label className="block text-sm font-medium text-[#374151] mb-2">Rooms & Guests</label>
                <button
                  data-testid="room-selector"
                  onClick={() => setShowRoomModal(true)}
                  className="w-full px-4 py-3 border border-[#E6ECEA] rounded-xl text-left flex items-center justify-between hover:border-[#5F8D7E] focus:ring-2 focus:ring-[#5F8D7E] focus:border-transparent"
                >
                  <div className="flex items-center space-x-2">
                    <Users className="h-5 w-5 text-[#9CA3AF]" />
                    <span>
                      {hotelRooms.rooms.length} room{hotelRooms.rooms.length !== 1 ? 's' : ''} • {totalGuests} guest
                      {totalGuests !== 1 ? 's' : ''}
                    </span>
                  </div>
                </button>
              </div>
            </div>
            
            {/* Note banner - consistent with Trains/Buses */}
            <div className="p-3 bg-[#F9F3E6] border border-[#E5D9B5] rounded-lg">
              <p className="text-sm text-[#8B7A2B]">
                <strong>Note:</strong> We compare prices from multiple hotel booking sites. You&apos;ll complete your booking on the partner website.
              </p>
            </div>
          </div>
        )}

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <svg className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800 mb-1">Please fix the following errors:</p>
                <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Search Button with validation */}
        {(() => {
          // Determine button state based on mode
          // HOTEL: Must have structured destination selection (CITY/AREA/HOTEL)
          const hotelValid = selectedHotelDestination !== null
          
          const isDisabled = 
            (searchType === 'flights' && (!originValid || !destinationValid)) ||
            (searchType === 'trains' && !trainSearchEnabled) ||
            (searchType === 'buses' && !busSearchEnabled) ||
            (searchType === 'hotels' && !hotelValid)
          
          const getDisabledReason = () => {
            if (searchType === 'trains') {
              if (!trainOriginValid && !trainDestinationValid) return 'Select origin and destination stations'
              if (!trainOriginValid) return 'Select origin station from the list'
              if (!trainDestinationValid) return 'Select destination station from the list'
              if (trainOrigin?.value === trainDestination?.value) return 'Origin and destination cannot be the same'
            }
            if (searchType === 'buses') {
              if (!busOriginValid && !busDestinationValid) return 'Select origin and destination from dropdown'
              if (!busOriginValid) return 'Select origin city from dropdown'
              if (!busDestinationValid) return 'Select destination city from dropdown'
              if (busSamePlace) return 'Origin and destination cannot be the same'
            }
            if (searchType === 'flights') {
              if (!originValid || !destinationValid) return 'Select valid airports from the list'
            }
            if (searchType === 'hotels') {
              if (!hotelValid) return 'Select a city from the dropdown'
            }
            return null
          }
          
          const disabledReason = getDisabledReason()
          
          return (
            <div className="relative">
              <button
                data-testid="search-button"
                onClick={
                  searchType === 'flights' ? handleFlightSearch :
                  searchType === 'trains' ? handleTrainSearch :
                  searchType === 'buses' ? handleBusSearch :
                  handleHotelSearch
                }
                disabled={isDisabled}
                className={`w-full mt-6 font-semibold py-4 px-6 rounded-xl transition-all duration-200 shadow-lg ${
                  isDisabled
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-xl'
                }`}
                title={disabledReason || undefined}
              >
                Search {searchType === 'flights' ? 'Flights' : searchType === 'trains' ? 'Trains' : searchType === 'buses' ? 'Buses' : 'Hotels'}
              </button>
              {isDisabled && disabledReason && (
                <p className="text-center text-xs text-gray-500 mt-2">{disabledReason}</p>
              )}
            </div>
          )
        })()}
        
        {/* Search Button Microcopy */}
        <SearchButtonMicrocopy />
      </div>
      </div>

      {showPassengerModal && (
        <AdvancedPassengerModal
          passengers={passengers}
          onUpdate={setPassengers}
          onClose={() => setShowPassengerModal(false)}
        />
      )}

      {showRoomModal && (
        <EnhancedHotelRoomSelector
          data={hotelRooms}
          onUpdate={setHotelRooms}
          onClose={() => setShowRoomModal(false)}
        />
      )}
    </div>
  )
}
