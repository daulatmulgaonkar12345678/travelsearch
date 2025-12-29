/**
 * Train Autocomplete API Route
 * 
 * Proxies to: /api/trains/autocomplete on FastAPI backend
 * Provides fallback if backend unavailable
 * 
 * Returns station-first format with _ALL tokens for city-wide search.
 */

import { NextRequest, NextResponse } from 'next/server'

// Fallback train stations/cities
const FALLBACK_TRAIN_DATA = [
  { value: 'PUNE_ALL', label: 'Pune (All Stations)', type: 'city_all', city: 'Pune', is_recommended: true },
  { value: 'MUMBAI_ALL', label: 'Mumbai (All Stations)', type: 'city_all', city: 'Mumbai', is_recommended: true },
  { value: 'DELHI_ALL', label: 'Delhi (All Stations)', type: 'city_all', city: 'Delhi', is_recommended: true },
  { value: 'CHENNAI_ALL', label: 'Chennai (All Stations)', type: 'city_all', city: 'Chennai', is_recommended: true },
  { value: 'BENGALURU_ALL', label: 'Bengaluru (All Stations)', type: 'city_all', city: 'Bengaluru', is_recommended: true },
  { value: 'KOLKATA_ALL', label: 'Kolkata (All Stations)', type: 'city_all', city: 'Kolkata', is_recommended: true },
  { value: 'HYDERABAD_ALL', label: 'Hyderabad (All Stations)', type: 'city_all', city: 'Hyderabad', is_recommended: true },
  { value: 'JAIPUR_ALL', label: 'Jaipur (All Stations)', type: 'city_all', city: 'Jaipur', is_recommended: true },
  { value: 'AHMEDABAD_ALL', label: 'Ahmedabad (All Stations)', type: 'city_all', city: 'Ahmedabad', is_recommended: true },
  { value: 'LUCKNOW_ALL', label: 'Lucknow (All Stations)', type: 'city_all', city: 'Lucknow', is_recommended: true },
  { value: 'NAGPUR_ALL', label: 'Nagpur (All Stations)', type: 'city_all', city: 'Nagpur', is_recommended: true },
  { value: 'VARANASI_ALL', label: 'Varanasi (All Stations)', type: 'city_all', city: 'Varanasi', is_recommended: true },
]

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q') || ''
  const limit = parseInt(searchParams.get('limit') || '10', 10)

  if (!q || q.length < 2) {
    return NextResponse.json({ results: [], query: q, total: 0 })
  }

  try {
    // Proxy to FastAPI backend
    const backendUrl = `${BACKEND_URL}/api/trains/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`
    
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
    console.error('Train autocomplete proxy error:', error)
    
    // Return fallback filtered results
    const queryLower = q.toLowerCase()
    const filtered = FALLBACK_TRAIN_DATA
      .filter(item => 
        item.label.toLowerCase().includes(queryLower) ||
        item.city.toLowerCase().includes(queryLower)
      )
      .slice(0, limit)

    return NextResponse.json({
      results: filtered,
      query: q,
      total: filtered.length,
      source: 'fallback',
    })
  }
}
