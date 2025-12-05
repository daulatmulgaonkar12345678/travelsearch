import type { Meta, StoryObj } from '@storybook/react'
import ResultCard from './ResultCard'

const meta: Meta<typeof ResultCard> = {
  title: 'Results/ResultCard',
  component: ResultCard,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
}

export default meta
type Story = StoryObj<typeof ResultCard>

const mockOffer = {
  offer_id: 'AMD-BOM-PNQ-001',
  provider: 'amadeus',
  price: 8500,
  currency: 'INR',
  segments: [
    {
      departure_airport: 'BOM',
      arrival_airport: 'PNQ',
      departure_time: '2025-12-15T09:30:00',
      arrival_time: '2025-12-15T11:00:00',
      carrier_code: '6E',
      carrier_name: 'IndiGo',
      flight_number: '6E-2341',
      aircraft_type: 'A320',
      duration_minutes: 90,
    },
  ],
  total_duration_minutes: 90,
  stops: 0,
  baggage_allowance: '15 kg checked',
  cabin_class: 'economy',
  emissions_kg: 75.5,
  rating: 85,
  providers: [
    {
      name: 'Expedia',
      price: 8500,
      deep_link: 'https://expedia.com/book',
      rating: 88,
      trust_bullets: ['Price match guarantee', 'Instant confirmation'],
    },
    {
      name: 'MakeMyTrip',
      price: 8200,
      deep_link: 'https://makemytrip.com/book',
      rating: 85,
      promo: 'Save ₹300 with code FLIGHT300',
      trust_bullets: ['24/7 customer support', 'Easy cancellation'],
    },
  ],
}

export const Default: Story = {
  args: {
    offer: mockOffer,
    onProviderSelect: (provider, offer) => {
      console.log('Provider selected:', provider, offer)
    },
  },
}

export const WithBestBadge: Story = {
  args: {
    offer: mockOffer,
    badge: 'best',
    onProviderSelect: (provider) => console.log('Selected:', provider),
  },
}

export const WithCheapestBadge: Story = {
  args: {
    offer: { ...mockOffer, price: 4800 },
    badge: 'cheapest',
    onProviderSelect: (provider) => console.log('Selected:', provider),
  },
}

export const WithFastestBadge: Story = {
  args: {
    offer: { ...mockOffer, total_duration_minutes: 85 },
    badge: 'fastest',
    onProviderSelect: (provider) => console.log('Selected:', provider),
  },
}

export const OneStopFlight: Story = {
  args: {
    offer: {
      ...mockOffer,
      stops: 1,
      total_duration_minutes: 340,
      segments: [
        {
          departure_airport: 'BOM',
          arrival_airport: 'DEL',
          departure_time: '2025-12-15T14:20:00',
          arrival_time: '2025-12-15T16:10:00',
          carrier_code: 'AI',
          carrier_name: 'Air India',
          flight_number: 'AI-445',
          aircraft_type: 'A320',
          duration_minutes: 110,
        },
        {
          departure_airport: 'DEL',
          arrival_airport: 'PNQ',
          departure_time: '2025-12-15T18:30:00',
          arrival_time: '2025-12-15T20:00:00',
          carrier_code: 'AI',
          carrier_name: 'Air India',
          flight_number: 'AI-892',
          aircraft_type: 'A321',
          duration_minutes: 90,
        },
      ],
    },
    onProviderSelect: (provider) => console.log('Selected:', provider),
  },
}

export const MultipleProviders: Story = {
  args: {
    offer: {
      ...mockOffer,
      providers: [
        {
          name: 'Expedia',
          price: 8500,
          deep_link: 'https://expedia.com',
          rating: 88,
        },
        {
          name: 'MakeMyTrip',
          price: 8200,
          deep_link: 'https://makemytrip.com',
          rating: 85,
          promo: 'Save ₹300',
        },
        {
          name: 'Cleartrip',
          price: 8350,
          deep_link: 'https://cleartrip.com',
          rating: 82,
        },
      ],
    },
    onProviderSelect: (provider) => console.log('Selected:', provider),
  },
}
