'use client'

import { useState, useEffect } from 'react'
import { X, Calendar, ChevronLeft, ChevronRight } from 'lucide-react'

interface DatePrice {
  date: string
  price: number | null
  isAvailable: boolean
}

interface MonthViewProps {
  isOpen: boolean
  onClose: () => void
  selectedDate: string
  onDateSelect: (date: string) => void
  origin: string
  destination: string
  fetchPricesForMonth: (month: string) => Promise<DatePrice[]>
}

export default function MonthView({
  isOpen,
  onClose,
  selectedDate,
  onDateSelect,
  origin,
  destination,
  fetchPricesForMonth,
}: MonthViewProps) {
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date(selectedDate))
  const [datePrices, setDatePrices] = useState<DatePrice[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadMonthPrices()
    }
  }, [isOpen, currentMonth])

  const loadMonthPrices = async () => {
    setLoading(true)
    try {
      const monthKey = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}`
      const prices = await fetchPricesForMonth(monthKey)
      setDatePrices(prices)
    } catch (error) {
      console.error('Failed to load month prices:', error)
    } finally {
      setLoading(false)
    }
  }

  const getPriceCategory = (price: number | null, allPrices: number[]) => {
    if (!price || allPrices.length === 0) return 'none'
    
    const sortedPrices = [...allPrices].sort((a, b) => a - b)
    const minPrice = sortedPrices[0]
    const maxPrice = sortedPrices[sortedPrices.length - 1]
    const range = maxPrice - minPrice
    
    // Cheapest 10-15%
    if (price <= minPrice + range * 0.15) return 'cheapest'
    
    // Higher than average
    if (price >= minPrice + range * 0.7) return 'higher'
    
    // Normal
    return 'normal'
  }

  const getTooltipText = (category: string) => {
    switch (category) {
      case 'cheapest':
        return 'Cheapest fare for this month'
      case 'higher':
        return 'Higher than average for this month'
      default:
        return 'Typical price compared to other days'
    }
  }

  const getPriceColorClass = (category: string) => {
    switch (category) {
      case 'cheapest':
        return 'text-green-700 font-semibold'
      case 'higher':
        return 'text-gray-400'
      default:
        return 'text-gray-700'
    }
  }

  const getBackgroundClass = (category: string, isSelected: boolean) => {
    if (isSelected) return 'bg-blue-600 text-white'
    if (category === 'cheapest') return 'bg-green-50 hover:bg-green-100'
    return 'hover:bg-gray-100'
  }

  const getDaysInMonth = () => {
    const year = currentMonth.getFullYear()
    const month = currentMonth.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    
    const days: Date[] = []
    for (let d = new Date(firstDay); d <= lastDay; d.setDate(d.getDate() + 1)) {
      days.push(new Date(d))
    }
    
    return days
  }

  const previousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))
  }

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))
  }

  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0]
  }

  const formatPrice = (price: number | null) => {
    if (!price) return '–'
    return `₹${Math.round(price).toLocaleString('en-IN')}`
  }

  if (!isOpen) return null

  const days = getDaysInMonth()
  const availablePrices = datePrices.filter(dp => dp.price !== null).map(dp => dp.price!)
  const cheapestPrice = availablePrices.length > 0 ? Math.min(...availablePrices) : null

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {origin} → {destination}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Select a date to update your search
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-5 w-5 text-gray-600" />
          </button>
        </div>

        {/* Month Navigation */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <button
              onClick={previousMonth}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <ChevronLeft className="h-5 w-5 text-gray-600" />
            </button>
            <div className="text-lg font-semibold text-gray-900">
              {currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </div>
            <button
              onClick={nextMonth}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <ChevronRight className="h-5 w-5 text-gray-600" />
            </button>
          </div>
        </div>

        {/* Calendar Grid */}
        <div className="p-4">
          {/* Weekday Headers */}
          <div className="grid grid-cols-7 gap-2 mb-2">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
              <div key={day} className="text-center text-sm font-semibold text-gray-600 py-2">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Days */}
          <div className="grid grid-cols-7 gap-2">
            {/* Empty cells for days before month start */}
            {Array.from({ length: days[0].getDay() }).map((_, idx) => (
              <div key={`empty-${idx}`} />
            ))}

            {/* Actual days */}
            {days.map((day) => {
              const dateStr = formatDate(day)
              const dateData = datePrices.find(dp => dp.date === dateStr)
              const price = dateData?.price
              const category = getPriceCategory(price, availablePrices)
              const isSelected = dateStr === selectedDate
              const isPast = day < new Date(new Date().setHours(0, 0, 0, 0))

              return (
                <button
                  key={dateStr}
                  onClick={() => {
                    if (!isPast && price !== null) {
                      onDateSelect(dateStr)
                      onClose()
                    }
                  }}
                  disabled={isPast || price === null}
                  className={`
                    group relative p-3 rounded-lg border transition-all
                    ${getBackgroundClass(category, isSelected)}
                    ${isPast || price === null ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer border-gray-200'}
                    ${category === 'cheapest' && !isSelected ? 'border-green-300' : ''}
                  `}
                  title={price ? getTooltipText(category) : 'No flights available'}
                >
                  <div className={`text-sm font-medium ${isSelected ? 'text-white' : 'text-gray-900'}`}>
                    {day.getDate()}
                  </div>
                  <div className={`text-xs mt-1 ${isSelected ? 'text-white' : getPriceColorClass(category)}`}>
                    {loading ? '...' : formatPrice(price)}
                  </div>

                  {/* Cheapest indicator */}
                  {category === 'cheapest' && !isSelected && (
                    <div className="absolute bottom-1 left-1/2 -translate-x-1/2">
                      <div className="h-1 w-6 bg-green-500 rounded-full"></div>
                    </div>
                  )}

                  {/* Tooltip */}
                  {price && !isPast && (
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                      <div className="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                        {getTooltipText(category)}
                      </div>
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* Legend */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-center space-x-6 text-xs text-gray-600">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span>Cheapest</span>
            </div>
            <span>•</span>
            <span>Prices vary by date</span>
            <span>•</span>
            <span>Final prices from partners</span>
          </div>
        </div>
      </div>
    </div>
  )
}
