/**
 * SEO Route Page: Mumbai to Delhi Flights
 * 
 * Static, SEO-optimized page for the Mumbai → Delhi route.
 * noindex on dynamic results pages, but this page is indexable.
 */

import { Metadata } from 'next'
import RoutePageTemplate, {
  generateRouteMetadata,
  RoutePageProps,
} from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Mumbai',
  originCode: 'BOM',
  destinationCity: 'Delhi',
  destinationCode: 'DEL',
  content: {
    title: 'Cheap Flights from Mumbai to Delhi',
    description:
      'Compare Mumbai to Delhi flights across major airlines on India\'s busiest air route. Search multiple providers for flight options.',
    flightInfo:
      'Flights from Mumbai (BOM) to Delhi (DEL) cover approximately 1,150 kilometers and typically take around 2 hours. This is India\'s busiest domestic air route, with over 100 daily flights operated by airlines including IndiGo, Air India, Vistara, SpiceJet, and GoFirst. Both airports are major hubs offering excellent connectivity to international and domestic destinations.',
    travelTips:
      'Delhi\'s Indira Gandhi International Airport (DEL) is located about 16 km from the city center. The Airport Express Metro line provides quick access to New Delhi Railway Station and Connaught Place. For business travelers, early morning departures (6-8 AM) and evening returns (7-9 PM) are most popular. Consider booking premium economy or business class for better flexibility and lounge access on this high-frequency route.',
    bestTime:
      'For the best fares on Mumbai to Delhi flights, book 3-4 weeks in advance. Prices spike during peak travel seasons (October-November for Diwali, December-January for New Year). Mid-week flights (Tuesday, Wednesday) typically offer lower fares than weekend travel. Red-eye flights and early morning departures often have the most competitive pricing.',
  },
  relatedRoutes: [
    { slug: 'delhi-to-mumbai', label: 'Delhi to Mumbai' },
    { slug: 'mumbai-to-bangalore', label: 'Mumbai to Bangalore' },
    { slug: 'delhi-to-bangalore', label: 'Delhi to Bangalore' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function MumbaiToDelhiFlights() {
  return <RoutePageTemplate {...routeData} />
}
