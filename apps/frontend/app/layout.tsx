import type { Metadata, Viewport } from 'next'
import { Inter, Space_Grotesk } from 'next/font/google'
import './globals.css'
import { JsonLd } from '@/components/seo/JsonLd'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const spaceGrotesk = Space_Grotesk({ subsets: ['latin'], variable: '--font-display' })

// Default metadata for all pages
export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://travelsearch.com'),
  title: {
    default: 'Compare Flights, Trains, Buses & Hotels | TravelSearch',
    template: '%s | TravelSearch',
  },
  description: 'Search and compare flights, trains, buses, and hotels from trusted travel partners. No hidden fees. Find the best deals instantly.',
  keywords: ['flight comparison', 'train booking', 'bus tickets', 'hotel comparison', 'travel search', 'cheap flights', 'India travel'],
  authors: [{ name: 'TravelSearch' }],
  creator: 'TravelSearch',
  publisher: 'TravelSearch',
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
  icons: {
    icon: '/favicon.svg',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/manifest.json',
  openGraph: {
    type: 'website',
    locale: 'en_IN',
    siteName: 'TravelSearch',
    title: 'Compare Flights, Trains, Buses & Hotels | TravelSearch',
    description: 'Search and compare flights, trains, buses, and hotels from trusted travel partners. No hidden fees.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Compare Flights, Trains, Buses & Hotels | TravelSearch',
    description: 'Search and compare flights, trains, buses, and hotels from trusted travel partners.',
  },
  alternates: {
    canonical: '/',
  },
  verification: {
    // Add when ready: google: 'your-google-verification-code',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#2563eb',
}

import ErrorBoundary from '@/components/ErrorBoundary'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        {/* Preconnect to partner domains for faster redirects */}
        <link rel="preconnect" href="https://www.makemytrip.com" />
        <link rel="preconnect" href="https://www.goibibo.com" />
        <link rel="dns-prefetch" href="https://www.makemytrip.com" />
        <link rel="dns-prefetch" href="https://www.goibibo.com" />
      </head>
      <body className={`${inter.variable} ${spaceGrotesk.variable} font-sans antialiased`}>
        <JsonLd />
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  )
}
