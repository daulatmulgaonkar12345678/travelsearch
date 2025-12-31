/**
 * JSON-LD Schema for Flight Route Pages
 * 
 * Implements:
 * - Product schema (for price comparison)
 * - BreadcrumbList schema (navigation path)
 * - FAQPage schema (for rich snippets)
 */

export interface FlightRouteSchemaProps {
  originCity: string
  originCode: string
  destinationCity: string
  destinationCode: string
  estimatedPrice?: {
    min: number
    max: number
    currency: string
  }
  faqs?: Array<{
    question: string
    answer: string
  }>
}

export function generateFlightRouteSchema(props: FlightRouteSchemaProps) {
  const {
    originCity,
    originCode,
    destinationCity,
    destinationCode,
    estimatedPrice = { min: 3000, max: 15000, currency: 'INR' },
    faqs = [],
  } = props

  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://travelsearch.in'
  const routeSlug = `${originCity.toLowerCase()}-to-${destinationCity.toLowerCase()}`
  const pageUrl = `${baseUrl}/flights/${routeSlug}`

  // Product Schema (shows price range in search results)
  const productSchema = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: `${originCity} to ${destinationCity} Flights`,
    description: `Compare flight prices from ${originCity} (${originCode}) to ${destinationCity} (${destinationCode}). Find cheap fares across multiple airlines and booking sites.`,
    brand: {
      '@type': 'Brand',
      name: 'TravelSearch',
    },
    offers: {
      '@type': 'AggregateOffer',
      priceCurrency: estimatedPrice.currency,
      lowPrice: estimatedPrice.min,
      highPrice: estimatedPrice.max,
      offerCount: '10+',
      availability: 'https://schema.org/InStock',
      seller: {
        '@type': 'Organization',
        name: 'TravelSearch',
      },
    },
    url: pageUrl,
  }

  // BreadcrumbList Schema (navigation trail)
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: baseUrl,
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Flights',
        item: `${baseUrl}/flights`,
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: `${originCity} to ${destinationCity}`,
        item: pageUrl,
      },
    ],
  }

  // FAQPage Schema (for rich snippets)
  const faqSchema = faqs.length > 0 ? {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  } : null

  return { productSchema, breadcrumbSchema, faqSchema }
}

export default function FlightRouteSchema(props: FlightRouteSchemaProps) {
  const { productSchema, breadcrumbSchema, faqSchema } = generateFlightRouteSchema(props)

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(productSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />
      {faqSchema && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
        />
      )}
    </>
  )
}
