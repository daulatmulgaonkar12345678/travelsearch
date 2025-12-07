/**
 * Vendor Configuration
 * 
 * Centralized configuration for travel booking vendors/OTAs.
 * Currently only Aviasales is integrated via Travelpayouts affiliate.
 */

export interface Vendor {
  id: string
  name: string
  type: 'real' | 'coming_soon'
  logo?: string
  description?: string
}

export const FLIGHT_VENDORS: Vendor[] = [
  {
    id: 'aviasales',
    name: 'Aviasales',
    type: 'real',
    description: 'Global flight search engine with competitive prices',
  },
  {
    id: 'makemytrip',
    name: 'MakeMyTrip',
    type: 'coming_soon',
    description: 'India\'s leading travel booking platform',
  },
  {
    id: 'paytm',
    name: 'Paytm Travel',
    type: 'coming_soon',
    description: 'Popular payment platform with travel services',
  },
]

export const HOTEL_VENDORS: Vendor[] = [
  {
    id: 'aviasales',
    name: 'Aviasales Hotels',
    type: 'real',
    description: 'Book hotels with Aviasales',
  },
  {
    id: 'booking',
    name: 'Booking.com',
    type: 'coming_soon',
    description: 'World\'s largest hotel booking platform',
  },
  {
    id: 'agoda',
    name: 'Agoda',
    type: 'coming_soon',
    description: 'Asia-focused hotel booking with great deals',
  },
]

/**
 * Get active (real) vendors only
 */
export function getActiveVendors(type: 'flight' | 'hotel'): Vendor[] {
  const vendors = type === 'flight' ? FLIGHT_VENDORS : HOTEL_VENDORS
  return vendors.filter(v => v.type === 'real')
}

/**
 * Check if a vendor is available
 */
export function isVendorAvailable(vendorId: string, type: 'flight' | 'hotel'): boolean {
  const vendors = type === 'flight' ? FLIGHT_VENDORS : HOTEL_VENDORS
  const vendor = vendors.find(v => v.id === vendorId)
  return vendor?.type === 'real'
}
