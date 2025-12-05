import type { Meta, StoryObj } from '@storybook/react'
import HotelResultCard from './HotelResultCard'

const meta: Meta<typeof HotelResultCard> = {
  title: 'Results/HotelResultCard',
  component: HotelResultCard,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
}

export default meta
type Story = StoryObj<typeof HotelResultCard>

const mockHotel = {
  offer_id: 'TRIP-Mumbai-001',
  provider: 'trip.com',
  hotel_name: 'Grand Plaza Hotel',
  address: '123 Main Street',
  city: 'Mumbai',
  rating: 4.5,
  review_score: 8.7,
  review_count: 1243,
  price_per_night: 4500,
  total_price: 13500,
  currency: 'INR',
  amenities: ['Free WiFi', 'Pool', 'Gym', 'Restaurant', 'Bar', '24h Reception'],
  room_type: 'Deluxe King Room',
  cancellation_policy: 'Free cancellation until 24h before check-in',
  images: [
    'https://via.placeholder.com/400x300?text=Hotel+Room',
    'https://via.placeholder.com/400x300?text=Hotel+Pool',
  ],
  deep_link: 'https://mock-trip.com/book?hotel=001',
}

export const Default: Story = {
  args: {
    hotel: mockHotel,
    onProviderSelect: (provider, hotel) => {
      console.log('Provider selected:', provider, hotel)
    },
  },
}

export const WithMultipleProviders: Story = {
  args: {
    hotel: mockHotel,
    providers: [
      {
        provider: 'trip.com',
        price: 13500,
        deep_link: 'https://trip.com/book',
      },
      {
        provider: 'agoda',
        price: 12800,
        deep_link: 'https://agoda.com/book',
      },
      {
        provider: 'booking.com',
        price: 14200,
        deep_link: 'https://booking.com/book',
      },
    ],
    onProviderSelect: (provider) => console.log('Selected:', provider),
  },
}

export const LuxuryHotel: Story = {
  args: {
    hotel: {
      ...mockHotel,
      hotel_name: 'Luxury Suites & Spa',
      rating: 5,
      review_score: 9.3,
      review_count: 2104,
      price_per_night: 8900,
      total_price: 26700,
      room_type: 'Executive Suite',
      amenities: ['Free WiFi', 'Pool', 'Spa', 'Gym', 'Fine Dining', 'Concierge', 'Valet'],
    },
    onProviderSelect: (provider) => console.log('Selected:', provider),
  },
}

export const BudgetHotel: Story = {
  args: {
    hotel: {
      ...mockHotel,
      hotel_name: 'City View Inn',
      rating: 3,
      review_score: 7.2,
      review_count: 456,
      price_per_night: 1800,
      total_price: 5400,
      room_type: 'Standard Double Room',
      amenities: ['Free WiFi', 'Breakfast'],
      cancellation_policy: 'Non-refundable',
    },
    onProviderSelect: (provider) => console.log('Selected:', provider),
  },
}
