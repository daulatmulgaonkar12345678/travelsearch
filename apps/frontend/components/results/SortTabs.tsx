"use client"

import { formatDuration } from '@/lib/formatters'

interface SortTabsProps {
  activeSort: 'best' | 'cheapest' | 'fastest'
  onSortChange: (sort: 'best' | 'cheapest' | 'fastest') => void
  prices?: {
    best?: number
    cheapest?: number
    fastest?: number
  }
  durations?: {
    best?: number
    cheapest?: number
    fastest?: number
  }
  currency?: string
}

const formatPrice = (price: number) => {
  return Math.round(price).toLocaleString()
}

export default function SortTabs({ 
  activeSort, 
  onSortChange, 
  prices, 
  durations,
  currency = 'INR' 
}: SortTabsProps) {
  const tabs = [
    { id: 'best' as const, label: 'Best' },
    { id: 'cheapest' as const, label: 'Cheapest' },
    { id: 'fastest' as const, label: 'Fastest' },
  ]

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="flex">
        {tabs.map((tab) => {
          const isActive = activeSort === tab.id
          const price = prices?.[tab.id]
          const duration = durations?.[tab.id]

          return (
            <button
              key={tab.id}
              onClick={() => onSortChange(tab.id)}
              className={`
                flex-1 px-6 py-4 text-center transition-all border-b-2
                ${isActive
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-transparent hover:bg-gray-50'
                }
              `}
            >
              {/* Tab Label */}
              <div className={`text-sm font-medium mb-1 ${isActive ? 'text-blue-600' : 'text-gray-600'}`}>
                {tab.label}
              </div>
              
              {/* Price */}
              {price !== undefined ? (
                <div className="text-lg font-semibold text-slate-900">
                  {currency} {formatPrice(price)}
                </div>
              ) : (
                <div className="text-sm text-gray-500">No flights</div>
              )}
              
              {/* Duration - only show if available */}
              {duration !== undefined && (
                <div className="text-xs text-slate-500 mt-0.5">
                  {formatDuration(duration)}
                </div>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
