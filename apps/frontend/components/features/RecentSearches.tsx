/**
 * Unified Recent Searches Component
 * 
 * Displays recent searches across ALL transport modes on the homepage.
 * - Flights, Trains, Buses, Hotels all appear together
 * - Data persisted in localStorage automatically
 * - Shows last 12 searches (FIFO)
 * - Clicking a search re-runs it
 * - Different icons/colors per transport mode
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, X, Plane, Train, Bus, Hotel } from 'lucide-react'
import {
  getRecentSearches,
  clearRecentSearches,
  removeRecentSearch,
  formatSearchDate,
  buildSearchUrl,
  type RecentSearch,
  type TransportMode,
} from '@/lib/unifiedRecentSearchStore'

/**
 * Animation variants
 */
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.25,
      ease: [0.16, 1, 0.3, 1]
    }
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: {
      duration: 0.2,
      ease: 'easeOut'
    }
  }
}

/**
 * Mode configuration for icons and colors
 */
const MODE_CONFIG: Record<TransportMode, {
  icon: typeof Plane
  color: string
  bgColor: string
  hoverBg: string
  hoverBorder: string
}> = {
  flight: {
    icon: Plane,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50',
    hoverBg: 'hover:bg-blue-50/50',
    hoverBorder: 'hover:border-blue-300',
  },
  train: {
    icon: Train,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    hoverBg: 'hover:bg-blue-50/50',
    hoverBorder: 'hover:border-blue-300',
  },
  bus: {
    icon: Bus,
    color: 'text-orange-500',
    bgColor: 'bg-orange-50',
    hoverBg: 'hover:bg-orange-50/50',
    hoverBorder: 'hover:border-orange-300',
  },
  hotel: {
    icon: Hotel,
    color: 'text-purple-500',
    bgColor: 'bg-purple-50',
    hoverBg: 'hover:bg-purple-50/50',
    hoverBorder: 'hover:border-purple-300',
  },
}

export default function RecentSearches() {
  const router = useRouter()
  const [searches, setSearches] = useState<RecentSearch[]>([])
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    setSearches(getRecentSearches())
  }, [])

  const handleSearchClick = (search: RecentSearch) => {
    const url = buildSearchUrl(search)
    router.push(url)
  }

  const handleRemoveSearch = (e: React.MouseEvent, search: RecentSearch) => {
    e.stopPropagation()
    const updated = removeRecentSearch(search)
    setSearches(updated)
  }

  const handleClearAll = () => {
    clearRecentSearches()
    setSearches([])
  }

  // Don't render until mounted (avoid hydration mismatch)
  if (!mounted) {
    return null
  }

  // Empty state
  if (searches.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.2 }}
        className="text-center py-4"
      >
        <p className="text-sm text-gray-500">
          Your recent searches will appear here.
        </p>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-gray-400" />
          <h3 className="text-sm font-medium text-gray-700">Recent searches</h3>
        </div>
        <button
          onClick={handleClearAll}
          className="text-xs text-gray-500 hover:text-gray-700 transition-colors duration-200"
        >
          Clear all
        </button>
      </div>
      
      {/* Search chips */}
      <motion.div 
        className="flex flex-wrap gap-2"
        variants={containerVariants}
      >
        <AnimatePresence mode="popLayout">
          {searches.map((search) => {
            const config = MODE_CONFIG[search.mode] || MODE_CONFIG.flight
            const Icon = config.icon
            
            return (
              <motion.button
                key={`${search.mode}-${search.origin}-${search.destination}-${search.departureDate}-${search.timestamp}`}
                layout
                variants={itemVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleSearchClick(search)}
                className={`
                  group relative flex items-center gap-2 px-3 py-2
                  bg-white border border-gray-200 rounded-lg
                  ${config.hoverBorder} ${config.hoverBg}
                  transition-colors duration-200
                  shadow-sm hover:shadow
                `}
              >
                {/* Transport icon */}
                <Icon className={`w-3.5 h-3.5 text-gray-400 group-hover:${config.color} transition-colors`} />
                
                {/* Route */}
                <span className="text-sm font-medium text-gray-900">
                  {search.origin}
                  <span className="text-gray-400 mx-1">→</span>
                  {search.destination}
                </span>
                
                {/* Date */}
                <span className="text-xs text-gray-500 border-l border-gray-200 pl-2">
                  {formatSearchDate(search.departureDate)}
                  {search.returnDate && (search.mode === 'flight' || search.mode === 'hotel') && (
                    <> - {formatSearchDate(search.returnDate)}</>
                  )}
                </span>
                
                {/* Mode badge */}
                <span className={`text-xs px-1.5 py-0.5 rounded ${config.bgColor} ${config.color} font-medium capitalize`}>
                  {search.mode}
                </span>
                
                {/* Price (display only - for reference) */}
                {search.displayPrice && (
                  <span className="text-xs font-medium text-green-600 border-l border-gray-200 pl-2">
                    {search.displayCurrency === 'INR' ? '₹' : '$'}
                    {search.displayPrice.toLocaleString()}
                  </span>
                )}
                
                {/* Remove button */}
                <button
                  onClick={(e) => handleRemoveSearch(e, search)}
                  className="
                    ml-1 p-0.5 rounded-full
                    opacity-0 group-hover:opacity-100
                    text-gray-400 hover:text-gray-600 hover:bg-gray-100
                    transition-all duration-200
                  "
                  aria-label="Remove search"
                >
                  <X className="w-3 h-3" />
                </button>
              </motion.button>
            )
          })}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  )
}
