import { Metadata } from 'next'
import TrainRoutePageTemplate, { generateTrainRouteMetadata, TrainRoutePageProps } from '@/components/seo/TrainRoutePageTemplate'

const routeData: TrainRoutePageProps = {
  originCity: 'Mumbai',
  originStation: 'Mumbai Central (BCT) / CSMT',
  destinationCity: 'Delhi',
  destinationStation: 'New Delhi (NDLS) / Hazrat Nizamuddin',
  content: {
    title: 'Mumbai to Delhi Trains',
    description: 'Compare train options from Mumbai to Delhi. India\'s busiest long-distance rail corridor connecting the financial and political capitals.',
    routeInfo: 'The Mumbai to Delhi train route spans approximately 1,400 kilometers, connecting India\'s two most important cities. Multiple trains operate daily including the prestigious Rajdhani Express, August Kranti Rajdhani, and Duronto Express. The journey takes you through Gujarat, Rajasthan, and Haryana.',
    trainClasses: 'Choose from various classes based on comfort and budget. AC First Class offers private cabins with beds. AC 2-Tier provides curtained sleeping berths. AC 3-Tier is the most popular air-conditioned option. Sleeper class offers budget berths without AC. Rajdhani trains include meals in the fare.',
    bookingTips: 'Book Rajdhani Express 2-3 weeks in advance as it fills up quickly. Tatkal quota opens at 10 AM one day before travel for AC classes. Premium Tatkal is available for urgent travel. Consider overnight Duronto for no-stop fast travel.',
  },
  estimatedPrice: { min: 500, max: 5000, currency: 'INR' },
  duration: '15-17 hours',
  relatedRoutes: [
    { slug: 'delhi-to-mumbai', label: 'Delhi to Mumbai' },
    { slug: 'mumbai-to-pune', label: 'Mumbai to Pune' },
    { slug: 'delhi-to-jaipur', label: 'Delhi to Jaipur' },
  ],
}

export const metadata: Metadata = generateTrainRouteMetadata(routeData)

export default function MumbaiToDelhiTrains() {
  return <TrainRoutePageTemplate {...routeData} />
}
