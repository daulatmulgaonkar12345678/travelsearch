import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Jaipur',
  originCode: 'JAI',
  destinationCity: 'Delhi',
  destinationCode: 'DEL',
  content: {
    title: 'Flights from Jaipur to Delhi',
    description: 'Search Jaipur to Delhi flights. Compare fares on this short-haul route connecting Rajasthan\'s capital with the NCR.',
    flightInfo: 'Jaipur to Delhi flights cover approximately 240 kilometers with flight times around 55 minutes. Jaipur International Airport (JAI) has seen significant development as Rajasthan\'s tourism grows. This short route competes with road and rail options but offers significant time savings.',
    travelTips: 'The short flight duration makes this route popular for business day trips. Delhi airport metro provides convenient onward connectivity. Jaipur airport is relatively close to the city center and major tourist areas.',
    bestTime: 'Tourist season in Rajasthan (October-March) sees increased demand on this route. Business travel remains steady throughout the year. The short distance means flight timing flexibility may be important for many travelers.',
  },
  relatedRoutes: [
    { slug: 'delhi-to-jaipur', label: 'Delhi to Jaipur' },
    { slug: 'jaipur-to-mumbai', label: 'Jaipur to Mumbai' },
    { slug: 'ahmedabad-to-delhi', label: 'Ahmedabad to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function JaipurToDelhiFlights() {
  return <RoutePageTemplate {...routeData} />
}
