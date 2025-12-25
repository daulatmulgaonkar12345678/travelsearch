import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Trivandrum',
  originCode: 'TRV',
  destinationCity: 'Bangalore',
  destinationCode: 'BLR',
  content: {
    title: 'Flights from Trivandrum to Bangalore',
    description: 'Search Trivandrum to Bangalore flights. Compare fares connecting Kerala\'s capital with the Karnataka technology hub.',
    flightInfo: 'Trivandrum to Bangalore flights span approximately 510 kilometers with an average duration of 1 hour 15 minutes. Trivandrum International Airport (TRV) serves as the gateway to southern Kerala. This route connects government workers, IT professionals, and travelers seeking Bangalore\'s connectivity for onward journeys.',
    travelTips: 'Trivandrum airport is closer to the city center than many Indian airports. Bangalore\'s airport location requires planning for ground transport. Both cities experience different monsoon patterns which may occasionally affect schedules.',
    bestTime: 'Kerala\'s tourism seasons and Bangalore\'s business calendar both influence this route. Government-related travel between the state capital and Bangalore maintains steady demand. Onam festival period sees specific travel patterns.',
  },
  relatedRoutes: [
    { slug: 'bangalore-to-trivandrum', label: 'Bangalore to Trivandrum' },
    { slug: 'kochi-to-bangalore', label: 'Kochi to Bangalore' },
    { slug: 'chennai-to-bangalore', label: 'Chennai to Bangalore' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function TrivandrumToBangaloreFlights() {
  return <RoutePageTemplate {...routeData} />
}
