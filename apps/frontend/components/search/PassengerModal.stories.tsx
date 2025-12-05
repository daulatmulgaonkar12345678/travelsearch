import type { Meta, StoryObj } from '@storybook/react'
import PassengerModal from './PassengerModal'

const meta: Meta<typeof PassengerModal> = {
  title: 'Search/PassengerModal',
  component: PassengerModal,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
}

export default meta
type Story = StoryObj<typeof PassengerModal>

export const Default: Story = {
  args: {
    passengers: {
      adults: 1,
      children: 0,
      infants: 0,
    },
    onUpdate: (passengers) => console.log('Updated passengers:', passengers),
    onClose: () => console.log('Modal closed'),
  },
}

export const WithChildren: Story = {
  args: {
    passengers: {
      adults: 2,
      children: 2,
      infants: 1,
    },
    onUpdate: (passengers) => console.log('Updated passengers:', passengers),
    onClose: () => console.log('Modal closed'),
  },
}
