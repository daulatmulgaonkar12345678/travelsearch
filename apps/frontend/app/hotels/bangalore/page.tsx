import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Bangalore',
  cityCode: 'BLR',
  content: {
    title: 'Hotels in Bangalore',
    description: 'Compare accommodation in Bangalore, India\'s technology capital known for its pleasant climate and vibrant culture.',
    whyVisit: 'Bangalore serves as India\'s technology and startup hub, attracting business travelers year-round. The city offers a blend of modern tech parks, historic landmarks like Bangalore Palace, and green spaces including Cubbon Park and Lalbagh. The pleasant climate and diverse food scene make it a comfortable base for exploring Karnataka.',
    accommodation: 'Bangalore\'s accommodation spreads across its expanding geography. IT corridor areas like Whitefield and Electronic City have business hotels, while central areas like MG Road and Indiranagar offer boutique and mid-range options. Budget stays cluster near major metro stations and transit points.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'chennai', label: 'Hotels in Chennai' },
    { slug: 'hyderabad', label: 'Hotels in Hyderabad' },
    { slug: 'kochi', label: 'Hotels in Kochi' },
  ],
  nearbyFlightRoutes: [
    { slug: 'mumbai-to-bangalore', label: 'Mumbai to Bangalore flights' },
    { slug: 'delhi-to-bangalore', label: 'Delhi to Bangalore flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function BangaloreHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
