/**
 * Unified Autocomplete API Route
 * 
 * Proxies autocomplete requests to the FastAPI backend.
 * Provides fallback data if backend is unavailable.
 * 
 * Supports:
 * - Bus autocomplete: ?q=pune&mode=bus
 * - Train autocomplete: ?q=pune&mode=train
 * - Hotel autocomplete: ?q=mumbai&mode=hotel
 * 
 * Response format (consistent across modes):
 * [
 *   { id: "PNQ", name: "Pune", state: "MH", country: "IN", type: "city" }
 * ]
 */

import { NextRequest, NextResponse } from 'next/server'

// Fallback data for when backend is unavailable
const FALLBACK_DATA = {
  bus: [
    { id: 'pune', name: 'Pune', state: 'Maharashtra', country: 'IN', type: 'city' },
    { id: 'mumbai', name: 'Mumbai', state: 'Maharashtra', country: 'IN', type: 'city' },
    { id: 'nagpur', name: 'Nagpur', state: 'Maharashtra', country: 'IN', type: 'city' },
    { id: 'nashik', name: 'Nashik', state: 'Maharashtra', country: 'IN', type: 'city' },
    { id: 'kolhapur', name: 'Kolhapur', state: 'Maharashtra', country: 'IN', type: 'city' },
    { id: 'satara', name: 'Satara', state: 'Maharashtra', country: 'IN', type: 'city' },
    { id: 'aurangabad', name: 'Aurangabad', state: 'Maharashtra', country: 'IN', type: 'city' },
    { id: 'solapur', name: 'Solapur', state: 'Maharashtra', country: 'IN', type: 'city' },
  ],
  train: [
    { id: 'PUNE_ALL', name: 'Pune (All Stations)', state: 'Maharashtra', country: 'IN', type: 'city_all' },
    { id: 'MUMBAI_ALL', name: 'Mumbai (All Stations)', state: 'Maharashtra', country: 'IN', type: 'city_all' },
    { id: 'DELHI_ALL', name: 'Delhi (All Stations)', state: 'Delhi', country: 'IN', type: 'city_all' },
    { id: 'CHENNAI_ALL', name: 'Chennai (All Stations)', state: 'Tamil Nadu', country: 'IN', type: 'city_all' },
    { id: 'BENGALURU_ALL', name: 'Bengaluru (All Stations)', state: 'Karnataka', country: 'IN', type: 'city_all' },
    { id: 'KOLKATA_ALL', name: 'Kolkata (All Stations)', state: 'West Bengal', country: 'IN', type: 'city_all' },
    { id: 'HYDERABAD_ALL', name: 'Hyderabad (All Stations)', state: 'Telangana', country: 'IN', type: 'city_all' },
    { id: 'JAIPUR_ALL', name: 'Jaipur (All Stations)', state: 'Rajasthan', country: 'IN', type: 'city_all' },
  ],
  hotel: [
    { id: 'mumbai', name: 'Mumbai', state: 'Maharashtra', country: 'IN', type: 'city' },
    { id: 'delhi', name: 'Delhi', state: 'Delhi', country: 'IN', type: 'city' },
    { id: 'goa', name: 'Goa', state: 'Goa', country: 'IN', type: 'city' },
    { id: 'bengaluru', name: 'Bengaluru', state: 'Karnataka', country: 'IN', type: 'city' },
    { id: 'jaipur', name: 'Jaipur', state: 'Rajasthan', country: 'IN', type: 'city' },
    { id: 'chennai', name: 'Chennai', state: 'Tamil Nadu', country: 'IN', type: 'city' },
  ],
}

// Backend URL - use environment variable or default to localhost
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q') || ''
  const mode = searchParams.get('mode') as 'bus' | 'train' | 'hotel' | null
  const limit = parseInt(searchParams.get('limit') || '15', 10)

  // Validate inputs
  if (!q || q.length < 2) {
    return NextResponse.json([])
  }

  if (!mode || !['bus', 'train', 'hotel'].includes(mode)) {
    return NextResponse.json([])
  }

  try {
    // Determine backend endpoint based on mode
    let backendUrl: string
    if (mode === 'bus') {
      backendUrl = `${BACKEND_URL}/api/autocomplete/bus?q=${encodeURIComponent(q)}&mode=bus&limit=${limit}`
    } else if (mode === 'train') {
      backendUrl = `${BACKEND_URL}/api/trains/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`
    } else {
      backendUrl = `${BACKEND_URL}/api/hotels/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`
    }

    const response = await fetch(backendUrl, {
      headers: {
        'Accept': 'application/json',
      },
      // Short timeout to fail fast
      signal: AbortSignal.timeout(5000),
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()
    
    // Transform response to consistent format based on mode
    let results: any[]
    
    if (mode === 'bus') {
      // Bus backend returns { results: [...] }
      results = (data.results || []).map((r: any) => ({
        id: r.id,
        name: r.label_en || r.label || r.city,
        name_local: r.label || r.city_local,
        state: r.state || 'Maharashtra',
        country: 'IN',
        type: r.type || 'bus_stop',
        cityName: r.cityName || r.city,
        cityId: r.cityId || r.id,
        operator: r.operator,
        is_search_surface: r.is_search_surface,
      }))
    } else if (mode === 'train') {
      // Train backend returns { results: [...] }
      results = (data.results || []).map((r: any) => ({
        id: r.value,
        name: r.label,
        state: r.city ? 'India' : '',
        country: 'IN',
        type: r.type,
        city: r.city,
        is_major: r.is_major,
        station_count: r.station_count,
        is_recommended: r.is_recommended,
      }))
    } else {
      // Hotel backend returns array directly or { results: [...] }
      const hotelsArray = Array.isArray(data) ? data : (data.results || [])
      results = hotelsArray.map((r: any) => ({
        id: r.city || r.id,
        name: r.city || r.name,
        state: r.country || 'India',
        country: 'IN',
        type: 'city',
      }))
    }

    return NextResponse.json(results.slice(0, limit))
  } catch (error) {
    console.error(`Autocomplete API error (${mode}):`, error)
    
    // Return filtered fallback data
    const fallbackList = FALLBACK_DATA[mode] || []
    const queryLower = q.toLowerCase()
    const filtered = fallbackList
      .filter(item => item.name.toLowerCase().includes(queryLower))
      .slice(0, limit)
    
    return NextResponse.json(filtered)
  }
}
