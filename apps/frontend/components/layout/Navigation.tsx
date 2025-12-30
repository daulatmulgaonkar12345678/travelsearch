"use client"

/**
 * Navigation - Top Navigation Bar
 * 
 * ONE COLOR RULE: Blue (#2563EB) is the ONLY selection indicator
 * 
 * STRICT TAB ORDER: Flights → Buses → Trains → Hotels
 * 
 * Selected tab: Blue icon, blue text, blue bottom border
 * Unselected tab: Gray icon, gray text, no border
 */

import Link from 'next/link'
import { usePathname, useSearchParams, useRouter } from 'next/navigation'
import { Plane, Hotel, Train, Bus } from 'lucide-react'
import { SERVICE_ORDER, type ServiceType } from '@/lib/theme'

interface NavItem {
  service: ServiceType
  label: string
  icon: typeof Plane
  href: string
}

// STRICT ORDER: Flights → Buses → Trains → Hotels
const navItems: NavItem[] = [
  { service: 'flights', label: 'Flights', icon: Plane, href: '/' },
  { service: 'buses', label: 'Buses', icon: Bus, href: '/buses' },
  { service: 'trains', label: 'Trains', icon: Train, href: '/trains' },
  { service: 'hotels', label: 'Hotels', icon: Hotel, href: '/hotels' },
]

export default function Navigation() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const router = useRouter()
  
  const getActiveService = (): ServiceType => {
    const tabParam = searchParams.get('tab') as ServiceType | null
    
    if (pathname === '/') {
      return tabParam && SERVICE_ORDER.includes(tabParam) ? tabParam : 'flights'
    }
    
    if (pathname.startsWith('/flights')) return 'flights'
    if (pathname.startsWith('/buses')) return 'buses'
    if (pathname.startsWith('/trains')) return 'trains'
    if (pathname.startsWith('/hotels')) return 'hotels'
    
    return 'flights'
  }
  
  const activeService = getActiveService()
  
  const handleClick = (e: React.MouseEvent, item: NavItem) => {
    if (pathname === '/') {
      e.preventDefault()
      const params = new URLSearchParams(searchParams.toString())
      params.set('tab', item.service)
      router.push(`/?${params.toString()}`, { scroll: false })
    }
  }
  
  return (
    <header className="border-b border-gray-200 bg-white sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          {/* Logo - Always blue */}
          <Link 
            href="/" 
            className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
          >
            <div className="p-1.5 rounded-lg bg-blue-50">
              <Plane className="h-6 w-6 sm:h-7 sm:w-7 text-blue-600" />
            </div>
            <span className="text-lg sm:text-2xl font-display font-bold text-gray-900 hidden xs:inline">
              TravelSearch
            </span>
          </Link>
          
          {/* Navigation Tabs - ONE COLOR RULE: Blue = Selected */}
          <nav className="flex items-center space-x-0.5 sm:space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = item.service === activeService
              
              return (
                <Link
                  key={item.service}
                  href={item.href}
                  onClick={(e) => handleClick(e, item)}
                  className={`
                    flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 md:px-4 py-2 rounded-lg
                    transition-all duration-200 font-medium text-xs sm:text-sm md:text-base
                    min-h-[40px] min-w-[40px] justify-center sm:justify-start
                    ${isActive 
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }
                  `}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon className={`h-4 w-4 sm:h-5 sm:w-5 ${isActive ? 'text-blue-600' : ''}`} />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}
