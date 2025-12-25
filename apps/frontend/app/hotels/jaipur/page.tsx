import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Jaipur',
  cityCode: 'JAI',
  content: {
    title: 'Hotels in Jaipur',
    description: 'Compare accommodation in Jaipur, Rajasthan\'s Pink City offering royal heritage and vibrant bazaars.',
    whyVisit: 'Jaipur forms part of India\'s Golden Triangle tourist circuit alongside Delhi and Agra. The city\'s Amber Fort, City Palace, Hawa Mahal, and colorful bazaars showcase Rajasthani heritage. As a UNESCO World Heritage Site, the old city\'s planned layout and pink-painted buildings offer a distinctive experience.',
    accommodation: 'Jaipur offers unique heritage accommodation in converted palaces and havelis alongside modern hotels. Luxury properties include palace hotels with historical significance. The old city has smaller heritage stays, while newer areas offer contemporary options. Budget travelers find options near the railway station and bus stands.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'delhi', label: 'Hotels in Delhi' },
    { slug: 'mumbai', label: 'Hotels in Mumbai' },
    { slug: 'goa', label: 'Hotels in Goa' },
  ],
  nearbyFlightRoutes: [
    { slug: 'jaipur-to-delhi', label: 'Jaipur to Delhi flights' },
    { slug: 'jaipur-to-mumbai', label: 'Jaipur to Mumbai flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function JaipurHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
