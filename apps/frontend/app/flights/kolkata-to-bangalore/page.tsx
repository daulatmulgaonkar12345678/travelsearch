import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Kolkata',
  originCode: 'CCU',
  destinationCity: 'Bangalore',
  destinationCode: 'BLR',
  content: {
    title: 'Flights from Kolkata to Bangalore',
    description: 'Compare Kolkata to Bangalore flights. Search fares connecting Eastern India with the South Indian technology hub.',
    flightInfo: 'The Kolkata to Bangalore route spans approximately 1,560 kilometers with flight times around 2 hours 30 minutes. This route connects two of India\'s major metropolitan areas, serving IT professionals, business travelers, and those visiting family. Both cities have well-developed aviation infrastructure.',
    travelTips: 'Bangalore airport is located on the northern outskirts with metro and bus connectivity to the city. Kolkata travelers should plan for ground transport time in Bangalore. The IT corridors of Electronic City and Whitefield require separate transport planning from the airport.',
    bestTime: 'IT industry hiring cycles and project timelines can influence travel patterns on this route. Festival seasons in both regions affect demand differently. Comparing options across multiple days can help identify suitable fare levels.',
  },
  relatedRoutes: [
    { slug: 'bangalore-to-kolkata', label: 'Bangalore to Kolkata' },
    { slug: 'kolkata-to-delhi', label: 'Kolkata to Delhi' },
    { slug: 'chennai-to-bangalore', label: 'Chennai to Bangalore' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function KolkataToBangaloreFlights() {
  return <RoutePageTemplate {...routeData} />
}
