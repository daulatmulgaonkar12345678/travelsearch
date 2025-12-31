/**
 * JSON-LD Schema for Bus Route Pages
 * 
 * Implements:
 * - Product schema (for price comparison)
 * - BreadcrumbList schema
 * - FAQPage schema
 */

export interface BusRouteSchemaProps {
  originCity: string
  destinationCity: string
  estimatedPrice?: {
    min: number
    max: number
    currency: string
  }
  duration?: string
  faqs?: Array<{
    question: string
    answer: string
  }>
}

export function generateBusRouteSchema(props: BusRouteSchemaProps) {
  const {
    originCity,
    destinationCity,
    estimatedPrice = { min: 300, max: 2500, currency: 'INR' },
    duration = '4-8 hours',
    faqs = [],
  } = props

  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://travelsearch.com'
  const routeSlug = `${originCity.toLowerCase()}-to-${destinationCity.toLowerCase()}`
  const pageUrl = `${baseUrl}/buses/${routeSlug}`

  // Product Schema
  const productSchema = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: `${originCity} to ${destinationCity} Bus Tickets`,
    description: `Compare bus ticket prices from ${originCity} to ${destinationCity}. Find AC, Non-AC, Sleeper, and Seater buses across operators.`,
    brand: {
      '@type': 'Brand',
      name: 'TravelSearch',
    },
    offers: {
      '@type': 'AggregateOffer',
      priceCurrency: estimatedPrice.currency,
      lowPrice: estimatedPrice.min,
      highPrice: estimatedPrice.max,
      offerCount: '20+',
      availability: 'https://schema.org/InStock',
    },
    url: pageUrl,
  }

  // BreadcrumbList Schema
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
        name: 'Buses',
        item: `${baseUrl}/buses`,
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: `${originCity} to ${destinationCity}`,
        item: pageUrl,
      },
    ],
  }

  // FAQPage Schema
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

export default function BusRouteSchema(props: BusRouteSchemaProps) {
  const { productSchema, breadcrumbSchema, faqSchema } = generateBusRouteSchema(props)

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
