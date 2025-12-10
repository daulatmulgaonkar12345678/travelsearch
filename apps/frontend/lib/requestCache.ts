/**
 * Request Cache Utility
 * 
 * In-memory cache for search requests to prevent duplicate API calls
 * and improve loading performance.
 * 
 * Features:
 * - Deduplicates identical requests within cache window
 * - Stores responses with timestamps
 * - Automatic cache expiration
 * - AbortController integration for cancelling inflight requests
 */

interface CacheEntry<T = any> {
  data: T
  timestamp: number
}

interface InflightRequest {
  promise: Promise<any>
  controller: AbortController
}

/**
 * Request cache configuration
 */
const CACHE_TTL = 20000 // 20 seconds (between 15-30s as per requirements)
const MAX_CACHE_SIZE = 50 // Prevent memory leak

/**
 * Request Cache Manager
 */
class RequestCacheManager {
  private cache: Map<string, CacheEntry> = new Map()
  private inflightRequests: Map<string, InflightRequest> = new Map()

  /**
   * Generate cache key from request parameters
   */
  private generateKey(endpoint: string, params: Record<string, any>): string {
    // Sort keys for consistent cache keys
    const sortedParams = Object.keys(params)
      .sort()
      .reduce((acc, key) => {
        acc[key] = params[key]
        return acc
      }, {} as Record<string, any>)
    
    return `${endpoint}::${JSON.stringify(sortedParams)}`
  }

  /**
   * Check if cache entry is still fresh
   */
  private isFresh(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp < CACHE_TTL
  }

  /**
   * Clean up expired cache entries
   */
  private cleanup(): void {
    const now = Date.now()
    const keysToDelete: string[] = []

    this.cache.forEach((entry, key) => {
      if (now - entry.timestamp >= CACHE_TTL) {
        keysToDelete.push(key)
      }
    })

    keysToDelete.forEach(key => this.cache.delete(key))

    // Enforce max cache size (LRU-like behavior)
    if (this.cache.size > MAX_CACHE_SIZE) {
      const entriesToDelete = this.cache.size - MAX_CACHE_SIZE
      let deleted = 0
      
      for (const key of this.cache.keys()) {
        if (deleted >= entriesToDelete) break
        this.cache.delete(key)
        deleted++
      }
    }
  }

  /**
   * Get cached data if available and fresh
   */
  get<T = any>(endpoint: string, params: Record<string, any>): T | null {
    const key = this.generateKey(endpoint, params)
    const entry = this.cache.get(key)

    if (entry && this.isFresh(entry)) {
      console.log(`[Cache] HIT: ${key}`)
      return entry.data as T
    }

    if (entry) {
      console.log(`[Cache] EXPIRED: ${key}`)
      this.cache.delete(key)
    }

    return null
  }

  /**
   * Store data in cache
   */
  set<T = any>(endpoint: string, params: Record<string, any>, data: T): void {
    const key = this.generateKey(endpoint, params)
    
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    })

    console.log(`[Cache] SET: ${key}`)
    
    // Periodic cleanup
    this.cleanup()
  }

  /**
   * Get or set inflight request
   * Returns existing inflight request if available, otherwise creates new one
   */
  getOrSetInflight<T = any>(
    endpoint: string,
    params: Record<string, any>,
    fetcher: (signal: AbortSignal) => Promise<T>
  ): { promise: Promise<T>, controller: AbortController } {
    const key = this.generateKey(endpoint, params)
    const existing = this.inflightRequests.get(key)

    if (existing) {
      console.log(`[Cache] INFLIGHT REUSE: ${key}`)
      return existing as { promise: Promise<T>, controller: AbortController }
    }

    console.log(`[Cache] INFLIGHT NEW: ${key}`)
    const controller = new AbortController()
    
    const promise = fetcher(controller.signal)
      .finally(() => {
        // Clean up inflight request when done
        this.inflightRequests.delete(key)
      })

    const inflightRequest = { promise, controller }
    this.inflightRequests.set(key, inflightRequest)

    return inflightRequest
  }

  /**
   * Abort all inflight requests (e.g., when component unmounts)
   */
  abortAll(): void {
    console.log(`[Cache] Aborting ${this.inflightRequests.size} inflight requests`)
    
    this.inflightRequests.forEach(({ controller }) => {
      controller.abort()
    })
    
    this.inflightRequests.clear()
  }

  /**
   * Abort specific inflight request
   */
  abort(endpoint: string, params: Record<string, any>): void {
    const key = this.generateKey(endpoint, params)
    const inflight = this.inflightRequests.get(key)

    if (inflight) {
      console.log(`[Cache] ABORT: ${key}`)
      inflight.controller.abort()
      this.inflightRequests.delete(key)
    }
  }

  /**
   * Clear all cache
   */
  clear(): void {
    console.log('[Cache] CLEAR ALL')
    this.cache.clear()
    this.abortAll()
  }

  /**
   * Get cache statistics (for debugging)
   */
  getStats() {
    return {
      cacheSize: this.cache.size,
      inflightRequests: this.inflightRequests.size,
      entries: Array.from(this.cache.keys())
    }
  }
}

/**
 * Global cache instance (singleton)
 */
export const requestCache = new RequestCacheManager()

/**
 * React hook for using the request cache
 */
export function useCachedRequest<T = any>(
  endpoint: string,
  params: Record<string, any>,
  fetcher: (signal: AbortSignal) => Promise<T>,
  options: {
    enabled?: boolean
    onSuccess?: (data: T) => void
    onError?: (error: Error) => void
  } = {}
): {
  data: T | null
  loading: boolean
  error: Error | null
  refetch: () => void
} {
  const { enabled = true, onSuccess, onError } = options

  // This is a simplified version - in a real implementation,
  // you'd use useState and useEffect here
  // For now, we'll just provide the cache utilities
  
  return {
    data: null,
    loading: false,
    error: null,
    refetch: () => {}
  }
}

/**
 * Helper to create cached fetch function
 */
export function createCachedFetch<T = any>(
  endpoint: string,
  fetchFn: (signal: AbortSignal) => Promise<T>
) {
  return async (params: Record<string, any>): Promise<T> => {
    // Check cache first
    const cached = requestCache.get<T>(endpoint, params)
    if (cached) {
      return cached
    }

    // Get or create inflight request
    const { promise } = requestCache.getOrSetInflight(
      endpoint,
      params,
      fetchFn
    )

    try {
      const data = await promise
      
      // Store in cache
      requestCache.set(endpoint, params, data)
      
      return data
    } catch (error) {
      // Don't cache errors
      throw error
    }
  }
}
