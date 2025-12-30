/**
 * TravelSearch Theme System
 * =========================
 * 
 * CONTEXT-AWARE SERVICE THEMING
 * Each service has its own accent color that applies to:
 * - Tab backgrounds & icons
 * - Search bar focus border
 * - CTA buttons
 * - Filter pills
 * - Price highlights
 * - Card tints (subtle)
 * 
 * SERVICE ORDER (STRICT - DO NOT CHANGE):
 * 1. Flights
 * 2. Buses
 * 3. Trains
 * 4. Hotels
 */

export type ServiceType = 'flights' | 'buses' | 'trains' | 'hotels'

// Service order for tabs - MUST match everywhere
export const SERVICE_ORDER: ServiceType[] = ['flights', 'buses', 'trains', 'hotels']

// Global Base Colors (Eye-Friendly, Low-Blue)
export const BASE_COLORS = {
  pageBackground: '#FAF9F6',      // Warm off-white
  sectionBackground: '#F3EFEA',  // Soft beige
  cardBackground: '#FFFFFF',      // Pure white
  primaryText: '#2B2B2B',         // Dark gray
  secondaryText: '#6B6B6B',       // Medium gray
  borderColor: '#E6E1D8',         // Warm gray border
  shadow: 'rgba(0,0,0,0.04)',     // Subtle shadow
} as const

// Service Accent Colors (Muted, Earthy, Eye-Friendly)
export const SERVICE_COLORS = {
  flights: {
    accent: '#6B8F71',           // Soft sage green
    accentHover: '#5A7A60',
    accentLight: '#E8F0E9',      // Very light sage
    cardTint: 'rgba(107,143,113,0.06)',
    icon: '#6B8F71',
  },
  buses: {
    accent: '#C47A4A',           // Warm clay / muted orange
    accentHover: '#B06A3A',
    accentLight: '#F9EDE6',      // Very light clay
    cardTint: 'rgba(196,122,74,0.06)',
    icon: '#C47A4A',
  },
  trains: {
    accent: '#7A8B5C',           // Muted olive green
    accentHover: '#697A4C',
    accentLight: '#EEF1E8',      // Very light olive
    cardTint: 'rgba(122,139,92,0.06)',
    icon: '#7A8B5C',
  },
  hotels: {
    accent: '#C9A24D',           // Soft sand gold
    accentHover: '#B8923D',
    accentLight: '#F9F3E6',      // Very light gold
    cardTint: 'rgba(201,162,77,0.06)',
    icon: '#C9A24D',
  },
} as const

// Neutral colors for inactive states
export const NEUTRAL = {
  inactive: '#9CA3AF',           // Gray-400
  inactiveLight: '#F3F4F6',      // Gray-100
  inactiveHover: '#E5E7EB',      // Gray-200
}

/**
 * Get service theme configuration
 */
export function getServiceTheme(service: ServiceType) {
  return SERVICE_COLORS[service]
}

/**
 * Get CSS classes for service-themed elements
 */
export function getServiceClasses(service: ServiceType, variant: 'button' | 'tab' | 'badge' | 'card') {
  const theme = SERVICE_COLORS[service]
  
  switch (variant) {
    case 'button':
      return {
        primary: `bg-[${theme.accent}] hover:bg-[${theme.accentHover}] text-white`,
        secondary: `border border-[${theme.accent}] text-[${theme.accent}] hover:bg-[${theme.accentLight}]`,
      }
    case 'tab':
      return {
        active: `bg-[${theme.accentLight}] text-[${theme.accent}]`,
        inactive: `text-gray-600 hover:text-[${theme.accent}] hover:bg-[${theme.accentLight}]`,
      }
    case 'badge':
      return `bg-[${theme.accentLight}] text-[${theme.accent}]`
    case 'card':
      return `bg-[${theme.cardTint}]`
    default:
      return ''
  }
}

/**
 * Service display names and icons
 */
export const SERVICE_META = {
  flights: { label: 'Flights', iconName: 'Plane' },
  buses: { label: 'Buses', iconName: 'Bus' },
  trains: { label: 'Trains', iconName: 'Train' },
  hotels: { label: 'Hotels', iconName: 'Hotel' },
} as const
