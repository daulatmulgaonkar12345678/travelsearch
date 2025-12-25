import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Kolkata',
  cityCode: 'CCU',
  content: {
    title: 'Hotels in Kolkata',
    description: 'Compare accommodation in Kolkata, the cultural capital of India known for its colonial heritage and artistic traditions.',
    whyVisit: 'Kolkata preserves its British colonial architecture alongside Bengali cultural traditions. The city\'s Durga Puja celebrations, literary heritage, and distinctive cuisine attract cultural travelers. Victoria Memorial, Howrah Bridge, and the colonial-era buildings along BBD Bagh showcase its historical significance.',
    accommodation: 'Kolkata\'s accommodation includes heritage hotels in the colonial core, modern business hotels near Salt Lake and New Town, and budget options near Howrah and Sealdah stations. The city\'s metro connectivity helps offset traffic challenges. Location choice affects access to cultural sites versus business areas.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'delhi', label: 'Hotels in Delhi' },
    { slug: 'bangalore', label: 'Hotels in Bangalore' },
    { slug: 'chennai', label: 'Hotels in Chennai' },
  ],
  nearbyFlightRoutes: [
    { slug: 'kolkata-to-delhi', label: 'Kolkata to Delhi flights' },
    { slug: 'kolkata-to-bangalore', label: 'Kolkata to Bangalore flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function KolkataHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
