import type { Meta, StoryObj } from '@storybook/react'
import DateStrip from './DateStrip'

const meta: Meta<typeof DateStrip> = {
  title: 'Search/DateStrip',
  component: DateStrip,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
}

export default meta
type Story = StoryObj<typeof DateStrip>

export const Default: Story = {
  args: {
    onDateSelect: (date) => console.log('Selected date:', date),
  },
}

export const WithPriceData: Story = {
  args: {
    priceData: {
      '2025-12-15': 3500,
      '2025-12-16': 4200,
      '2025-12-17': 2900,
      '2025-12-18': 5100,
      '2025-12-19': 3800,
      '2025-12-20': 4500,
      '2025-12-21': 3200,
    },
    onDateSelect: (date) => console.log('Selected date:', date),
  },
}

export const WithSelectedDate: Story = {
  args: {
    selectedDate: new Date().toISOString().split('T')[0],
    onDateSelect: (date) => console.log('Selected date:', date),
  },
}
