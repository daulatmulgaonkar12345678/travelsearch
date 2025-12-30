/**
 * Bus Autocomplete API Route
 * ==========================
 * 
 * Proxies to: /api/autocomplete/bus on FastAPI backend
 * 
 * PRODUCTION RULES:
 * - MUST use BACKEND_URL (no fallback)
 * - Returns 503 if backend unreachable
 * - Never returns static/mock data
 * 
 * DEVELOPMENT/PREVIEW:
 * - Falls back to static data if backend unreachable
 */

import { NextRequest, NextResponse } from 'next/server'
import { getBackendUrl, isFallbackAllowed } from '@/lib/env'

// Fallback data - ONLY used in development/preview
const FALLBACK_BUS_DATA = [
  { id: 'pune_swargate', name: 'Pune Swargate', state: 'Maharashtra', city: 'Pune', type: 'bus_stop', is_search_surface: true },
  { id: 'pune_shivaji', name: 'Pune Shivajinagar', state: 'Maharashtra', city: 'Pune', type: 'bus_stop', is_search_surface: true },
  { id: 'pune_station', name: 'Pune Station', state: 'Maharashtra', city: 'Pune', type: 'bus_stop', is_search_surface: true },
  { id: 'pune_city', name: 'Pune', state: 'Maharashtra', city: 'Pune', type: 'city', is_search_surface: true },
  { id: 'pune_university', name: 'Pune University', state: 'Maharashtra', city: 'Pune', type: 'bus_stop', is_search_surface: false },
  { id: 'nashik_pune_highway', name: 'Nashik Pune Highway', state: 'Maharashtra', city: 'Nashik', type: 'bus_stop', is_search_surface: false },
  { id: 'mumbai_dadar', name: 'Mumbai Dadar', state: 'Maharashtra', city: 'Mumbai', type: 'bus_stop', is_search_surface: true },
  { id: 'mumbai_borivali', name: 'Mumbai Borivali', state: 'Maharashtra', city: 'Mumbai', type: 'bus_stop', is_search_surface: true },
  { id: 'mumbai_city', name: 'Mumbai', state: 'Maharashtra', city: 'Mumbai', type: 'city', is_search_surface: true },
  { id: 'nashik', name: 'Nashik', state: 'Maharashtra', city: 'Nashik', type: 'city', is_search_surface: true },
  { id: 'nagpur', name: 'Nagpur', state: 'Maharashtra', city: 'Nagpur', type: 'city', is_search_surface: true },
  { id: 'kolhapur', name: 'Kolhapur', state: 'Maharashtra', city: 'Kolhapur', type: 'city', is_search_surface: true },
  { id: 'satara', name: 'Satara', state: 'Maharashtra', city: 'Satara', type: 'city', is_search_surface: true },
  { id: 'sangli', name: 'Sangli', state: 'Maharashtra', city: 'Sangli', type: 'city', is_search_surface: true },
  { id: 'solapur', name: 'Solapur', state: 'Maharashtra', city: 'Solapur', type: 'city', is_search_surface: true },
  { id: 'aurangabad', name: 'Aurangabad', state: 'Maharashtra', city: 'Aurangabad', type: 'city', is_search_surface: true },
  { id: 'latur', name: 'Latur', state: 'Maharashtra', city: 'Latur', type: 'city', is_search_surface: true },
  { id: 'latur_stand', name: 'Latur Bus Stand', state: 'Maharashtra', city: 'Latur', type: 'bus_stop', is_search_surface: true },
  { id: 'beed_stand', name: 'Beed Bus Stand', state: 'Maharashtra', city: 'Beed', type: 'bus_stop', is_search_surface: true },
  { id: 'beed_city', name: 'Beed', state: 'Maharashtra', city: 'Beed', type: 'city', is_search_surface: true },
  { id: 'dusrbeed', name: 'Dusrbeed', state: 'Maharashtra', city: 'Buldhana', type: 'bus_stop', is_search_surface: false },
  { id: 'osmanabad_stand', name: 'Osmanabad Bus Stand', state: 'Maharashtra', city: 'Osmanabad', type: 'bus_stop', is_search_surface: true },
  { id: 'osmanabad_city', name: 'Osmanabad', state: 'Maharashtra', city: 'Osmanabad', type: 'city', is_search_surface: true },
  { id: 'osmanabad_road', name: 'Osmanabad Road', state: 'Maharashtra', city: 'Osmanabad', type: 'bus_stop', is_search_surface: false },
]

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q') || ''
  const limit = parseInt(searchParams.get('limit') || '15', 10)

  if (!q || q.length < 2) {
    return NextResponse.json({ query: q, mode: 'bus', count: 0, results: [] })
  }

  let backendUrl: string
  try {
    backendUrl = getBackendUrl()
  } catch (error) {
    // Production without BACKEND_URL - fail fast
    return NextResponse.json(
      { error: 'Service configuration error', results: [] },
      { status: 503 }
    )
  }

  try {
    const url = `${backendUrl}/api/autocomplete/bus?q=${encodeURIComponent(q)}&mode=bus&limit=${limit}`
    
    const response = await fetch(url, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(5000),
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)

  } catch (error) {
    // In production: return 503, no fallback
    if (!isFallbackAllowed()) {
      return NextResponse.json(
        { query: q, mode: 'bus', count: 0, results: [], error: 'Backend unavailable' },
        { status: 503 }
      )
    }

    // Development/preview: use fallback data
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
        is_search_surface: item.is_search_surface,
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
