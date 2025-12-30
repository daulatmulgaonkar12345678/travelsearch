/**
 * API Proxy: /api/pricing/date-range
 * 
 * Browser -> Next.js API -> Backend
 * This ensures no CORS issues and works across all environments.
 */
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function POST(request: NextRequest) {
  const body = await request.json()
  const url = `${BACKEND_URL}/api/pricing/date-range`

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      cache: 'no-store',
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('[API Proxy] /pricing/date-range error:', error)
    return NextResponse.json(
      { detail: 'Backend service unavailable' },
      { status: 503 }
    )
  }
}
