import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Ahmedabad',
  originCode: 'AMD',
  destinationCity: 'Mumbai',
  destinationCode: 'BOM',
  content: {
    title: 'Flights from Ahmedabad to Mumbai',
    description: 'Search Ahmedabad to Mumbai flights. Compare fares on this Gujarat-Maharashtra business corridor.',
    flightInfo: 'The Ahmedabad to Mumbai route covers approximately 440 kilometers with flight times around 1 hour 15 minutes. Sardar Vallabhbhai Patel International Airport (AMD) connects Gujarat\'s commercial capital with Mumbai. This route serves significant business and trade traffic between the two states.',
    travelTips: 'Mumbai airport\'s proximity to the Bandra-Kurla Complex business area makes it convenient for meetings. The short flight competes with express train services. Ahmedabad airport has undergone recent expansion with improved facilities.',
    bestTime: 'Business travel patterns on weekdays drive demand on this route. Trade fair seasons and major business events in either city can affect availability. The relatively short distance makes this route suitable for day trips with early morning and evening flights.',
  },
  relatedRoutes: [
    { slug: 'mumbai-to-ahmedabad', label: 'Mumbai to Ahmedabad' },
    { slug: 'ahmedabad-to-delhi', label: 'Ahmedabad to Delhi' },
    { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function AhmedabadToMumbaiFlights() {
  return <RoutePageTemplate {...routeData} />
}
