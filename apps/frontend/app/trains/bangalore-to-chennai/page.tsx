import { Metadata } from 'next'
import TrainRoutePageTemplate, { generateTrainRouteMetadata, TrainRoutePageProps } from '@/components/seo/TrainRoutePageTemplate'

const routeData: TrainRoutePageProps = {
  originCity: 'Bangalore',
  originStation: 'KSR Bengaluru (SBC) / Yeshwanthpur',
  destinationCity: 'Chennai',
  destinationStation: 'Chennai Central (MAS) / Egmore',
  content: {
    title: 'Bangalore to Chennai Trains',
    description: 'Compare train options from Bangalore to Chennai. Frequent services connect Karnataka\'s tech capital to Tamil Nadu\'s gateway.',
    routeInfo: 'The Bangalore to Chennai train route covers approximately 360 kilometers through the Eastern Deccan. This is South India\'s busiest rail corridor with 30+ daily trains. The Shatabdi Express and Double Decker are popular for business travel, while overnight trains suit leisure travelers.',
    trainClasses: 'Shatabdi Express offers chair car AC seating with meals. Double Decker provides unique two-level AC seating. Brindavan Express is a budget-friendly superfast option. Overnight trains like Lalbagh Express offer sleeper berths. Several Express trains provide AC 3-Tier options.',
    bookingTips: 'Shatabdi books out quickly for morning business meetings. Book sleeper class for overnight travel to save on hotel costs. IRCTC i-Ticket option provides instant confirmation. Tatkal opens at 10 AM day before for AC classes.',
  },
  estimatedPrice: { min: 200, max: 2000, currency: 'INR' },
  duration: '5-7 hours',
  relatedRoutes: [
    { slug: 'chennai-to-bangalore', label: 'Chennai to Bangalore' },
    { slug: 'bangalore-to-mysore', label: 'Bangalore to Mysore' },
    { slug: 'chennai-to-hyderabad', label: 'Chennai to Hyderabad' },
  ],
}

export const metadata: Metadata = generateTrainRouteMetadata(routeData)

export default function BangaloreToChennaiTrains() {
  return <TrainRoutePageTemplate {...routeData} />
}
