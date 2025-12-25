import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Ahmedabad',
  originCode: 'AMD',
  destinationCity: 'Delhi',
  destinationCode: 'DEL',
  content: {
    title: 'Flights from Ahmedabad to Delhi',
    description: 'Compare Ahmedabad to Delhi flights. Search across airlines connecting Gujarat with the national capital.',
    flightInfo: 'Ahmedabad to Delhi flights span approximately 780 kilometers with an average flight time of 1 hour 45 minutes. This route connects Gujarat\'s largest city with the NCR region, serving business travelers, government visitors, and those connecting to international flights. Both airports are well-equipped modern facilities.',
    travelTips: 'Delhi airport provides metro connectivity to the city center and major areas. Travelers from Ahmedabad should note seasonal weather variations in Delhi. Both cities have developing metro networks that serve their respective airports.',
    bestTime: 'This route maintains regular service throughout the year. Business and government-related travel keeps demand steady. Garba festival season (Navratri) may see increased outbound travel from Delhi to Gujarat, potentially affecting return flight patterns.',
  },
  relatedRoutes: [
    { slug: 'delhi-to-ahmedabad', label: 'Delhi to Ahmedabad' },
    { slug: 'ahmedabad-to-mumbai', label: 'Ahmedabad to Mumbai' },
    { slug: 'jaipur-to-delhi', label: 'Jaipur to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function AhmedabadToDelhiFlights() {
  return <RoutePageTemplate {...routeData} />
}
