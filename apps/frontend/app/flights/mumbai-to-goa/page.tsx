import { Metadata } from 'next'
import RoutePageTemplate, { generateRouteMetadata, RoutePageProps } from '@/components/seo/RoutePageTemplate'

const routeData: RoutePageProps = {
  originCity: 'Mumbai',
  originCode: 'BOM',
  destinationCity: 'Goa',
  destinationCode: 'GOI',
  content: {
    title: 'Flights from Mumbai to Goa',
    description: 'Compare Mumbai to Goa flights. This short-haul route connects Maharashtra\'s capital to India\'s popular coastal destination.',
    flightInfo: 'The Mumbai to Goa flight covers approximately 450 kilometers with flight times around 1 hour. This is one of the shorter domestic routes, making it a convenient alternative to road or rail travel. Multiple daily departures operate from Chhatrapati Shivaji Maharaj International Airport to both Dabolim and Mopa airports in Goa.',
    travelTips: 'Given the short flight duration, many travelers opt for flights over the 10-12 hour drive. Goa\'s Mopa airport is newer and closer to North Goa beaches, while Dabolim serves South Goa better. Weekend flights tend to be busier with leisure travelers from Mumbai.',
    bestTime: 'This route maintains consistent service year-round with increased frequency during weekends and holidays. The monsoon months may see some schedule variations. Comparing prices across different departure times within the same day can reveal fare differences.',
  },
  relatedRoutes: [
    { slug: 'delhi-to-goa', label: 'Delhi to Goa' },
    { slug: 'bangalore-to-goa', label: 'Bangalore to Goa' },
    { slug: 'pune-to-goa', label: 'Pune to Goa' },
  ],
}

export const metadata: Metadata = generateRouteMetadata(routeData)

export default function MumbaiToGoaFlights() {
  return <RoutePageTemplate {...routeData} />
}
