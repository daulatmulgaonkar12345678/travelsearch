'use client'

import { Edit3 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { 
  saveModifySearchPayload, 
  FlightSearchPayload, 
  HotelSearchPayload, 
  BusSearchPayload, 
  TrainSearchPayload,
  createAirportFromCode,
} from '@/lib/modifySearchStore'

interface ModifySearchButtonProps {
  service: 'flights' | 'hotels' | 'buses' | 'trains'
  searchParams: {
    // Common
    departure_date?: string
    // Flights
    origin?: string
    destination?: string
    origin_name?: string      // Full airport name if available
    destination_name?: string
    origin_city?: string
    destination_city?: string
    return_date?: string
    adults?: string
    children?: string
    infants?: string
    cabin_class?: string
    trip_type?: string
    // Hotels
    city?: string
    check_in?: string
    check_out?: string
    hotel_name?: string
    rooms?: string
    // Buses/Trains
    passengers?: string
    bus_type?: string
    train_class?: string
  }
  variant?: 'default' | 'compact'
  className?: string
}

/**
 * ModifySearch Button - Opens search form with pre-filled values
 * 
 * FLOW:
 * 1. Saves search payload to localStorage (single source of truth)
 * 2. Navigates to homepage with ?modify=true&tab={service}
 * 3. SearchBarV3 reads from localStorage and hydrates form state
 * 
 * IMPORTANT: Stores FULL OBJECTS (not just codes) for validation
 */
export default function ModifySearchButton({
  service,
  searchParams,
  variant = 'default',
  className = '',
}: ModifySearchButtonProps) {
  const router = useRouter()

  const handleModifySearch = () => {
    // Step 1: Save payload to localStorage (SINGLE SOURCE OF TRUTH)
    savePayloadToStorage()
    
    // Step 2: Navigate to homepage with modify flag
    router.push(`/?tab=${service}&modify=true`)
  }

  /**
   * Save the search payload to localStorage before navigation
   * Creates full airport objects to pass validation on hydration
   */
  const savePayloadToStorage = () => {
    switch (service) {
      case 'flights': {
        // Create full airport objects from codes
        const originCode = searchParams.origin || ''
        const destCode = searchParams.destination || ''
        
        const payload: FlightSearchPayload = {
          service: 'flights',
          origin: createAirportFromCode(originCode),
          destination: createAirportFromCode(destCode),
          departure_date: searchParams.departure_date || '',
          return_date: searchParams.return_date,
          adults: parseInt(searchParams.adults || '1'),
          children: searchParams.children ? parseInt(searchParams.children) : undefined,
          infants: searchParams.infants ? parseInt(searchParams.infants) : undefined,
          cabin_class: searchParams.cabin_class,
          trip_type: searchParams.trip_type,
        }
        saveModifySearchPayload(payload)
        break
      }
        
      case 'hotels': {
        // Store full hotel destination object
        const city = searchParams.city || ''
        const payload: HotelSearchPayload = {
          service: 'hotels',
          destination: {
            type: 'city',
            id: `city_${city.toLowerCase().replace(/\s+/g, '_')}`,
            label: `${city}, India`,
            city: city,
            country: 'India',
          },
          check_in: searchParams.check_in || searchParams.departure_date || '',
          check_out: searchParams.check_out || '',
          adults: parseInt(searchParams.adults || '2'),
          rooms: searchParams.rooms ? parseInt(searchParams.rooms) : undefined,
        }
        saveModifySearchPayload(payload)
        break
      }
        
      case 'buses': {
        const payload: BusSearchPayload = {
          service: 'buses',
          origin: searchParams.origin_city || searchParams.origin || '',
          destination: searchParams.destination_city || searchParams.destination || '',
          departure_date: searchParams.departure_date || '',
          passengers: searchParams.passengers ? parseInt(searchParams.passengers) : 1,
          bus_type: searchParams.bus_type,
        }
        saveModifySearchPayload(payload)
        break
      }
        
      case 'trains': {
        const payload: TrainSearchPayload = {
          service: 'trains',
          origin: searchParams.origin_city || searchParams.origin || '',
          destination: searchParams.destination_city || searchParams.destination || '',
          origin_city: searchParams.origin_city,
          destination_city: searchParams.destination_city,
          departure_date: searchParams.departure_date || '',
          passengers: searchParams.passengers ? parseInt(searchParams.passengers) : 1,
          train_class: searchParams.train_class,
        }
        saveModifySearchPayload(payload)
        break
      }
    }
  }

  if (variant === 'compact') {
    return (
      <button
        onClick={handleModifySearch}
        className={`flex items-center gap-1.5 px-3 py-1.5 text-sm text-[#6B6B6B] hover:text-[#1A1A1A] hover:bg-[#F3EFEA] rounded-lg transition-colors ${className}`}
      >
        <Edit3 className="w-4 h-4" />
        Modify
      </button>
    )
  }

  return (
    <button
      onClick={handleModifySearch}
      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium text-[#6B6B6B] hover:text-[#1A1A1A] bg-white border border-[#E6E1D8] hover:border-[#C4C0B8] rounded-lg transition-colors ${className}`}
    >
      <Edit3 className="w-4 h-4" />
      Modify Search
    </button>
  )
}
