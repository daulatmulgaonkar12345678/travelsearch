/**
 * API Proxy: /api/autocomplete/bus
 * 
 * TRANSPARENT PROXY - NO LOGIC
 * Browser -> Next.js API -> Backend
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
  const searchParams = request.nextUrl.searchParams.toString()
  const url = `${BACKEND_URL}/api/autocomplete/bus${searchParams ? `?${searchParams}` : ''}`

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
    console.error('[API Proxy] /autocomplete/bus error:', error)
    return NextResponse.json(
      { detail: 'Backend service unavailable' },
      { status: 503 }
    )
  }
}
