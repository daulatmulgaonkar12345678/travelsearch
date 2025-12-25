/**
 * Layout for Flight Results Page
 * 
 * Sets noindex, nofollow for dynamic search results pages.
 * These pages should not be indexed by search engines.
 */

import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Flight Search Results | TravelSearch',
  description: 'Compare flight prices and book with our travel partners.',
  robots: {
    index: false,
    follow: false,
  },
}

export default function FlightResultsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
