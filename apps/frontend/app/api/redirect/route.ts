/**
 * API Proxy: /api/redirect
 * 
 * Browser -> Next.js API -> Backend
 * Proxies redirect requests for affiliate click tracking.
 * 
 * Flow:
 * 1. Frontend calls /api/redirect with query params
 * 2. This proxy forwards to backend /api/redirect
 * 3. Backend logs the click and returns 302 redirect
 * 4. Browser follows redirect to vendor URL
 */
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams.toString()
  const url = `${BACKEND_URL}/api/redirect${searchParams ? `?${searchParams}` : ''}`

  try {
    // Forward the request to the backend
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json, text/html',
      },
      redirect: 'manual', // Don't follow redirects automatically
    })

    // Backend returns a 302 redirect
    if (response.status === 302 || response.status === 301) {
      const location = response.headers.get('location')
      if (location) {
        // Return a redirect response to the browser
        return NextResponse.redirect(location, { status: 302 })
      }
    }

    // If not a redirect, return the response as-is
    const data = await response.json().catch(() => ({ error: 'Unknown error' }))
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('[API Proxy] /redirect error:', error)
    return NextResponse.json(
      { detail: 'Backend service unavailable' },
      { status: 503 }
    )
  }
}
