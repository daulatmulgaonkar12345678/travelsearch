import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Delhi',
  originCode: 'DEL',
  destinationCity: 'Mumbai',
  destinationCode: 'BOM',
  content: {
    title: 'Flights from Delhi to Mumbai',
    description: 'Compare flight options from Delhi to Mumbai. Search across multiple airlines operating on India\'s busiest domestic corridor.',
    flightInfo: 'The Delhi to Mumbai route spans approximately 1,150 kilometers with flight times averaging 2 hours. As India\'s most-traveled air corridor, this route sees frequent departures throughout the day from carriers including IndiGo, Air India, Vistara, and SpiceJet. Indira Gandhi International Airport (DEL) serves as a major hub connecting travelers to Mumbai\'s Chhatrapati Shivaji Maharaj International Airport (BOM).',
    travelTips: 'Mumbai airport offers metro connectivity to key business districts. For travelers heading to South Mumbai, pre-booking airport transfers is recommended during peak hours. Business travelers often prefer morning departures to maximize productive time in Mumbai. Both terminals at BOM are well-equipped with lounges and dining options.',
    bestTime: 'Advance booking of 2-4 weeks typically provides more fare options on this route. Prices tend to increase during festival seasons and major business events. Tuesday and Wednesday departures often show different pricing patterns compared to Monday and Friday business travel days.',
  },
  relatedRoutes: [
    { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi' },
    { slug: 'delhi-to-bangalore', label: 'Delhi to Bangalore' },
    { slug: 'delhi-to-goa', label: 'Delhi to Goa' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function DelhiToMumbaiFlights() {
  return <RoutePageTemplate {...routeData} />
}
