'use client'

import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export interface FlightFilterState {
  // Price
  maxPrice: number
  
  // Stops
  stops: string[]
  
  // Airlines
  airlines: string[]
  
  // Times
  departureTimeRange: [number, number]
  arrivalTimeRange: [number, number]
  
  // Duration
  maxDuration: number
  
  // Policies
  refundableOnly: boolean
  includeRedEye: boolean
  greenOnly: boolean
  
  // Baggage
  baggage: string[]
  
  // Aircraft type
  aircraftTypes: string[]
}

interface FlightFilterSidebarProps {
  filters: FlightFilterState
  onFilterChange: (filters: FlightFilterState) => void
  availableAirlines?: string[]
  maxPriceLimit?: number
}

export default function FlightFilterSidebar({
  filters,
  onFilterChange,
  availableAirlines = ['IndiGo', 'Air India', 'Vistara', 'SpiceJet', 'GoAir', 'AirAsia'],
  maxPriceLimit = 50000,
}: FlightFilterSidebarProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    price: true,
    stops: true,
    airlines: false,
    time: false,
    duration: false,
    policies: false,
    baggage: false,
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const toggleArrayItem = (key: keyof FlightFilterState, item: string) => {
    const currentArray = filters[key] as string[]
    const newArray = currentArray.includes(item)
      ? currentArray.filter(i => i !== item)
      : [...currentArray, item]
    onFilterChange({ ...filters, [key]: newArray })
  }

  const FilterSection = ({ title, sectionKey, children }: any) => (
    <div className="border-b border-gray-200 last:border-b-0">
      <button
        onClick={() => toggleSection(sectionKey)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
      >
        <span className="font-medium text-gray-900">{title}</span>
        {expandedSections[sectionKey] ? (
          <ChevronUp className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        )}
      </button>
      {expandedSections[sectionKey] && (
        <div className="px-4 pb-4 space-y-2">
          {children}
        </div>
      )}
    </div>
  )

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden sticky top-4">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="font-semibold text-lg">Filters</h2>
      </div>

      {/* Price Range */}
      <FilterSection title="Price Range" sectionKey="price">
        <div>
          <label className="text-xs text-gray-600 block mb-1">
            Max: ₹{filters.maxPrice.toLocaleString()}
          </label>
          <input
            type="range"
            min="1000"
            max={maxPriceLimit}
            step="500"
            value={filters.maxPrice}
            onChange={(e) => onFilterChange({ ...filters, maxPrice: parseInt(e.target.value) })}
            className="w-full"
          />
        </div>
      </FilterSection>

      {/* Stops */}
      <FilterSection title="Stops" sectionKey="stops">
        {['Non-stop', '1 Stop', '2+ Stops'].map(stop => (
          <label key={stop} className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.stops.includes(stop)}
              onChange={() => toggleArrayItem('stops', stop)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{stop}</span>
          </label>
        ))}
      </FilterSection>

      {/* Airlines */}
      <FilterSection title="Airlines" sectionKey="airlines">
        {availableAirlines.map(airline => (
          <label key={airline} className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.airlines.includes(airline)}
              onChange={() => toggleArrayItem('airlines', airline)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{airline}</span>
          </label>
        ))}
      </FilterSection>

      {/* Departure Time */}
      <FilterSection title="Departure Time" sectionKey="time">
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-600 block mb-1">
              Earliest: {filters.departureTimeRange[0].toString().padStart(2, '0')}:00
            </label>
            <input
              type="range"
              min="0"
              max="23"
              value={filters.departureTimeRange[0]}
              onChange={(e) => onFilterChange({
                ...filters,
                departureTimeRange: [parseInt(e.target.value), filters.departureTimeRange[1]]
              })}
              className="w-full"
            />
          </div>
          <div>
            <label className="text-xs text-gray-600 block mb-1">
              Latest: {filters.departureTimeRange[1].toString().padStart(2, '0')}:00
            </label>
            <input
              type="range"
              min="0"
              max="23"
              value={filters.departureTimeRange[1]}
              onChange={(e) => onFilterChange({
                ...filters,
                departureTimeRange: [filters.departureTimeRange[0], parseInt(e.target.value)]
              })}
              className="w-full"
            />
          </div>
        </div>
      </FilterSection>

      {/* Duration */}
      <FilterSection title="Max Duration" sectionKey="duration">
        <div>
          <label className="text-xs text-gray-600 block mb-1">
            Up to {filters.maxDuration} hours
          </label>
          <input
            type="range"
            min="1"
            max="24"
            value={filters.maxDuration}
            onChange={(e) => onFilterChange({ ...filters, maxDuration: parseInt(e.target.value) })}
            className="w-full"
          />
        </div>
      </FilterSection>

      {/* Policies */}
      <FilterSection title="Policies & Preferences" sectionKey="policies">
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.refundableOnly}
            onChange={(e) => onFilterChange({ ...filters, refundableOnly: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Refundable only</span>
        </label>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={!filters.includeRedEye}
            onChange={(e) => onFilterChange({ ...filters, includeRedEye: !e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Exclude red-eye flights</span>
        </label>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.greenOnly}
            onChange={(e) => onFilterChange({ ...filters, greenOnly: e.target.checked })}
            className="rounded border-gray-300 text-green-600 focus:ring-green-500"
          />
          <span className="text-sm text-gray-700">Sustainable flights only</span>
        </label>
      </FilterSection>

      {/* Baggage */}
      <FilterSection title="Baggage" sectionKey="baggage">
        {['Cabin Only', 'Checked Baggage (1 piece)', 'Checked Baggage (2 pieces)'].map(baggage => (
          <label key={baggage} className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.baggage.includes(baggage)}
              onChange={() => toggleArrayItem('baggage', baggage)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{baggage}</span>
          </label>
        ))}
      </FilterSection>
    </div>
  )
}
