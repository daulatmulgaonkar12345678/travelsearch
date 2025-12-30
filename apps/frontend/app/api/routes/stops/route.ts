/**
 * API Proxy: /api/routes/stops
 * 
 * Browser -> Next.js API -> Backend
 * This ensures no CORS issues and works across all environments.
 */
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams.toString()
  const url = `${BACKEND_URL}/api/routes/stops${searchParams ? `?${searchParams}` : ''}`

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('[API Proxy] /routes/stops error:', error)
    return NextResponse.json(
      { detail: 'Backend service unavailable' },
      { status: 503 }
    )
  }
}
