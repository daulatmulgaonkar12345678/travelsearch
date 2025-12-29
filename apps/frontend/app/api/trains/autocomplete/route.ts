/**
 * Train Autocomplete API Route
 * 
 * Proxies to: /api/trains/autocomplete on FastAPI backend
 * Provides fallback if backend unavailable
 * 
 * Returns station-first format with _ALL tokens for city-wide search.
 */

import { NextRequest, NextResponse } from 'next/server'

// Comprehensive fallback train stations/cities for major Indian cities
const FALLBACK_TRAIN_DATA = [
  // Multi-station cities with _ALL tokens
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
  { value: 'VARANASI_ALL', label: 'Varanasi (All Stations)', type: 'city_all', city: 'Varanasi', station_count: 3, is_recommended: true },
  
  // Major individual stations
  { value: 'NDLS', label: 'NDLS – New Delhi', type: 'station', city: 'Delhi', is_major: true },
  { value: 'DLI', label: 'DLI – Old Delhi Junction', type: 'station', city: 'Delhi', is_major: true },
  { value: 'NZM', label: 'NZM – Hazrat Nizamuddin', type: 'station', city: 'Delhi', is_major: true },
  { value: 'CSMT', label: 'CSMT – Chhatrapati Shivaji Maharaj Terminus', type: 'station', city: 'Mumbai', is_major: true },
  { value: 'BCT', label: 'BCT – Mumbai Central', type: 'station', city: 'Mumbai', is_major: true },
  { value: 'LTT', label: 'LTT – Lokmanya Tilak Terminus', type: 'station', city: 'Mumbai', is_major: true },
  { value: 'HWH', label: 'HWH – Howrah Junction', type: 'station', city: 'Kolkata', is_major: true },
  { value: 'SDAH', label: 'SDAH – Sealdah', type: 'station', city: 'Kolkata', is_major: true },
  { value: 'MAS', label: 'MAS – Chennai Central', type: 'station', city: 'Chennai', is_major: true },
  { value: 'MS', label: 'MS – Chennai Egmore', type: 'station', city: 'Chennai', is_major: true },
  { value: 'SBC', label: 'SBC – KSR Bangalore City Junction', type: 'station', city: 'Bengaluru', is_major: true },
  { value: 'YPR', label: 'YPR – Yesvantpur Junction', type: 'station', city: 'Bengaluru', is_major: true },
  { value: 'SC', label: 'SC – Secunderabad Junction', type: 'station', city: 'Hyderabad', is_major: true },
  { value: 'HYB', label: 'HYB – Hyderabad Deccan (Nampally)', type: 'station', city: 'Hyderabad', is_major: true },
  { value: 'PUNE', label: 'PUNE – Pune Junction', type: 'station', city: 'Pune', is_major: true },
  { value: 'ADI', label: 'ADI – Ahmedabad Junction', type: 'station', city: 'Ahmedabad', is_major: true },
  { value: 'JP', label: 'JP – Jaipur Junction', type: 'station', city: 'Jaipur', is_major: true },
  { value: 'LKO', label: 'LKO – Lucknow Charbagh', type: 'station', city: 'Lucknow', is_major: true },
  { value: 'NGP', label: 'NGP – Nagpur Junction', type: 'station', city: 'Nagpur', is_major: true },
  { value: 'BSB', label: 'BSB – Varanasi Junction', type: 'station', city: 'Varanasi', is_major: true },
]

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q') || ''
  const limit = parseInt(searchParams.get('limit') || '10', 10)

  if (!q || q.length < 1) {
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
        item.city.toLowerCase().includes(queryLower) ||
        item.value.toLowerCase().includes(queryLower)
      )
      // Sort: city_all first, then major stations
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
