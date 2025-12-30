'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Plane, Hotel, Calendar, Users, Train, Bus } from 'lucide-react'
import TripTypeSelector from './TripTypeSelector'
import CabinClassSelector from './CabinClassSelector'
import AdvancedPassengerModal from './AdvancedPassengerModal'
import EnhancedHotelRoomSelector from './EnhancedHotelRoomSelector'
import DateInputs from './DateInputs'
import AirportAutocomplete from './AirportAutocomplete'
import ValidatedAirportInput from './ValidatedAirportInput'
import BusLocationAutocomplete, { BusPlace } from './BusLocationAutocomplete'
import TrainStationAutocomplete, { TrainStationOption } from './TrainStationAutocomplete'
import HotelLocationAutocomplete, { HotelCity } from './HotelLocationAutocomplete'
import { Airport, validateFlightSearch, extractIATACodes } from '@/lib/airportValidation'
import { SearchButtonMicrocopy } from '@/components/trust/Microcopy'
import { PREFILL_SEARCH_EVENT, PrefillEventData } from '@/components/seo/InternalLinks'

/* ======================================================
   🎨 SERVICE COLOR THEME (Low blue light, eye-friendly)
====================================================== */

const SERVICE_THEME = {
  flights: {
    primary: '#5F8D7E',
    bg: 'rgba(95,141,126,0.08)',
    border: 'rgba(95,141,126,0.25)',
    hover: '#4E7A6C',
  },
  buses: {
    primary: '#C0703D',
    bg: 'rgba(192,112,61,0.08)',
    border: 'rgba(192,112,61,0.25)',
    hover: '#A95F33',
  },
  trains: {
    primary: '#6E8B5C',
    bg: 'rgba(110,139,92,0.08)',
    border: 'rgba(110,139,92,0.25)',
    hover: '#5F7A4E',
  },
  hotels: {
    primary: '#C6A15B',
    bg: 'rgba(198,161,91,0.08)',
    border: 'rgba(198,161,91,0.25)',
    hover: '#B08E4F',
  },
} as const

type SearchType = keyof typeof SERVICE_THEME

export default function SearchBarV3({ defaultTab = 'flights' }: { defaultTab?: SearchType }) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const searchFormRef = useRef<HTMLDivElement>(null)
  const [mounted, setMounted] = useState(false)

  const getTabFromUrl = (): SearchType => {
    const tab = searchParams.get('tab') as SearchType
    return tab && SERVICE_THEME[tab] ? tab : defaultTab
  }

  const [searchType, setSearchTypeState] = useState<SearchType>(getTabFromUrl)

  useEffect(() => {
    setSearchTypeState(getTabFromUrl())
  }, [searchParams])

  const setSearchType = (type: SearchType) => {
    setSearchTypeState(type)
    router.push(`/?tab=${type}`, { scroll: false })
  }

  useEffect(() => setMounted(true), [])

  if (!mounted) {
    return <div className="h-96 bg-white rounded-3xl animate-pulse" />
  }

  const theme = SERVICE_THEME[searchType]

  return (
    <div
      ref={searchFormRef}
      className="rounded-3xl shadow-xl transition-colors duration-300 overflow-hidden"
      style={{
        backgroundColor: theme.bg,
        border: `1px solid ${theme.border}`,
      }}
    >
      {/* Tabs */}
      <div className="flex border-b overflow-x-auto">
        {(['flights', 'buses', 'trains', 'hotels'] as SearchType[]).map((tab) => {
          const Icon =
            tab === 'flights' ? Plane : tab === 'buses' ? Bus : tab === 'trains' ? Train : Hotel
          const isActive = searchType === tab
          const t = SERVICE_THEME[tab]

          return (
            <button
              key={tab}
              onClick={() => setSearchType(tab)}
              className="flex-1 min-w-[110px] py-4 flex items-center justify-center gap-2 font-medium transition"
              style={
                isActive
                  ? {
                      backgroundColor: t.bg,
                      color: t.primary,
                      borderBottom: `3px solid ${t.primary}`,
                    }
                  : undefined
              }
            >
              <Icon className="h-5 w-5" />
              <span className="capitalize">{tab}</span>
            </button>
          )
        })}
      </div>

      {/* Content */}
      <div className="p-6">
        <div className="text-sm text-gray-700 mb-4">
          {searchType === 'flights' && 'Search flights across trusted airlines'}
          {searchType === 'buses' && 'Compare bus routes and fares'}
          {searchType === 'trains' && 'Find train schedules and prices'}
          {searchType === 'hotels' && 'Compare hotel prices'}
        </div>

        {/* Search Button */}
        <button
          className="w-full mt-6 py-4 rounded-xl text-white font-semibold shadow-lg transition-all"
          style={{ backgroundColor: theme.primary }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = theme.hover)}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = theme.primary)}
        >
          Search {searchType}
        </button>

        <SearchButtonMicrocopy />
      </div>
    </div>
  )
}
