import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Hyderabad',
  originCode: 'HYD',
  destinationCity: 'Delhi',
  destinationCode: 'DEL',
  content: {
    title: 'Flights from Hyderabad to Delhi',
    description: 'Compare Hyderabad to Delhi flights. Search options connecting Telangana\'s capital with the national capital region.',
    flightInfo: 'Hyderabad to Delhi flights cover approximately 1,260 kilometers with an average duration of 2 hours 15 minutes. Rajiv Gandhi International Airport (HYD) serves as a major hub in South-Central India with excellent facilities. This route serves IT professionals, government visitors, and travelers connecting to international flights from Delhi.',
    travelTips: 'Delhi\'s IGI Airport connects well to the city via metro and various ground transport. Hyderabad travelers should plan for potential weather differences, particularly during North Indian winters. Both airports offer premium lounge access for eligible passengers.',
    bestTime: 'The route sees steady demand year-round with variations during major festivals and political events in Delhi. IT industry schedules and government calendars influence travel patterns. Comparing flights across different days of the week can help identify various fare options.',
  },
  relatedRoutes: [
    { slug: 'delhi-to-hyderabad', label: 'Delhi to Hyderabad' },
    { slug: 'hyderabad-to-bangalore', label: 'Hyderabad to Bangalore' },
    { slug: 'bangalore-to-delhi', label: 'Bangalore to Delhi' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function HyderabadToDelhiFlights() {
  return <RoutePageTemplate {...routeData} />
}
