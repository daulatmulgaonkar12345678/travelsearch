"use client"

/**
 * ServiceContext - Single Source of Truth for Active Service
 * 
 * Ensures UI consistency across:
 * - Top navigation
 * - Hero section tabs
 * - Search forms
 * 
 * State is synced with URL (?tab=xxx) for:
 * - Bookmarkable state
 * - Page refresh preservation
 * - Browser back/forward support
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'

export type ServiceType = 'flights' | 'trains' | 'buses' | 'hotels'

interface ServiceContextType {
  activeService: ServiceType
  setActiveService: (service: ServiceType) => void
  isServiceActive: (service: ServiceType) => boolean
}

const ServiceContext = createContext<ServiceContextType | null>(null)

// Map service to its dedicated page
const SERVICE_PAGES: Record<ServiceType, string> = {
  flights: '/',
  trains: '/trains',
  buses: '/buses',
  hotels: '/hotels',
}

// Map pathname back to service
const PATH_TO_SERVICE: Record<string, ServiceType> = {
  '/': 'flights',
  '/flights': 'flights',
  '/trains': 'trains',
  '/buses': 'buses',
  '/hotels': 'hotels',
}

export function ServiceProvider({ children, initialService }: { 
  children: ReactNode
  initialService?: ServiceType 
}) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  
  // Determine initial service from URL
  const getServiceFromUrl = useCallback((): ServiceType => {
    // First check ?tab= param (for home page tabs)
    const tabParam = searchParams.get('tab') as ServiceType | null
    if (tabParam && ['flights', 'trains', 'buses', 'hotels'].includes(tabParam)) {
      return tabParam
    }
    
    // Then check pathname
    const pathService = PATH_TO_SERVICE[pathname]
    if (pathService) {
      return pathService
    }
    
    // Check if pathname starts with a service path
    if (pathname.startsWith('/trains')) return 'trains'
    if (pathname.startsWith('/buses')) return 'buses'
    if (pathname.startsWith('/hotels')) return 'hotels'
    if (pathname.startsWith('/flights')) return 'flights'
    
    return initialService || 'flights'
  }, [pathname, searchParams, initialService])
  
  const [activeService, setActiveServiceState] = useState<ServiceType>(getServiceFromUrl)
  
  // Sync state when URL changes (browser back/forward)
  useEffect(() => {
    const urlService = getServiceFromUrl()
    if (urlService !== activeService) {
      setActiveServiceState(urlService)
    }
  }, [pathname, searchParams, getServiceFromUrl, activeService])
  
  // Update URL when service changes
  const setActiveService = useCallback((service: ServiceType) => {
    setActiveServiceState(service)
    
    // Only update URL if we're on the home page
    if (pathname === '/' || pathname === '') {
      const params = new URLSearchParams(searchParams.toString())
      params.set('tab', service)
      router.push(`/?${params.toString()}`, { scroll: false })
    }
  }, [pathname, searchParams, router])
  
  const isServiceActive = useCallback((service: ServiceType): boolean => {
    return activeService === service
  }, [activeService])
  
  return (
    <ServiceContext.Provider value={{ activeService, setActiveService, isServiceActive }}>
      {children}
    </ServiceContext.Provider>
  )
}

export function useService() {
  const context = useContext(ServiceContext)
  if (!context) {
    throw new Error('useService must be used within a ServiceProvider')
  }
  return context
}

/**
 * Hook for Navigation component to determine active state
 * Works with both pathname and tab params
 */
export function useNavigationActive() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  
  const isActive = useCallback((href: string, service: ServiceType): boolean => {
    // Check tab param first (for home page)
    const tabParam = searchParams.get('tab')
    if (pathname === '/' && tabParam) {
      if (href === '/' && tabParam === 'flights') return true
      if (href === '/trains' && tabParam === 'trains') return true
      if (href === '/buses' && tabParam === 'buses') return true
      if (href === '/hotels' && tabParam === 'hotels') return true
      return false
    }
    
    // Default: home page with no tab = flights
    if (pathname === '/' && !tabParam && href === '/') {
      return true
    }
    
    // Check pathname
    if (href === '/') {
      return pathname === '/' && !tabParam
    }
    
    return pathname === href || pathname.startsWith(href + '/')
  }, [pathname, searchParams])
  
  return { isActive }
}
