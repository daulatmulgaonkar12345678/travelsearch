import type { Meta, StoryObj } from '@storybook/react'
import InterstitialRedirectModal from './InterstitialRedirectModal'
import { useState } from 'react'

const meta: Meta<typeof InterstitialRedirectModal> = {
  title: 'Common/InterstitialRedirectModal',
  component: InterstitialRedirectModal,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
}

export default meta
type Story = StoryObj<typeof InterstitialRedirectModal>

const InterstitialWithControl = (args: any) => {
  const [isOpen, setIsOpen] = useState(true)
  return (
    <div>
      <button
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg"
      >
        Open Interstitial
      </button>
      <InterstitialRedirectModal
        {...args}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </div>
  )
}

export const Default: Story = {
  render: (args) => <InterstitialWithControl {...args} />,
  args: {
    provider: 'Expedia',
    price: 8500,
    currency: 'INR',
    redirectUrl: 'https://expedia.com/book',
    countdownSeconds: 3,
  },
}

export const ShortCountdown: Story = {
  render: (args) => <InterstitialWithControl {...args} />,
  args: {
    provider: 'MakeMyTrip',
    price: 7200,
    currency: 'INR',
    redirectUrl: 'https://makemytrip.com/book',
    countdownSeconds: 1,
  },
}

export const HighPrice: Story = {
  render: (args) => <InterstitialWithControl {...args} />,
  args: {
    provider: 'Booking.com',
    price: 25000,
    currency: 'INR',
    redirectUrl: 'https://booking.com',
    countdownSeconds: 3,
  },
}
