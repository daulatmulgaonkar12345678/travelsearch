'use client'

import { ArrowRight, ArrowLeftRight, MapPin } from 'lucide-react'

type TripType = 'oneway' | 'roundtrip' | 'multicity'

interface TripTypeSelectorProps {
  value: TripType
  onChange: (type: TripType) => void
  /** Service accent color for active state (defaults to flights sage green) */
  accentColor?: string
}

export default function TripTypeSelector({ 
  value, 
  onChange,
  accentColor = '#5F8D7E' // Flights sage green default
}: TripTypeSelectorProps) {
  
  // Solid background color (lighter version of accent)
  const getActiveBg = () => {
    // Map accent to its light background version
    const colorMap: Record<string, string> = {
      '#5F8D7E': '#E8F0ED', // Flights - sage green
      '#C0703D': '#F9EBE0', // Buses - clay terracotta
      '#6E8B5C': '#EBF0E6', // Trains - olive green
      '#C6A15B': '#F9F3E6', // Hotels - sand gold
    }
    return colorMap[accentColor] || '#E8F0ED'
  }

  const activeBg = getActiveBg()

  return (
    <div className="flex gap-2 mb-4">
      {/* One-way Button */}
      <button
        onClick={() => onChange('oneway')}
        className="flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors"
        style={value === 'oneway' ? {
          backgroundColor: activeBg,
          color: accentColor,
        } : {
          backgroundColor: '#F3F4F6',
          color: '#6B7280',
        }}
      >
        <ArrowRight className="h-4 w-4 inline mr-1" />
        One-way
      </button>
      
      {/* Round-trip Button */}
      <button
        onClick={() => onChange('roundtrip')}
        className="flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors"
        style={value === 'roundtrip' ? {
          backgroundColor: activeBg,
          color: accentColor,
        } : {
          backgroundColor: '#F3F4F6',
          color: '#6B7280',
        }}
      >
        <ArrowLeftRight className="h-4 w-4 inline mr-1" />
        Round-trip
      </button>
      
      {/* Multi-city Button */}
      <button
        onClick={() => onChange('multicity')}
        className="flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors"
        style={value === 'multicity' ? {
          backgroundColor: activeBg,
          color: accentColor,
        } : {
          backgroundColor: '#F3F4F6',
          color: '#6B7280',
        }}
      >
        <MapPin className="h-4 w-4 inline mr-1" />
        Multi-city
      </button>
    </div>
  )
}
