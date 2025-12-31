/**
 * SEO IMPLEMENTATION GUIDE
 * Complete technical specification for TravelSearch platform
 */

// ============================================================
// 1. ROOT LAYOUT - GLOBAL SEO CONFIGURATION
// ============================================================

// File: app/layout.tsx

import { Metadata, Viewport } from 'next'

export const metadata: Metadata = {
  metadataBase: new URL('https://travelsearch.in'),
  
  // Primary metadata
  title: {
    default: 'TravelSearch | Compare Flights from Multiple Providers',
    template: '%s | TravelSearch'
  },
  description: 'Independent flight comparison platform. Search and compare flights from multiple airlines and booking providers. Find the best option for your travel dates.',
  
  // Keywords (still useful for some search engines)
  keywords: [
    'flight comparison',
    'compare flights',
    'cheap flights',
    'flight search',
    'airline tickets',
    'travel comparison',
    'flight deals'
  ],
  
  // Author and creator
  authors: [{ name: 'TravelSearch' }],
  creator: 'TravelSearch',
  publisher: 'TravelSearch',
  
  // Robots
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  
  // OpenGraph
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://travelsearch.in',
    siteName: 'TravelSearch',
    title: 'TravelSearch | Compare Flights from Multiple Providers',
    description: 'Independent flight comparison platform. Compare flights, prices, and schedules from multiple airlines and booking providers.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'TravelSearch - Flight Comparison Platform',
      }
    ],
  },
  
  // Twitter Card
  twitter: {
    card: 'summary_large_image',
    title: 'TravelSearch | Compare Flights from Multiple Providers',
    description: 'Independent flight comparison platform. Find and compare flights from multiple sources.',
    images: ['/twitter-image.png'],
    creator: '@travelsearch',
  },
  
  // Verification tags
  verification: {
    google: 'YOUR_GOOGLE_VERIFICATION_CODE',
    yandex: 'YOUR_YANDEX_VERIFICATION_CODE',
    bing: 'YOUR_BING_VERIFICATION_CODE',
  },
  
  // Alternate languages (if applicable)
  alternates: {
    canonical: 'https://travelsearch.in',
    languages: {
      'en-US': 'https://travelsearch.in',
      'en-GB': 'https://travelsearch.in/en-gb',
    },
  },
  
  // Application configuration
  applicationName: 'TravelSearch',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'TravelSearch',
  },
  
  // Format detection
  formatDetection: {
    telephone: false,
  },
}

export const viewport: Viewport = {
  themeColor: '#2563eb',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
}

// ============================================================
// 2. JSON-LD STRUCTURED DATA
// ============================================================

// File: components/seo/StructuredData.tsx

interface OrganizationSchema {
  '@context': 'https://schema.org'
  '@type': 'Organization'
  name: string
  url: string
  logo: string
  description: string
  sameAs: string[]
  contactPoint: {
    '@type': 'ContactPoint'
    contactType: string
    email: string
  }
}

interface WebSiteSchema {
  '@context': 'https://schema.org'
  '@type': 'WebSite'
  name: string
  url: string
  potentialAction: {
    '@type': 'SearchAction'
    target: {
      '@type': 'EntryPoint'
      urlTemplate: string
    }
    'query-input': string
  }
}

interface BreadcrumbSchema {
  '@context': 'https://schema.org'
  '@type': 'BreadcrumbList'
  itemListElement: Array<{
    '@type': 'ListItem'
    position: number
    name: string
    item?: string
  }>
}

// Organization Schema (for homepage)
export function OrganizationStructuredData() {
  const schema: OrganizationSchema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'TravelSearch',
    url: 'https://travelsearch.in',
    logo: 'https://travelsearch.in/logo.png',
    description: 'Independent flight comparison platform helping travelers find and compare flights from multiple providers.',
    sameAs: [
      'https://twitter.in/travelsearch',
      'https://facebook.in/travelsearch',
      'https://linkedin.in/company/travelsearch'
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'Customer Service',
      email: 'support@travelsearch.in'
    }
  }
  
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

// Website Search Schema
export function WebsiteSearchStructuredData() {
  const schema: WebSiteSchema = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'TravelSearch',
    url: 'https://travelsearch.in',
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: 'https://travelsearch.in/flights/results?origin={origin}&destination={destination}'
      },
      'query-input': 'required name=origin name=destination'
    }
  }
  
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

// Breadcrumb Schema (for result/detail pages)
export function BreadcrumbStructuredData({ items }: { items: Array<{ name: string; url?: string }> }) {
  const schema: BreadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      ...(item.url && { item: item.url })
    }))
  }
  
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

// ============================================================
// 3. PAGE-SPECIFIC SEO IMPLEMENTATION
// ============================================================

// Homepage (app/page.tsx)
export const homepageMetadata: Metadata = {
  title: 'TravelSearch | Compare Flights from Multiple Providers',
  description: 'Search and compare flights from multiple airlines and booking providers. Find the best flight options for your travel dates. Independent comparison platform.',
  alternates: {
    canonical: 'https://travelsearch.in'
  },
  openGraph: {
    title: 'TravelSearch - Flight Comparison Platform',
    description: 'Compare flights from multiple providers. Find the best option for your journey.',
    url: 'https://travelsearch.in',
  }
}

// Flight Results Page (app/flights/results/page.tsx)
export function generateFlightResultsMetadata(
  origin: string,
  destination: string,
  date: string
): Metadata {
  return {
    title: `Flights from ${origin} to ${destination} - ${date}`,
    description: `Compare flights from ${origin} to ${destination} on ${date}. View prices, departure times, and airlines. Book directly with providers.`,
    alternates: {
      canonical: `https://travelsearch.in/flights/results?origin=${origin}&destination=${destination}&date=${date}`
    },
    openGraph: {
      title: `${origin} to ${destination} Flights`,
      description: `Compare available flights and find the best option for your journey.`,
    },
    robots: {
      index: true,
      follow: true
    }
  }
}

// Route Static Pages (app/routes/[origin]-to-[destination]/page.tsx)
export function generateRouteMetadata(
  originCity: string,
  destinationCity: string,
  originCode: string,
  destinationCode: string
): Metadata {
  return {
    title: `${originCity} to ${destinationCity} Flights (${originCode}-${destinationCode}) | Compare & Book`,
    description: `Compare flights from ${originCity} (${originCode}) to ${destinationCity} (${destinationCode}). View schedules, prices, and book directly with airlines.`,
    alternates: {
      canonical: `https://travelsearch.in/routes/${originCode.toLowerCase()}-to-${destinationCode.toLowerCase()}`
    },
    openGraph: {
      title: `${originCity} to ${destinationCity} Flights`,
      description: `Find and compare flights between ${originCity} and ${destinationCity}.`,
      type: 'website'
    }
  }
}

// ============================================================
// 4. PERFORMANCE OPTIMIZATIONS
// ============================================================

// next.config.js additions

module.exports = {
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    domains: ['travelsearch.in'],
  },
  
  // Compression
  compress: true,
  
  // Headers for caching and security
  async headers() {
    return [
      {
        source: '/:all*(svg|jpg|png|webp|avif)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
        ],
      },
    ]
  },
}

// ============================================================
// 5. ACCESSIBILITY IMPLEMENTATION
// ============================================================

// Best practices checklist:

/*
✅ Semantic HTML
- Use proper heading hierarchy (h1 → h2 → h3)
- Use <nav>, <main>, <footer>, <article>, <section>
- Use <button> for actions, <a> for navigation

✅ ARIA Labels
- Add aria-label to icon-only buttons
- Use aria-describedby for form validation
- Implement aria-live regions for dynamic content

✅ Keyboard Navigation
- All interactive elements keyboard-accessible
- Visible focus indicators
- Logical tab order

✅ Color Contrast
- WCAG AA minimum (4.5:1 for normal text)
- AAA preferred (7:1 for normal text)
- Don't rely on color alone

✅ Forms
- Label all inputs properly
- Associate error messages with fields
- Provide clear validation feedback

✅ Images
- Alt text for all meaningful images
- Decorative images: alt=""
- Complex images: aria-describedby

✅ Skip Links
- "Skip to main content" link
- Hidden but keyboard-accessible
*/

// Example Skip Link Component
export function SkipLink() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded"
    >
      Skip to main content
    </a>
  )
}

// ============================================================
// 6. SITEMAP GENERATION
// ============================================================

// File: app/sitemap.ts

import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://travelsearch.in'
  
  // Static pages
  const staticPages = [
    '',
    '/about-us',
    '/contact',
    '/privacy-policy',
    '/terms-and-conditions',
    '/service-disclaimer',
    '/affiliate-disclosure',
  ].map(route => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: route === '' ? 1.0 : 0.5,
  }))
  
  // Dynamic route pages (generate from database or static list)
  const routePages = [
    // Example: { origin: 'DEL', destination: 'BOM', originCity: 'Delhi', destCity: 'Mumbai' }
    // Generate dynamically from your popular routes
  ].map(route => ({
    url: `${baseUrl}/routes/${route.origin.toLowerCase()}-to-${route.destination.toLowerCase()}`,
    lastModified: new Date(),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))
  
  return [...staticPages, ...routePages]
}

// ============================================================
// 7. ROBOTS.TXT
// ============================================================

// File: app/robots.ts

import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/admin/',
          '/api/',
          '/internal/',
          '/*.json',
          '/flights/results?*', // Prevent indexing of search result pages
        ],
      },
    ],
    sitemap: 'https://travelsearch.in/sitemap.xml',
  }
}

// ============================================================
// 8. CRAWLABILITY CHECKLIST
// ============================================================

/*
✅ Server-Side Rendering (SSR)
- Use Next.js App Router
- Generate pages server-side for better SEO
- Ensure content is in HTML (not just client-side JS)

✅ Clean URLs
- Use descriptive paths: /routes/del-to-bom
- Avoid query parameters for main content
- Implement canonical URLs

✅ Internal Linking
- Link between related pages
- Use descriptive anchor text
- Create logical site hierarchy

✅ Page Speed
- Optimize images (WebP, AVIF)
- Minimize JavaScript
- Use CDN for static assets
- Implement lazy loading

✅ Mobile-First
- Responsive design
- Touch-friendly targets (44x44px minimum)
- Fast mobile performance

✅ Structured Data
- Organization schema on homepage
- WebSite search schema
- Breadcrumb schema on result pages

✅ Security
- HTTPS everywhere
- Secure headers
- CSP policy

✅ International
- hreflang tags if multi-language
- Geo-targeting in Search Console
- Currency/language selectors
*/
