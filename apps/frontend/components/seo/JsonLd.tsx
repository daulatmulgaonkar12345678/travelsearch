/**
 * JSON-LD Structured Data Components
 * 
 * Implements Schema.org structured data for better SEO:
 * - WebSite schema for homepage
 * - Organization schema for brand
 * - BreadcrumbList for navigation
 * 
 * DO NOT add Product or Offer schema (we're a meta-search, not a seller)
 */

export function JsonLd() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://travelsearch.com'
  
  // WebSite schema with SearchAction
  const websiteSchema = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'TravelSearch',
    url: baseUrl,
    description: 'Compare flights, trains, buses, and hotels from trusted travel partners.',
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${baseUrl}/?tab=flights`,
      },
      'query-input': 'required name=search_term_string',
    },
  }
  
  // Organization schema
  const organizationSchema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'TravelSearch',
    url: baseUrl,
    logo: `${baseUrl}/favicon.svg`,
    description: 'Travel meta-search platform comparing flights, trains, buses, and hotels from verified partners.',
    sameAs: [],
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'customer service',
      url: `${baseUrl}/contact`,
    },
  }
  
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
      />
    </>
  )
}

/**
 * Breadcrumb JSON-LD for route pages
 */
export function BreadcrumbJsonLd({ items }: { items: { name: string; url: string }[] }) {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://travelsearch.com'
  
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url.startsWith('http') ? item.url : `${baseUrl}${item.url}`,
    })),
  }
  
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
    />
  )
}

/**
 * FAQ JSON-LD for pages with FAQs
 */
export function FAQJsonLd({ faqs }: { faqs: { question: string; answer: string }[] }) {
  const faqSchema = {
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
  }
  
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
    />
  )
}
