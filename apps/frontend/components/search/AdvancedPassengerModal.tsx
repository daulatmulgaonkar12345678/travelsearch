'use client'

import { X, Plus, Minus } from 'lucide-react'
import { useState } from 'react'

interface Child {
  age: number
}

interface PassengerData {
  adults: number
  children: Child[]
  infants: number
}

interface AdvancedPassengerModalProps {
  passengers: PassengerData
  onUpdate: (passengers: PassengerData) => void
  onClose: () => void
}

export default function AdvancedPassengerModal({
  passengers,
  onUpdate,
  onClose,
}: AdvancedPassengerModalProps) {
  const [local, setLocal] = useState<PassengerData>(passengers)

  const updateAdults = (delta: number) => {
    const newAdults = Math.max(1, Math.min(9, local.adults + delta))
    setLocal({ ...local, adults: newAdults })
  }

  const updateInfants = (delta: number) => {
    const newInfants = Math.max(0, Math.min(local.adults, local.infants + delta))
    setLocal({ ...local, infants: newInfants })
  }

  const addChild = () => {
    if (local.children.length < 8) {
      setLocal({ ...local, children: [...local.children, { age: 5 }] })
    }
  }

  const removeChild = (index: number) => {
    setLocal({
      ...local,
      children: local.children.filter((_, i) => i !== index),
    })
  }

  const updateChildAge = (index: number, age: number) => {
    setLocal({
      ...local,
      children: local.children.map((child, i) =>
        i === index ? { age } : child
      ),
    })
  }

  const handleDone = () => {
    onUpdate(local)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h3 className="text-xl font-semibold">Passengers</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Adults */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Adults</div>
              <div className="text-sm text-gray-500">Age 12+</div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => updateAdults(-1)}
                disabled={local.adults <= 1}
                className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center disabled:opacity-30 hover:bg-gray-100"
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="w-8 text-center font-medium">{local.adults}</span>
              <button
                onClick={() => updateAdults(1)}
                disabled={local.adults >= 9}
                className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center disabled:opacity-30 hover:bg-gray-100"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Children */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="font-medium">Children</div>
                <div className="text-sm text-gray-500">Age 2-11</div>
              </div>
              <button
                onClick={addChild}
                disabled={local.children.length >= 8}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-30"
              >
                Add Child
              </button>
            </div>
            {local.children.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-2">No children</p>
            )}
            {local.children.map((child, index) => (
              <div key={index} className="flex items-center gap-3 mb-2">
                <span className="text-sm font-medium">Child {index + 1}</span>
                <select
                  value={child.age}
                  onChange={(e) => updateChildAge(index, Number(e.target.value))}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  {Array.from({ length: 10 }, (_, i) => i + 2).map((age) => (
                    <option key={age} value={age}>
                      {age} years old
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => removeChild(index)}
                  className="text-red-500 hover:text-red-700"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Infants */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Infants</div>
              <div className="text-sm text-gray-500">Under 2 (on lap)</div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => updateInfants(-1)}
                disabled={local.infants <= 0}
                className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center disabled:opacity-30 hover:bg-gray-100"
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="w-8 text-center font-medium">{local.infants}</span>
              <button
                onClick={() => updateInfants(1)}
                disabled={local.infants >= local.adults}
                className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center disabled:opacity-30 hover:bg-gray-100"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg">
            Maximum {local.adults} infant(s) allowed (one per adult)
          </div>
        </div>

        <div className="sticky bottom-0 bg-white border-t px-6 py-4">
          <button
            onClick={handleDone}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
