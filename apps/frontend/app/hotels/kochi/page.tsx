import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Kochi',
  cityCode: 'COK',
  content: {
    title: 'Hotels in Kochi',
    description: 'Compare accommodation in Kochi, Kerala\'s port city blending colonial heritage with backwater beauty.',
    whyVisit: 'Kochi showcases Kerala\'s multicultural history through its Jewish synagogue, Dutch Palace, Chinese fishing nets, and colonial churches. Fort Kochi\'s artistic scene hosts the Kochi-Muziris Biennale. The city serves as a gateway to Kerala\'s backwaters and hill stations, attracting both cultural tourists and those seeking Ayurvedic experiences.',
    accommodation: 'Kochi offers varied accommodation across its islands and mainland. Fort Kochi has heritage homestays and boutique hotels in converted colonial buildings. Ernakulam provides modern business options, while areas toward the backwaters offer resort properties. Budget options cluster near transport hubs.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'bangalore', label: 'Hotels in Bangalore' },
    { slug: 'chennai', label: 'Hotels in Chennai' },
    { slug: 'goa', label: 'Hotels in Goa' },
  ],
  nearbyFlightRoutes: [
    { slug: 'kochi-to-bangalore', label: 'Kochi to Bangalore flights' },
    { slug: 'kochi-to-mumbai', label: 'Kochi to Mumbai flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function KochiHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
