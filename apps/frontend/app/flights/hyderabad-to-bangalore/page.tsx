import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Hyderabad',
  originCode: 'HYD',
  destinationCity: 'Bangalore',
  destinationCode: 'BLR',
  content: {
    title: 'Flights from Hyderabad to Bangalore',
    description: 'Search Hyderabad to Bangalore flights. Compare fares connecting two of South India\'s leading technology and business centers.',
    flightInfo: 'The Hyderabad to Bangalore route covers approximately 500 kilometers with flight times around 1 hour 15 minutes. Rajiv Gandhi International Airport (HYD) and Kempegowda International Airport (BLR) are both modern facilities serving India\'s growing IT sectors. This route sees significant business travel between the two tech hubs.',
    travelTips: 'Both airports are located on the outskirts of their respective cities. Hyderabad airport has metro connectivity to the city, while Bangalore\'s airport metro is operational. IT corridor locations in both cities should be considered when planning ground transport.',
    bestTime: 'This technology corridor sees consistent demand from IT professionals throughout the year. Major tech conferences and events can influence travel patterns. Weekday morning and evening slots are popular for business day trips between the cities.',
  },
  relatedRoutes: [
    { slug: 'bangalore-to-hyderabad', label: 'Bangalore to Hyderabad' },
    { slug: 'hyderabad-to-delhi', label: 'Hyderabad to Delhi' },
    { slug: 'chennai-to-bangalore', label: 'Chennai to Bangalore' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function HyderabadToBangaloreFlights() {
  return <RoutePageTemplate {...routeData} />
}
