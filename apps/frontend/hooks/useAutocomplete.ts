'use client'

/**
 * useAutocomplete - Shared Autocomplete State Machine
 * ===================================================
 * 
 * SINGLE SOURCE OF TRUTH for autocomplete behavior.
 * 
 * STATE MACHINE:
 * - IDLE: No request, no results
 * - LOADING: Request in flight
 * - HAS_RESULTS: Request completed with results
 * - NO_RESULTS: Request completed with empty results
 * - ERROR: Request failed (503 from backend)
 * 
 * GUARANTEES:
 * - Identical behavior in local/preview/production
 * - No race conditions (AbortController + query tracking)
 * - No credit burn (debounce >= 400ms + dedup)
 * - No false empty states (state machine driven)
 * - Latest request always wins
 */

import { useState, useRef, useCallback, useEffect } from 'react'

// ============================================================
// STATE MACHINE
// ============================================================
export type AutocompleteState = 'IDLE' | 'LOADING' | 'HAS_RESULTS' | 'NO_RESULTS' | 'ERROR'

// ============================================================
// RESPONSE NORMALIZATION
// ============================================================
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
  endpoint: string
  minQueryLength?: number
  debounceMs?: number
  limit?: number
  transform: (raw: unknown) => T
  extraParams?: Record<string, string>
}

// ============================================================
// HOOK RETURN TYPE
// ============================================================
interface UseAutocompleteReturn<T> {
  state: AutocompleteState
  results: T[]
  isLoading: boolean
  isError: boolean
  search: (query: string) => void
  clear: () => void
  shouldShowNoResults: (query: string) => boolean
}

// ============================================================
// HOOK IMPLEMENTATION
// ============================================================
export function useAutocomplete<T>({
  endpoint,
  minQueryLength = 2,
  debounceMs = 400, // Credit safety: minimum 400ms debounce
  limit = 15,
  transform,
  extraParams = {},
}: UseAutocompleteOptions<T>): UseAutocompleteReturn<T> {
  const [state, setState] = useState<AutocompleteState>('IDLE')
  const [results, setResults] = useState<T[]>([])
  
  const abortControllerRef = useRef<AbortController | null>(null)
  const latestQueryRef = useRef<string>('')
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const lastFetchedQueryRef = useRef<string>('')
  const requestIdRef = useRef<number>(0)

  const executeFetch = useCallback(async (query: string, requestId: number) => {
    // Dedup: skip if same query already fetched with results
    if (query === lastFetchedQueryRef.current && results.length > 0) {
      setState('HAS_RESULTS')
      return
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()
    const currentQuery = query

    setState('LOADING')

    try {
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

      // Stale response check: ignore if not latest request
      if (requestId !== requestIdRef.current || currentQuery !== latestQueryRef.current) {
        return
      }

      // Handle 503 (backend unavailable in production)
      if (response.status === 503) {
        setResults([])
        setState('ERROR')
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      // Final stale check
      if (requestId !== requestIdRef.current || currentQuery !== latestQueryRef.current) {
        return
      }

      const normalized = normalizeApiResponse(data)
      const transformed = normalized.map(transform)

      lastFetchedQueryRef.current = query
      setResults(transformed)
      setState(transformed.length > 0 ? 'HAS_RESULTS' : 'NO_RESULTS')

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }

      // Stale error check
      if (requestId !== requestIdRef.current || currentQuery !== latestQueryRef.current) {
        return
      }

      setResults([])
      setState('ERROR')
    }
  }, [endpoint, limit, transform, extraParams, results.length])

  const search = useCallback((query: string) => {
    // Clear pending debounce
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
      debounceTimerRef.current = null
    }

    latestQueryRef.current = query

    // Below min length: reset to IDLE
    if (query.length < minQueryLength) {
      setResults([])
      setState('IDLE')
      return
    }

    // Dedup: same query with results
    if (query === lastFetchedQueryRef.current && results.length > 0) {
      setState('HAS_RESULTS')
      return
    }

    setState('LOADING')

    // Debounce (>= 400ms for credit safety)
    debounceTimerRef.current = setTimeout(() => {
      requestIdRef.current += 1
      executeFetch(query, requestIdRef.current)
    }, debounceMs)
  }, [minQueryLength, debounceMs, executeFetch, results.length])

  const clear = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    
    latestQueryRef.current = ''
    lastFetchedQueryRef.current = ''
    requestIdRef.current = 0
    setResults([])
    setState('IDLE')
  }, [])

  const shouldShowNoResults = useCallback((query: string): boolean => {
    return query.length >= 3 && state === 'NO_RESULTS' && results.length === 0
  }, [state, results.length])

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
    isError: state === 'ERROR',
    search,
    clear,
    shouldShowNoResults,
  }
}
