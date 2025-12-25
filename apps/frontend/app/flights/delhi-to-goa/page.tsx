import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Delhi',
  originCode: 'DEL',
  destinationCity: 'Goa',
  destinationCode: 'GOI',
  content: {
    title: 'Flights from Delhi to Goa',
    description: 'Search flights from Delhi to Goa. Compare options across airlines serving this popular leisure destination route.',
    flightInfo: 'Flights from Delhi to Goa cover approximately 1,500 kilometers with an average flight duration of 2 hours 30 minutes. Goa\'s Dabolim Airport (GOI) and the newer Manohar International Airport at Mopa receive flights from multiple carriers. This route sees increased frequency during the peak tourist season from October to March.',
    travelTips: 'Goa has two airports - Dabolim in South Goa and Mopa in North Goa. Check which airport is closer to your accommodation when comparing flights. Pre-arranged transfers or taxi services are available at both airports. The state offers diverse accommodation from beach resorts to heritage properties.',
    bestTime: 'The Delhi to Goa route experiences seasonal demand variations. The monsoon season (June-September) typically sees reduced flight frequency, while the winter months are peak travel period. Booking 3-6 weeks ahead during peak season may provide more options.',
  },
  relatedRoutes: [
    { slug: 'mumbai-to-goa', label: 'Mumbai to Goa' },
    { slug: 'bangalore-to-goa', label: 'Bangalore to Goa' },
    { slug: 'delhi-to-mumbai', label: 'Delhi to Mumbai' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function DelhiToGoaFlights() {
  return <RoutePageTemplate {...routeData} />
}
