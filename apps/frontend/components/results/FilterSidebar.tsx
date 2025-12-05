'use client'

import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface FilterState {
  stops: string[]
  baggage: string[]
  departureTime: [number, number]
  arrivalTime: [number, number]
  duration: [number, number]
  airlines: string[]
  emissions: boolean
}

interface FilterSidebarProps {
  filters: FilterState
  onFilterChange: (filters: FilterState) => void
  availableAirlines?: string[]
}

export default function FilterSidebar({
  filters,
  onFilterChange,
  availableAirlines = ['IndiGo', 'Air India', 'Vistara', 'SpiceJet', 'GoAir']
}: FilterSidebarProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    stops: true,
    baggage: true,
    time: false,
    duration: false,
    airlines: false,
    emissions: false,
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const toggleStop = (stop: string) => {
    const newStops = filters.stops.includes(stop)
      ? filters.stops.filter(s => s !== stop)
      : [...filters.stops, stop]
    onFilterChange({ ...filters, stops: newStops })
  }

  const toggleBaggage = (baggage: string) => {
    const newBaggage = filters.baggage.includes(baggage)
      ? filters.baggage.filter(b => b !== baggage)
      : [...filters.baggage, baggage]
    onFilterChange({ ...filters, baggage: newBaggage })
  }

  const toggleAirline = (airline: string) => {
    const newAirlines = filters.airlines.includes(airline)
      ? filters.airlines.filter(a => a !== airline)
      : [...filters.airlines, airline]
    onFilterChange({ ...filters, airlines: newAirlines })
  }

  const FilterSection = ({ title, sectionKey, children }: any) => (
    <div className="border-b border-gray-200 last:border-b-0">
      <button
        data-testid={`filter-section-${sectionKey}`}
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
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden" data-testid="filter-sidebar">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="font-semibold text-lg">Filters</h2>
      </div>

      <FilterSection title="Stops" sectionKey="stops">
        {['Non-stop', '1 Stop', '2+ Stops'].map(stop => (
          <label key={stop} className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.stops.includes(stop)}
              onChange={() => toggleStop(stop)}
              data-testid={`filter-stop-${stop}`}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{stop}</span>
          </label>
        ))}
      </FilterSection>

      <FilterSection title="Baggage" sectionKey="baggage">
        {['Cabin Only', 'Checked Baggage'].map(baggage => (
          <label key={baggage} className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.baggage.includes(baggage)}
              onChange={() => toggleBaggage(baggage)}
              data-testid={`filter-baggage-${baggage}`}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{baggage}</span>
          </label>
        ))}
      </FilterSection>

      <FilterSection title="Departure Time" sectionKey="time">
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-600 block mb-1">Earliest: {filters.departureTime[0]}:00</label>
            <input
              type="range"
              min="0"
              max="23"
              value={filters.departureTime[0]}
              onChange={(e) => onFilterChange({
                ...filters,
                departureTime: [parseInt(e.target.value), filters.departureTime[1]]
              })}
              data-testid="filter-departure-start"
              className="w-full"
            />
          </div>
          <div>
            <label className="text-xs text-gray-600 block mb-1">Latest: {filters.departureTime[1]}:00</label>
            <input
              type="range"
              min="0"
              max="23"
              value={filters.departureTime[1]}
              onChange={(e) => onFilterChange({
                ...filters,
                departureTime: [filters.departureTime[0], parseInt(e.target.value)]
              })}
              data-testid="filter-departure-end"
              className="w-full"
            />
          </div>
        </div>
      </FilterSection>

      <FilterSection title="Duration" sectionKey="duration">
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-600 block mb-1">Max Duration: {filters.duration[1]} hours</label>
            <input
              type="range"
              min="1"
              max="24"
              value={filters.duration[1]}
              onChange={(e) => onFilterChange({
                ...filters,
                duration: [0, parseInt(e.target.value)]
              })}
              data-testid="filter-duration"
              className="w-full"
            />
          </div>
        </div>
      </FilterSection>

      <FilterSection title="Airlines" sectionKey="airlines">
        {availableAirlines.map(airline => (
          <label key={airline} className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.airlines.includes(airline)}
              onChange={() => toggleAirline(airline)}
              data-testid={`filter-airline-${airline}`}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{airline}</span>
          </label>
        ))}
      </FilterSection>

      <FilterSection title="Emissions" sectionKey="emissions">
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.emissions}
            onChange={(e) => onFilterChange({ ...filters, emissions: e.target.checked })}
            data-testid="filter-emissions"
            className="rounded border-gray-300 text-green-600 focus:ring-green-500"
          />
          <span className="text-sm text-gray-700">Show low emissions only</span>
        </label>
      </FilterSection>
    </div>
  )
}
