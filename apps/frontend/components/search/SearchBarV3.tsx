'use client'

import { useState, useEffect } from 'react'
import { Plane, Hotel, Calendar, Users, Train, Bus } from 'lucide-react'
import TripTypeSelector from './TripTypeSelector'
import CabinClassSelector from './CabinClassSelector'
import AdvancedPassengerModal from './AdvancedPassengerModal'
import EnhancedHotelRoomSelector from './EnhancedHotelRoomSelector'
import DateInputs from './DateInputs'
import AirportAutocomplete from './AirportAutocomplete'
import ValidatedAirportInput from './ValidatedAirportInput'
import CityAutocomplete from './CityAutocomplete'
import TransportAutocomplete, { TransportLocation } from './TransportAutocomplete'
import { Airport, validateFlightSearch, extractIATACodes } from '@/lib/airportValidation'
import { SearchButtonMicrocopy } from '@/components/trust/Microcopy'

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
  // SSR-safe state initialization
  const [mounted, setMounted] = useState(false)
  const [searchType, setSearchType] = useState<SearchType>(defaultTab)
  
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
  const [tripType, setTripType] = useState<TripType>('roundtrip')
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
  
  // Hotels state
  const [city, setCity] = useState('')
  const [checkIn, setCheckIn] = useState(getTodayDate())
  const [checkOut, setCheckOut] = useState(getTomorrowDate())
  const [hotelRooms, setHotelRooms] = useState<EnhancedHotelRoomData>({
    rooms: [{ adults: 2, children: [], roomType: 'Standard', ac: true }],
  })
  const [showRoomModal, setShowRoomModal] = useState(false)

  // Trains & Buses state - with validated locations
  const [trainOriginText, setTrainOriginText] = useState('')
  const [trainOriginLocation, setTrainOriginLocation] = useState<TransportLocation | null>(null)
  const [trainDestinationText, setTrainDestinationText] = useState('')
  const [trainDestinationLocation, setTrainDestinationLocation] = useState<TransportLocation | null>(null)
  const [trainDate, setTrainDate] = useState(getTomorrowDate())
  const [trainPassengers, setTrainPassengers] = useState(1)
  const [trainClass, setTrainClass] = useState<string>('')
  
  const [busOriginText, setBusOriginText] = useState('')
  const [busOriginLocation, setBusOriginLocation] = useState<TransportLocation | null>(null)
  const [busDestinationText, setBusDestinationText] = useState('')
  const [busDestinationLocation, setBusDestinationLocation] = useState<TransportLocation | null>(null)
  const [busDate, setBusDate] = useState(getTomorrowDate())
  const [busPassengers, setBusPassengers] = useState(1)
  const [busType, setBusType] = useState<string>('')  // '', 'ac_seater', 'ac_sleeper', 'non_ac'

  // Validation flags for trains and buses
  const trainOriginValid = trainOriginLocation !== null
  const trainDestinationValid = trainDestinationLocation !== null
  const trainSearchEnabled = trainOriginValid && trainDestinationValid && 
    trainOriginLocation?.city_id !== trainDestinationLocation?.city_id
  
  const busOriginValid = busOriginLocation !== null
  const busDestinationValid = busDestinationLocation !== null
  const busSearchEnabled = busOriginValid && busDestinationValid &&
    busOriginLocation?.city_id !== busDestinationLocation?.city_id

  // Synchronize dates between all modes
  useEffect(() => {
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
      window.location.href = `/flights/results?${params}`
    }
  }

  const handleHotelSearch = () => {
    if (!city) {
      alert('Please enter a city')
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
    
    const params = new URLSearchParams({
      city,
      check_in: checkIn,
      check_out: checkOut,
      rooms: hotelRooms.rooms.length.toString(),
    })
    hotelRooms.rooms.forEach((room, roomIdx) => {
      params.append(`room_${roomIdx}_adults`, room.adults.toString())
      params.append(`room_${roomIdx}_type`, room.roomType)
      params.append(`room_${roomIdx}_ac`, room.ac.toString())
      room.children.forEach((age, childIdx) => {
        params.append(`room_${roomIdx}_child_${childIdx}_age`, age.toString())
      })
    })
    window.location.href = `/hotels/results?${params}`
  }

  const handleTrainSearch = () => {
    // Validate selections from dropdown
    if (!trainOriginLocation || !trainDestinationLocation) {
      alert('Please select origin and destination from the dropdown')
      return
    }
    
    if (trainOriginLocation.city_id === trainDestinationLocation.city_id) {
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
    
    // Use city names for backend search (it will normalize them)
    const params = new URLSearchParams({
      origin: trainOriginLocation.city,
      destination: trainDestinationLocation.city,
      departure_date: trainDate,
      passengers: trainPassengers.toString(),
    })
    
    if (trainClass) {
      params.append('train_class', trainClass)
    }
    
    window.location.href = `/trains/results?${params}`
  }

  const handleBusSearch = () => {
    // Validate selections from dropdown
    if (!busOriginLocation || !busDestinationLocation) {
      alert('Please select origin and destination from the dropdown')
      return
    }
    
    if (busOriginLocation.city_id === busDestinationLocation.city_id) {
      alert('Origin and destination cannot be the same')
      return
    }
    
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const searchDate = new Date(busDate)
    
    if (searchDate < today) {
      alert('Date cannot be in the past')
      return
    }
    
    // Use city names for backend search
    const params = new URLSearchParams({
      origin: busOriginLocation.city,
      destination: busDestinationLocation.city,
      departure_date: busDate,
      passengers: busPassengers.toString(),
    })
    
    if (busType) {
      params.append('bus_type', busType)
    }
    
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

  // Don't render until mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
        <div className="h-96 flex items-center justify-center">
          <div className="animate-pulse text-gray-400">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
      {/* Tab Selector */}
      <div className="flex border-b border-gray-200 overflow-x-auto">
        <button
          data-testid="flights-tab"
          onClick={() => setSearchType('flights')}
          className={`flex-1 min-w-[100px] py-4 px-4 flex items-center justify-center space-x-2 font-medium transition-colors ${
            searchType === 'flights'
              ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          <Plane className="h-5 w-5" />
          <span>Flights</span>
        </button>
        <button
          data-testid="trains-tab"
          onClick={() => setSearchType('trains')}
          className={`flex-1 min-w-[100px] py-4 px-4 flex items-center justify-center space-x-2 font-medium transition-colors ${
            searchType === 'trains'
              ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          <Train className="h-5 w-5" />
          <span>Trains</span>
        </button>
        <button
          data-testid="buses-tab"
          onClick={() => setSearchType('buses')}
          className={`flex-1 min-w-[100px] py-4 px-4 flex items-center justify-center space-x-2 font-medium transition-colors ${
            searchType === 'buses'
              ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          <Bus className="h-5 w-5" />
          <span>Buses</span>
        </button>
        <button
          data-testid="hotels-tab"
          onClick={() => setSearchType('hotels')}
          className={`flex-1 min-w-[100px] py-4 px-4 flex items-center justify-center space-x-2 font-medium transition-colors ${
            searchType === 'hotels'
              ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          <Hotel className="h-5 w-5" />
          <span>Hotels</span>
        </button>
      </div>

      {/* Search Form */}
      <div className="p-6">
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
                      <span className="text-sm font-medium text-gray-700">Flight {index + 1}</span>
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
                        <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
                        <div className="relative">
                          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                          <input
                            type="date"
                            value={segment.date}
                            min={index === 0 ? getTodayDate() : multiCitySegments[index - 1]?.date}
                            onChange={(e) => handleMultiCitySegmentUpdate(segment.id, 'date', e.target.value)}
                            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addMultiCitySegment}
                  className="w-full py-2 px-4 border-2 border-dashed border-gray-300 rounded-xl text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-colors"
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
                        className="h-4 w-4 text-blue-600 focus:ring-2 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                      <label 
                        htmlFor="nearby-origin" 
                        className={`text-sm select-none ${!origin ? 'text-gray-400' : 'text-gray-700 cursor-pointer'}`}
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
                        className="h-4 w-4 text-blue-600 focus:ring-2 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                      <label 
                        htmlFor="nearby-destination" 
                        className={`text-sm select-none ${!destination ? 'text-gray-400' : 'text-gray-700 cursor-pointer'}`}
                      >
                        Add nearby airports (within 250 km)
                      </label>
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Departure</label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        data-testid="departure-date-input"
                        type="date"
                        value={departureDate}
                        min={getTodayDate()}
                        onChange={(e) => handleDepartureDateChange(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Return {tripType === 'oneway' && '(N/A)'}
                    </label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        data-testid="return-date-input"
                        type="date"
                        value={returnDate}
                        min={departureDate}
                        onChange={(e) => handleReturnDateChange(e.target.value)}
                        disabled={tripType === 'oneway'}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Passengers</label>
              <button
                data-testid="passenger-selector"
                onClick={() => setShowPassengerModal(true)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl text-left flex items-center justify-between hover:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-gray-400" />
                  <span>
                    {totalPassengers} passenger{totalPassengers !== 1 ? 's' : ''} • {cabinClass.replace('_', ' ')}
                  </span>
                </div>
              </button>
            </div>
          </div>
        ) : searchType === 'trains' ? (
          /* Train Search Form - Same dropdown behavior as Flights */
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <TransportAutocomplete
                value={trainOriginText}
                selectedLocation={trainOriginLocation}
                onChange={(text, location) => {
                  setTrainOriginText(text)
                  setTrainOriginLocation(location)
                }}
                mode="train"
                label="From"
                testId="train-origin"
                placeholder="Select city (e.g., Delhi)"
              />
              <TransportAutocomplete
                value={trainDestinationText}
                selectedLocation={trainDestinationLocation}
                onChange={(text, location) => {
                  setTrainDestinationText(text)
                  setTrainDestinationLocation(location)
                }}
                mode="train"
                label="To"
                testId="train-destination"
                placeholder="Select city (e.g., Mumbai)"
              />
            </div>
            
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="date"
                    data-testid="train-date"
                    value={trainDate}
                    min={getTodayDate()}
                    onChange={(e) => handleTrainDateChange(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Class (Optional)</label>
                <select
                  data-testid="train-class"
                  value={trainClass}
                  onChange={(e) => setTrainClass(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Passengers</label>
                <div className="relative">
                  <Users className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <select
                    data-testid="train-passengers"
                    value={trainPassengers}
                    onChange={(e) => setTrainPassengers(Number(e.target.value))}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {[1, 2, 3, 4, 5, 6].map(n => (
                      <option key={n} value={n}>{n} Passenger{n > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-800">
                <strong>Note:</strong> Fares shown are average/estimated. We&apos;ll redirect you to IRCTC, ixigo, or Paytm for live availability & booking.
              </p>
            </div>
          </div>
        ) : searchType === 'buses' ? (
          /* Bus Search Form - Same dropdown behavior as Flights */
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <TransportAutocomplete
                value={busOriginText}
                selectedLocation={busOriginLocation}
                onChange={(text, location) => {
                  setBusOriginText(text)
                  setBusOriginLocation(location)
                }}
                mode="bus"
                label="From"
                testId="bus-origin"
                placeholder="Select city (e.g., Mumbai)"
              />
              <TransportAutocomplete
                value={busDestinationText}
                selectedLocation={busDestinationLocation}
                onChange={(text, location) => {
                  setBusDestinationText(text)
                  setBusDestinationLocation(location)
                }}
                mode="bus"
                label="To"
                testId="bus-destination"
                placeholder="Select city (e.g., Pune)"
              />
            </div>
            
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
                    onChange={(e) => handleBusDateChange(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Bus Type</label>
                <select
                  data-testid="bus-type"
                  value={busType}
                  onChange={(e) => setBusType(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {[1, 2, 3, 4, 5, 6].map(n => (
                      <option key={n} value={n}>{n} Passenger{n > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-800">
                <strong>Note:</strong> Fares shown are average/estimated. We&apos;ll redirect you to redBus, AbhiBus, or Paytm for live availability & booking.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <CityAutocomplete
              value={city}
              onChange={setCity}
              label="City or Hotel"
              placeholder="Where are you going?"
              testId="city-input"
            />

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
                <label className="block text-sm font-medium text-gray-700 mb-2">Rooms & Guests</label>
                <button
                  data-testid="room-selector"
                  onClick={() => setShowRoomModal(true)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl text-left flex items-center justify-between hover:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <div className="flex items-center space-x-2">
                    <Users className="h-5 w-5 text-gray-400" />
                    <span>
                      {hotelRooms.rooms.length} room{hotelRooms.rooms.length !== 1 ? 's' : ''} • {totalGuests} guest
                      {totalGuests !== 1 ? 's' : ''}
                    </span>
                  </div>
                </button>
              </div>
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
          const isDisabled = 
            (searchType === 'flights' && (!originValid || !destinationValid)) ||
            (searchType === 'trains' && !trainSearchEnabled) ||
            (searchType === 'buses' && !busSearchEnabled)
          
          const getDisabledReason = () => {
            if (searchType === 'trains') {
              if (!trainOriginValid && !trainDestinationValid) return 'Select origin and destination cities'
              if (!trainOriginValid) return 'Select origin city from the list'
              if (!trainDestinationValid) return 'Select destination city from the list'
              if (trainOriginLocation?.city_id === trainDestinationLocation?.city_id) return 'Origin and destination cannot be the same'
            }
            if (searchType === 'buses') {
              if (!busOriginValid && !busDestinationValid) return 'Select origin and destination cities'
              if (!busOriginValid) return 'Select origin city from the list'
              if (!busDestinationValid) return 'Select destination city from the list'
              if (busOriginLocation?.city_id === busDestinationLocation?.city_id) return 'Origin and destination cannot be the same'
            }
            if (searchType === 'flights') {
              if (!originValid || !destinationValid) return 'Select valid airports from the list'
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
                className={`w-full mt-6 font-semibold py-4 px-6 rounded-xl transition-colors shadow-lg ${
                  isDisabled
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : searchType === 'buses' 
                      ? 'bg-orange-600 hover:bg-orange-700 text-white hover:shadow-xl'
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
