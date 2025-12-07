"use client"

interface SortTabsProps {
  activeSort: 'best' | 'cheapest' | 'fastest'
  onSortChange: (sort: 'best' | 'cheapest' | 'fastest') => void
  prices?: {
    best?: number
    cheapest?: number
    fastest?: number
  }
  currency?: string
}

const formatPrice = (price: number) => {
  return Math.round(price).toLocaleString()
}

export default function SortTabs({ activeSort, onSortChange, prices, currency = 'INR' }: SortTabsProps) {
  const tabs = [
    { id: 'best' as const, label: 'Best', description: 'Optimized picks' },
    { id: 'cheapest' as const, label: 'Cheapest', description: 'Lowest price' },
    { id: 'fastest' as const, label: 'Fastest', description: 'Shortest duration' },
  ]

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="flex">
        {tabs.map((tab) => {
          const isActive = activeSort === tab.id
          const price = prices?.[tab.id]

          return (
            <button
              key={tab.id}
              onClick={() => onSortChange(tab.id)}
              className={`
                flex-1 px-6 py-4 text-center transition-all border-b-2
                ${isActive
                  ? 'border-blue-600 text-blue-600 bg-blue-50'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }
              `}
            >
              <div className="font-semibold text-lg">{tab.label}</div>
              <div className="text-xs mt-1 text-gray-600">
                {price !== undefined 
                  ? `${tab.description} – from ${currency} ${formatPrice(price)}`
                  : `${tab.description} – no flights`
                }
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
