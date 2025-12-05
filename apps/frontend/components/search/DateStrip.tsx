'use client'

import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { formatCurrency } from '@/lib/utils'

interface DateStripProps {
  selectedDate?: string
  onDateSelect?: (date: string) => void
  priceData?: Record<string, number>
}

export default function DateStrip({ selectedDate, onDateSelect, priceData = {} }: DateStripProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [showFullMonth, setShowFullMonth] = useState(false)

  // Generate dates for the strip (7 days)
  const generateDates = () => {
    const dates = []
    const today = new Date()
    for (let i = 0; i < 7; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      dates.push(date)
    }
    return dates
  }

  // Generate full month dates
  const generateMonthDates = () => {
    const dates = []
    const year = currentMonth.getFullYear()
    const month = currentMonth.getMonth()
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day)
      if (date >= new Date()) {
        dates.push(date)
      }
    }
    return dates
  }

  const dates = showFullMonth ? generateMonthDates() : generateDates()

  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0]
  }

  const getPrice = (date: Date): number => {
    const dateStr = formatDate(date)
    return priceData[dateStr] || 3500 + Math.floor(Math.random() * 5000)
  }

  const findCheapestDate = () => {
    let cheapest = dates[0]
    let lowestPrice = getPrice(dates[0])
    
    dates.forEach(date => {
      const price = getPrice(date)
      if (price < lowestPrice) {
        lowestPrice = price
        cheapest = date
      }
    })
    return formatDate(cheapest)
  }

  const cheapestDate = findCheapestDate()

  const scrollMonth = (direction: 'prev' | 'next') => {
    const newMonth = new Date(currentMonth)
    newMonth.setMonth(currentMonth.getMonth() + (direction === 'next' ? 1 : -1))
    setCurrentMonth(newMonth)
  }

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-medium text-gray-700">Select Date</h3>
            <span className="text-xs text-green-600 font-medium">Cheapest: {cheapestDate}</span>
          </div>
          <button
            data-testid="toggle-month-view"
            onClick={() => setShowFullMonth(!showFullMonth)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {showFullMonth ? 'Show Week' : 'Show Full Month'}
          </button>
        </div>

        {showFullMonth && (
          <div className="flex items-center justify-between mb-2">
            <button
              onClick={() => scrollMonth('prev')}
              className="p-2 hover:bg-gray-100 rounded-lg"
              data-testid="prev-month"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span className="text-sm font-medium">
              {currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </span>
            <button
              onClick={() => scrollMonth('next')}
              className="p-2 hover:bg-gray-100 rounded-lg"
              data-testid="next-month"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        )}

        <div className={`grid gap-2 ${
          showFullMonth ? 'grid-cols-7' : 'grid-cols-7'
        } overflow-x-auto`}>
          {dates.map((date) => {
            const dateStr = formatDate(date)
            const price = getPrice(date)
            const isSelected = selectedDate === dateStr
            const isCheapest = dateStr === cheapestDate

            return (
              <button
                key={dateStr}
                data-testid={`date-${dateStr}`}
                onClick={() => onDateSelect?.(dateStr)}
                className={`p-3 rounded-xl border-2 transition-all ${
                  isSelected
                    ? 'border-blue-600 bg-blue-50'
                    : isCheapest
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-center">
                  <div className="text-xs text-gray-500 mb-1">
                    {date.toLocaleDateString('en-US', { weekday: 'short' })}
                  </div>
                  <div className="text-lg font-bold mb-1">
                    {date.getDate()}
                  </div>
                  <div className={`text-xs font-medium ${
                    isCheapest ? 'text-green-600' : 'text-gray-700'
                  }`}>
                    {formatCurrency(price)}
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
