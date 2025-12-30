/**
 * Bus Autocomplete API Route
 * 
 * Proxies to: /api/autocomplete/bus on FastAPI backend
 * Provides fallback if backend unavailable
 * 
 * IMPORTANT: Set BACKEND_URL environment variable in Vercel:
 * BACKEND_URL=https://travelsearch-backend.onrender.com
 * 
 * This route exists for backwards compatibility with existing frontend code
 * that calls /api/autocomplete/bus directly.
 */

import { NextRequest, NextResponse } from 'next/server'

// Extended Maharashtra cities fallback (used when backend is unavailable)
// NOTE: This is a limited fallback. For full results, ensure BACKEND_URL is configured.
const FALLBACK_BUS_DATA = [
  // Major cities
  { id: 'pune_swargate', name: 'Pune Swargate', state: 'Maharashtra', city: 'Pune', type: 'bus_stop', is_search_surface: true },
  { id: 'pune_shivaji', name: 'Pune Shivajinagar', state: 'Maharashtra', city: 'Pune', type: 'bus_stop', is_search_surface: true },
  { id: 'pune_station', name: 'Pune Station', state: 'Maharashtra', city: 'Pune', type: 'bus_stop', is_search_surface: true },
  { id: 'pune_city', name: 'Pune', state: 'Maharashtra', city: 'Pune', type: 'city', is_search_surface: true },
  { id: 'pune_university', name: 'Pune University', state: 'Maharashtra', city: 'Pune', type: 'bus_stop', is_search_surface: false },
  { id: 'mumbai_dadar', name: 'Mumbai Dadar', state: 'Maharashtra', city: 'Mumbai', type: 'bus_stop', is_search_surface: true },
  { id: 'mumbai_borivali', name: 'Mumbai Borivali', state: 'Maharashtra', city: 'Mumbai', type: 'bus_stop', is_search_surface: true },
  { id: 'mumbai_city', name: 'Mumbai', state: 'Maharashtra', city: 'Mumbai', type: 'city', is_search_surface: true },
  // District cities
  { id: 'nashik', name: 'Nashik', state: 'Maharashtra', city: 'Nashik', type: 'city', is_search_surface: true },
  { id: 'nagpur', name: 'Nagpur', state: 'Maharashtra', city: 'Nagpur', type: 'city', is_search_surface: true },
  { id: 'kolhapur', name: 'Kolhapur', state: 'Maharashtra', city: 'Kolhapur', type: 'city', is_search_surface: true },
  { id: 'satara', name: 'Satara', state: 'Maharashtra', city: 'Satara', type: 'city', is_search_surface: true },
  { id: 'sangli', name: 'Sangli', state: 'Maharashtra', city: 'Sangli', type: 'city', is_search_surface: true },
  { id: 'solapur', name: 'Solapur', state: 'Maharashtra', city: 'Solapur', type: 'city', is_search_surface: true },
  { id: 'aurangabad', name: 'Aurangabad', state: 'Maharashtra', city: 'Aurangabad', type: 'city', is_search_surface: true },
  { id: 'karad', name: 'Karad', state: 'Maharashtra', city: 'Satara', type: 'city', is_search_surface: true },
  // Beed district
  { id: 'beed_stand', name: 'Beed Bus Stand', state: 'Maharashtra', city: 'Beed', type: 'bus_stop', is_search_surface: true },
  { id: 'beed_city', name: 'Beed', state: 'Maharashtra', city: 'Beed', type: 'city', is_search_surface: true },
  { id: 'dusrbeed', name: 'Dusrbeed', state: 'Maharashtra', city: 'Buldhana', type: 'bus_stop', is_search_surface: false },
  // Osmanabad district
  { id: 'osmanabad_stand', name: 'Osmanabad Bus Stand', state: 'Maharashtra', city: 'Osmanabad', type: 'bus_stop', is_search_surface: true },
  { id: 'osmanabad_city', name: 'Osmanabad', state: 'Maharashtra', city: 'Osmanabad', type: 'city', is_search_surface: true },
  { id: 'osmanabad_road', name: 'Osmanabad Road', state: 'Maharashtra', city: 'Osmanabad', type: 'bus_stop', is_search_surface: false },
]

// Backend URL - MUST be set in Vercel environment variables for production
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q') || ''
  const limit = parseInt(searchParams.get('limit') || '15', 10)

  if (!q || q.length < 2) {
    return NextResponse.json({ query: q, mode: 'bus', count: 0, results: [] })
  }

  try {
    // Proxy to FastAPI backend
    const backendUrl = `${BACKEND_URL}/api/autocomplete/bus?q=${encodeURIComponent(q)}&mode=bus&limit=${limit}`
    
    const response = await fetch(backendUrl, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(5000),
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Bus autocomplete proxy error:', error)
    
    // Return fallback filtered results
    const queryLower = q.toLowerCase()
    const filtered = FALLBACK_BUS_DATA
      .filter(item => 
        item.name.toLowerCase().includes(queryLower) ||
        item.city.toLowerCase().includes(queryLower)
      )
      .slice(0, limit)
      .map(item => ({
        id: item.id,
        type: item.type,
        label: item.name,
        label_en: item.name,
        city: item.city,
        state: item.state,
        cityName: item.city,
        cityId: item.id,
        is_search_surface: true,
      }))

    return NextResponse.json({
      query: q,
      mode: 'bus',
      count: filtered.length,
      results: filtered,
      source: 'fallback',
    })
  }
}
