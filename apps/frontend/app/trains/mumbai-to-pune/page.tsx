import { Metadata } from 'next'
import TrainRoutePageTemplate, { generateTrainRouteMetadata, TrainRoutePageProps } from '@/components/seo/TrainRoutePageTemplate'

const routeData: TrainRoutePageProps = {
  originCity: 'Mumbai',
  originStation: 'CSMT / Dadar / LTT',
  destinationCity: 'Pune',
  destinationStation: 'Pune Junction (PUNE)',
  content: {
    title: 'Mumbai to Pune Trains',
    description: 'Compare train options from Mumbai to Pune. Scenic Deccan rail journey connecting Maharashtra\'s commercial hub to its cultural capital.',
    routeInfo: 'The Mumbai to Pune train route covers approximately 190 kilometers through the picturesque Western Ghats. The famous Bhor and Khandala ghat sections feature tunnels, bridges, and stunning valley views. This is one of the most scenic train journeys in India, especially during monsoon.',
    trainClasses: 'Deccan Queen is the historic premier train with chair car seating. Deccan Express offers comfortable AC chair cars. Pragati Express and Indrayani Express provide budget options. Sinhagad Express is popular for overnight travel. Most trains offer 2nd class unreserved for short trips.',
    bookingTips: 'Deccan Queen window seats on the left side offer best views of the ghats. Book in advance for weekend travel. Unreserved travel works well for short trips as the journey is short. The monsoon season (June-September) offers spectacular views but expect delays.',
  },
  estimatedPrice: { min: 100, max: 800, currency: 'INR' },
  duration: '3-4 hours',
  relatedRoutes: [
    { slug: 'pune-to-mumbai', label: 'Pune to Mumbai' },
    { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi' },
    { slug: 'pune-to-bangalore', label: 'Pune to Bangalore' },
  ],
}

export const metadata: Metadata = generateTrainRouteMetadata(routeData)

export default function MumbaiToPuneTrains() {
  return <TrainRoutePageTemplate {...routeData} />
}
