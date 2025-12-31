import { Metadata } from 'next'
import BusRoutePageTemplate, { generateBusRouteMetadata, BusRoutePageProps } from '@/components/seo/BusRoutePageTemplate'

const routeData: BusRoutePageProps = {
  originCity: 'Bangalore',
  destinationCity: 'Chennai',
  content: {
    title: 'Bangalore to Chennai Bus Tickets',
    description: 'Compare bus options from Bangalore to Chennai. High-frequency route connecting Karnataka\'s tech hub to Tamil Nadu\'s capital.',
    routeInfo: 'The Bangalore to Chennai bus route spans approximately 350 kilometers via NH48. This is one of South India\'s busiest inter-city routes with buses departing every few minutes throughout the day. The journey takes you through the Eastern Deccan plateau.',
    busTypes: 'Government KSRTC and SETC buses offer reliable, economical services. Private operators run AC sleepers for overnight travel and AC seaters for day journeys. Volvo Multi-axle buses provide premium comfort. Early morning Airavat buses are popular with business travelers.',
    travelTips: 'Day buses avoid the overnight fatigue while enjoying the scenic route. KSRTC Airavat buses offer good value for money. Book return tickets together for potential discounts. Traffic near both cities can add 1-2 hours during peak times.',
  },
  estimatedPrice: { min: 400, max: 1800, currency: 'INR' },
  duration: '6-8 hours',
  relatedRoutes: [
    { slug: 'chennai-to-bangalore', label: 'Chennai to Bangalore' },
    { slug: 'bangalore-to-hyderabad', label: 'Bangalore to Hyderabad' },
    { slug: 'bangalore-to-mysore', label: 'Bangalore to Mysore' },
  ],
}

export const metadata: Metadata = generateBusRouteMetadata(routeData)

export default function BangaloreToChennai() {
  return <BusRoutePageTemplate {...routeData} />
}
