import type { Meta, StoryObj } from '@storybook/react'
import FilterSidebar from './FilterSidebar'
import { useState } from 'react'

const meta: Meta<typeof FilterSidebar> = {
  title: 'Results/FilterSidebar',
  component: FilterSidebar,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
}

export default meta
type Story = StoryObj<typeof FilterSidebar>

const FilterSidebarWithState = () => {
  const [filters, setFilters] = useState({
    stops: [],
    baggage: [],
    departureTime: [0, 23] as [number, number],
    arrivalTime: [0, 23] as [number, number],
    duration: [0, 24] as [number, number],
    airlines: [],
    emissions: false,
  })

  return <FilterSidebar filters={filters} onFilterChange={setFilters} />
}

export const Default: Story = {
  render: () => <FilterSidebarWithState />,
}

export const WithSelectedFilters: Story = {
  args: {
    filters: {
      stops: ['Non-stop'],
      baggage: ['Checked Baggage'],
      departureTime: [6, 18],
      arrivalTime: [0, 23],
      duration: [0, 5],
      airlines: ['IndiGo', 'Vistara'],
      emissions: true,
    },
    onFilterChange: (filters) => console.log('Filters changed:', filters),
  },
}
