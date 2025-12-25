import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Goa',
  cityCode: 'GOI',
  content: {
    title: 'Hotels in Goa',
    description: 'Compare accommodation in Goa, India\'s popular beach destination known for its Portuguese heritage and coastal charm.',
    whyVisit: 'Goa attracts visitors with its beaches, colonial Portuguese architecture, and relaxed atmosphere. North Goa offers livelier beaches and nightlife around Baga and Calangute, while South Goa provides quieter beaches and heritage sites. The state\'s churches, including those at Old Goa, are UNESCO World Heritage sites.',
    accommodation: 'Goa offers diverse accommodation from beach resorts to heritage homes. North Goa has options ranging from party hostels to luxury resorts along the beach strip. South Goa features quieter properties and wellness resorts. Interior areas offer heritage homestays. Location affects beach access and atmosphere significantly.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'mumbai', label: 'Hotels in Mumbai' },
    { slug: 'pune', label: 'Hotels in Pune' },
    { slug: 'bangalore', label: 'Hotels in Bangalore' },
  ],
  nearbyFlightRoutes: [
    { slug: 'mumbai-to-goa', label: 'Mumbai to Goa flights' },
    { slug: 'delhi-to-goa', label: 'Delhi to Goa flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function GoaHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
