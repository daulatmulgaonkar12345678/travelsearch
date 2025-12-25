import { Metadata } from 'next'
import HotelCityPageTemplate, { generateHotelCityMetadata, HotelCityPageProps } from '@/components/seo/HotelCityPageTemplate'

const cityData: HotelCityPageProps = {
  cityName: 'Hyderabad',
  cityCode: 'HYD',
  content: {
    title: 'Hotels in Hyderabad',
    description: 'Compare accommodation in Hyderabad, the city of pearls and biryani, blending Nizami heritage with modern tech industry.',
    whyVisit: 'Hyderabad showcases its Nizami heritage through landmarks like Charminar, Golconda Fort, and the Salar Jung Museum. The city\'s IT sector in HITEC City draws business travelers, while its renowned cuisine, particularly biryani, attracts food enthusiasts. The mix of old city charm and new city modernity offers diverse experiences.',
    accommodation: 'Hyderabad\'s accommodation splits between the old city and HITEC City areas. Business hotels cluster around the tech corridor and Banjara Hills, while budget options serve the old city and railway station vicinity. Heritage properties offer experiences near historic areas. Location significantly affects commute times across the sprawling city.',
    bookingInfo: 'TravelSearch compares hotel options across multiple booking platforms. Prices shown are provided by our travel partners and may vary based on dates, room types, and availability. You\'ll complete your booking directly on the partner website.',
  },
  relatedCities: [
    { slug: 'bangalore', label: 'Hotels in Bangalore' },
    { slug: 'chennai', label: 'Hotels in Chennai' },
    { slug: 'mumbai', label: 'Hotels in Mumbai' },
  ],
  nearbyFlightRoutes: [
    { slug: 'hyderabad-to-bangalore', label: 'Hyderabad to Bangalore flights' },
    { slug: 'hyderabad-to-delhi', label: 'Hyderabad to Delhi flights' },
  ],
}

export const metadata: Metadata = generateHotelCityMetadata(cityData)

export default function HyderabadHotels() {
  return <HotelCityPageTemplate {...cityData} />
}
