"use client"

import { useState } from 'react'
import { ChevronDown, ChevronUp, X } from 'lucide-react'

interface AdvancedFiltersProps {
  filters: {
    stops: string[]
    departureTimeRange: [number, number]
    durationRange: [number, number]
    airlines: string[]
  }
  onFilterChange: (filters: any) => void
  availableAirlines: string[]
  minDuration: number
  maxDuration: number
}

export default function AdvancedFilters({ 
  filters, 
  onFilterChange, 
  availableAirlines,
  minDuration,
  maxDuration
}: AdvancedFiltersProps) {
  const [expandedSections, setExpandedSections] = useState({
    stops: true,
    departureTime: false,
    duration: false,
    airlines: false,
  })

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const handleStopsChange = (stop: string) => {
    const newStops = filters.stops.includes(stop)
      ? filters.stops.filter(s => s !== stop)
      : [...filters.stops, stop]
    onFilterChange({ ...filters, stops: newStops })
  }

  const handleAirlineChange = (airline: string) => {
    const newAirlines = filters.airlines.includes(airline)
      ? filters.airlines.filter(a => a !== airline)
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
            {['Direct', '1 stop', '2+ stops'].map((stop) => (
              <label key={stop} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.stops.includes(stop)}
                  onChange={() => handleStopsChange(stop)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-gray-700">{stop}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Departure Time Filter */}
      <div className="p-4">
        <button
          onClick={() => toggleSection('departureTime')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="font-semibold text-gray-900">Departure Time</h3>
          {expandedSections.departureTime ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>
        
        {expandedSections.departureTime && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>{formatTime(filters.departureTimeRange[0])}</span>
              <span>{formatTime(filters.departureTimeRange[1])}</span>
            </div>
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
            <input
              type="range"
              min="0"
              max="23"
              value={filters.departureTimeRange[1]}
              onChange={(e) => onFilterChange({
                ...filters,
                departureTimeRange: [filters.departureTimeRange[0], parseInt(e.target.value)]
              })}
              className="w-full mt-2"
            />
          </div>
        )}
      </div>

      {/* Duration Filter */}
      <div className="p-4">
        <button
          onClick={() => toggleSection('duration')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="font-semibold text-gray-900">Journey Duration</h3>
          {expandedSections.duration ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>
        
        {expandedSections.duration && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>{formatDuration(filters.durationRange[0])}</span>
              <span>{formatDuration(filters.durationRange[1])}</span>
            </div>
            <input
              type="range"
              min={minDuration}
              max={maxDuration}
              value={filters.durationRange[1]}
              onChange={(e) => onFilterChange({
                ...filters,
                durationRange: [filters.durationRange[0], parseInt(e.target.value)]
              })}
              className="w-full"
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
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                Select All
              </button>
              <span className="text-gray-400">|</span>
              <button
                onClick={handleAirlineClearAll}
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                Clear All
              </button>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {availableAirlines.map((airline) => (
                <label key={airline} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.airlines.includes(airline)}
                    onChange={() => handleAirlineChange(airline)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700 text-sm">{airline}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
