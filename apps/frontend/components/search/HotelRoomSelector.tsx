'use client'

import { X, Plus, Minus, Users } from 'lucide-react'
import { useState } from 'react'

interface RoomGuests {
  adults: number
  children: number[]
}

interface HotelRoomData {
  rooms: RoomGuests[]
}

interface HotelRoomSelectorProps {
  data: HotelRoomData
  onUpdate: (data: HotelRoomData) => void
  onClose: () => void
}

export default function HotelRoomSelector({
  data,
  onUpdate,
  onClose,
}: HotelRoomSelectorProps) {
  const [local, setLocal] = useState<HotelRoomData>(data)

  const addRoom = () => {
    if (local.rooms.length < 5) {
      setLocal({
        rooms: [...local.rooms, { adults: 2, children: [] }],
      })
    }
  }

  const removeRoom = (index: number) => {
    if (local.rooms.length > 1) {
      setLocal({
        rooms: local.rooms.filter((_, i) => i !== index),
      })
    }
  }

  const updateRoomAdults = (roomIndex: number, delta: number) => {
    setLocal({
      rooms: local.rooms.map((room, i) =>
        i === roomIndex
          ? { ...room, adults: Math.max(1, Math.min(8, room.adults + delta)) }
          : room
      ),
    })
  }

  const addChild = (roomIndex: number) => {
    setLocal({
      rooms: local.rooms.map((room, i) =>
        i === roomIndex && room.children.length < 6
          ? { ...room, children: [...room.children, 8] }
          : room
      ),
    })
  }

  const removeChild = (roomIndex: number, childIndex: number) => {
    setLocal({
      rooms: local.rooms.map((room, i) =>
        i === roomIndex
          ? { ...room, children: room.children.filter((_, ci) => ci !== childIndex) }
          : room
      ),
    })
  }

  const updateChildAge = (roomIndex: number, childIndex: number, age: number) => {
    setLocal({
      rooms: local.rooms.map((room, i) =>
        i === roomIndex
          ? {
              ...room,
              children: room.children.map((a, ci) => (ci === childIndex ? age : a)),
            }
          : room
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
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h3 className="text-xl font-semibold">Rooms & Guests</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {local.rooms.map((room, roomIndex) => (
            <div key={roomIndex} className="border border-gray-200 rounded-xl p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold">Room {roomIndex + 1}</h4>
                {local.rooms.length > 1 && (
                  <button
                    onClick={() => removeRoom(roomIndex)}
                    className="text-red-500 hover:text-red-700 text-sm"
                  >
                    Remove Room
                  </button>
                )}
              </div>

              {/* Adults */}
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="font-medium text-sm">Adults</div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => updateRoomAdults(roomIndex, -1)}
                    disabled={room.adults <= 1}
                    className="w-7 h-7 rounded-full border border-gray-300 flex items-center justify-center disabled:opacity-30 hover:bg-gray-100"
                  >
                    <Minus className="h-3 w-3" />
                  </button>
                  <span className="w-6 text-center text-sm font-medium">{room.adults}</span>
                  <button
                    onClick={() => updateRoomAdults(roomIndex, 1)}
                    disabled={room.adults >= 8}
                    className="w-7 h-7 rounded-full border border-gray-300 flex items-center justify-center disabled:opacity-30 hover:bg-gray-100"
                  >
                    <Plus className="h-3 w-3" />
                  </button>
                </div>
              </div>

              {/* Children */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium text-sm">Children</div>
                  <button
                    onClick={() => addChild(roomIndex)}
                    disabled={room.children.length >= 6}
                    className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-30"
                  >
                    Add Child
                  </button>
                </div>
                {room.children.length === 0 && (
                  <p className="text-xs text-gray-400 text-center py-2">No children</p>
                )}
                {room.children.map((age, childIndex) => (
                  <div key={childIndex} className="flex items-center gap-2 mb-2">
                    <span className="text-xs">Child {childIndex + 1}</span>
                    <select
                      value={age}
                      onChange={(e) => updateChildAge(roomIndex, childIndex, Number(e.target.value))}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs"
                    >
                      {Array.from({ length: 18 }, (_, i) => i).map((a) => (
                        <option key={a} value={a}>
                          {a === 0 ? 'Under 1' : `${a} year${a > 1 ? 's' : ''}`}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() => removeChild(roomIndex, childIndex)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}

          <button
            onClick={addRoom}
            disabled={local.rooms.length >= 5}
            className="w-full py-2 border-2 border-dashed border-gray-300 rounded-xl text-sm text-gray-600 hover:border-blue-500 hover:text-blue-600 disabled:opacity-30 transition-colors"
          >
            + Add Another Room
          </button>
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
