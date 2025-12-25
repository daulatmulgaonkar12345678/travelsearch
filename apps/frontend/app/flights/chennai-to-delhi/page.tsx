import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Chennai',
  originCode: 'MAA',
  destinationCity: 'Delhi',
  destinationCode: 'DEL',
  content: {
    title: 'Flights from Chennai to Delhi',
    description: 'Compare Chennai to Delhi flights. Search across airlines connecting South India\'s major port city with the national capital.',
    flightInfo: 'Chennai to Delhi flights span approximately 1,760 kilometers with an average duration of 2 hours 50 minutes. This North-South corridor connects Chennai International Airport (MAA) with Indira Gandhi International Airport (DEL). The route serves business, government, and leisure travelers moving between these important metros.',
    travelTips: 'Delhi airport offers comprehensive connectivity via the Airport Express Metro. Chennai travelers should note the significant climate difference, particularly during winter months. Both cities have extensive public transport networks for onward travel from the airports.',
    bestTime: 'The Chennai-Delhi route sees year-round demand with variations during festival seasons and government calendar events. Summer months in Delhi (May-June) may see different travel patterns. Advance comparison of flights can help identify suitable options across different dates.',
  },
  relatedRoutes: [
    { slug: 'delhi-to-chennai', label: 'Delhi to Chennai' },
    { slug: 'chennai-to-bangalore', label: 'Chennai to Bangalore' },
    { slug: 'hyderabad-to-delhi', label: 'Hyderabad to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function ChennaiToDelhiFlights() {
  return <RoutePageTemplate {...routeData} />
}
