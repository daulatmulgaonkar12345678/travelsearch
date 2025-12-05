import type { Meta, StoryObj } from '@storybook/react'
import ProviderOfferCard from './ProviderOfferCard'

const meta: Meta<typeof ProviderOfferCard> = {
  title: 'Results/ProviderOfferCard',
  component: ProviderOfferCard,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
}

export default meta
type Story = StoryObj<typeof ProviderOfferCard>

export const Default: Story = {
  args: {
    provider: {
      name: 'Expedia',
      price: 8500,
      deep_link: 'https://expedia.com/book',
      rating: 88,
    },
    currency: 'INR',
    onSelect: () => console.log('Provider selected'),
  },
}

export const WithPromo: Story = {
  args: {
    provider: {
      name: 'MakeMyTrip',
      price: 7200,
      deep_link: 'https://makemytrip.com/book',
      rating: 85,
      promo: 'Save ₹500 with code FLIGHT500',
    },
    currency: 'INR',
    onSelect: () => console.log('Provider selected'),
  },
}

export const HighRating: Story = {
  args: {
    provider: {
      name: 'Booking.com',
      price: 8900,
      deep_link: 'https://booking.com',
      rating: 92,
      trust_bullets: ['Best price guarantee', 'Instant confirmation', 'Free cancellation'],
    },
    currency: 'INR',
    onSelect: () => console.log('Provider selected'),
  },
}

export const LowRating: Story = {
  args: {
    provider: {
      name: 'Budget Travel',
      price: 6500,
      deep_link: 'https://budgettravel.com',
      rating: 65,
    },
    currency: 'INR',
    onSelect: () => console.log('Provider selected'),
  },
}
