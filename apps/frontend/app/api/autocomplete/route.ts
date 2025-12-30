/**
 * API Proxy: /api/autocomplete (unified)
 * 
 * TRANSPARENT PROXY - NO LOGIC
 * Browser -> Next.js API -> Backend
 * 
 * Routes based on mode parameter:
 * - mode=bus -> /api/autocomplete/bus
 * - mode=train -> /api/trains/autocomplete
 * - mode=hotel -> /api/hotels/autocomplete
 * 
 * Rules:
 * - Forward request as-is
 * - Forward response as-is
 * - No filtering
 * - No fallback data
 * - No transformation
 */
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const mode = searchParams.get('mode')
  const q = searchParams.get('q') || ''
  const limit = searchParams.get('limit') || '15'

  // Determine backend endpoint based on mode
  let backendPath: string
  if (mode === 'bus') {
    backendPath = `/api/autocomplete/bus?q=${encodeURIComponent(q)}&mode=bus&limit=${limit}`
  } else if (mode === 'train') {
    backendPath = `/api/trains/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`
  } else if (mode === 'hotel') {
    backendPath = `/api/hotels/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`
  } else {
    return NextResponse.json(
      { detail: 'Invalid mode parameter. Use: bus, train, or hotel' },
      { status: 400 }
    )
  }

  const url = `${BACKEND_URL}${backendPath}`

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store',
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error(`[API Proxy] /autocomplete (${mode}) error:`, error)
    return NextResponse.json(
      { detail: 'Backend service unavailable' },
      { status: 503 }
    )
  }
}
