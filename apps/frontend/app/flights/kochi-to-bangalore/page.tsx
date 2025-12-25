import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Kochi',
  originCode: 'COK',
  destinationCity: 'Bangalore',
  destinationCode: 'BLR',
  content: {
    title: 'Flights from Kochi to Bangalore',
    description: 'Compare Kochi to Bangalore flights. Search options connecting Kerala\'s commercial hub with South India\'s technology center.',
    flightInfo: 'The Kochi to Bangalore route covers approximately 340 kilometers with flight times around 1 hour. Cochin International Airport (COK) serves as Kerala\'s busiest airport. This route connects IT professionals, business travelers, and those transiting through Bangalore\'s hub for onward connections.',
    travelTips: 'Kochi airport is located at Nedumbassery, about 30 km from the city center. Bangalore airport\'s distance from the city should be factored into travel plans. Both airports have developed ground transport options including buses and taxis.',
    bestTime: 'This route sees steady demand from the IT sector in both cities. Kerala\'s tourism seasons and Bangalore\'s business calendars both influence travel patterns. The short flight duration makes it suitable for day trips when schedules align.',
  },
  relatedRoutes: [
    { slug: 'bangalore-to-kochi', label: 'Bangalore to Kochi' },
    { slug: 'trivandrum-to-bangalore', label: 'Trivandrum to Bangalore' },
    { slug: 'chennai-to-bangalore', label: 'Chennai to Bangalore' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function KochiToBangaloreFlights() {
  return <RoutePageTemplate {...routeData} />
}
