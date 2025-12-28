"use client"

/**
 * Navigation - Top Navigation Bar
 * 
 * Uses URL as single source of truth for active service:
 * - On home page: reads from ?tab= param
 * - On service pages: reads from pathname
 * 
 * Clicking a service:
 * - On home page: updates ?tab= param (keeps user on home)
 * - Elsewhere: navigates to service page
 */

import Link from 'next/link'
import { usePathname, useSearchParams, useRouter } from 'next/navigation'
import { Plane, Hotel, Train, Bus } from 'lucide-react'

type ServiceType = 'flights' | 'trains' | 'buses' | 'hotels'

interface NavItem {
  service: ServiceType
  label: string
  icon: typeof Plane
  href: string
}

const navItems: NavItem[] = [
  { service: 'flights', label: 'Flights', icon: Plane, href: '/' },
  { service: 'trains', label: 'Trains', icon: Train, href: '/trains' },
  { service: 'buses', label: 'Buses', icon: Bus, href: '/buses' },
  { service: 'hotels', label: 'Hotels', icon: Hotel, href: '/hotels' },
]

export default function Navigation() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const router = useRouter()
  
  /**
   * Determine if a nav item is active
   * Uses both pathname and tab param for home page
   */
  const isActive = (item: NavItem): boolean => {
    const tabParam = searchParams.get('tab')
    
    // On home page
    if (pathname === '/') {
      // If tab param exists, use it
      if (tabParam) {
        return item.service === tabParam
      }
      // Default: flights is active on home with no tab
      return item.service === 'flights'
    }
    
    // On service-specific pages
    if (item.href === '/') {
      // Flights link active if on flights results page
      return pathname.startsWith('/flights')
    }
    
    return pathname === item.href || pathname.startsWith(item.href + '/')
  }
  
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
    <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
            <Plane className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-display font-bold text-gray-900">TravelSearch</span>
          </Link>
          
          <nav className="flex items-center space-x-1 md:space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = isActive(item)
              
              return (
                <Link
                  key={item.service}
                  href={item.href}
                  onClick={(e) => handleClick(e, item)}
                  className={`
                    flex items-center space-x-1 md:space-x-2 px-2 md:px-4 py-2 rounded-lg
                    transition-all duration-200 font-medium text-sm md:text-base
                    ${active 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                    }
                  `}
                  aria-current={active ? 'page' : undefined}
                >
                  <Icon className="h-4 w-4" />
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
