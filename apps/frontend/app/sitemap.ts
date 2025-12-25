/**
 * Sitemap Generator
 * 
 * Generates XML sitemap for search engine indexing.
 * Includes only static, indexable pages.
 * Dynamic results pages are excluded (noindex).
 */

import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://travelsearch.com' // Replace with actual domain
  const lastModified = new Date()

  // Static pages
  const staticPages = [
    '',
    '/about-us',
    '/affiliate-disclosure',
    '/service-disclaimer',
    '/privacy-policy',
    '/terms-and-conditions',
    '/contact',
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

  // Combine all URLs
  const allUrls = [...staticPages, ...flightRoutes, ...hotelCities]

  return allUrls.map((path) => ({
    url: `${baseUrl}${path}`,
    lastModified,
    changeFrequency: path === '' ? 'daily' : 'weekly',
    priority: path === '' ? 1.0 : path.startsWith('/flights/') || path.startsWith('/hotels/') ? 0.8 : 0.6,
  }))
}
