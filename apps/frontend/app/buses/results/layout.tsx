/**
 * Layout for Bus Results Page
 * 
 * Sets noindex, nofollow for dynamic search results pages.
 * These pages should not be indexed by search engines.
 */

import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Bus Search Results | TravelSearch',
  description: 'Compare bus fares, operators, and book with our travel partners.',
  robots: {
    index: false,
    follow: false,
  },
}

export default function BusResultsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
