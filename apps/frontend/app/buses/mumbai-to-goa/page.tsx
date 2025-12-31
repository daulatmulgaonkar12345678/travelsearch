import { Metadata } from 'next'
import BusRoutePageTemplate, { generateBusRouteMetadata, BusRoutePageProps } from '@/components/seo/BusRoutePageTemplate'

const routeData: BusRoutePageProps = {
  originCity: 'Mumbai',
  destinationCity: 'Goa',
  content: {
    title: 'Mumbai to Goa Bus Tickets',
    description: 'Compare bus options from Mumbai to Goa. Popular route connecting Maharashtra\'s capital to India\'s favorite beach destination.',
    routeInfo: 'The Mumbai to Goa bus route covers approximately 600 kilometers along the scenic Konkan coast via NH66. This overnight journey takes you through beautiful coastal towns and the Western Ghats. Most buses depart in the evening and arrive early morning in Goa.',
    busTypes: 'Sleeper buses are most popular for this overnight journey, available in both AC and non-AC variants. Multi-axle Volvo sleepers offer the smoothest ride. Semi-sleeper options provide a middle ground between comfort and cost. Some operators offer luxury buses with individual entertainment systems.',
    travelTips: 'Book sleeper buses for overnight comfort on this long journey. The coastal route via Ratnagiri is scenic but longer. Carry snacks as rest stops are limited at night. Monsoon travel may face delays due to heavy rainfall on the Konkan coast.',
  },
  estimatedPrice: { min: 700, max: 2500, currency: 'INR' },
  duration: '10-14 hours',
  relatedRoutes: [
    { slug: 'pune-to-goa', label: 'Pune to Goa' },
    { slug: 'bangalore-to-goa', label: 'Bangalore to Goa' },
    { slug: 'mumbai-to-pune', label: 'Mumbai to Pune' },
  ],
}

export const metadata: Metadata = generateBusRouteMetadata(routeData)

export default function MumbaiToGoaBus() {
  return <BusRoutePageTemplate {...routeData} />
}
