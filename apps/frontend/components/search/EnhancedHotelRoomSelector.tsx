"use client"

import { X, Plus, Minus } from 'lucide-react'
import { useState } from 'react'

type RoomType = 'Standard' | 'Deluxe' | 'Suite'

interface Room {
  adults: number
  children: number[]
  roomType: RoomType
  ac: boolean
}

interface EnhancedHotelRoomData {
  rooms: Room[]
}

interface EnhancedHotelRoomSelectorProps {
  data: EnhancedHotelRoomData
  onUpdate: (data: EnhancedHotelRoomData) => void
  onClose: () => void
}

export default function EnhancedHotelRoomSelector({
  data,
  onUpdate,
  onClose,
}: EnhancedHotelRoomSelectorProps) {
  const [local, setLocal] = useState<EnhancedHotelRoomData>(data)

  const ROOM_TYPES: RoomType[] = ['Standard', 'Deluxe', 'Suite']

  const addRoom = () => {
    if (local.rooms.length < 5) {
      setLocal({
        rooms: [...local.rooms, { adults: 2, children: [], roomType: 'Standard', ac: true }],
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

  const updateRoom = (index: number, patch: Partial<Room>) => {
    setLocal({
      rooms: local.rooms.map((room, i) =>
        i === index ? { ...room, ...patch } : room
      ),
    })
  }

  const updateRoomAdults = (roomIndex: number, delta: number) => {
    const room = local.rooms[roomIndex]
    const newAdults = Math.max(1, Math.min(8, room.adults + delta))
    updateRoom(roomIndex, { adults: newAdults })
  }

  const addChild = (roomIndex: number) => {
    const room = local.rooms[roomIndex]
    if (room.children.length < 6) {
      updateRoom(roomIndex, { children: [...room.children, 8] })
    }
  }

  const removeChild = (roomIndex: number, childIndex: number) => {
    const room = local.rooms[roomIndex]
    updateRoom(roomIndex, {
      children: room.children.filter((_, ci) => ci !== childIndex),
    })
  }

  const updateChildAge = (roomIndex: number, childIndex: number, age: number) => {
    const room = local.rooms[roomIndex]
    updateRoom(roomIndex, {
      children: room.children.map((a, ci) => (ci === childIndex ? age : a)),
    })
  }

  const handleDone = () => {
    onUpdate(local)
    onClose()
  }

  const getTotalGuests = () => {
    return local.rooms.reduce((sum, room) => sum + room.adults + room.children.length, 0)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl mx-4 max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <div>
            <h3 className="text-xl font-semibold">Rooms & Guests</h3>
            <p className="text-sm text-gray-500">
              {local.rooms.length} {local.rooms.length === 1 ? 'room' : 'rooms'} • {getTotalGuests()} guests
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {local.rooms.map((room, roomIndex) => (
            <div key={roomIndex} className="border border-gray-200 rounded-xl p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-lg">Room {roomIndex + 1}</h4>
                {local.rooms.length > 1 && (
                  <button
                    onClick={() => removeRoom(roomIndex)}
                    className="text-red-500 hover:text-red-700 text-sm font-medium"
                  >
                    Remove Room
                  </button>
                )}
              </div>

              {/* Room Type Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Room Type</label>
                <select
                  value={room.roomType}
                  onChange={(e) => updateRoom(roomIndex, { roomType: e.target.value as RoomType })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {ROOM_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              {/* AC Toggle */}
              <div className="mb-4">
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={room.ac}
                    onChange={(e) => updateRoom(roomIndex, { ac: e.target.checked })}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Air Conditioned (AC)</span>
                </label>
              </div>

              {/* Adults */}
              <div className="flex items-center justify-between mb-3 pb-3 border-b border-gray-200">
                <div>
                  <div className="font-medium text-sm">Adults</div>
                  <div className="text-xs text-gray-500">Age 12+</div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => updateRoomAdults(roomIndex, -1)}
                    disabled={room.adults <= 1}
                    className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center disabled:opacity-30 hover:bg-gray-100"
                  >
                    <Minus className="h-3 w-3" />
                  </button>
                  <span className="w-8 text-center text-sm font-medium">{room.adults}</span>
                  <button
                    onClick={() => updateRoomAdults(roomIndex, 1)}
                    disabled={room.adults >= 8}
                    className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center disabled:opacity-30 hover:bg-gray-100"
                  >
                    <Plus className="h-3 w-3" />
                  </button>
                </div>
              </div>

              {/* Children */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <div className="font-medium text-sm">Children</div>
                    <div className="text-xs text-gray-500">Age 0-17</div>
                  </div>
                  <button
                    onClick={() => addChild(roomIndex)}
                    disabled={room.children.length >= 6}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-30"
                  >
                    Add Child
                  </button>
                </div>
                {room.children.length === 0 && (
                  <p className="text-xs text-gray-400 text-center py-2">No children</p>
                )}
                <div className="space-y-2">
                  {room.children.map((age, childIndex) => (
                    <div key={childIndex} className="flex items-center gap-2">
                      <span className="text-xs font-medium w-16">Child {childIndex + 1}</span>
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
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}

          <button
            onClick={addRoom}
            disabled={local.rooms.length >= 5}
            className="w-full py-3 border-2 border-dashed border-gray-300 rounded-xl text-sm text-gray-600 hover:border-blue-500 hover:text-blue-600 disabled:opacity-30 transition-colors font-medium"
          >
            + Add Another Room
          </button>
        </div>

        <div className="sticky bottom-0 bg-white border-t px-6 py-4 rounded-b-2xl">
          <button
            onClick={handleDone}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            Done ({local.rooms.length} {local.rooms.length === 1 ? 'room' : 'rooms'}, {getTotalGuests()} guests)
          </button>
        </div>
      </div>
    </div>
  )
}
