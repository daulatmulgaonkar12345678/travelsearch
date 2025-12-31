/**
 * JSON-LD Schema for Hotel City Pages
 * 
 * Implements:
 * - Hotel schema with AggregateOffer
 * - BreadcrumbList schema
 * - FAQPage schema
 */

export interface HotelCitySchemaProps {
  cityName: string
  cityCode: string
  estimatedPrice?: {
    min: number
    max: number
    currency: string
  }
  starRating?: number
  faqs?: Array<{
    question: string
    answer: string
  }>
}

export function generateHotelCitySchema(props: HotelCitySchemaProps) {
  const {
    cityName,
    cityCode,
    estimatedPrice = { min: 1500, max: 25000, currency: 'INR' },
    starRating = 3,
    faqs = [],
  } = props

  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://travelsearch.in'
  const citySlug = cityName.toLowerCase().replace(/\s+/g, '-')
  const pageUrl = `${baseUrl}/hotels/${citySlug}`

  // Hotel Schema with AggregateOffer
  const hotelSchema = {
    '@context': 'https://schema.org',
    '@type': 'Hotel',
    name: `Hotels in ${cityName}`,
    description: `Compare hotel prices in ${cityName}, India. Find accommodation from budget to luxury options across multiple booking platforms.`,
    address: {
      '@type': 'PostalAddress',
      addressLocality: cityName,
      addressCountry: 'IN',
    },
    starRating: {
      '@type': 'Rating',
      ratingValue: starRating,
    },
    priceRange: `${estimatedPrice.currency} ${estimatedPrice.min} - ${estimatedPrice.max}`,
    offers: {
      '@type': 'AggregateOffer',
      priceCurrency: estimatedPrice.currency,
      lowPrice: estimatedPrice.min,
      highPrice: estimatedPrice.max,
      offerCount: '50+',
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
        name: 'Hotels',
        item: `${baseUrl}/hotels`,
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: `Hotels in ${cityName}`,
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

  return { hotelSchema, breadcrumbSchema, faqSchema }
}

export default function HotelCitySchema(props: HotelCitySchemaProps) {
  const { hotelSchema, breadcrumbSchema, faqSchema } = generateHotelCitySchema(props)

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(hotelSchema) }}
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
