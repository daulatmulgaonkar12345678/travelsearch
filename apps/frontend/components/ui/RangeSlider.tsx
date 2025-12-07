'use client'

import { useState, useRef, useEffect } from 'react'

interface RangeSliderProps {
  min: number
  max: number
  value: [number, number]
  onChange: (value: [number, number]) => void
  step?: number
  formatLabel?: (value: number) => string
  className?: string
}

export default function RangeSlider({
  min,
  max,
  value,
  onChange,
  step = 1,
  formatLabel,
  className = '',
}: RangeSliderProps) {
  const [isDragging, setIsDragging] = useState<'min' | 'max' | null>(null)
  const trackRef = useRef<HTMLDivElement>(null)

  const minValue = value[0]
  const maxValue = value[1]

  const getPercentage = (val: number) => {
    return ((val - min) / (max - min)) * 100
  }

  const getValueFromPosition = (clientX: number) => {
    if (!trackRef.current) return min

    const rect = trackRef.current.getBoundingClientRect()
    const percentage = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
    const rawValue = min + percentage * (max - min)
    return Math.round(rawValue / step) * step
  }

  const handleMouseDown = (handle: 'min' | 'max') => (e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(handle)
  }

  const handleTouchStart = (handle: 'min' | 'max') => (e: React.TouchEvent) => {
    e.preventDefault()
    setIsDragging(handle)
  }

  useEffect(() => {
    const handleMove = (clientX: number) => {
      if (!isDragging) return

      const newValue = getValueFromPosition(clientX)

      if (isDragging === 'min') {
        // Ensure min doesn't go beyond max
        const clampedValue = Math.min(newValue, maxValue)
        if (clampedValue !== minValue) {
          onChange([clampedValue, maxValue])
        }
      } else {
        // Ensure max doesn't go below min
        const clampedValue = Math.max(newValue, minValue)
        if (clampedValue !== maxValue) {
          onChange([minValue, clampedValue])
        }
      }
    }

    const handleMouseMove = (e: MouseEvent) => {
      handleMove(e.clientX)
    }

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length > 0) {
        handleMove(e.touches[0].clientX)
      }
    }

    const handleEnd = () => {
      setIsDragging(null)
    }

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleEnd)
      document.addEventListener('touchmove', handleTouchMove)
      document.addEventListener('touchend', handleEnd)

      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleEnd)
        document.removeEventListener('touchmove', handleTouchMove)
        document.removeEventListener('touchend', handleEnd)
      }
    }
  }, [isDragging, minValue, maxValue, min, max, step, onChange])

  const minPercentage = getPercentage(minValue)
  const maxPercentage = getPercentage(maxValue)

  return (
    <div className={`relative ${className}`}>
      {/* Track */}
      <div
        ref={trackRef}
        className="relative h-2 bg-gray-200 rounded-full cursor-pointer"
        onClick={(e) => {
          const newValue = getValueFromPosition(e.clientX)
          // Snap to nearest handle
          const distToMin = Math.abs(newValue - minValue)
          const distToMax = Math.abs(newValue - maxValue)

          if (distToMin < distToMax) {
            onChange([Math.min(newValue, maxValue), maxValue])
          } else {
            onChange([minValue, Math.max(newValue, minValue)])
          }
        }}
      >
        {/* Active range */}
        <div
          className="absolute h-full bg-blue-600 rounded-full"
          style={{
            left: `${minPercentage}%`,
            width: `${maxPercentage - minPercentage}%`,
          }}
        />

        {/* Min handle */}
        <div
          className={`absolute top-1/2 -translate-y-1/2 w-5 h-5 bg-white border-2 border-blue-600 rounded-full cursor-grab shadow-md transition-transform hover:scale-110 ${
            isDragging === 'min' ? 'scale-110 cursor-grabbing' : ''
          }`}
          style={{ left: `${minPercentage}%`, transform: 'translate(-50%, -50%)' }}
          onMouseDown={handleMouseDown('min')}
          onTouchStart={handleTouchStart('min')}
        />

        {/* Max handle */}
        <div
          className={`absolute top-1/2 -translate-y-1/2 w-5 h-5 bg-white border-2 border-blue-600 rounded-full cursor-grab shadow-md transition-transform hover:scale-110 ${
            isDragging === 'max' ? 'scale-110 cursor-grabbing' : ''
          }`}
          style={{ left: `${maxPercentage}%`, transform: 'translate(-50%, -50%)' }}
          onMouseDown={handleMouseDown('max')}
          onTouchStart={handleTouchStart('max')}
        />
      </div>

      {/* Labels (optional) */}
      {formatLabel && (
        <div className="flex justify-between mt-2 text-sm text-gray-600">
          <span>{formatLabel(minValue)}</span>
          <span>{formatLabel(maxValue)}</span>
        </div>
      )}
    </div>
  )
}
