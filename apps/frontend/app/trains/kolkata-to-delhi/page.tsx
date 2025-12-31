import { Metadata } from 'next'
import TrainRoutePageTemplate, { generateTrainRouteMetadata, TrainRoutePageProps } from '@/components/seo/TrainRoutePageTemplate'

const routeData: TrainRoutePageProps = {
  originCity: 'Kolkata',
  originStation: 'Howrah (HWH) / Sealdah',
  destinationCity: 'Delhi',
  destinationStation: 'New Delhi (NDLS) / Anand Vihar',
  content: {
    title: 'Kolkata to Delhi Trains',
    description: 'Compare train options from Kolkata to Delhi. Historic rail corridor connecting the City of Joy to India\'s national capital.',
    routeInfo: 'The Kolkata to Delhi train route spans approximately 1,500 kilometers across the Gangetic plains. This is one of India\'s oldest and most important rail corridors. Trains pass through Bihar, Uttar Pradesh, and touch Jharkhand. The Rajdhani Express is the flagship service on this route.',
    trainClasses: 'Howrah Rajdhani offers premium all-AC travel with meals included. Sealdah Rajdhani provides an alternative departure point. Duronto Express offers non-stop service. Poorva Express is a popular Superfast option with sleeper class. Multiple mail trains provide budget options.',
    bookingTips: 'Book Rajdhani at least 3 weeks in advance for confirmed berths. Howrah station trains are generally more crowded than Sealdah. Consider overnight departure to arrive fresh in Delhi. Bihar stretch may have security checks during elections.',
  },
  estimatedPrice: { min: 600, max: 5500, currency: 'INR' },
  duration: '17-20 hours',
  relatedRoutes: [
    { slug: 'delhi-to-kolkata', label: 'Delhi to Kolkata' },
    { slug: 'kolkata-to-mumbai', label: 'Kolkata to Mumbai' },
    { slug: 'kolkata-to-chennai', label: 'Kolkata to Chennai' },
  ],
}

export const metadata: Metadata = generateTrainRouteMetadata(routeData)

export default function KolkataToDelhiTrains() {
  return <TrainRoutePageTemplate {...routeData} />
}
