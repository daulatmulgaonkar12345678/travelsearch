'use client'

import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export interface HotelFilterState {
  // Price
  priceRange: [number, number]
  
  // Star rating
  starRatings: number[]
  
  // Guest rating
  minGuestRating: number
  
  // Room types
  roomTypes: string[]
  acOnly: boolean
  
  // Amenities
  amenities: string[]
  
  // Policies
  freeCancellation: boolean
  payAtHotel: boolean
  
  // Location
  maxDistanceKm: number
}

interface HotelFilterSidebarProps {
  filters: HotelFilterState
  onFilterChange: (filters: HotelFilterState) => void
  maxPriceLimit?: number
}

export default function HotelFilterSidebar({
  filters,
  onFilterChange,
  maxPriceLimit = 20000,
}: HotelFilterSidebarProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    price: true,
    rating: true,
    roomType: false,
    amenities: false,
    policies: false,
    location: false,
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const toggleArrayItem = (key: keyof HotelFilterState, item: string | number) => {
    const currentArray = filters[key] as (string | number)[]
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
      <FilterSection title="Price per Night" sectionKey="price">
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-600 block mb-1">
              Min: ₹{filters.priceRange[0].toLocaleString()}
            </label>
            <input
              type="range"
              min="500"
              max={maxPriceLimit}
              step="500"
              value={filters.priceRange[0]}
              onChange={(e) => onFilterChange({
                ...filters,
                priceRange: [parseInt(e.target.value), filters.priceRange[1]]
              })}
              className="w-full"
            />
          </div>
          <div>
            <label className="text-xs text-gray-600 block mb-1">
              Max: ₹{filters.priceRange[1].toLocaleString()}
            </label>
            <input
              type="range"
              min="500"
              max={maxPriceLimit}
              step="500"
              value={filters.priceRange[1]}
              onChange={(e) => onFilterChange({
                ...filters,
                priceRange: [filters.priceRange[0], parseInt(e.target.value)]
              })}
              className="w-full"
            />
          </div>
        </div>
      </FilterSection>

      {/* Star Rating */}
      <FilterSection title="Star Rating" sectionKey="rating">
        <div className="space-y-2">
          {[5, 4, 3, 2, 1].map(stars => (
            <label key={stars} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.starRatings.includes(stars)}
                onChange={() => toggleArrayItem('starRatings', stars)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                {'⭐'.repeat(stars)} {stars === 1 ? 'star' : 'stars'}
              </span>
            </label>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t border-gray-100">
          <label className="text-xs text-gray-600 block mb-1">
            Min Guest Rating: {filters.minGuestRating}/10
          </label>
          <input
            type="range"
            min="0"
            max="10"
            step="0.5"
            value={filters.minGuestRating}
            onChange={(e) => onFilterChange({ ...filters, minGuestRating: parseFloat(e.target.value) })}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Any</span>
            <span>7+</span>
            <span>8+</span>
            <span>9+</span>
          </div>
        </div>
      </FilterSection>

      {/* Room Type */}
      <FilterSection title="Room Type" sectionKey="roomType">
        {['Standard', 'Deluxe', 'Super Deluxe', 'Suite'].map(type => (
          <label key={type} className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.roomTypes.includes(type)}
              onChange={() => toggleArrayItem('roomTypes', type)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{type}</span>
          </label>
        ))}
        <label className="flex items-center space-x-2 cursor-pointer mt-2 pt-2 border-t border-gray-100">
          <input
            type="checkbox"
            checked={filters.acOnly}
            onChange={(e) => onFilterChange({ ...filters, acOnly: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">AC Only</span>
        </label>
      </FilterSection>

      {/* Amenities */}
      <FilterSection title="Amenities" sectionKey="amenities">
        {[
          { value: 'wifi', label: 'Free WiFi' },
          { value: 'breakfast', label: 'Breakfast Included' },
          { value: 'pool', label: 'Swimming Pool' },
          { value: 'gym', label: 'Gym/Fitness Center' },
          { value: 'parking', label: 'Free Parking' },
          { value: 'airport_shuttle', label: 'Airport Shuttle' },
          { value: 'pet_friendly', label: 'Pet-Friendly' },
          { value: 'kitchenette', label: 'Kitchenette' },
        ].map(amenity => (
          <label key={amenity.value} className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.amenities.includes(amenity.value)}
              onChange={() => toggleArrayItem('amenities', amenity.value)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{amenity.label}</span>
          </label>
        ))}
      </FilterSection>

      {/* Policies */}
      <FilterSection title="Booking Policies" sectionKey="policies">
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.freeCancellation}
            onChange={(e) => onFilterChange({ ...filters, freeCancellation: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Free Cancellation</span>
        </label>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.payAtHotel}
            onChange={(e) => onFilterChange({ ...filters, payAtHotel: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Pay at Hotel</span>
        </label>
      </FilterSection>

      {/* Location */}
      <FilterSection title="Distance from Center" sectionKey="location">
        <div>
          <label className="text-xs text-gray-600 block mb-1">
            Within {filters.maxDistanceKm === 50 ? '50+' : filters.maxDistanceKm} km
          </label>
          <input
            type="range"
            min="1"
            max="50"
            value={filters.maxDistanceKm}
            onChange={(e) => onFilterChange({ ...filters, maxDistanceKm: parseInt(e.target.value) })}
            className="w-full"
          />
        </div>
      </FilterSection>
    </div>
  )
}
