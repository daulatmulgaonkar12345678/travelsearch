/**
 * Sitemap Generator (Enhanced)
 * 
 * Generates comprehensive XML sitemap for search engine indexing.
 * Includes:
 * - Static pages (homepage, info pages)
 * - Flight route SEO pages
 * - Hotel city SEO pages  
 * - Bus route SEO pages
 * - Train route SEO pages
 * 
 * INDEXED: All static SEO-optimized pages
 * EXCLUDED: Dynamic results pages, admin pages, API routes
 */

import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://travelsearch.com'
  const lastModified = new Date()

  // ============================================
  // STATIC PAGES
  // ============================================
  const staticPages = [
    { path: '', priority: 1.0, changeFrequency: 'daily' as const },
    { path: '/flights', priority: 0.9, changeFrequency: 'daily' as const },
    { path: '/trains', priority: 0.9, changeFrequency: 'daily' as const },
    { path: '/buses', priority: 0.9, changeFrequency: 'daily' as const },
    { path: '/hotels', priority: 0.9, changeFrequency: 'daily' as const },
    { path: '/about-us', priority: 0.5, changeFrequency: 'monthly' as const },
    { path: '/affiliate-disclosure', priority: 0.3, changeFrequency: 'monthly' as const },
    { path: '/service-disclaimer', priority: 0.3, changeFrequency: 'monthly' as const },
    { path: '/privacy-policy', priority: 0.3, changeFrequency: 'monthly' as const },
    { path: '/terms-and-conditions', priority: 0.3, changeFrequency: 'monthly' as const },
    { path: '/contact', priority: 0.5, changeFrequency: 'monthly' as const },
  ]

  // ============================================
  // FLIGHT ROUTES (High traffic India routes)
  // ============================================
  const flightRoutes = [
    // Metro to Metro
    '/flights/delhi-to-mumbai',
    '/flights/mumbai-to-delhi',
    '/flights/bangalore-to-delhi',
    '/flights/delhi-to-bangalore',
    '/flights/bangalore-to-mumbai',
    '/flights/mumbai-to-bangalore',
    '/flights/chennai-to-delhi',
    '/flights/delhi-to-chennai',
    '/flights/chennai-to-bangalore',
    '/flights/bangalore-to-chennai',
    '/flights/hyderabad-to-bangalore',
    '/flights/bangalore-to-hyderabad',
    '/flights/hyderabad-to-delhi',
    '/flights/delhi-to-hyderabad',
    '/flights/kolkata-to-delhi',
    '/flights/delhi-to-kolkata',
    '/flights/kolkata-to-bangalore',
    '/flights/bangalore-to-kolkata',
    // Popular Leisure Routes
    '/flights/delhi-to-goa',
    '/flights/mumbai-to-goa',
    '/flights/bangalore-to-goa',
    // Tier 2 City Routes
    '/flights/pune-to-delhi',
    '/flights/pune-to-mumbai',
    '/flights/ahmedabad-to-mumbai',
    '/flights/ahmedabad-to-delhi',
    '/flights/jaipur-to-delhi',
    '/flights/kochi-to-bangalore',
    '/flights/trivandrum-to-bangalore',
    '/flights/indore-to-mumbai',
  ]

  // ============================================
  // HOTEL CITIES (Top India destinations)
  // ============================================
  const hotelCities = [
    '/hotels/mumbai',
    '/hotels/delhi',
    '/hotels/bangalore',
    '/hotels/goa',
    '/hotels/pune',
    '/hotels/hyderabad',
    '/hotels/chennai',
    '/hotels/kolkata',
    '/hotels/jaipur',
    '/hotels/kochi',
  ]

  // ============================================
  // BUS ROUTES (High traffic India routes)
  // ============================================
  const busRoutes = [
    // Maharashtra Routes
    '/buses/pune-to-mumbai',
    '/buses/mumbai-to-pune',
    '/buses/mumbai-to-goa',
    // South India Routes  
    '/buses/bangalore-to-chennai',
    '/buses/chennai-to-bangalore',
    '/buses/bangalore-to-mysore',
    '/buses/bangalore-to-hyderabad',
    // North India Routes
    '/buses/delhi-to-jaipur',
    '/buses/jaipur-to-delhi',
    '/buses/delhi-to-agra',
  ]

  // ============================================
  // TRAIN ROUTES (Major India routes)
  // ============================================
  const trainRoutes = [
    // Long Distance Premium Routes
    '/trains/mumbai-to-delhi',
    '/trains/delhi-to-mumbai',
    '/trains/kolkata-to-delhi',
    '/trains/delhi-to-kolkata',
    '/trains/chennai-to-delhi',
    '/trains/delhi-to-chennai',
    // Regional Routes
    '/trains/bangalore-to-chennai',
    '/trains/chennai-to-bangalore',
    '/trains/mumbai-to-pune',
    '/trains/pune-to-mumbai',
    '/trains/delhi-to-jaipur',
    '/trains/jaipur-to-delhi',
  ]

  // ============================================
  // BUILD SITEMAP ENTRIES
  // ============================================
  const entries: MetadataRoute.Sitemap = [
    // Static pages with custom priorities
    ...staticPages.map(({ path, priority, changeFrequency }) => ({
      url: `${baseUrl}${path}`,
      lastModified,
      changeFrequency,
      priority,
    })),
    
    // Flight routes (High priority - good search volume)
    ...flightRoutes.map((path) => ({
      url: `${baseUrl}${path}`,
      lastModified,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    })),
    
    // Hotel cities (High priority)
    ...hotelCities.map((path) => ({
      url: `${baseUrl}${path}`,
      lastModified,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    })),
    
    // Bus routes (Medium-high priority)
    ...busRoutes.map((path) => ({
      url: `${baseUrl}${path}`,
      lastModified,
      changeFrequency: 'weekly' as const,
      priority: 0.7,
    })),
    
    // Train routes (Medium-high priority)
    ...trainRoutes.map((path) => ({
      url: `${baseUrl}${path}`,
      lastModified,
      changeFrequency: 'weekly' as const,
      priority: 0.7,
    })),
  ]

  return entries
}
