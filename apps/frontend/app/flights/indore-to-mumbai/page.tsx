import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Indore',
  originCode: 'IDR',
  destinationCity: 'Mumbai',
  destinationCode: 'BOM',
  content: {
    title: 'Flights from Indore to Mumbai',
    description: 'Compare Indore to Mumbai flights. Search options connecting Madhya Pradesh\'s commercial center with India\'s financial capital.',
    flightInfo: 'The Indore to Mumbai route covers approximately 470 kilometers with flight times around 1 hour 20 minutes. Devi Ahilyabai Holkar Airport (IDR) serves central India\'s growing business hub. This route connects business travelers, students, and families with Mumbai\'s extensive network.',
    travelTips: 'Mumbai airport provides connections to both domestic and international destinations. Indore airport has seen recent upgrades to handle growing traffic. The flight offers significant time savings over road or rail alternatives.',
    bestTime: 'Business travel from Indore to Mumbai maintains steady demand. Trade and commerce patterns between the regions influence travel flows. Comparing options across different days can reveal various fare levels.',
  },
  relatedRoutes: [
    { slug: 'mumbai-to-indore', label: 'Mumbai to Indore' },
    { slug: 'indore-to-delhi', label: 'Indore to Delhi' },
    { slug: 'ahmedabad-to-mumbai', label: 'Ahmedabad to Mumbai' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function IndoreToMumbaiFlights() {
  return <RoutePageTemplate {...routeData} />
}
