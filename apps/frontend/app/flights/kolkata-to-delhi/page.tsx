import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Kolkata',
  originCode: 'CCU',
  destinationCity: 'Delhi',
  destinationCode: 'DEL',
  content: {
    title: 'Flights from Kolkata to Delhi',
    description: 'Search Kolkata to Delhi flights. Compare options connecting Eastern India with the national capital.',
    flightInfo: 'Kolkata to Delhi flights cover approximately 1,300 kilometers with an average duration of 2 hours 15 minutes. Netaji Subhas Chandra Bose International Airport (CCU) serves as Eastern India\'s primary aviation hub. This route connects Kolkata\'s cultural and business centers with Delhi\'s government and corporate sectors.',
    travelTips: 'Delhi airport\'s metro connectivity facilitates easy travel to various parts of the NCR. Kolkata airport is relatively close to the city center with good taxi and metro access. Time zone difference is not a factor on this domestic route, but seasonal weather variations should be considered.',
    bestTime: 'The route sees year-round demand with peaks during Durga Puja season when many Kolkata residents travel for work while others visit the city. Government and business calendars influence travel patterns. Major cultural events in either city can affect flight demand.',
  },
  relatedRoutes: [
    { slug: 'delhi-to-kolkata', label: 'Delhi to Kolkata' },
    { slug: 'kolkata-to-bangalore', label: 'Kolkata to Bangalore' },
    { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function KolkataToDelhiFlights() {
  return <RoutePageTemplate {...routeData} />
}
