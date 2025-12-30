'use client'

import { Edit3 } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface ModifySearchButtonProps {
  service: 'flights' | 'hotels' | 'buses' | 'trains'
  searchParams: {
    // Common
    departure_date?: string
    // Flights
    origin?: string
    destination?: string
    return_date?: string
    adults?: string
    children?: string
    infants?: string
    // Hotels
    city?: string
    check_in?: string
    check_out?: string
    hotel_name?: string
    // Buses/Trains
    origin_city?: string
    destination_city?: string
  }
  variant?: 'default' | 'compact'
  className?: string
}

/**
 * ModifySearch Button - Opens search form with pre-filled values
 * Used on both results and vendor comparison pages
 */
export default function ModifySearchButton({
  service,
  searchParams,
  variant = 'default',
  className = '',
}: ModifySearchButtonProps) {
  const router = useRouter()

  const handleModifySearch = () => {
    // Build query params for search page
    const params = new URLSearchParams()
    
    switch (service) {
      case 'flights':
        if (searchParams.origin) params.set('origin', searchParams.origin)
        if (searchParams.destination) params.set('destination', searchParams.destination)
        if (searchParams.departure_date) params.set('departure_date', searchParams.departure_date)
        if (searchParams.return_date) params.set('return_date', searchParams.return_date)
        if (searchParams.adults) params.set('adults', searchParams.adults)
        if (searchParams.children) params.set('children', searchParams.children)
        if (searchParams.infants) params.set('infants', searchParams.infants)
        router.push(`/?tab=flights&modify=true&${params.toString()}`)
        break
        
      case 'hotels':
        if (searchParams.city) params.set('city', searchParams.city)
        if (searchParams.check_in) params.set('check_in', searchParams.check_in)
        if (searchParams.check_out) params.set('check_out', searchParams.check_out)
        if (searchParams.adults) params.set('adults', searchParams.adults)
        router.push(`/?tab=hotels&modify=true&${params.toString()}`)
        break
        
      case 'buses':
        if (searchParams.origin_city || searchParams.origin) {
          params.set('origin', searchParams.origin_city || searchParams.origin || '')
        }
        if (searchParams.destination_city || searchParams.destination) {
          params.set('destination', searchParams.destination_city || searchParams.destination || '')
        }
        if (searchParams.departure_date) params.set('departure_date', searchParams.departure_date)
        router.push(`/?tab=buses&modify=true&${params.toString()}`)
        break
        
      case 'trains':
        if (searchParams.origin_city || searchParams.origin) {
          params.set('origin', searchParams.origin_city || searchParams.origin || '')
        }
        if (searchParams.destination_city || searchParams.destination) {
          params.set('destination', searchParams.destination_city || searchParams.destination || '')
        }
        if (searchParams.departure_date) params.set('departure_date', searchParams.departure_date)
        router.push(`/?tab=trains&modify=true&${params.toString()}`)
        break
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
