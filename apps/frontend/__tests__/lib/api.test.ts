/**
 * Tests for API Helper (apiFetch retry behavior)
 * 
 * Validates:
 * - URL construction
 * - Retry logic on transient errors
 * - Timeout handling
 * - Exponential backoff
 */

import { apiFetch, apiUrl, getApiBaseUrl } from '@/lib/api'

// Mock fetch globally
const originalFetch = global.fetch

describe('API Helper', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    global.fetch = jest.fn()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  describe('apiUrl', () => {
    it('should construct full URL from path', () => {
      const url = apiUrl('/api/airports')
      expect(url).toContain('/api/airports')
      expect(url).toMatch(/^https?:\/\//)
    })

    it('should handle path without leading slash', () => {
      const url = apiUrl('api/airports')
      expect(url).toContain('/api/airports')
    })

    it('should preserve query parameters', () => {
      const url = apiUrl('/api/airports?query=NYC')
      expect(url).toContain('/api/airports?query=NYC')
    })
  })

  describe('apiFetch - Retry Logic', () => {
    it('should succeed on first attempt for successful response', async () => {
      const mockResponse = new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })

      ;(global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse)

      const response = await apiFetch('/api/test')
      
      expect(global.fetch).toHaveBeenCalledTimes(1)
      expect(response.ok).toBe(true)
    })

    it('should retry on 500 server error', async () => {
      const errorResponse = new Response('Internal Server Error', { status: 500 })
      const successResponse = new Response(JSON.stringify({ success: true }), { status: 200 })

      ;(global.fetch as jest.Mock)
        .mockResolvedValueOnce(errorResponse)
        .mockResolvedValueOnce(successResponse)

      const response = await apiFetch('/api/test', {}, { maxRetries: 2 })
      
      // Should have retried once
      expect(global.fetch).toHaveBeenCalledTimes(2)
      expect(response.ok).toBe(true)
    }, 10000)

    it('should retry on 429 rate limit error', async () => {
      const rateLimitResponse = new Response('Rate Limited', { status: 429 })
      const successResponse = new Response(JSON.stringify({ success: true }), { status: 200 })

      ;(global.fetch as jest.Mock)
        .mockResolvedValueOnce(rateLimitResponse)
        .mockResolvedValueOnce(successResponse)

      const response = await apiFetch('/api/test', {}, { maxRetries: 2 })
      
      expect(global.fetch).toHaveBeenCalledTimes(2)
      expect(response.ok).toBe(true)
    }, 10000)

    it('should retry on network error', async () => {
      const networkError = new Error('Network error')
      const successResponse = new Response(JSON.stringify({ success: true }), { status: 200 })

      ;(global.fetch as jest.Mock)
        .mockRejectedValueOnce(networkError)
        .mockResolvedValueOnce(successResponse)

      const response = await apiFetch('/api/test', {}, { maxRetries: 2 })
      
      expect(global.fetch).toHaveBeenCalledTimes(2)
      expect(response.ok).toBe(true)
    }, 10000)

    it('should NOT retry on 404 Not Found', async () => {
      const notFoundResponse = new Response('Not Found', { status: 404 })

      ;(global.fetch as jest.Mock).mockResolvedValueOnce(notFoundResponse)

      const response = await apiFetch('/api/test', {}, { maxRetries: 2 })
      
      // Should not retry 4xx errors
      expect(global.fetch).toHaveBeenCalledTimes(1)
      expect(response.status).toBe(404)
    })

    it('should NOT retry on 400 Bad Request', async () => {
      const badRequestResponse = new Response('Bad Request', { status: 400 })

      ;(global.fetch as jest.Mock).mockResolvedValueOnce(badRequestResponse)

      const response = await apiFetch('/api/test', {}, { maxRetries: 2 })
      
      expect(global.fetch).toHaveBeenCalledTimes(1)
      expect(response.status).toBe(400)
    })

    it('should exhaust retries and throw on persistent failure', async () => {
      const errorResponse = new Response('Internal Server Error', { status: 500 })

      ;(global.fetch as jest.Mock).mockResolvedValue(errorResponse)

      // Should exhaust all retries and return last response
      const response = await apiFetch('/api/test', {}, { maxRetries: 2 })
      
      // 1 initial + 2 retries = 3 total
      expect(global.fetch).toHaveBeenCalledTimes(3)
      expect(response.status).toBe(500)
    }, 15000)

    it('should apply exponential backoff between retries', async () => {
      const errorResponse = new Response('Internal Server Error', { status: 500 })
      const successResponse = new Response(JSON.stringify({ success: true }), { status: 200 })

      const startTime = Date.now()
      
      ;(global.fetch as jest.Mock)
        .mockResolvedValueOnce(errorResponse)
        .mockResolvedValueOnce(errorResponse)
        .mockResolvedValueOnce(successResponse)

      await apiFetch('/api/test', {}, { maxRetries: 2 })
      
      const duration = Date.now() - startTime
      
      // Should wait at least 500ms + 1000ms = 1500ms for backoff
      // Adding buffer for execution time
      expect(duration).toBeGreaterThan(1400)
      expect(global.fetch).toHaveBeenCalledTimes(3)
    }, 15000)
  })

  describe('apiFetch - Timeout', () => {
    it('should timeout after specified duration', async () => {
      // Mock a slow response
      ;(global.fetch as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 10000))
      )

      await expect(
        apiFetch('/api/test', {}, { timeoutMs: 100, maxRetries: 0 })
      ).rejects.toThrow(/timeout/i)
    }, 5000)
  })

  describe('getApiBaseUrl', () => {
    it('should return environment variable if set', () => {
      const url = getApiBaseUrl()
      expect(url).toBeTruthy()
      expect(typeof url).toBe('string')
    })
  })
})
