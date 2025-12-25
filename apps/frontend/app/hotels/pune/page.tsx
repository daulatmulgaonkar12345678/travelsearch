import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Pune',
  cityCode: 'PNQ',
  content: {
    title: 'Hotels in Pune',
    description: 'Compare accommodation in Pune, Maharashtra\'s cultural capital and a growing IT and educational hub.',
    whyVisit: 'Pune combines educational prestige with a growing IT sector and rich Maratha heritage. The city houses prestigious institutions, historic sites like Shaniwar Wada, and serves as a gateway to hill stations like Lonavala and Mahabaleshwar. Its relatively moderate climate and cosmopolitan culture attract long-term visitors.',
    accommodation: 'Pune\'s accommodation centers around distinct hubs. Hinjewadi and Kharadi serve the IT sector with business hotels, while central areas like Koregaon Park offer boutique and mid-range options. Budget stays cluster near the railway station and educational institutions.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'mumbai', label: 'Hotels in Mumbai' },
    { slug: 'goa', label: 'Hotels in Goa' },
    { slug: 'bangalore', label: 'Hotels in Bangalore' },
  ],
  nearbyFlightRoutes: [
    { slug: 'delhi-to-pune', label: 'Delhi to Pune flights' },
    { slug: 'pune-to-mumbai', label: 'Pune to Mumbai flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function PuneHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
