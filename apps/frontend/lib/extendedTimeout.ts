/**
 * Extended Search Timeout Handler
 * 
 * Handles slow backend responses gracefully with:
 * - Extended timeout (90-120s)
 * - Staged UX messages
 * - Automatic retries (up to 2 times)
 * - Smart cancellation
 */

export interface TimeoutStage {
  duration: number
  message: string
  type: 'searching' | 'warming' | 'retry'
}

export const TIMEOUT_STAGES: TimeoutStage[] = [
  {
    duration: 10000, // 0-10s
    message: 'Searching flights...',
    type: 'searching',
  },
  {
    duration: 30000, // 10-30s
    message: 'Still searching, checking more airlines...',
    type: 'searching',
  },
  {
    duration: 60000, // 30-60s
    message: 'Warming up search engine, please wait...',
    type: 'warming',
  },
  {
    duration: 120000, // 60-120s
    message: 'This is taking longer than usual. You can retry or wait a bit more.',
    type: 'retry',
  },
]

export class ExtendedTimeoutHandler {
  private currentStage: number = 0
  private stageTimers: NodeJS.Timeout[] = []
  private onStageChange?: (stage: TimeoutStage, stageIndex: number) => void
  private startTime: number = 0

  constructor(onStageChange?: (stage: TimeoutStage, stageIndex: number) => void) {
    this.onStageChange = onStageChange
  }

  start() {
    this.startTime = Date.now()
    this.currentStage = 0
    this.setupStages()
    
    // Immediately trigger first stage
    if (this.onStageChange && TIMEOUT_STAGES[0]) {
      this.onStageChange(TIMEOUT_STAGES[0], 0)
    }
  }

  private setupStages() {
    // Clear existing timers
    this.clear()

    // Set up timers for each stage
    TIMEOUT_STAGES.forEach((stage, index) => {
      if (index === 0) return // Skip first stage (already triggered)

      const timer = setTimeout(() => {
        this.currentStage = index
        if (this.onStageChange) {
          this.onStageChange(stage, index)
        }
      }, stage.duration)

      this.stageTimers.push(timer)
    })
  }

  clear() {
    this.stageTimers.forEach(timer => clearTimeout(timer))
    this.stageTimers = []
  }

  getCurrentStage(): TimeoutStage {
    return TIMEOUT_STAGES[this.currentStage] || TIMEOUT_STAGES[0]
  }

  getElapsedTime(): number {
    return Date.now() - this.startTime
  }

  isInRetryStage(): boolean {
    return this.currentStage >= TIMEOUT_STAGES.length - 1
  }
}

export interface RetryConfig {
  maxRetries: number
  currentRetry: number
  shouldRetry: boolean
  retryDelay: number
}

export class RetryHandler {
  private maxRetries: number
  private currentRetry: number = 0
  private retryDelay: number
  private onRetry?: (retryNumber: number) => void

  constructor(
    maxRetries: number = 2,
    retryDelay: number = 2000,
    onRetry?: (retryNumber: number) => void
  ) {
    this.maxRetries = maxRetries
    this.retryDelay = retryDelay
    this.onRetry = onRetry
  }

  canRetry(): boolean {
    return this.currentRetry < this.maxRetries
  }

  async executeWithRetry<T>(
    operation: () => Promise<T>,
    onError?: (error: any, retryNumber: number) => void
  ): Promise<T> {
    let lastError: any

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, this.retryDelay))
          console.log(`Retry attempt ${attempt}/${this.maxRetries}`)
          this.onRetry?.(attempt)
        }

        this.currentRetry = attempt
        return await operation()
      } catch (error: any) {
        lastError = error
        
        // Don't retry on abort errors
        if (error.name === 'AbortError') {
          throw error
        }

        // Don't retry on validation errors (4xx except 429)
        if (error.status >= 400 && error.status < 500 && error.status !== 429) {
          throw error
        }

        onError?.(error, attempt)
        
        // If last attempt, throw
        if (attempt >= this.maxRetries) {
          throw lastError
        }
      }
    }

    throw lastError
  }

  getCurrentRetry(): number {
    return this.currentRetry
  }

  reset() {
    this.currentRetry = 0
  }
}
