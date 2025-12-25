import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Mumbai',
  cityCode: 'BOM',
  content: {
    title: 'Hotels in Mumbai',
    description: 'Compare accommodation options in Mumbai, India\'s financial capital and entertainment hub.',
    whyVisit: 'Mumbai serves as India\'s commercial and entertainment capital. The city attracts business travelers to its financial districts in Nariman Point and Bandra-Kurla Complex, while tourists visit landmarks like the Gateway of India, Marine Drive, and Bollywood studios. The city\'s diverse neighborhoods offer distinct experiences from the historic charm of South Mumbai to the modern energy of the western suburbs.',
    accommodation: 'Mumbai offers accommodation across all categories. The city has international luxury hotels near business districts, boutique properties in Bandra and Colaba, mid-range options across the suburbs, and budget stays near transit hubs. Location choice significantly impacts commute times given the city\'s size and traffic patterns.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'pune', label: 'Hotels in Pune' },
    { slug: 'goa', label: 'Hotels in Goa' },
    { slug: 'delhi', label: 'Hotels in Delhi' },
  ],
  nearbyFlightRoutes: [
    { slug: 'delhi-to-mumbai', label: 'Delhi to Mumbai flights' },
    { slug: 'bangalore-to-mumbai', label: 'Bangalore to Mumbai flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function MumbaiHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
