import { Metadata } from 'next'
import BusRoutePageTemplate, { generateBusRouteMetadata, BusRoutePageProps } from '@/components/seo/BusRoutePageTemplate'

const routeData: BusRoutePageProps = {
  originCity: 'Mumbai',
  destinationCity: 'Pune',
  content: {
    title: 'Mumbai to Pune Bus Tickets',
    description: 'Compare bus options from Mumbai to Pune. Frequent departures connecting India\'s financial capital to the IT hub of Maharashtra.',
    routeInfo: 'The Mumbai to Pune bus route connects two of India\'s most important cities via the modern Mumbai-Pune Expressway. The 150 km journey takes you through the scenic Western Ghats. Buses depart from various points in Mumbai including Dadar, Borivali, and Sion.',
    busTypes: 'Choose from AC sleepers for comfortable overnight travel, AC seaters for daytime journeys, and budget non-AC buses. MSRTC Shivneri buses offer comfortable government-operated service. Private operators provide luxury Volvo and Mercedes buses with WiFi and charging points.',
    travelTips: 'Avoid Friday evening and Sunday evening departures due to heavy weekend traffic. Early morning and late night buses often have less traffic. Khandala and Lonavala make good rest stops. The journey can be longer during monsoon due to reduced speed limits on the ghats.',
  },
  estimatedPrice: { min: 300, max: 1500, currency: 'INR' },
  duration: '3-4 hours',
  relatedRoutes: [
    { slug: 'pune-to-mumbai', label: 'Pune to Mumbai' },
    { slug: 'mumbai-to-goa', label: 'Mumbai to Goa' },
    { slug: 'mumbai-to-nashik', label: 'Mumbai to Nashik' },
  ],
}

export const metadata: Metadata = generateBusRouteMetadata(routeData)

export default function MumbaiToPuneBus() {
  return <BusRoutePageTemplate {...routeData} />
}
