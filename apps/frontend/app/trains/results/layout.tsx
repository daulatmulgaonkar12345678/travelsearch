/**
 * Layout for Train Results Page
 * 
 * Sets noindex, nofollow for dynamic search results pages.
 * These pages should not be indexed by search engines.
 */

import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Train Search Results | TravelSearch',
  description: 'Compare train timings, fares, and book with our travel partners.',
  robots: {
    index: false,
    follow: false,
  },
}

export default function TrainResultsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
