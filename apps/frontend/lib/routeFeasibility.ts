/**
 * Route Feasibility Checker
 * 
 * Determines if surface transport (train/bus) is logically possible between two airports.
 * Uses simple country/region logic - NO API calls.
 * 
 * Rules:
 * - Same country (India) → Train/Bus possible
 * - Both in Indian subcontinent → Maybe train (limited)
 * - International → Train/Bus NOT possible
 */

// Indian airport codes (3-letter IATA)
// This is a comprehensive list of Indian airports
const INDIAN_AIRPORTS = new Set([
  // Major metros
  'DEL', 'BOM', 'BLR', 'MAA', 'CCU', 'HYD',
  // Tier-1 cities
  'AMD', 'COK', 'GOI', 'PNQ', 'JAI', 'LKO', 'PAT', 'GAU', 'IXC', 'SXR',
  'TRV', 'IXE', 'VNS', 'IDR', 'BHO', 'NAG', 'RPR', 'VTZ', 'IXB', 'IMF',
  'CCJ', 'CJB', 'IXR', 'IXA', 'GAY', 'JLR', 'BBI', 'IXJ', 'IXU', 'UDR',
  // Regional airports
  'ATQ', 'BDQ', 'DIB', 'DED', 'DHM', 'HBX', 'JDH', 'JSA', 'KLH', 'KNU',
  'KUU', 'IXL', 'IXM', 'IXS', 'IXZ', 'PBD', 'PGH', 'PYB', 'RAJ', 'SAG',
  'STV', 'TEZ', 'TIR', 'TRZ', 'AGR', 'AJL', 'BEK', 'BEP', 'BHJ', 'BHU',
  'CBD', 'CDP', 'CNN', 'DIU', 'GBI', 'GOP', 'GUX', 'GWL', 'HJR', 'HRI',
  'HSS', 'ISK', 'IXD', 'IXG', 'IXH', 'IXI', 'IXK', 'IXN', 'IXP', 'IXQ',
  'IXT', 'IXV', 'IXW', 'IXY', 'JGB', 'JRH', 'KJB', 'KQH', 'KTU', 'LDA',
  'LUH', 'MYQ', 'NMB', 'OMN', 'PNY', 'PYG', 'PUT', 'RDP', 'REW', 'RJA',
  'RRK', 'RTC', 'RUP', 'SHL', 'SLV', 'SSE', 'TCR', 'TEI', 'TNI', 'VGA',
  'VDY', 'ZER', 'AIP', 'AGX', 'AYJ', 'BUP', 'DBD', 'DMU', 'GOP', 'HGI',
  'JGA', 'JSG', 'KBK', 'MZA', 'NDC', 'NVY', 'PAB', 'PBH', 'PCW', 'PGT',
  'PXO', 'RGH', 'SAG', 'TEQ', 'VNS', 'ZWR',
])

// Neighboring countries with LIMITED rail connectivity to India
// (Only for very specific border routes)
const NEIGHBOR_COUNTRIES_LIMITED_RAIL: Record<string, string[]> = {
  // Pakistan airports - rail only for Samjhauta Express (limited)
  'PK': ['LHE', 'KHI', 'ISB', 'UET', 'MUX', 'PEW'],
  // Bangladesh airports - rail via Maitree Express
  'BD': ['DAC', 'CGP', 'ZYL', 'RJH', 'SPD', 'JSR'],
  // Nepal airports - bus possible to border
  'NP': ['KTM', 'PKR', 'BIR', 'BWA'],
}

// Major international hub airports for suggesting alternatives
export const INTERNATIONAL_HUBS = {
  'IN': [
    { code: 'DEL', name: 'Delhi', fullName: 'Indira Gandhi International' },
    { code: 'BOM', name: 'Mumbai', fullName: 'Chhatrapati Shivaji Maharaj' },
    { code: 'BLR', name: 'Bangalore', fullName: 'Kempegowda International' },
    { code: 'MAA', name: 'Chennai', fullName: 'Chennai International' },
    { code: 'CCU', name: 'Kolkata', fullName: 'Netaji Subhas Chandra Bose' },
    { code: 'HYD', name: 'Hyderabad', fullName: 'Rajiv Gandhi International' },
  ],
}

export type RouteFeasibility = {
  isSameCountry: boolean
  isIndia: boolean
  isSurfaceTransportPossible: boolean
  surfaceTransportNote: string | null
  routeType: 'domestic' | 'regional' | 'international'
  suggestedHubs: Array<{ code: string; name: string; fullName: string }>
}

/**
 * Check if an airport code is Indian
 */
export function isIndianAirport(code: string): boolean {
  return INDIAN_AIRPORTS.has(code.toUpperCase())
}

/**
 * Check if an airport is in a neighboring country with limited rail/bus
 */
function getNeighborCountry(code: string): string | null {
  const upperCode = code.toUpperCase()
  for (const [country, airports] of Object.entries(NEIGHBOR_COUNTRIES_LIMITED_RAIL)) {
    if (airports.includes(upperCode)) {
      return country
    }
  }
  return null
}

/**
 * Analyze route feasibility for surface transport
 * 
 * @param origin - Origin airport IATA code
 * @param destination - Destination airport IATA code
 * @returns RouteFeasibility object with details
 */
export function analyzeRouteFeasibility(origin: string, destination: string): RouteFeasibility {
  const originUpper = origin.toUpperCase()
  const destUpper = destination.toUpperCase()
  
  const originIsIndia = isIndianAirport(originUpper)
  const destIsIndia = isIndianAirport(destUpper)
  
  // Case 1: Both airports in India → Domestic, surface transport possible
  if (originIsIndia && destIsIndia) {
    return {
      isSameCountry: true,
      isIndia: true,
      isSurfaceTransportPossible: true,
      surfaceTransportNote: 'Trains and buses operate on this route.',
      routeType: 'domestic',
      suggestedHubs: [],
    }
  }
  
  // Case 2: One in India, one in neighboring country → Regional, limited surface
  const originNeighbor = getNeighborCountry(originUpper)
  const destNeighbor = getNeighborCountry(destUpper)
  
  if ((originIsIndia && destNeighbor) || (destIsIndia && originNeighbor)) {
    // Very limited cross-border rail/bus exists
    let note = null
    if (destNeighbor === 'NP' || originNeighbor === 'NP') {
      note = 'Bus services to Nepal border available. Onward travel required.'
    } else if (destNeighbor === 'BD' || originNeighbor === 'BD') {
      note = 'Limited rail service (Maitree Express) available on select routes.'
    }
    
    return {
      isSameCountry: false,
      isIndia: originIsIndia || destIsIndia,
      isSurfaceTransportPossible: false, // Not practical for most routes
      surfaceTransportNote: note,
      routeType: 'regional',
      suggestedHubs: originIsIndia 
        ? INTERNATIONAL_HUBS['IN'].filter(h => h.code !== originUpper)
        : INTERNATIONAL_HUBS['IN'].filter(h => h.code !== destUpper),
    }
  }
  
  // Case 3: International route → Surface transport NOT possible
  return {
    isSameCountry: false,
    isIndia: originIsIndia || destIsIndia,
    isSurfaceTransportPossible: false,
    surfaceTransportNote: null,
    routeType: 'international',
    suggestedHubs: originIsIndia 
      ? INTERNATIONAL_HUBS['IN'].filter(h => h.code !== originUpper).slice(0, 3)
      : destIsIndia 
        ? INTERNATIONAL_HUBS['IN'].filter(h => h.code !== destUpper).slice(0, 3)
        : INTERNATIONAL_HUBS['IN'].slice(0, 3),
  }
}

/**
 * Get a user-friendly description of the route type
 */
export function getRouteTypeDescription(routeType: 'domestic' | 'regional' | 'international'): string {
  switch (routeType) {
    case 'domestic':
      return 'This is a domestic route within India.'
    case 'regional':
      return 'This is a regional route between neighboring countries.'
    case 'international':
      return 'This is an international long-haul route.'
  }
}
