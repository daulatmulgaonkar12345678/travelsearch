import type { Meta, StoryObj } from '@storybook/react'
import SearchBar from './SearchBar'

const meta: Meta<typeof SearchBar> = {
  title: 'Search/SearchBar',
  component: SearchBar,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
}

export default meta
type Story = StoryObj<typeof SearchBar>

export const Default: Story = {}

export const Mobile: Story = {
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
}
