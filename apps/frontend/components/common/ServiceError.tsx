'use client'

/**
 * ServiceError - User-friendly error states
 * =========================================
 * 
 * Translates backend errors to user-friendly messages.
 * Raw errors (404, 500, stack traces) are NEVER shown to users.
 * 
 * Error Translation:
 * - 404 → "Something went wrong" (log internally)
 * - 503 → "Service temporarily unavailable"
 * - Network → "Unable to connect"
 * - Other → Generic friendly message
 */

import { AlertCircle, RefreshCw, ArrowLeft, WifiOff } from 'lucide-react'

export type ErrorType = 'not_found' | 'service_unavailable' | 'network' | 'generic'

interface ServiceErrorProps {
  type?: ErrorType
  onRetry?: () => void
  onGoBack?: () => void
  /** For developer debugging - logged to console, never shown to user */
  technicalDetails?: string
}

const ERROR_MESSAGES: Record<ErrorType, { title: string; message: string }> = {
  not_found: {
    title: 'Something went wrong',
    message: 'We couldn\'t complete your request. Please try again.',
  },
  service_unavailable: {
    title: 'Service temporarily unavailable',
    message: 'Our servers are busy. Please try again in a few moments.',
  },
  network: {
    title: 'Unable to connect',
    message: 'Please check your internet connection and try again.',
  },
  generic: {
    title: 'Something went wrong',
    message: 'An unexpected error occurred. Please try again.',
  },
}

/**
 * Determine error type from HTTP status or error
 */
export function getErrorType(status?: number, error?: Error): ErrorType {
  if (status === 404) return 'not_found'
  if (status === 503 || status === 502 || status === 504) return 'service_unavailable'
  if (error?.message?.toLowerCase().includes('network') || 
      error?.message?.toLowerCase().includes('fetch') ||
      error?.name === 'TypeError') {
    return 'network'
  }
  return 'generic'
}

export default function ServiceError({
  type = 'generic',
  onRetry,
  onGoBack,
  technicalDetails,
}: ServiceErrorProps) {
  const { title, message } = ERROR_MESSAGES[type]

  // Log technical details for developers (never shown to users)
  if (technicalDetails) {
    console.error('[ServiceError]', type, technicalDetails)
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
      {/* Icon */}
      <div className="text-gray-400 mx-auto mb-4">
        {type === 'network' ? (
          <WifiOff className="h-12 w-12 mx-auto" />
        ) : (
          <AlertCircle className="h-12 w-12 mx-auto" />
        )}
      </div>

      {/* Title */}
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        {title}
      </h2>

      {/* Message */}
      <p className="text-gray-500 mb-6">
        {message}
      </p>

      {/* Action Buttons */}
      <div className="flex flex-wrap justify-center gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-gray-900 text-white hover:bg-gray-800 transition"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
        )}
        
        {onGoBack && (
          <button
            onClick={onGoBack}
            className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium border border-gray-300 text-gray-700 hover:bg-gray-100 transition"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </button>
        )}
      </div>
    </div>
  )
}
