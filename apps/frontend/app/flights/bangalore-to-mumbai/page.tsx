import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Bangalore',
  originCode: 'BLR',
  destinationCity: 'Mumbai',
  destinationCode: 'BOM',
  content: {
    title: 'Flights from Bangalore to Mumbai',
    description: 'Search Bangalore to Mumbai flights. Compare options on this key business corridor linking two of India\'s major metropolitan areas.',
    flightInfo: 'The Bangalore to Mumbai route spans approximately 840 kilometers with flights averaging 1 hour 45 minutes. This route sees heavy business traffic connecting India\'s technology sector in Bangalore with Mumbai\'s financial and entertainment industries. Chhatrapati Shivaji Maharaj International Airport offers extensive domestic and international connectivity.',
    travelTips: 'Mumbai airport\'s domestic terminal connects to the city via metro and various ground transport options. South Mumbai destinations may require additional travel time from the airport. The Bandra-Kurla Complex business district is relatively accessible from both airport terminals.',
    bestTime: 'Business travel patterns drive demand on this route, with higher frequency on weekday mornings and evenings. Weekend leisure travel to Mumbai for events and entertainment also contributes to demand. Comparing different departure times can help identify various fare options.',
  },
  relatedRoutes: [
    { slug: 'mumbai-to-bangalore', label: 'Mumbai to Bangalore' },
    { slug: 'bangalore-to-delhi', label: 'Bangalore to Delhi' },
    { slug: 'chennai-to-bangalore', label: 'Chennai to Bangalore' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function BangaloreToMumbaiFlights() {
  return <RoutePageTemplate {...routeData} />
}
