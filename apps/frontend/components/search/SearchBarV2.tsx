'use client'

import { useState, useEffect } from 'react'
import { Plane, Hotel, Calendar, Users } from 'lucide-react'
import TripTypeSelector from './TripTypeSelector'
import CabinClassSelector from './CabinClassSelector'
import MultiCityBuilder from './MultiCityBuilder'
import AdvancedPassengerModal from './AdvancedPassengerModal'
import EnhancedHotelRoomSelector from './EnhancedHotelRoomSelector'
import DateInputs from './DateInputs'

type SearchType = 'flights' | 'hotels'
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

interface SearchBarV2Props {
  defaultTab?: SearchType
}

export default function SearchBarV2({ defaultTab = 'flights' }: SearchBarV2Props) {
  // Common
  const [searchType, setSearchType] = useState<SearchType>(defaultTab)
  
  // Get tomorrow's date as minimum
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
  
  // Flights
  const [tripType, setTripType] = useState<TripType>('roundtrip')
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [departureDate, setDepartureDate] = useState('')
  const [returnDate, setReturnDate] = useState('')
  const [cabinClass, setCabinClass] = useState<CabinClass>('economy')
  const [passengers, setPassengers] = useState<PassengerData>({
    adults: 1,
    children: [],
    infants: 0,
  })
  const [multiCitySegments, setMultiCitySegments] = useState<FlightSegment[]>([
    { id: 'seg-1', origin: '', destination: '', date: '' },
    { id: 'seg-2', origin: '', destination: '', date: '' },
  ])
  const [showPassengerModal, setShowPassengerModal] = useState(false)
  
  // Hotels
  const [city, setCity] = useState('')
  const [checkIn, setCheckIn] = useState(getTomorrowDate())
  const [checkOut, setCheckOut] = useState(getDayAfterTomorrow())
  const [hotelRooms, setHotelRooms] = useState<EnhancedHotelRoomData>({
    rooms: [{ adults: 2, children: [], roomType: 'Standard', ac: true }],
  })
  const [showRoomModal, setShowRoomModal] = useState(false)

  const totalPassengers = passengers.adults + passengers.children.length + passengers.infants
  const totalGuests = hotelRooms.rooms.reduce((sum, room) => sum + room.adults + room.children.length, 0)

  const handleFlightSearch = () => {
    if (tripType === 'multicity') {
      // Multi-city search
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
      // One-way or Round-trip
      const params = new URLSearchParams({
        trip_type: tripType,
        origin,
        destination,
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
      window.location.href = `/flights/results?${params}`
    }
  }

  const handleHotelSearch = () => {
    const params = new URLSearchParams({
      city,
      check_in: checkIn,
      check_out: checkOut,
      rooms: hotelRooms.rooms.length.toString(),
    })
    hotelRooms.rooms.forEach((room, roomIdx) => {
      params.append(`room_${roomIdx}_adults`, room.adults.toString())
      room.children.forEach((age, childIdx) => {
        params.append(`room_${roomIdx}_child_${childIdx}_age`, age.toString())
      })
    })
    window.location.href = `/hotels/results?${params}`
  }

  return (
    <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
      {/* Tab Selector */}
      <div className="flex border-b border-gray-200">
        <button
          data-testid="flights-tab"
          onClick={() => setSearchType('flights')}
          className={`flex-1 py-4 px-6 flex items-center justify-center space-x-2 font-medium transition-colors ${
            searchType === 'flights'
              ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          <Plane className="h-5 w-5" />
          <span>Flights</span>
        </button>
        <button
          data-testid="hotels-tab"
          onClick={() => setSearchType('hotels')}
          className={`flex-1 py-4 px-6 flex items-center justify-center space-x-2 font-medium transition-colors ${
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
            {/* Trip Type Selector */}
            <TripTypeSelector value={tripType} onChange={setTripType} />

            {tripType === 'multicity' ? (
              // Multi-city Form
              <MultiCityBuilder segments={multiCitySegments} onChange={setMultiCitySegments} />
            ) : (
              // One-way / Round-trip Form
              <>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">From</label>
                    <input
                      data-testid="origin-input"
                      type="text"
                      value={origin}
                      onChange={(e) => setOrigin(e.target.value)}
                      placeholder="Origin (e.g., BOM)"
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">To</label>
                    <input
                      data-testid="destination-input"
                      type="text"
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      placeholder="Destination (e.g., PNQ)"
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Departure</label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        data-testid="departure-date-input"
                        type="date"
                        value={departureDate}
                        onChange={(e) => setDepartureDate(e.target.value)}
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
                        onChange={(e) => setReturnDate(e.target.value)}
                        disabled={tripType === 'oneway'}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                      />
                    </div>
                  </div>
                  <CabinClassSelector value={cabinClass} onChange={setCabinClass} />
                </div>
              </>
            )}

            {/* Passengers */}
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
        ) : (
          // Hotels Form
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">City or Hotel</label>
              <input
                data-testid="city-input"
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Where are you going?"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Check-in</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    data-testid="checkin-date-input"
                    type="date"
                    value={checkIn}
                    onChange={(e) => setCheckIn(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Check-out</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    data-testid="checkout-date-input"
                    type="date"
                    value={checkOut}
                    onChange={(e) => setCheckOut(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
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

        {/* Search Button */}
        <button
          data-testid="search-button"
          onClick={searchType === 'flights' ? handleFlightSearch : handleHotelSearch}
          className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-xl transition-colors shadow-lg hover:shadow-xl"
        >
          Search {searchType === 'flights' ? 'Flights' : 'Hotels'}
        </button>
      </div>

      {/* Modals */}
      {showPassengerModal && (
        <AdvancedPassengerModal
          passengers={passengers}
          onUpdate={setPassengers}
          onClose={() => setShowPassengerModal(false)}
        />
      )}

      {showRoomModal && (
        <HotelRoomSelector
          data={hotelRooms}
          onUpdate={setHotelRooms}
          onClose={() => setShowRoomModal(false)}
        />
      )}
    </div>
  )
}
