import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Pune',
  originCode: 'PNQ',
  destinationCity: 'Delhi',
  destinationCode: 'DEL',
  content: {
    title: 'Flights from Pune to Delhi',
    description: 'Compare Pune to Delhi flights. Search across airlines connecting Maharashtra\'s educational and IT hub with the national capital.',
    flightInfo: 'Pune to Delhi flights cover approximately 1,170 kilometers with flight times around 2 hours 15 minutes. Pune\'s Lohegaon Airport (PNQ) serves as a growing aviation hub with increasing connectivity. This route serves business travelers, students, and visitors to the national capital region.',
    travelTips: 'Pune airport is located closer to the city center compared to many Indian airports. Delhi\'s extensive metro network provides convenient access from IGI Airport to various parts of the NCR region. Flight schedules accommodate both early morning business travelers and evening departures.',
    bestTime: 'The Pune-Delhi route sees consistent demand from IT sector professionals and educational visitors. Academic calendar periods may influence demand patterns. Comparing weekday versus weekend options can reveal different fare structures.',
  },
  relatedRoutes: [
    { slug: 'delhi-to-pune', label: 'Delhi to Pune' },
    { slug: 'pune-to-mumbai', label: 'Pune to Mumbai' },
    { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function PuneToDelhiFlights() {
  return <RoutePageTemplate {...routeData} />
}
