import { Metadata } from 'next'
import BusRoutePageTemplate, { generateBusRouteMetadata, BusRoutePageProps } from '@/components/seo/BusRoutePageTemplate'

const routeData: BusRoutePageProps = {
  originCity: 'Delhi',
  destinationCity: 'Jaipur',
  content: {
    title: 'Delhi to Jaipur Bus Tickets',
    description: 'Compare bus options from Delhi to Jaipur. Popular Golden Triangle route connecting India\'s capital to the Pink City of Rajasthan.',
    routeInfo: 'The Delhi to Jaipur bus route covers approximately 280 kilometers via NH48 (Delhi-Jaipur Expressway). This historic route is part of the famous Golden Triangle tourist circuit. The modern expressway has significantly reduced travel time on this corridor.',
    busTypes: 'Rajasthan Roadways and DTC provide economical government services. Private Volvo buses offer comfort with reclining seats and entertainment. AC sleeper buses are available for those preferring to travel overnight. Many operators offer women-only seating sections.',
    travelTips: 'The new expressway has made daytime travel faster and more comfortable. Weekend trips to Jaipur should be booked in advance. Morning departures help you reach by afternoon to start sightseeing. Some buses stop at Neemrana Fort which makes a good break.',
  },
  estimatedPrice: { min: 400, max: 1600, currency: 'INR' },
  duration: '5-6 hours',
  relatedRoutes: [
    { slug: 'jaipur-to-delhi', label: 'Jaipur to Delhi' },
    { slug: 'delhi-to-agra', label: 'Delhi to Agra' },
    { slug: 'jaipur-to-udaipur', label: 'Jaipur to Udaipur' },
  ],
}

export const metadata: Metadata = generateBusRouteMetadata(routeData)

export default function DelhiToJaipurBus() {
  return <BusRoutePageTemplate {...routeData} />
}
