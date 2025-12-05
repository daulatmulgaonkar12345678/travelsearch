'use client'

import { useState } from 'react'
import { Plane, Hotel, Calendar, Users } from 'lucide-react'
import PassengerModal from './PassengerModal'

type SearchType = 'flights' | 'hotels'

export default function SearchBar() {
  const [searchType, setSearchType] = useState<SearchType>('flights')
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [departureDate, setDepartureDate] = useState('')
  const [returnDate, setReturnDate] = useState('')
  const [checkIn, setCheckIn] = useState('')
  const [checkOut, setCheckOut] = useState('')
  const [city, setCity] = useState('')
  const [passengers, setPassengers] = useState({ adults: 1, children: 0, infants: 0 })
  const [showPassengerModal, setShowPassengerModal] = useState(false)

  const totalPassengers = passengers.adults + passengers.children + passengers.infants

  const handleSearch = () => {
    if (searchType === 'flights') {
      const params = new URLSearchParams({
        origin,
        destination,
        departure_date: departureDate,
        adults: passengers.adults.toString(),
        children: passengers.children.toString(),
        infants: passengers.infants.toString(),
      })
      window.location.href = `/flights/results?${params}`
    } else {
      const params = new URLSearchParams({
        city,
        check_in: checkIn,
        check_out: checkOut,
        adults: passengers.adults.toString(),
        children: passengers.children.toString(),
      })
      window.location.href = `/hotels/results?${params}`
    }
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Return (Optional)</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    data-testid="return-date-input"
                    type="date"
                    value={returnDate}
                    onChange={(e) => setReturnDate(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Passengers</label>
                <button
                  data-testid="passenger-selector"
                  onClick={() => setShowPassengerModal(true)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl text-left flex items-center justify-between hover:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <div className="flex items-center space-x-2">
                    <Users className="h-5 w-5 text-gray-400" />
                    <span>{totalPassengers} passenger{totalPassengers !== 1 ? 's' : ''}</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        ) : (
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Guests</label>
                <button
                  data-testid="guest-selector"
                  onClick={() => setShowPassengerModal(true)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl text-left flex items-center justify-between hover:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <div className="flex items-center space-x-2">
                    <Users className="h-5 w-5 text-gray-400" />
                    <span>{totalPassengers} guest{totalPassengers !== 1 ? 's' : ''}</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Search Button */}
        <button
          data-testid="search-button"
          onClick={handleSearch}
          className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-xl transition-colors shadow-lg hover:shadow-xl"
        >
          Search {searchType === 'flights' ? 'Flights' : 'Hotels'}
        </button>
      </div>

      {/* Passenger Modal */}
      {showPassengerModal && (
        <PassengerModal
          passengers={passengers}
          onUpdate={setPassengers}
          onClose={() => setShowPassengerModal(false)}
        />
      )}
    </div>
  )
}
