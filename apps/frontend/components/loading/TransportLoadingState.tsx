'use client'

import { useState, useEffect } from 'react'
import { Train, Bus, Lock } from 'lucide-react'

type TransportMode = 'train' | 'bus'

interface TransportLoadingStateProps {
  mode: TransportMode
  origin?: string
  destination?: string
}

const TRAIN_MESSAGES = [
  '🚆 Checking train availability…',
  '🔍 Searching Indian Railways database…',
  '🎫 Finding available seats for you…',
  '💰 Comparing prices across classes…',
]

const BUS_MESSAGES = [
  '🚌 Finding the best bus options…',
  '🔍 Checking with operators…',
  '🛣️ Searching all available routes…',
  '💰 Comparing fares from trusted partners…',
]

export default function TransportLoadingState({ mode, origin, destination }: TransportLoadingStateProps) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)
  const messages = mode === 'train' ? TRAIN_MESSAGES : BUS_MESSAGES
  const Icon = mode === 'train' ? Train : Bus
  const accentColor = mode === 'train' ? 'blue' : 'orange'

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % messages.length)
    }, 2000)

    return () => clearInterval(interval)
  }, [messages.length])

  return (
    <div className="min-h-[500px] flex flex-col items-center justify-center px-4 py-12">
      {/* Route Display */}
      {origin && destination && (
        <div className="text-center mb-8 animate-fade-in">
          <div className="text-2xl font-semibold text-gray-900">
            {origin} → {destination}
          </div>
        </div>
      )}

      {/* Animated Transport Route */}
      <div className="relative w-full max-w-md mb-12">
        {/* Track/Road Line */}
        <div className={`absolute top-1/2 left-0 right-0 h-1 ${
          mode === 'train' 
            ? 'bg-gradient-to-r from-gray-300 via-gray-400 to-gray-300' 
            : 'bg-gradient-to-r from-gray-300 via-gray-400 to-gray-300'
        }`}>
          {/* Track ties for train */}
          {mode === 'train' && (
            <div className="absolute inset-0 flex items-center justify-around">
              {[...Array(12)].map((_, i) => (
                <div key={i} className="w-1 h-3 bg-gray-400 rounded-sm" />
              ))}
            </div>
          )}
          {/* Dashed road for bus */}
          {mode === 'bus' && (
            <div className="absolute top-1/2 left-0 right-0 border-t-2 border-dashed border-yellow-500" />
          )}
        </div>
        
        {/* Start Point */}
        <div className={`absolute left-0 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-${accentColor}-500 z-10`} />
        
        {/* End Point */}
        <div className={`absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-${accentColor}-500 z-10`} />

        {/* Animated Icon */}
        <div className="relative w-full h-16">
          <div className={`transport-animation-${mode}`}>
            <div className={`bg-white rounded-full p-2 shadow-lg border-2 border-${accentColor}-500`}>
              <Icon className={`h-8 w-8 text-${accentColor}-600`} />
            </div>
          </div>
        </div>
      </div>

      {/* Rotating Status Text */}
      <div className="text-center mb-12">
        <div className="text-lg font-medium text-gray-700 h-8 flex items-center justify-center transition-all duration-300 ease-out">
          {messages[currentMessageIndex]}
        </div>
      </div>

      {/* Trust Message */}
      <div className="flex items-start space-x-2 text-sm text-gray-600 max-w-md text-center mb-12">
        <Lock className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />
        <div>
          <div className="font-medium text-gray-700">
            {mode === 'train' 
              ? 'We compare prices from official IRCTC and trusted partners'
              : 'We compare prices from multiple bus operators'
            }
          </div>
          <div className="text-gray-500 mt-1">You'll be redirected securely to book</div>
        </div>
      </div>

      {/* Skeleton Cards */}
      <div className="w-full max-w-4xl space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className="flex items-center justify-between">
              {/* Left side skeleton */}
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-3">
                  <div className={`h-10 w-10 rounded-lg bg-${accentColor}-100`} />
                  <div>
                    <div className="h-4 bg-gray-200 rounded w-32 mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-20" />
                  </div>
                </div>
              </div>

              {/* Middle skeleton */}
              <div className="flex-1 text-center space-y-3">
                <div className="h-3 bg-gray-200 rounded w-20 mx-auto" />
                <div className="h-1 bg-gray-200 rounded w-32 mx-auto" />
                <div className="h-3 bg-gray-200 rounded w-16 mx-auto" />
              </div>

              {/* Right side skeleton */}
              <div className="flex-1 flex flex-col items-end space-y-3">
                <div className="h-8 bg-gray-200 rounded w-24" />
                <div className="h-3 bg-gray-200 rounded w-16" />
                <div className="h-10 bg-gray-200 rounded w-28" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* CSS Animations */}
      <style jsx>{`
        @keyframes transport-move-train {
          0% {
            left: 0%;
            transform: translateX(0) translateY(-50%);
          }
          50% {
            transform: translateX(0) translateY(-52%);
          }
          100% {
            left: 100%;
            transform: translateX(-100%) translateY(-50%);
          }
        }

        @keyframes transport-move-bus {
          0% {
            left: 0%;
            transform: translateX(0) translateY(-50%);
          }
          25% {
            transform: translateX(0) translateY(-48%);
          }
          50% {
            transform: translateX(0) translateY(-52%);
          }
          75% {
            transform: translateX(0) translateY(-48%);
          }
          100% {
            left: 100%;
            transform: translateX(-100%) translateY(-50%);
          }
        }

        .transport-animation-train {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          animation: transport-move-train 2.5s ease-in-out infinite;
        }

        .transport-animation-bus {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          animation: transport-move-bus 2s ease-in-out infinite;
        }

        .animate-fade-in {
          animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @media (prefers-reduced-motion: reduce) {
          .transport-animation-train,
          .transport-animation-bus {
            animation: none;
            left: 50%;
            transform: translateX(-50%) translateY(-50%);
          }
        }
      `}</style>
    </div>
  )
}
