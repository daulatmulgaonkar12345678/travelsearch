"use client"

import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react'

interface DateOption {
  date: string // YYYY-MM-DD
  dayName: string
  dayNum: string
  month: string
  bestPrice: number | null
  currency: string
}

interface FlexibleDateBarProps {
  dates: DateOption[]
  selectedDate: string
  onDateSelect: (date: string) => void
  loading?: boolean
  onMonthViewClick?: () => void
}

export default function FlexibleDateBar({ 
  dates, 
  selectedDate, 
  onDateSelect,
  loading 
}: FlexibleDateBarProps) {
  const formatPrice = (price: number | null, currency: string) => {
    if (price === null) return '–'
    return `${currency} ${Math.round(price).toLocaleString()}`
  }

  return (
    <div className="bg-white border-b border-gray-200 py-2 sticky top-16 z-40 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center gap-2">
          <button
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors flex-shrink-0"
            onClick={() => {
              const currentIndex = dates.findIndex(d => d.date === selectedDate)
              if (currentIndex > 0) {
                onDateSelect(dates[currentIndex - 1].date)
              }
            }}
            disabled={loading}
          >
            <ChevronLeft className="h-5 w-5 text-gray-600" />
          </button>

          <div className="flex-1 overflow-x-auto scrollbar-hide">
            <div className="flex w-full gap-3">
              {dates.map((dateOption) => {
                const isSelected = dateOption.date === selectedDate
                const hasPrice = dateOption.bestPrice !== null

                return (
                  <button
                    key={dateOption.date}
                    onClick={() => onDateSelect(dateOption.date)}
                    disabled={loading}
                    className={`
                      flex-1 px-4 py-3 rounded-lg border-2 transition-all min-w-[120px]
                      ${isSelected
                        ? 'border-blue-600 bg-blue-50 shadow-sm'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                      }
                      ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    <div className="text-center">
                      <div className={`text-xs font-medium ${isSelected ? 'text-blue-600' : 'text-gray-500'}`}>
                        {dateOption.dayName}
                      </div>
                      <div className={`text-lg font-bold mt-1 ${isSelected ? 'text-blue-600' : 'text-gray-900'}`}>
                        {dateOption.dayNum}
                      </div>
                      <div className={`text-xs mt-1 font-medium ${hasPrice ? 'text-green-600' : 'text-gray-400'}`}>
                        {loading && isSelected ? '...' : formatPrice(dateOption.bestPrice, dateOption.currency)}
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          <button
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors flex-shrink-0"
            onClick={() => {
              const currentIndex = dates.findIndex(d => d.date === selectedDate)
              if (currentIndex < dates.length - 1) {
                onDateSelect(dates[currentIndex + 1].date)
              }
            }}
            disabled={loading}
          >
            <ChevronRight className="h-5 w-5 text-gray-600" />
          </button>
        </div>
      </div>
    </div>
  )
}
