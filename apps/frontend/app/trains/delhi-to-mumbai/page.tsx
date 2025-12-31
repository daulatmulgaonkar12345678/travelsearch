import { Metadata } from 'next'
import TrainRoutePageTemplate, { generateTrainRouteMetadata, TrainRoutePageProps } from '@/components/seo/TrainRoutePageTemplate'

const routeData: TrainRoutePageProps = {
  originCity: 'Delhi',
  originStation: 'New Delhi (NDLS) / Hazrat Nizamuddin',
  destinationCity: 'Mumbai',
  destinationStation: 'Mumbai Central (BCT) / CSMT',
  content: {
    title: 'Delhi to Mumbai Trains',
    description: 'Compare train options from Delhi to Mumbai. Premium trains including Rajdhani and Duronto connect India\'s capital to the city of dreams.',
    routeInfo: 'The Delhi to Mumbai train route covers approximately 1,400 kilometers through the heartland of India. This is one of the most traveled rail corridors with multiple daily departures. Trains depart from New Delhi and Hazrat Nizamuddin stations, arriving at Mumbai Central or Bandra Terminus.',
    trainClasses: 'Rajdhani Express offers all-AC travel with meals included. August Kranti Rajdhani is a popular alternative. Duronto Express provides non-stop overnight service. For budget travel, Superfast trains offer Sleeper and AC 3-Tier options. Golden Temple Mail is a historic overnight option.',
    bookingTips: 'IRCTC advance booking opens 120 days before travel. Rajdhani trains require early booking especially during festivals. Waitlisted tickets often confirm on this route due to high cancellations. Consider flexible dates for better availability.',
  },
  estimatedPrice: { min: 500, max: 5000, currency: 'INR' },
  duration: '15-17 hours',
  relatedRoutes: [
    { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi' },
    { slug: 'delhi-to-jaipur', label: 'Delhi to Jaipur' },
    { slug: 'delhi-to-kolkata', label: 'Delhi to Kolkata' },
  ],
}

export const metadata: Metadata = generateTrainRouteMetadata(routeData)

export default function DelhiToMumbaiTrains() {
  return <TrainRoutePageTemplate {...routeData} />
}
