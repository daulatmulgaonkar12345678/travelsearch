/**
 * ServiceUnavailable Component
 * 
 * Production-grade component for handling service unavailability.
 * Follows best practices from Skyscanner/Booking.com systems.
 * 
 * Features:
 * - Mobile-friendly responsive design
 * - Dynamic service name display
 * - Clear retry instructions
 * - Consistent with existing Tailwind CSS design
 * - No alerts or modals
 */

import { AlertCircle, RefreshCw, Info } from 'lucide-react'

interface ServiceUnavailableProps {
  service: 'Flights' | 'Hotels' | 'Backend'
  message?: string
  details?: string
  onRetry?: () => void
}

export default function ServiceUnavailable({
  service,
  message,
  details,
  onRetry,
}: ServiceUnavailableProps) {
  const defaultMessage = message || `${service} service is temporarily unavailable`
  
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-2xl w-full">
        {/* Main Card */}
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8 md:p-12">
          {/* Icon */}
          <div className="flex justify-center mb-6">
            <div className="bg-yellow-100 rounded-full p-4">
              <AlertCircle className="h-12 w-12 text-yellow-600" />
            </div>
          </div>
          
          {/* Title */}
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 text-center mb-4">
            {service} Temporarily Unavailable
          </h1>
          
          {/* Message */}
          <p className="text-lg text-gray-600 text-center mb-6">
            {defaultMessage}
          </p>
          
          {/* Details (if provided) */}
          {details && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start space-x-3">
                <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-800">{details}</p>
              </div>
            </div>
          )}
          
          {/* What to do section */}
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h2 className="font-semibold text-gray-900 mb-3">What you can do:</h2>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="inline-block w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span>Wait a few moments and try again</span>
              </li>
              <li className="flex items-start">
                <span className="inline-block w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span>Check your internet connection</span>
              </li>
              <li className="flex items-start">
                <span className="inline-block w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span>If the problem persists, please try again later</span>
              </li>
            </ul>
          </div>
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            {onRetry && (
              <button
                onClick={onRetry}
                className="flex-1 flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                <RefreshCw className="h-5 w-5" />
                <span>Try Again</span>
              </button>
            )}
            
            <button
              onClick={() => window.location.href = '/'}
              className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-900 font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Back to Home
            </button>
          </div>
        </div>
        
        {/* Status Note */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            We're working to restore service as quickly as possible.
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Thank you for your patience.
          </p>
        </div>
      </div>
    </div>
  )
}
