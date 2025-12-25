import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Delhi',
  cityCode: 'DEL',
  content: {
    title: 'Hotels in Delhi',
    description: 'Compare accommodation in Delhi, India\'s capital territory offering history, culture, and modern amenities.',
    whyVisit: 'Delhi combines India\'s political center with rich Mughal and British colonial heritage. Visitors explore historic sites like the Red Fort, Qutub Minar, and Humayun\'s Tomb alongside modern attractions in Connaught Place and Hauz Khas. The city serves as a base for exploring North India and is a major business destination.',
    accommodation: 'The NCR region offers extensive accommodation options. Central Delhi has heritage hotels and luxury properties near government areas, while Gurgaon and Noida offer modern business hotels. Budget and mid-range options are available across metro-connected areas. Airport proximity varies significantly by location.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'jaipur', label: 'Hotels in Jaipur' },
    { slug: 'mumbai', label: 'Hotels in Mumbai' },
    { slug: 'bangalore', label: 'Hotels in Bangalore' },
  ],
  nearbyFlightRoutes: [
    { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi flights' },
    { slug: 'bangalore-to-delhi', label: 'Bangalore to Delhi flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function DelhiHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
