import { FlightValidator, HotelValidator, getTomorrowDate, getDaysFromNow } from '@/lib/validation'

describe('FlightValidator', () => {
  describe('validateOriginDestination', () => {
    it('should reject when origin equals destination', () => {
      const result = FlightValidator.validateOriginDestination('BOM', 'BOM')
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('must be different')
    })

    it('should reject when origin equals destination (case insensitive)', () => {
      const result = FlightValidator.validateOriginDestination('bom', 'BOM')
      expect(result.isValid).toBe(false)
    })

    it('should accept when origin and destination are different', () => {
      const result = FlightValidator.validateOriginDestination('BOM', 'DEL')
      expect(result.isValid).toBe(true)
      expect(result.error).toBeUndefined()
    })

    it('should reject when origin is empty', () => {
      const result = FlightValidator.validateOriginDestination('', 'DEL')
      expect(result.isValid).toBe(false)
    })
  })

  describe('validateDepartureDate', () => {
    it('should reject today as departure', () => {
      const today = new Date().toISOString().split('T')[0]
      const result = FlightValidator.validateDepartureDate(today)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('tomorrow')
    })

    it('should accept tomorrow as departure', () => {
      const tomorrow = getTomorrowDate()
      const result = FlightValidator.validateDepartureDate(tomorrow)
      expect(result.isValid).toBe(true)
    })

    it('should accept future dates', () => {
      const future = getDaysFromNow(30)
      const result = FlightValidator.validateDepartureDate(future)
      expect(result.isValid).toBe(true)
    })
  })

  describe('validateReturnDate', () => {
    it('should reject when return equals departure', () => {
      const tomorrow = getTomorrowDate()
      const result = FlightValidator.validateReturnDate(tomorrow, tomorrow)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('after')
    })

    it('should reject when return is before departure', () => {
      const tomorrow = getTomorrowDate()
      const dayAfter = getDaysFromNow(2)
      const result = FlightValidator.validateReturnDate(dayAfter, tomorrow)
      expect(result.isValid).toBe(false)
    })

    it('should accept when return is after departure', () => {
      const tomorrow = getTomorrowDate()
      const dayAfter = getDaysFromNow(2)
      const result = FlightValidator.validateReturnDate(tomorrow, dayAfter)
      expect(result.isValid).toBe(true)
    })
  })

  describe('validateMulticitySegments', () => {
    it('should reject less than 2 segments', () => {
      const result = FlightValidator.validateMulticitySegments([{ origin: 'BOM', destination: 'DEL', date: getTomorrowDate() }])
      expect(result.isValid).toBe(false)
    })

    it('should reject when segment has origin === destination', () => {
      const segments = [
        { origin: 'BOM', destination: 'BOM', date: getTomorrowDate() },
        { origin: 'DEL', destination: 'BLR', date: getDaysFromNow(2) }
      ]
      const result = FlightValidator.validateMulticitySegments(segments)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('must be different')
    })

    it('should reject when dates are not in order', () => {
      const tomorrow = getTomorrowDate()
      const segments = [
        { origin: 'BOM', destination: 'DEL', date: getDaysFromNow(2) },
        { origin: 'DEL', destination: 'BLR', date: tomorrow }
      ]
      const result = FlightValidator.validateMulticitySegments(segments)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('after')
    })

    it('should accept valid multicity segments', () => {
      const segments = [
        { origin: 'BOM', destination: 'DEL', date: getTomorrowDate() },
        { origin: 'DEL', destination: 'BLR', date: getDaysFromNow(2) },
        { origin: 'BLR', destination: 'MAA', date: getDaysFromNow(3) }
      ]
      const result = FlightValidator.validateMulticitySegments(segments)
      expect(result.isValid).toBe(true)
    })
  })

  describe('validatePassengers', () => {
    it('should reject 0 adults', () => {
      const result = FlightValidator.validatePassengers(0, 2, 0)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('1 adult')
    })

    it('should reject more infants than adults', () => {
      const result = FlightValidator.validatePassengers(2, 0, 3)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('infants cannot exceed')
    })

    it('should reject more than 9 total passengers', () => {
      const result = FlightValidator.validatePassengers(5, 3, 2)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('Maximum 9')
    })

    it('should accept valid passenger configuration', () => {
      const result = FlightValidator.validatePassengers(2, 2, 1)
      expect(result.isValid).toBe(true)
    })
  })
})

describe('HotelValidator', () => {
  describe('validateCheckInDate', () => {
    it('should reject today as check-in', () => {
      const today = new Date().toISOString().split('T')[0]
      const result = HotelValidator.validateCheckInDate(today)
      expect(result.isValid).toBe(false)
    })

    it('should accept tomorrow as check-in', () => {
      const tomorrow = getTomorrowDate()
      const result = HotelValidator.validateCheckInDate(tomorrow)
      expect(result.isValid).toBe(true)
    })
  })

  describe('validateCheckOutDate', () => {
    it('should reject same-day checkout', () => {
      const tomorrow = getTomorrowDate()
      const result = HotelValidator.validateCheckOutDate(tomorrow, tomorrow)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('1 day after')
    })

    it('should enforce minimum 1 night stay', () => {
      const tomorrow = getTomorrowDate()
      const result = HotelValidator.validateCheckOutDate(tomorrow, tomorrow)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('1 night')
    })

    it('should accept valid checkout (1+ nights)', () => {
      const checkIn = getTomorrowDate()
      const checkOut = getDaysFromNow(2)
      const result = HotelValidator.validateCheckOutDate(checkIn, checkOut)
      expect(result.isValid).toBe(true)
    })
  })

  describe('validateRoomConfiguration', () => {
    it('should reject 0 rooms', () => {
      const result = HotelValidator.validateRoomConfiguration([])
      expect(result.isValid).toBe(false)
    })

    it('should reject room with 0 adults', () => {
      const rooms = [{ adults: 0, children: [5, 8] }]
      const result = HotelValidator.validateRoomConfiguration(rooms)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('1 adult')
    })

    it('should reject room with more than 8 total guests', () => {
      const rooms = [{ adults: 5, children: [5, 6, 7, 8] }]
      const result = HotelValidator.validateRoomConfiguration(rooms)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('Maximum 8')
    })

    it('should accept valid room configuration', () => {
      const rooms = [
        { adults: 2, children: [5, 8] },
        { adults: 1, children: [] }
      ]
      const result = HotelValidator.validateRoomConfiguration(rooms)
      expect(result.isValid).toBe(true)
    })
  })
})
