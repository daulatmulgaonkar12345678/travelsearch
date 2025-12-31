/**
 * API Proxy: /api/admin/click-logs
 * 
 * Browser -> Next.js API -> Backend
 * Proxies booking click logs for admin dashboard.
 */
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams.toString()
  const url = `${BACKEND_URL}/api/admin/click-logs${searchParams ? `?${searchParams}` : ''}`

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
    console.error('[API Proxy] /admin/click-logs error:', error)
    return NextResponse.json(
      { detail: 'Backend service unavailable' },
      { status: 503 }
    )
  }
}
