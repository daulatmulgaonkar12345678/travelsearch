import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Chennai',
  originCode: 'MAA',
  destinationCity: 'Bangalore',
  destinationCode: 'BLR',
  content: {
    title: 'Flights from Chennai to Bangalore',
    description: 'Search Chennai to Bangalore flights. Compare options on this South Indian business corridor connecting two major metropolitan centers.',
    flightInfo: 'The Chennai to Bangalore route covers approximately 290 kilometers with flight times around 55 minutes. This short-haul route competes with road and rail options but offers time savings for business travelers. Chennai International Airport (MAA) and Kempegowda International Airport (BLR) both serve as regional hubs.',
    travelTips: 'The short flight duration makes this route popular for day trips between the cities. Both airports have good ground transportation including metro services. Business travelers often compare flight options against the Shatabdi Express train service on this route.',
    bestTime: 'This route maintains steady service throughout the year. Given the short distance, flight pricing may be compared against other transport modes. Early morning and late evening slots are popular with business travelers making day trips.',
  },
  relatedRoutes: [
    { slug: 'bangalore-to-chennai', label: 'Bangalore to Chennai' },
    { slug: 'chennai-to-delhi', label: 'Chennai to Delhi' },
    { slug: 'bangalore-to-mumbai', label: 'Bangalore to Mumbai' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function ChennaiToBangaloreFlights() {
  return <RoutePageTemplate {...routeData} />
}
