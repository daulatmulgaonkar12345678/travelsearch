import { Metadata } from 'next'
import BusRoutePageTemplate, { generateBusRouteMetadata, BusRoutePageProps } from '@/components/seo/BusRoutePageTemplate'

const routeData: BusRoutePageProps = {
  originCity: 'Pune',
  destinationCity: 'Mumbai',
  content: {
    title: 'Pune to Mumbai Bus Tickets',
    description: 'Compare bus options from Pune to Mumbai. One of the busiest inter-city bus routes in India with multiple departures throughout the day.',
    routeInfo: 'The Pune to Mumbai bus route covers approximately 150 kilometers via the Mumbai-Pune Expressway. This is one of India\'s most traveled inter-city routes, connecting Maharashtra\'s two largest cities. The expressway offers a smooth, scenic journey through the Western Ghats with multiple food stops along the way.',
    busTypes: 'Multiple bus types operate on this route including AC sleeper buses for overnight journeys, AC seater buses ideal for day travel, and economical non-AC options. Luxury Volvo buses offer extra legroom and amenities. State transport (MSRTC) provides budget-friendly services while private operators like RedBus partners offer premium options.',
    travelTips: 'Book in advance during weekends and holidays as this route experiences heavy traffic. Morning and late evening departures help avoid expressway congestion. The Lonavala stop midway offers refreshment options. Keep motion sickness medication handy for the ghat section.',
  },
  estimatedPrice: { min: 300, max: 1500, currency: 'INR' },
  duration: '3-4 hours',
  relatedRoutes: [
    { slug: 'mumbai-to-pune', label: 'Mumbai to Pune' },
    { slug: 'pune-to-bangalore', label: 'Pune to Bangalore' },
    { slug: 'mumbai-to-goa', label: 'Mumbai to Goa' },
  ],
}

export const metadata: Metadata = generateBusRouteMetadata(routeData)

export default function PuneToMumbaiBus() {
  return <BusRoutePageTemplate {...routeData} />
}
