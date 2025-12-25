import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Mumbai',
  originCode: 'BOM',
  destinationCity: 'Bangalore',
  destinationCode: 'BLR',
  content: {
    title: 'Flights from Mumbai to Bangalore',
    description: 'Search Mumbai to Bangalore flights. Compare fares on this major business route connecting India\'s financial and technology capitals.',
    flightInfo: 'The Mumbai to Bangalore route covers approximately 840 kilometers with typical flight times of 1 hour 45 minutes. This business-heavy corridor connects India\'s financial hub with its technology center. Kempegowda International Airport (BLR) in Bangalore serves as a major hub for South India connectivity.',
    travelTips: 'Bangalore airport is located about 40 km from the city center. The Kempegowda International Airport Express metro and various bus services provide city connectivity. Business travelers frequently use this route for day trips, with early morning and late evening flights being popular choices.',
    bestTime: 'As a business route, Mumbai-Bangalore sees consistent demand throughout the week with particularly high frequency on Monday mornings and Friday evenings. Comparing different times of day may show varying fare levels based on business travel patterns.',
  },
  relatedRoutes: [
    { slug: 'bangalore-to-mumbai', label: 'Bangalore to Mumbai' },
    { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi' },
    { slug: 'bangalore-to-delhi', label: 'Bangalore to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function MumbaiToBangaloreFlights() {
  return <RoutePageTemplate {...routeData} />
}
