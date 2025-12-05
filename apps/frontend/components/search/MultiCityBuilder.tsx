'use client'

import { Plus, X, Calendar } from 'lucide-react'
import { useState } from 'react'

interface FlightSegment {
  id: string
  origin: string
  destination: string
  date: string
}

interface MultiCityBuilderProps {
  segments: FlightSegment[]
  onChange: (segments: FlightSegment[]) => void
}

export default function MultiCityBuilder({ segments, onChange }: MultiCityBuilderProps) {
  const addSegment = () => {
    onChange([
      ...segments,
      {
        id: `segment-${Date.now()}`,
        origin: '',
        destination: '',
        date: '',
      },
    ])
  }

  const removeSegment = (id: string) => {
    if (segments.length > 2) {
      onChange(segments.filter(seg => seg.id !== id))
    }
  }

  const updateSegment = (id: string, field: keyof FlightSegment, value: string) => {
    onChange(
      segments.map(seg =>
        seg.id === id ? { ...seg, [field]: value } : seg
      )
    )
  }

  return (
    <div className="space-y-4">
      {segments.map((segment, index) => (
        <div key={segment.id} className="border border-gray-200 rounded-xl p-4 bg-gray-50">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-700">Flight {index + 1}</span>
            {segments.length > 2 && (
              <button
                type="button"
                onClick={() => removeSegment(segment.id)}
                className="text-red-500 hover:text-red-700 p-1"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          
          <div className="grid md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">From</label>
              <input
                type="text"
                value={segment.origin}
                onChange={(e) => updateSegment(segment.id, 'origin', e.target.value)}
                placeholder="Origin"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">To</label>
              <input
                type="text"
                value={segment.destination}
                onChange={(e) => updateSegment(segment.id, 'destination', e.target.value)}
                placeholder="Destination"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Date</label>
              <div className="relative">
                <Calendar className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="date"
                  value={segment.date}
                  onChange={(e) => updateSegment(segment.id, 'date', e.target.value)}
                  className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>
      ))}
      
      <button
        type="button"
        onClick={addSegment}
        className="w-full py-2 px-4 border-2 border-dashed border-gray-300 rounded-xl text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-colors flex items-center justify-center gap-2"
      >
        <Plus className="h-4 w-4" />
        Add Another Flight
      </button>
    </div>
  )
}
