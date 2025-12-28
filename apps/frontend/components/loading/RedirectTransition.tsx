'use client'

import { useEffect, useState } from 'react'
import { Train, Bus, ExternalLink } from 'lucide-react'

type TransportMode = 'train' | 'bus'

interface RedirectTransitionProps {
  mode: TransportMode
  partnerName: string
  isVisible: boolean
  onComplete: () => void
  duration?: number // Default 500ms
}

/**
 * Pre-redirect transition overlay
 * Shows a brief animation before redirecting to booking partner
 * Duration: 300-600ms as per requirements
 */
export default function RedirectTransition({
  mode,
  partnerName,
  isVisible,
  onComplete,
  duration = 500,
}: RedirectTransitionProps) {
  const [progress, setProgress] = useState(0)
  
  const Icon = mode === 'train' ? Train : Bus
  const accentColor = mode === 'train' ? 'blue' : 'orange'
  const bgGradient = mode === 'train' 
    ? 'from-blue-600 to-blue-700' 
    : 'from-orange-500 to-orange-600'

  useEffect(() => {
    if (!isVisible) {
      setProgress(0)
      return
    }

    // Animate progress bar
    const progressInterval = setInterval(() => {
      setProgress((prev) => Math.min(prev + 10, 100))
    }, duration / 10)

    // Trigger completion
    const timer = setTimeout(() => {
      onComplete()
    }, duration)

    return () => {
      clearTimeout(timer)
      clearInterval(progressInterval)
    }
  }, [isVisible, duration, onComplete])

  if (!isVisible) return null

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-overlay-in"
      role="dialog"
      aria-label={`Redirecting to ${partnerName}`}
    >
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 animate-modal-in">
        {/* Icon Animation */}
        <div className="relative mb-6">
          <div className="flex justify-center">
            <div className={`relative bg-gradient-to-br ${bgGradient} rounded-full p-4 shadow-lg`}>
              <Icon className="h-10 w-10 text-white animate-bounce-subtle" />
              {/* Pulse ring */}
              <div className={`absolute inset-0 rounded-full bg-${accentColor}-400 animate-ping opacity-30`} />
            </div>
          </div>
          
          {/* Moving Icon Track */}
          <div className="mt-4 relative h-8 overflow-hidden">
            <div className="absolute inset-x-0 top-1/2 h-0.5 bg-gray-200" />
            <div className={`redirect-icon-animation-${mode}`}>
              <Icon className={`h-5 w-5 text-${accentColor}-500`} />
            </div>
          </div>
        </div>

        {/* Text */}
        <div className="text-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Redirecting to {partnerName}
          </h3>
          <p className="text-sm text-gray-600">
            {mode === 'train' 
              ? 'Taking you to check live availability & book your train…'
              : 'Taking you to check live seats & book your bus…'
            }
          </p>
        </div>

        {/* Progress Bar */}
        <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
          <div 
            className={`absolute inset-y-0 left-0 bg-gradient-to-r ${bgGradient} rounded-full transition-all duration-100 ease-linear`}
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* External link indicator */}
        <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
          <ExternalLink className="h-3 w-3" />
          <span>Opening in new tab</span>
        </div>
      </div>

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes overlay-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes modal-in {
          from { 
            opacity: 0; 
            transform: scale(0.95) translateY(10px);
          }
          to { 
            opacity: 1; 
            transform: scale(1) translateY(0);
          }
        }

        @keyframes bounce-subtle {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }

        @keyframes redirect-move {
          0% { left: 10%; }
          100% { left: 90%; transform: translateX(-100%); }
        }

        .animate-overlay-in {
          animation: overlay-in 150ms ease-out;
        }

        .animate-modal-in {
          animation: modal-in 200ms ease-out;
        }

        .animate-bounce-subtle {
          animation: bounce-subtle 0.6s ease-in-out infinite;
        }

        .redirect-icon-animation-train,
        .redirect-icon-animation-bus {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          animation: redirect-move ${duration}ms linear forwards;
        }

        @media (prefers-reduced-motion: reduce) {
          .animate-overlay-in,
          .animate-modal-in,
          .animate-bounce-subtle,
          .redirect-icon-animation-train,
          .redirect-icon-animation-bus {
            animation: none;
          }
          
          .redirect-icon-animation-train,
          .redirect-icon-animation-bus {
            left: 50%;
            transform: translateX(-50%) translateY(-50%);
          }
        }
      `}</style>
    </div>
  )
}
