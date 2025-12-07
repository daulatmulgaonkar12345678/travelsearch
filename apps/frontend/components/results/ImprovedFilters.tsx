'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, X } from 'lucide-react'
import { FlightOffer } from './ResultCard'

interface FilterState {
  stops: string[]
  departureTimeRange: [number, number]
  durationRange: [number, number]
  airlines: string[]
}

interface ImprovedFiltersProps {
  filters: FilterState
  onFilterChange: (filters: FilterState) => void
  offers: FlightOffer[] // Original unfiltered offers
  filteredOffers: FlightOffer[] // Current filtered offers
  minDuration: number
  maxDuration: number
}

export default function ImprovedFilters({
  filters,
  onFilterChange,
  offers,
  filteredOffers,
  minDuration,
  maxDuration,
}: ImprovedFiltersProps) {
  const [expandedSections, setExpandedSections] = useState({
    stops: true,
    departureTime: true,
    duration: false,
    airlines: true,
  })

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  // Calculate cheapest price for each stop category
  const getStopPrice = (stopCount: string) => {
    let relevantOffers: FlightOffer[] = []

    if (stopCount === 'Direct') {
      relevantOffers = filteredOffers.filter((o) => o.stops === 0)
    } else if (stopCount === '1 stop') {
      relevantOffers = filteredOffers.filter((o) => o.stops === 1)
    } else if (stopCount === '2+ stops') {
      relevantOffers = filteredOffers.filter((o) => o.stops >= 2)
    }

    if (relevantOffers.length === 0) return null
    return Math.min(...relevantOffers.map((o) => o.price))
  }

  // Calculate cheapest price for each airline
  const getAirlinePrice = (airline: string) => {
    const relevantOffers = filteredOffers.filter((o) =>
      o.segments.some((seg) => seg.carrier_name === airline)
    )
    if (relevantOffers.length === 0) return null
    return Math.min(...relevantOffers.map((o) => o.price))
  }

  // Get unique airlines from offers
  const availableAirlines = Array.from(
    new Set(offers.flatMap((o) => o.segments.map((s) => s.carrier_name)))
  ).sort()

  // Get airlines that appear in current filtered results
  const airlinesInResults = Array.from(
    new Set(filteredOffers.flatMap((o) => o.segments.map((s) => s.carrier_name)))
  )

  const handleStopsChange = (stop: string) => {
    const newStops = filters.stops.includes(stop)
      ? filters.stops.filter((s) => s !== stop)
      : [...filters.stops, stop]
    onFilterChange({ ...filters, stops: newStops })
  }

  const handleAirlineChange = (airline: string) => {
    const newAirlines = filters.airlines.includes(airline)
      ? filters.airlines.filter((a) => a !== airline)
      : [...filters.airlines, airline]
    onFilterChange({ ...filters, airlines: newAirlines })
  }

  const handleAirlineSelectAll = () => {
    onFilterChange({ ...filters, airlines: availableAirlines })
  }

  const handleAirlineClearAll = () => {
    onFilterChange({ ...filters, airlines: [] })
  }

  const formatTime = (hour: number) => {
    return `${hour.toString().padStart(2, '0')}:00`
  }

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  const formatPrice = (price: number | null, currency: string = 'INR') => {
    if (price === null) return '–'
    return `${currency} ${Math.round(price).toLocaleString()}`
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200">
      {/* Stops Filter */}
      <div className="p-4">
        <button
          onClick={() => toggleSection('stops')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="font-semibold text-gray-900">Stops</h3>
          {expandedSections.stops ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {expandedSections.stops && (
          <div className="mt-3 space-y-2">
            {['Direct', '1 stop', '2+ stops'].map((stop) => {
              const price = getStopPrice(stop)
              const hasFlights = price !== null

              return (
                <label
                  key={stop}
                  className={`flex items-center justify-between cursor-pointer ${
                    !hasFlights ? 'opacity-50' : ''
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={filters.stops.includes(stop)}
                      onChange={() => handleStopsChange(stop)}
                      disabled={!hasFlights}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-gray-700">{stop}</span>
                  </div>
                  <span className="text-sm text-gray-600 font-medium">
                    {hasFlights ? `from ${formatPrice(price)}` : '–'}
                  </span>
                </label>
              )
            })}
          </div>
        )}
      </div>

      {/* Departure Time Filter */}
      <div className="p-4">
        <button
          onClick={() => toggleSection('departureTime')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="font-semibold text-gray-900">Departure times</h3>
          {expandedSections.departureTime ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {expandedSections.departureTime && (
          <div className="mt-3">
            <div className="text-sm text-gray-600 mb-3">
              Outbound {formatTime(filters.departureTimeRange[0])} –{' '}
              {formatTime(filters.departureTimeRange[1])}
            </div>
            <div className="relative pt-2 pb-1">
              <input
                type="range"
                min="0"
                max="23"
                value={filters.departureTimeRange[1]}
                onChange={(e) =>
                  onFilterChange({
                    ...filters,
                    departureTimeRange: [filters.departureTimeRange[0], parseInt(e.target.value)],
                  })
                }
                className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>
          </div>
        )}
      </div>

      {/* Duration Filter */}
      <div className="p-4">
        <button
          onClick={() => toggleSection('duration')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="font-semibold text-gray-900">Journey duration</h3>
          {expandedSections.duration ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {expandedSections.duration && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>{formatDuration(minDuration)}</span>
              <span>Up to {formatDuration(filters.durationRange[1])}</span>
            </div>
            <input
              type="range"
              min={minDuration}
              max={maxDuration}
              value={filters.durationRange[1]}
              onChange={(e) =>
                onFilterChange({
                  ...filters,
                  durationRange: [filters.durationRange[0], parseInt(e.target.value)],
                })
              }
              className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>
        )}
      </div>

      {/* Airlines Filter */}
      <div className="p-4">
        <button
          onClick={() => toggleSection('airlines')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="font-semibold text-gray-900">Airlines</h3>
          {expandedSections.airlines ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {expandedSections.airlines && (
          <div className="mt-3">
            <div className="flex space-x-2 mb-3">
              <button
                onClick={handleAirlineSelectAll}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                Select all
              </button>
              <span className="text-gray-400">|</span>
              <button
                onClick={handleAirlineClearAll}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                Clear all
              </button>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {availableAirlines
                .filter((airline) => airlinesInResults.includes(airline))
                .map((airline) => {
                  const price = getAirlinePrice(airline)

                  return (
                    <label
                      key={airline}
                      className="flex items-center justify-between cursor-pointer"
                    >
                      <div className="flex items-center space-x-2 min-w-0 flex-1">
                        <input
                          type="checkbox"
                          checked={filters.airlines.includes(airline)}
                          onChange={() => handleAirlineChange(airline)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 flex-shrink-0"
                        />
                        <span className="text-gray-700 text-sm truncate">{airline}</span>
                      </div>
                      <span className="text-sm text-gray-600 font-medium ml-2 flex-shrink-0">
                        from {formatPrice(price)}
                      </span>
                    </label>
                  )
                })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
