/**
 * Bus Autocomplete API Route
 * 
 * Proxies to: /api/autocomplete/bus on FastAPI backend
 * Provides fallback if backend unavailable
 * 
 * This route exists for backwards compatibility with existing frontend code
 * that calls /api/autocomplete/bus directly.
 */

import { NextRequest, NextResponse } from 'next/server'

// Maharashtra cities fallback
const FALLBACK_BUS_DATA = [
  { id: 'pune_swargate', name: 'Pune Swargate', state: 'Maharashtra', city: 'Pune', type: 'bus_stop' },
  { id: 'pune_shivaji', name: 'Pune Shivajinagar', state: 'Maharashtra', city: 'Pune', type: 'bus_stop' },
  { id: 'mumbai_dadar', name: 'Mumbai Dadar', state: 'Maharashtra', city: 'Mumbai', type: 'bus_stop' },
  { id: 'mumbai_borivali', name: 'Mumbai Borivali', state: 'Maharashtra', city: 'Mumbai', type: 'bus_stop' },
  { id: 'nashik', name: 'Nashik', state: 'Maharashtra', city: 'Nashik', type: 'city' },
  { id: 'nagpur', name: 'Nagpur', state: 'Maharashtra', city: 'Nagpur', type: 'city' },
  { id: 'kolhapur', name: 'Kolhapur', state: 'Maharashtra', city: 'Kolhapur', type: 'city' },
  { id: 'satara', name: 'Satara', state: 'Maharashtra', city: 'Satara', type: 'city' },
  { id: 'sangli', name: 'Sangli', state: 'Maharashtra', city: 'Sangli', type: 'city' },
  { id: 'solapur', name: 'Solapur', state: 'Maharashtra', city: 'Solapur', type: 'city' },
  { id: 'aurangabad', name: 'Aurangabad', state: 'Maharashtra', city: 'Aurangabad', type: 'city' },
  { id: 'karad', name: 'Karad', state: 'Maharashtra', city: 'Satara', type: 'city' },
]

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
