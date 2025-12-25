/**
 * SEO Route Page: Pune to Mumbai Flights
 * 
 * Static, SEO-optimized page for the Pune → Mumbai route.
 * noindex on dynamic results pages, but this page is indexable.
 */

import { Metadata } from 'next'
import RoutePageTemplate, {
  generateRouteMetadata,
  RoutePageProps,
} from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Pune',
  originCode: 'PNQ',
  destinationCity: 'Mumbai',
  destinationCode: 'BOM',
  content: {
    title: 'Cheap Flights from Pune to Mumbai',
    description:
      'Compare Pune to Mumbai flights from multiple airlines. Search flight options on this popular domestic route.',
    flightInfo:
      'Flights from Pune (PNQ) to Mumbai (BOM) cover approximately 120 kilometers and typically take around 45 minutes by air. This is one of the busiest domestic routes in India, with multiple daily departures from major carriers including IndiGo, Air India, and SpiceJet. While the distance is short, flying can save significant time compared to road travel, especially during peak traffic hours on the Mumbai-Pune Expressway.',
    travelTips:
      'For travelers heading to Mumbai, Chhatrapati Shivaji Maharaj International Airport (BOM) is well-connected to the city center via metro, taxi, and ride-sharing services. If you\'re flexible with dates, consider flying mid-week (Tuesday or Wednesday) when fares tend to be lower. Early morning flights often offer the best combination of price and punctuality.',
    bestTime:
      'The best time to book Pune to Mumbai flights is 2-3 weeks in advance for domestic travel. Prices typically increase closer to the departure date, especially for business travel on weekdays. For the lowest fares, consider traveling during off-peak seasons (monsoon months from June to September) when demand is lower.',
  },
  relatedRoutes: [
    { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi' },
    { slug: 'mumbai-to-bangalore', label: 'Mumbai to Bangalore' },
    { slug: 'pune-to-delhi', label: 'Pune to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function PuneToMumbaiFlights() {
  return <RoutePageTemplate {...routeData} />
}
