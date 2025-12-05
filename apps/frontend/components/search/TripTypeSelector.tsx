'use client'

import { ArrowRight, ArrowLeftRight, MapPin } from 'lucide-react'

type TripType = 'oneway' | 'roundtrip' | 'multicity'

interface TripTypeSelectorProps {
  value: TripType
  onChange: (type: TripType) => void
}

export default function TripTypeSelector({ value, onChange }: TripTypeSelectorProps) {
  return (
    <div className="flex gap-2 mb-4">
      <button
        onClick={() => onChange('oneway')}
        className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
          value === 'oneway'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        <ArrowRight className="h-4 w-4 inline mr-1" />
        One-way
      </button>
      <button
        onClick={() => onChange('roundtrip')}
        className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
          value === 'roundtrip'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        <ArrowLeftRight className="h-4 w-4 inline mr-1" />
        Round-trip
      </button>
      <button
        onClick={() => onChange('multicity')}
        className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
          value === 'multicity'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        <MapPin className="h-4 w-4 inline mr-1" />
        Multi-city
      </button>
    </div>
  )
}
