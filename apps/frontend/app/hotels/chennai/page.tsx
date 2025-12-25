import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Chennai',
  cityCode: 'MAA',
  content: {
    title: 'Hotels in Chennai',
    description: 'Compare accommodation in Chennai, Tamil Nadu\'s capital known for its temples, beaches, and South Indian culture.',
    whyVisit: 'Chennai serves as the cultural gateway to South India, with ancient temples, colonial-era architecture, and Marina Beach. The city hosts the famous December music and dance season, attracting cultural enthusiasts. Its automotive and IT industries draw business travelers, while nearby Mahabalipuram offers UNESCO heritage sites.',
    accommodation: 'Chennai\'s accommodation concentrates in distinct areas. The business district around Anna Salai and Nungambakkam has corporate hotels, while beach-facing properties line the coast. IT corridor areas like OMR have options for tech sector visitors. Heritage properties exist in traditional neighborhoods.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'bangalore', label: 'Hotels in Bangalore' },
    { slug: 'hyderabad', label: 'Hotels in Hyderabad' },
    { slug: 'kochi', label: 'Hotels in Kochi' },
  ],
  nearbyFlightRoutes: [
    { slug: 'chennai-to-bangalore', label: 'Chennai to Bangalore flights' },
    { slug: 'chennai-to-delhi', label: 'Chennai to Delhi flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function ChennaiHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
