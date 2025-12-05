'use client'

import { ChevronDown } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

type CabinClass = 'economy' | 'premium_economy' | 'business' | 'first'

interface CabinClassSelectorProps {
  value: CabinClass
  onChange: (cabin: CabinClass) => void
}

const CABIN_OPTIONS = [
  { value: 'economy' as const, label: 'Economy' },
  { value: 'premium_economy' as const, label: 'Premium Economy' },
  { value: 'business' as const, label: 'Business' },
  { value: 'first' as const, label: 'First Class' },
]

export default function CabinClassSelector({ value, onChange }: CabinClassSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectedLabel = CABIN_OPTIONS.find(opt => opt.value === value)?.label || 'Economy'

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-sm font-medium text-gray-700 mb-2">Cabin Class</label>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 border border-gray-300 rounded-xl text-left flex items-center justify-between hover:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
      >
        <span>{selectedLabel}</span>
        <ChevronDown className="h-5 w-5 text-gray-400" />
      </button>
      
      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg">
          {CABIN_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                onChange(option.value)
                setIsOpen(false)
              }}
              className={`w-full px-4 py-3 text-left hover:bg-gray-50 first:rounded-t-xl last:rounded-b-xl transition-colors ${
                value === option.value ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-700'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
