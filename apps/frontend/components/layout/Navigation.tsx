"use client"

/**
 * Navigation - Top Navigation Bar
 * 
 * STRICT TAB ORDER: Flights → Buses → Trains → Hotels
 * 
 * Uses URL as single source of truth for active service:
 * - On home page: reads from ?tab= param
 * - On service pages: reads from pathname
 * 
 * CONTEXT-AWARE THEMING:
 * - Active tab gets service-specific accent color
 * - Inactive tabs are neutral gray
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

// STRICT ORDER: Flights → Buses → Trains → Hotels (matches SERVICE_ORDER)
const navItems: NavItem[] = [
  { service: 'flights', label: 'Flights', icon: Plane, href: '/' },
  { service: 'buses', label: 'Buses', icon: Bus, href: '/buses' },
  { service: 'trains', label: 'Trains', icon: Train, href: '/trains' },
  { service: 'hotels', label: 'Hotels', icon: Hotel, href: '/hotels' },
]

// Service-specific accent colors (inline for reliability)
const serviceAccentClasses: Record<ServiceType, { active: string; icon: string }> = {
  flights: { 
    active: 'bg-[#E8F0E9] text-[#6B8F71]', 
    icon: 'text-[#6B8F71]' 
  },
  buses: { 
    active: 'bg-[#F9EDE6] text-[#C47A4A]', 
    icon: 'text-[#C47A4A]' 
  },
  trains: { 
    active: 'bg-[#EEF1E8] text-[#7A8B5C]', 
    icon: 'text-[#7A8B5C]' 
  },
  hotels: { 
    active: 'bg-[#F9F3E6] text-[#C9A24D]', 
    icon: 'text-[#C9A24D]' 
  },
}

export default function Navigation() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const router = useRouter()
  
  /**
   * Determine active service from URL
   */
  const getActiveService = (): ServiceType => {
    const tabParam = searchParams.get('tab') as ServiceType | null
    
    // On home page
    if (pathname === '/') {
      return tabParam && SERVICE_ORDER.includes(tabParam) ? tabParam : 'flights'
    }
    
    // On service-specific pages
    if (pathname.startsWith('/flights')) return 'flights'
    if (pathname.startsWith('/buses')) return 'buses'
    if (pathname.startsWith('/trains')) return 'trains'
    if (pathname.startsWith('/hotels')) return 'hotels'
    
    return 'flights'
  }
  
  const activeService = getActiveService()
  
  /**
   * Handle nav item click
   * On home page: just update tab param (no page navigation)
   * Elsewhere: navigate to service page
   */
  const handleClick = (e: React.MouseEvent, item: NavItem) => {
    // Only intercept on home page
    if (pathname === '/') {
      e.preventDefault()
      
      // Update URL with new tab param
      const params = new URLSearchParams(searchParams.toString())
      params.set('tab', item.service)
      router.push(`/?${params.toString()}`, { scroll: false })
    }
    // For other pages, let the Link component handle navigation normally
  }
  
  return (
    <header className="border-b border-[#E6E1D8] bg-white/90 backdrop-blur-sm sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link 
            href="/" 
            className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
          >
            <div className={`p-1.5 rounded-lg ${serviceAccentClasses[activeService].active}`}>
              <Plane className={`h-6 w-6 sm:h-7 sm:w-7 ${serviceAccentClasses[activeService].icon}`} />
            </div>
            <span className="text-lg sm:text-2xl font-display font-bold text-[#2B2B2B] hidden xs:inline">
              TravelSearch
            </span>
          </Link>
          
          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-0.5 sm:space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = item.service === activeService
              const colors = serviceAccentClasses[item.service]
              
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
                      ? colors.active
                      : 'text-[#6B6B6B] hover:text-[#2B2B2B] hover:bg-[#F3EFEA]'
                    }
                  `}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon className={`h-4 w-4 sm:h-5 sm:w-5 ${isActive ? colors.icon : ''}`} />
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
