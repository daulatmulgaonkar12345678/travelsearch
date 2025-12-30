/**
 * API Proxy: /api/clicks/log
 * 
 * Browser -> Next.js API -> Backend
 * This ensures no CORS issues and works across all environments.
 */
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function POST(request: NextRequest) {
  const body = await request.json()
  const url = `${BACKEND_URL}/api/clicks/log`

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

    // If backend doesn't have this endpoint, just return success
    if (response.status === 404) {
      return NextResponse.json({ success: true }, { status: 200 })
    }

    const data = await response.json().catch(() => ({ success: true }))
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    // Click logging is fire-and-forget, don't fail
    console.warn('[API Proxy] /clicks/log error:', error)
    return NextResponse.json({ success: true }, { status: 200 })
  }
}
