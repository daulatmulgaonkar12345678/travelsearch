/**
 * JSON-LD Schema for Train Route Pages
 * 
 * Implements:
 * - Product schema (for price comparison)
 * - BreadcrumbList schema
 * - FAQPage schema
 */

export interface TrainRouteSchemaProps {
  originCity: string
  originStation?: string
  destinationCity: string
  destinationStation?: string
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

export function generateTrainRouteSchema(props: TrainRouteSchemaProps) {
  const {
    originCity,
    destinationCity,
    estimatedPrice = { min: 200, max: 4000, currency: 'INR' },
    faqs = [],
  } = props

  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://travelsearch.com'
  const routeSlug = `${originCity.toLowerCase()}-to-${destinationCity.toLowerCase()}`
  const pageUrl = `${baseUrl}/trains/${routeSlug}`

  // Product Schema
  const productSchema = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: `${originCity} to ${destinationCity} Trains`,
    description: `Compare train options from ${originCity} to ${destinationCity}. Find Sleeper, AC, and General class tickets across booking platforms.`,
    brand: {
      '@type': 'Brand',
      name: 'TravelSearch',
    },
    offers: {
      '@type': 'AggregateOffer',
      priceCurrency: estimatedPrice.currency,
      lowPrice: estimatedPrice.min,
      highPrice: estimatedPrice.max,
      offerCount: '15+',
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
        name: 'Trains',
        item: `${baseUrl}/trains`,
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

export default function TrainRouteSchema(props: TrainRouteSchemaProps) {
  const { productSchema, breadcrumbSchema, faqSchema } = generateTrainRouteSchema(props)

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
