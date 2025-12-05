'use client'

import { X, Plus, Minus } from 'lucide-react'

interface PassengerModalProps {
  passengers: {
    adults: number
    children: number
    infants: number
  }
  onUpdate: (passengers: any) => void
  onClose: () => void
}

export default function PassengerModal({ passengers, onUpdate, onClose }: PassengerModalProps) {
  const updateCount = (type: 'adults' | 'children' | 'infants', delta: number) => {
    const newValue = passengers[type] + delta
    if (newValue >= 0 && newValue <= 9) {
      onUpdate({ ...passengers, [type]: newValue })
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4"
        onClick={(e) => e.stopPropagation()}
        data-testid="passenger-modal"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-xl font-semibold">Passengers</h3>
          <button
            onClick={onClose}
            data-testid="close-passenger-modal"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Adults */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Adults</div>
              <div className="text-sm text-gray-500">Age 12+</div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                data-testid="decrease-adults"
                onClick={() => updateCount('adults', -1)}
                disabled={passengers.adults <= 1}
                className="h-10 w-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Minus className="h-4 w-4" />
              </button>
              <span data-testid="adults-count" className="w-8 text-center font-medium">{passengers.adults}</span>
              <button
                data-testid="increase-adults"
                onClick={() => updateCount('adults', 1)}
                disabled={passengers.adults >= 9}
                className="h-10 w-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Children */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Children</div>
              <div className="text-sm text-gray-500">Age 2-11</div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                data-testid="decrease-children"
                onClick={() => updateCount('children', -1)}
                disabled={passengers.children <= 0}
                className="h-10 w-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Minus className="h-4 w-4" />
              </button>
              <span data-testid="children-count" className="w-8 text-center font-medium">{passengers.children}</span>
              <button
                data-testid="increase-children"
                onClick={() => updateCount('children', 1)}
                disabled={passengers.children >= 9}
                className="h-10 w-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Infants */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Infants</div>
              <div className="text-sm text-gray-500">Under 2</div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                data-testid="decrease-infants"
                onClick={() => updateCount('infants', -1)}
                disabled={passengers.infants <= 0}
                className="h-10 w-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Minus className="h-4 w-4" />
              </button>
              <span data-testid="infants-count" className="w-8 text-center font-medium">{passengers.infants}</span>
              <button
                data-testid="increase-infants"
                onClick={() => updateCount('infants', 1)}
                disabled={passengers.infants >= 9}
                className="h-10 w-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t">
          <button
            data-testid="done-button"
            onClick={onClose}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
