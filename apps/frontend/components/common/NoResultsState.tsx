'use client'

/**
 * NoResultsState - User-friendly "No Results" UI
 * ==============================================
 * 
 * Used when search completes successfully (200) but returns empty results.
 * This is NOT an error - it's valid business state.
 * 
 * NEVER show raw errors (404, 500) to users through this component.
 */

import { Bus, Train, Plane, Hotel, Calendar, Search, ArrowLeft } from 'lucide-react'

export type ServiceType = 'bus' | 'train' | 'flight' | 'hotel'

interface NoResultsStateProps {
  service: ServiceType
  origin?: string
  destination?: string
  date?: string
  onChangeDate?: () => void
  onModifySearch?: () => void
  onGoBack?: () => void
}

const SERVICE_CONFIG = {
  bus: {
    icon: Bus,
    color: 'orange',
    title: 'No buses available for this route right now',
    subtitle: 'Try a different date or check nearby stops',
  },
  train: {
    icon: Train,
    color: 'blue',
    title: 'No trains available for this route right now',
    subtitle: 'Try a different date or nearby stations',
  },
  flight: {
    icon: Plane,
    color: 'sky',
    title: 'No flights found for this date',
    subtitle: 'Try adjusting your travel date or airports',
  },
  hotel: {
    icon: Hotel,
    color: 'purple',
    title: 'No hotels available for selected dates',
    subtitle: 'Try different dates or nearby locations',
  },
}

export default function NoResultsState({
  service,
  origin,
  destination,
  date,
  onChangeDate,
  onModifySearch,
  onGoBack,
}: NoResultsStateProps) {
  const config = SERVICE_CONFIG[service]
  const Icon = config.icon

  // Color mapping for different services
  const colorClasses = {
    orange: {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      icon: 'text-orange-500',
      buttonPrimary: 'bg-orange-600 hover:bg-orange-700 text-white',
      buttonSecondary: 'border-orange-300 text-orange-700 hover:bg-orange-50',
    },
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      icon: 'text-blue-500',
      buttonPrimary: 'bg-blue-600 hover:bg-blue-700 text-white',
      buttonSecondary: 'border-blue-300 text-blue-700 hover:bg-blue-50',
    },
    sky: {
      bg: 'bg-sky-50',
      border: 'border-sky-200',
      icon: 'text-sky-500',
      buttonPrimary: 'bg-sky-600 hover:bg-sky-700 text-white',
      buttonSecondary: 'border-sky-300 text-sky-700 hover:bg-sky-50',
    },
    purple: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      icon: 'text-purple-500',
      buttonPrimary: 'bg-purple-600 hover:bg-purple-700 text-white',
      buttonSecondary: 'border-purple-300 text-purple-700 hover:bg-purple-50',
    },
  }

  const colors = colorClasses[config.color as keyof typeof colorClasses]

  return (
    <div className={`${colors.bg} ${colors.border} border rounded-xl p-8 text-center`}>
      {/* Icon */}
      <div className={`${colors.icon} mx-auto mb-4`}>
        <Icon className="h-12 w-12 mx-auto opacity-60" />
      </div>

      {/* Title */}
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        {config.title}
      </h2>

      {/* Route info if provided */}
      {origin && destination && (
        <p className="text-gray-600 mb-2">
          {origin} → {destination}
          {date && ` on ${new Date(date).toLocaleDateString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric' 
          })}`}
        </p>
      )}

      {/* Subtitle */}
      <p className="text-gray-500 mb-6">
        {config.subtitle}
      </p>

      {/* Action Buttons */}
      <div className="flex flex-wrap justify-center gap-3">
        {onChangeDate && (
          <button
            onClick={onChangeDate}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${colors.buttonPrimary}`}
          >
            <Calendar className="h-4 w-4" />
            Change Date
          </button>
        )}
        
        {onModifySearch && (
          <button
            onClick={onModifySearch}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium border transition ${colors.buttonSecondary}`}
          >
            <Search className="h-4 w-4" />
            Modify Search
          </button>
        )}

        {onGoBack && (
          <button
            onClick={onGoBack}
            className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium border border-gray-300 text-gray-700 hover:bg-gray-50 transition"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </button>
        )}
      </div>
    </div>
  )
}
