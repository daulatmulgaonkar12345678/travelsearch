/**
 * Train Autocomplete API Route
 * ============================
 * 
 * Proxies to: /api/trains/autocomplete on FastAPI backend
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
const FALLBACK_TRAIN_DATA = [
  { value: 'DELHI_ALL', label: 'Delhi (All Stations)', type: 'city_all', city: 'Delhi', station_count: 6, is_recommended: true },
  { value: 'MUMBAI_ALL', label: 'Mumbai (All Stations)', type: 'city_all', city: 'Mumbai', station_count: 9, is_recommended: true },
  { value: 'KOLKATA_ALL', label: 'Kolkata (All Stations)', type: 'city_all', city: 'Kolkata', station_count: 6, is_recommended: true },
  { value: 'CHENNAI_ALL', label: 'Chennai (All Stations)', type: 'city_all', city: 'Chennai', station_count: 6, is_recommended: true },
  { value: 'BENGALURU_ALL', label: 'Bengaluru (All Stations)', type: 'city_all', city: 'Bengaluru', station_count: 6, is_recommended: true },
  { value: 'HYDERABAD_ALL', label: 'Hyderabad (All Stations)', type: 'city_all', city: 'Hyderabad', station_count: 4, is_recommended: true },
  { value: 'PUNE_ALL', label: 'Pune (All Stations)', type: 'city_all', city: 'Pune', station_count: 5, is_recommended: true },
  { value: 'AHMEDABAD_ALL', label: 'Ahmedabad (All Stations)', type: 'city_all', city: 'Ahmedabad', station_count: 4, is_recommended: true },
  { value: 'JAIPUR_ALL', label: 'Jaipur (All Stations)', type: 'city_all', city: 'Jaipur', station_count: 3, is_recommended: true },
  { value: 'LUCKNOW_ALL', label: 'Lucknow (All Stations)', type: 'city_all', city: 'Lucknow', station_count: 4, is_recommended: true },
  { value: 'NAGPUR_ALL', label: 'Nagpur (All Stations)', type: 'city_all', city: 'Nagpur', station_count: 2, is_recommended: true },
  { value: 'LATUR_ALL', label: 'Latur (All Stations)', type: 'city_all', city: 'Latur', station_count: 2, is_recommended: true },
  { value: 'NDLS', label: 'NDLS – New Delhi', type: 'station', city: 'Delhi', is_major: true },
  { value: 'DLI', label: 'DLI – Old Delhi Junction', type: 'station', city: 'Delhi', is_major: true },
  { value: 'NZM', label: 'NZM – Hazrat Nizamuddin', type: 'station', city: 'Delhi', is_major: true },
  { value: 'CSMT', label: 'CSMT – Chhatrapati Shivaji Maharaj Terminus', type: 'station', city: 'Mumbai', is_major: true },
  { value: 'BCT', label: 'BCT – Mumbai Central', type: 'station', city: 'Mumbai', is_major: true },
  { value: 'LTT', label: 'LTT – Lokmanya Tilak Terminus', type: 'station', city: 'Mumbai', is_major: true },
  { value: 'HWH', label: 'HWH – Howrah Junction', type: 'station', city: 'Kolkata', is_major: true },
  { value: 'SDAH', label: 'SDAH – Sealdah', type: 'station', city: 'Kolkata', is_major: true },
  { value: 'MAS', label: 'MAS – Chennai Central', type: 'station', city: 'Chennai', is_major: true },
  { value: 'SBC', label: 'SBC – KSR Bangalore City Junction', type: 'station', city: 'Bengaluru', is_major: true },
  { value: 'SC', label: 'SC – Secunderabad Junction', type: 'station', city: 'Hyderabad', is_major: true },
  { value: 'PUNE', label: 'PUNE – Pune Junction', type: 'station', city: 'Pune', is_major: true },
  { value: 'NGP', label: 'NGP – Nagpur Junction', type: 'station', city: 'Nagpur', is_major: true },
  { value: 'LUR', label: 'LUR – Latur', type: 'station', city: 'Latur', is_major: true },
]

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q') || ''
  const limit = parseInt(searchParams.get('limit') || '10', 10)

  if (!q || q.length < 1) {
    return NextResponse.json({ results: [], query: q, total: 0 })
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
    const url = `${backendUrl}/api/trains/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`
    
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
        { query: q, results: [], total: 0, error: 'Backend unavailable' },
        { status: 503 }
      )
    }

    // Development/preview: use fallback data
    const queryLower = q.toLowerCase()
    const filtered = FALLBACK_TRAIN_DATA
      .filter(item => 
        item.label.toLowerCase().includes(queryLower) ||
        item.city.toLowerCase().includes(queryLower) ||
        item.value.toLowerCase().includes(queryLower)
      )
      .sort((a, b) => {
        if (a.type === 'city_all' && b.type !== 'city_all') return -1
        if (a.type !== 'city_all' && b.type === 'city_all') return 1
        if (a.is_major && !b.is_major) return -1
        if (!a.is_major && b.is_major) return 1
        return 0
      })
      .slice(0, limit)

    return NextResponse.json({
      results: filtered,
      query: q,
      total: filtered.length,
      source: 'fallback',
    })
  }
}
