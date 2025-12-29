/**
 * Sitemap Generator
 * 
 * Generates XML sitemap for search engine indexing.
 * Includes only static, indexable pages.
 * Dynamic results pages are excluded (noindex).
 * 
 * INDEXED: Homepage, popular routes, popular destinations, info pages
 * EXCLUDED: Results pages, pages with date/filter params
 */

import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://travelsearch.com'
  const lastModified = new Date()

  // Static pages
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

  // Flight route pages (20 India routes)
  const flightRoutes = [
    '/flights/delhi-to-mumbai',
    '/flights/delhi-to-goa',
    '/flights/mumbai-to-goa',
    '/flights/mumbai-to-bangalore',
    '/flights/mumbai-to-delhi',
    '/flights/bangalore-to-delhi',
    '/flights/bangalore-to-mumbai',
    '/flights/pune-to-delhi',
    '/flights/pune-to-mumbai',
    '/flights/chennai-to-bangalore',
    '/flights/chennai-to-delhi',
    '/flights/hyderabad-to-bangalore',
    '/flights/hyderabad-to-delhi',
    '/flights/ahmedabad-to-mumbai',
    '/flights/ahmedabad-to-delhi',
    '/flights/kolkata-to-delhi',
    '/flights/kolkata-to-bangalore',
    '/flights/jaipur-to-delhi',
    '/flights/kochi-to-bangalore',
    '/flights/trivandrum-to-bangalore',
    '/flights/indore-to-mumbai',
  ]

  // Hotel city pages (10 India cities)
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

  // Build sitemap entries
  const entries: MetadataRoute.Sitemap = [
    // Static pages with custom priorities
    ...staticPages.map(({ path, priority, changeFrequency }) => ({
      url: `${baseUrl}${path}`,
      lastModified,
      changeFrequency,
      priority,
    })),
    // Flight routes
    ...flightRoutes.map((path) => ({
      url: `${baseUrl}${path}`,
      lastModified,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    })),
    // Hotel cities
    ...hotelCities.map((path) => ({
      url: `${baseUrl}${path}`,
      lastModified,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    })),
  ]

  return entries
}
