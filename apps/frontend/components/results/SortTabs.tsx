"use client"

interface SortTabsProps {
  activeSort: 'best' | 'cheapest' | 'fastest'
  onSortChange: (sort: 'best' | 'cheapest' | 'fastest') => void
  counts?: {
    best: number
    cheapest: number
    fastest: number
  }
}

export default function SortTabs({ activeSort, onSortChange, counts }: SortTabsProps) {
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
          const count = counts?.[tab.id]

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
              <div className="text-xs mt-1">
                {isActive && count !== undefined ? `${count} results` : tab.description}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
