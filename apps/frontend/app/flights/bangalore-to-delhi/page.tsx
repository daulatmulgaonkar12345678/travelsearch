import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Bangalore',
  originCode: 'BLR',
  destinationCity: 'Delhi',
  destinationCode: 'DEL',
  content: {
    title: 'Flights from Bangalore to Delhi',
    description: 'Compare Bangalore to Delhi flights. Search across airlines connecting South India\'s tech hub with the national capital.',
    flightInfo: 'Bangalore to Delhi flights cover approximately 1,740 kilometers with an average duration of 2 hours 45 minutes. This route connects Kempegowda International Airport (BLR) with Indira Gandhi International Airport (DEL). High demand from business travelers and government visitors keeps this route well-served by major carriers.',
    travelTips: 'Delhi airport\'s Terminal 3 handles most domestic flights on this route. The Airport Express Metro provides direct connectivity to New Delhi Railway Station and central Delhi. For meetings in Gurgaon, domestic terminals at both airports may offer better ground connectivity.',
    bestTime: 'The Bangalore-Delhi route maintains steady demand year-round. Parliament sessions, major conferences, and festival seasons can affect availability. Mid-week travel often shows different pricing patterns compared to weekend flights.',
  },
  relatedRoutes: [
    { slug: 'delhi-to-bangalore', label: 'Delhi to Bangalore' },
    { slug: 'bangalore-to-mumbai', label: 'Bangalore to Mumbai' },
    { slug: 'hyderabad-to-delhi', label: 'Hyderabad to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function BangaloreToDelhiFlights() {
  return <RoutePageTemplate {...routeData} />
}
