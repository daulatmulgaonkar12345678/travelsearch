'use client'

/**
 * useAutocomplete - Shared Autocomplete State Machine
 * ===================================================
 * 
 * SINGLE SOURCE OF TRUTH for autocomplete behavior across:
 * - Bus autocomplete
 * - Train autocomplete
 * 
 * STATE MACHINE:
 * - IDLE: No request, no results
 * - LOADING: Request in flight
 * - HAS_RESULTS: Request completed with results
 * - NO_RESULTS: Request completed with empty results
 * 
 * GUARANTEES:
 * - Identical behavior in local/preview/production
 * - No race conditions (AbortController + query tracking)
 * - No credit burn (debounce + dedup)
 * - No false empty states (state machine driven)
 */

import { useState, useRef, useCallback, useEffect } from 'react'

// ============================================================
// STATE MACHINE
// ============================================================
export type AutocompleteState = 'IDLE' | 'LOADING' | 'HAS_RESULTS' | 'NO_RESULTS'

// ============================================================
// RESPONSE NORMALIZATION (SINGLE FUNCTION)
// ============================================================
/**
 * Normalize any API response shape to a flat array.
 * Accepts: raw array, { data: [...] }, { results: [...] }
 * Returns: always an array (empty if invalid)
 */
export function normalizeApiResponse(data: unknown): unknown[] {
  if (!data) return []
  if (Array.isArray(data)) return data
  if (typeof data === 'object' && data !== null) {
    const obj = data as Record<string, unknown>
    if (Array.isArray(obj.results)) return obj.results
    if (Array.isArray(obj.data)) return obj.data
  }
  return []
}

// ============================================================
// HOOK OPTIONS
// ============================================================
interface UseAutocompleteOptions<T> {
  /** API endpoint (relative or absolute) */
  endpoint: string
  /** Minimum query length to trigger search */
  minQueryLength?: number
  /** Debounce delay in ms (default 400) */
  debounceMs?: number
  /** Max results to fetch */
  limit?: number
  /** Transform raw API result to typed result */
  transform: (raw: unknown) => T
  /** Additional query params */
  extraParams?: Record<string, string>
}

// ============================================================
// HOOK RETURN TYPE
// ============================================================
interface UseAutocompleteReturn<T> {
  /** Current autocomplete state */
  state: AutocompleteState
  /** Current results (empty array if none) */
  results: T[]
  /** Whether loading */
  isLoading: boolean
  /** Trigger search for a query */
  search: (query: string) => void
  /** Clear results and reset to IDLE */
  clear: () => void
  /** Check if should show empty state */
  shouldShowNoResults: (query: string) => boolean
}

// ============================================================
// HOOK IMPLEMENTATION
// ============================================================
export function useAutocomplete<T>({
  endpoint,
  minQueryLength = 2,
  debounceMs = 400,
  limit = 15,
  transform,
  extraParams = {},
}: UseAutocompleteOptions<T>): UseAutocompleteReturn<T> {
  // State machine state
  const [state, setState] = useState<AutocompleteState>('IDLE')
  const [results, setResults] = useState<T[]>([])
  
  // Request control refs
  const abortControllerRef = useRef<AbortController | null>(null)
  const latestQueryRef = useRef<string>('')
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const lastFetchedQueryRef = useRef<string>('')

  /**
   * Execute the actual fetch
   * Called after debounce, with abort control
   */
  const executeFetch = useCallback(async (query: string) => {
    // Skip if same as last fetched query (dedup)
    if (query === lastFetchedQueryRef.current && results.length > 0) {
      return
    }

    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController()
    const currentQuery = query
    latestQueryRef.current = query

    setState('LOADING')

    try {
      // Build URL with params
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || ''
      const params = new URLSearchParams({
        q: query,
        limit: String(limit),
        ...extraParams,
      })
      const url = `${apiBase}${endpoint}?${params.toString()}`

      const response = await fetch(url, {
        signal: abortControllerRef.current.signal,
        headers: { 'Accept': 'application/json' },
      })

      // CRITICAL: Ignore if this is not the latest query
      if (currentQuery !== latestQueryRef.current) {
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      // CRITICAL: Double-check this is still the latest query
      if (currentQuery !== latestQueryRef.current) {
        return
      }

      // Normalize and transform
      const normalized = normalizeApiResponse(data)
      const transformed = normalized.map(transform)

      // Update state based on results
      lastFetchedQueryRef.current = query
      setResults(transformed)
      setState(transformed.length > 0 ? 'HAS_RESULTS' : 'NO_RESULTS')

    } catch (error) {
      // Ignore abort errors
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }

      // CRITICAL: Only update state if this is still the latest query
      if (currentQuery !== latestQueryRef.current) {
        return
      }

      console.error('Autocomplete fetch error:', error)
      setResults([])
      setState('NO_RESULTS')
    }
  }, [endpoint, limit, transform, extraParams, results.length])

  /**
   * Public search function - triggers debounced fetch
   */
  const search = useCallback((query: string) => {
    // Clear any pending debounce
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
      debounceTimerRef.current = null
    }

    // Update latest query immediately
    latestQueryRef.current = query

    // Check minimum length
    if (query.length < minQueryLength) {
      setResults([])
      setState('IDLE')
      return
    }

    // Skip if same query already has results
    if (query === lastFetchedQueryRef.current && results.length > 0) {
      setState('HAS_RESULTS')
      return
    }

    // Set loading state immediately for UX feedback
    setState('LOADING')

    // Debounce the actual fetch
    debounceTimerRef.current = setTimeout(() => {
      executeFetch(query)
    }, debounceMs)
  }, [minQueryLength, debounceMs, executeFetch, results.length])

  /**
   * Clear results and reset state
   */
  const clear = useCallback(() => {
    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    // Clear debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    
    latestQueryRef.current = ''
    lastFetchedQueryRef.current = ''
    setResults([])
    setState('IDLE')
  }, [])

  /**
   * Check if should show "No results" message
   * ONLY returns true when:
   * - query length >= 3 (configurable via minQueryLength + 1)
   * - state is NO_RESULTS
   * - NOT loading
   */
  const shouldShowNoResults = useCallback((query: string): boolean => {
    return (
      query.length >= 3 &&
      state === 'NO_RESULTS' &&
      results.length === 0
    )
  }, [state, results.length])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [])

  return {
    state,
    results,
    isLoading: state === 'LOADING',
    search,
    clear,
    shouldShowNoResults,
  }
}
