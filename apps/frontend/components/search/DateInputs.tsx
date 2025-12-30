"use client"

import { Calendar } from 'lucide-react'
import { useState, useEffect, useCallback } from 'react'

interface DateInputsProps {
  checkIn: string
  checkOut: string
  onChange: (dates: { checkIn: string; checkOut: string }) => void
  minCheckIn?: string
}

export default function DateInputs({ checkIn, checkOut, onChange, minCheckIn }: DateInputsProps) {
  // Calculate min check-in (today by default)
  const getMinCheckIn = useCallback(() => {
    if (minCheckIn) return minCheckIn
    const today = new Date()
    return today.toISOString().split('T')[0]
  }, [minCheckIn])

  const [ci, setCi] = useState(checkIn || getMinCheckIn())
  const [co, setCo] = useState(() => {
    if (checkOut) return checkOut
    const minCi = new Date(getMinCheckIn())
    minCi.setDate(minCi.getDate() + 1)
    return minCi.toISOString().split('T')[0]
  })

  // Sync internal state with props when they change (for Modify Search hydration)
  useEffect(() => {
    if (checkIn && checkIn !== ci) {
      setCi(checkIn)
    }
  }, [checkIn]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (checkOut && checkOut !== co) {
      setCo(checkOut)
    }
  }, [checkOut]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    onChange({ checkIn: ci, checkOut: co })
  }, [ci, co]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleCheckInChange = (value: string) => {
    const minAllowed = getMinCheckIn()
    const selected = new Date(value)
    const minDate = new Date(minAllowed)
    
    // Enforce minimum check-in date
    if (selected < minDate) {
      setCi(minAllowed)
      return
    }
    
    setCi(value)
    
    // Ensure check-out is after check-in
    const currentCheckOut = new Date(co)
    const newCheckIn = new Date(value)
    if (currentCheckOut <= newCheckIn) {
      const nextDay = new Date(newCheckIn)
      nextDay.setDate(nextDay.getDate() + 1)
      setCo(nextDay.toISOString().split('T')[0])
    }
  }

  const handleCheckOutChange = (value: string) => {
    const selected = new Date(value)
    const checkInDate = new Date(ci)
    
    // Enforce check-out > check-in
    if (selected <= checkInDate) {
      const nextDay = new Date(checkInDate)
      nextDay.setDate(nextDay.getDate() + 1)
      setCo(nextDay.toISOString().split('T')[0])
      return
    }
    
    setCo(value)
  }

  // Get minimum check-out date (check-in + 1 day)
  const getMinCheckOut = () => {
    const checkInDate = new Date(ci)
    checkInDate.setDate(checkInDate.getDate() + 1)
    return checkInDate.toISOString().split('T')[0]
  }

  return (
    <>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Check-in</label>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            data-testid="checkin-date-input"
            type="date"
            value={ci}
            min={getMinCheckIn()}
            onChange={(e) => handleCheckInChange(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Check-out</label>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            data-testid="checkout-date-input"
            type="date"
            value={co}
            min={getMinCheckOut()}
            onChange={(e) => handleCheckOutChange(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
    </>
  )
}
