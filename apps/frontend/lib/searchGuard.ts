/**
 * Search Concurrency Guard
 * 
 * Ensures only ONE active search request per search type.
 * Cancels or ignores previous in-flight requests.
 * 
 * Usage:
 *   const guard = createSearchGuard()
 *   const result = await guard.execute(searchFn)
 */

// Store for active abort controllers
const activeControllers: Map<string, AbortController> = new Map()

// Request ID counter for tracking latest requests
const requestCounters: Map<string, number> = new Map()

/**
 * Create a search guard for a specific search type
 * 
 * @param searchType Unique identifier for the search type (e.g., 'flights', 'hotels')
 * @returns Guard object with execute method
 */
export function createSearchGuard(searchType: string) {
  return {
    /**
     * Execute a search function with concurrency protection
     * 
     * @param searchFn Async function that performs the search
     * @returns Search result or null if cancelled
     */
    async execute<T>(searchFn: (signal: AbortSignal) => Promise<T>): Promise<T | null> {
      // Cancel any existing request for this search type
      const existingController = activeControllers.get(searchType)
      if (existingController) {
        existingController.abort()
      }

      // Create new abort controller
      const controller = new AbortController()
      activeControllers.set(searchType, controller)

      // Increment request counter
      const currentCount = (requestCounters.get(searchType) || 0) + 1
      requestCounters.set(searchType, currentCount)
      const myRequestId = currentCount

      try {
        const result = await searchFn(controller.signal)

        // Check if this is still the latest request
        if (requestCounters.get(searchType) !== myRequestId) {
          console.log(`[SearchGuard] Request ${myRequestId} superseded by newer request`)
          return null
        }

        return result
      } catch (error) {
        // Check if aborted
        if (error instanceof Error && error.name === 'AbortError') {
          console.log(`[SearchGuard] Request ${myRequestId} was cancelled`)
          return null
        }
        throw error
      } finally {
        // Clean up if this was the active controller
        if (activeControllers.get(searchType) === controller) {
          activeControllers.delete(searchType)
        }
      }
    },

    /**
     * Cancel any active search for this type
     */
    cancel() {
      const controller = activeControllers.get(searchType)
      if (controller) {
        controller.abort()
        activeControllers.delete(searchType)
      }
    },

    /**
     * Check if a search is currently active
     */
    isActive(): boolean {
      return activeControllers.has(searchType)
    }
  }
}

/**
 * Simple debounce utility for search inputs
 * 
 * @param fn Function to debounce
 * @param delay Delay in milliseconds
 * @returns Debounced function
 */
export function debounceSearch<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number = 300
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      fn(...args)
      timeoutId = null
    }, delay)
  }
}

/**
 * Pre-configured search guards for each search type
 */
export const searchGuards = {
  flights: createSearchGuard('flights'),
  hotels: createSearchGuard('hotels'),
  buses: createSearchGuard('buses'),
  trains: createSearchGuard('trains'),
  autocomplete: createSearchGuard('autocomplete'),
}
