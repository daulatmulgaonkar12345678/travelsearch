'use client'

import { MapPin, Star, Wifi, Coffee, Dumbbell, Lock, Shield } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { useState } from 'react'
import PriceDisplay from '@/components/ui/PriceDisplay'

interface HotelOffer {
  offer_id: string
  provider: string
  hotel_name: string
  address: string
  city: string
  rating?: number
  review_score?: number
  review_count?: number
  price_per_night: number
  total_price: number
  currency: string
  amenities: string[]
  room_type?: string
  cancellation_policy?: string
  images: string[]
  deep_link: string
}

interface HotelProviderOffer {
  provider: string
  price: number
  deep_link: string
}

interface HotelResultCardProps {
  hotel: HotelOffer
  providers?: HotelProviderOffer[]
  onProviderSelect?: (provider: HotelProviderOffer, hotel: HotelOffer) => void
}

export default function HotelResultCard({ hotel, providers = [], onProviderSelect }: HotelResultCardProps) {
  const [selectedImage, setSelectedImage] = useState(0)

  const amenityIcons: Record<string, any> = {
    'Free WiFi': Wifi,
    'Wifi': Wifi,
    'Gym': Dumbbell,
    'Fitness': Dumbbell,
    'Restaurant': Coffee,
    'Breakfast': Coffee,
  }

  const getAmenityIcon = (amenity: string) => {
    for (const [key, Icon] of Object.entries(amenityIcons)) {
      if (amenity.includes(key)) return Icon
    }
    return Coffee
  }

  const displayProviders = providers.length > 0 ? providers : [
    { provider: hotel.provider, price: hotel.total_price, deep_link: hotel.deep_link }
  ]

  return (
    <article
      data-testid={`hotel-card-${hotel.offer_id}`}
      className="bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all overflow-hidden"
      aria-labelledby={`hotel-${hotel.offer_id}`}
    >
      <div className="grid md:grid-cols-[300px,1fr] gap-0">
        {/* Image Gallery */}
        <div className="relative h-64 md:h-auto bg-gray-100">
          {hotel.images && hotel.images.length > 0 ? (
            <>
              <img
                src={hotel.images[selectedImage] || hotel.images[0]}
                alt={hotel.hotel_name}
                className="w-full h-full object-cover"
              />
              {hotel.images.length > 1 && (
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex space-x-2">
                  {hotel.images.slice(0, 5).map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedImage(idx)}
                      className={`h-2 w-2 rounded-full transition-all ${
                        idx === selectedImage ? 'bg-white w-8' : 'bg-white/60'
                      }`}
                      aria-label={`View image ${idx + 1}`}
                    />
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <Coffee className="h-16 w-16" />
            </div>
          )}
        </div>

        {/* Hotel Details */}
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 id={`hotel-${hotel.offer_id}`} className="text-xl font-bold text-gray-900 mb-2">
                {hotel.hotel_name}
              </h3>
              
              {/* Location */}
              <div className="mb-2">
                <div className="flex items-center space-x-2 text-gray-600">
                  <MapPin className="h-4 w-4" />
                  <span className="text-sm">{hotel.city}</span>
                </div>
                {hotel.address && (
                  <div className="text-xs text-gray-500 mt-1 ml-6">
                    {hotel.address}
                  </div>
                )}
                {(hotel.rating && hotel.rating >= 4) || (hotel.review_score && hotel.review_score >= 8) ? (
                  <div className="text-xs text-green-600 font-medium mt-1 ml-6">
                    Excellent location
                  </div>
                ) : null}
              </div>

              {/* Rating */}
              <div className="flex items-center space-x-4">
                {hotel.rating && (
                  <div className="flex items-center space-x-1">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`h-4 w-4 ${
                          i < hotel.rating!
                            ? 'text-yellow-400 fill-yellow-400'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                )}
                {hotel.review_score && (
                  <div className="text-sm">
                    <span className="font-semibold text-gray-900">{hotel.review_score}/10</span>
                    <span className="text-gray-600 ml-1">({hotel.review_count} reviews)</span>
                  </div>
                )}
              </div>
            </div>

            {/* Price */}
            <div className="text-right ml-4">
              <div className="text-sm text-gray-500 mb-1">From</div>
              <PriceDisplay 
                price={hotel.price_per_night}
                currency={hotel.currency}
                size="md"
                showTrustLabel={true}
                className="mb-1"
              />
              <div className="text-xs text-gray-500">per night</div>
              {hotel.cancellation_policy === 'FREE_CANCELLATION' && (
                <div className="text-xs text-green-600 font-medium mt-1">
                  Free cancellation
                </div>
              )}
            </div>
          </div>

          {/* Room Type */}
          {hotel.room_type && (
            <div className="mb-4 inline-block px-3 py-1 bg-blue-50 text-blue-700 text-sm font-medium rounded-full">
              {hotel.room_type}
            </div>
          )}

          {/* Amenities */}
          {hotel.amenities && hotel.amenities.length > 0 && (
            <div className="mb-4">
              <div className="flex flex-wrap gap-3">
                {hotel.amenities.slice(0, 5).map((amenity) => {
                  const Icon = getAmenityIcon(amenity)
                  return (
                    <div key={amenity} className="flex items-center space-x-2 text-sm text-gray-600">
                      <Icon className="h-4 w-4" />
                      <span>{amenity}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Cancellation Policy */}
          {hotel.cancellation_policy && (
            <div className="mb-4 text-sm text-gray-600">
              <span className="font-medium">Cancellation:</span> {hotel.cancellation_policy}
            </div>
          )}

          {/* Provider Comparison */}
          <div className="border-t border-gray-200 pt-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-medium text-gray-700">Available on:</div>
              <div className="flex items-center space-x-1 text-xs text-gray-600">
                <Lock className="h-3 w-3 text-green-600" />
                <span>Secure redirection</span>
              </div>
            </div>
            <div className="text-xs text-gray-600 mb-3">
              You'll be redirected securely to complete booking on partner site
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {displayProviders.map((provider) => (
                <button
                  key={provider.provider}
                  data-testid={`hotel-provider-${provider.provider}`}
                  onClick={() => onProviderSelect?.(provider, hotel)}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-1">
                      <div className="h-8 w-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded flex items-center justify-center">
                        <span className="text-white text-xs font-bold">
                          {provider.provider.slice(0, 2).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900 text-sm">{provider.provider}</span>
                        <span className="inline-flex items-center space-x-1 text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full border border-green-200">
                          <Shield className="h-3 w-3" />
                          <span>Trusted partner</span>
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <PriceDisplay 
                      price={provider.price}
                      currency={hotel.currency}
                      size="sm"
                      showTrustLabel={true}
                    />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </article>
  )
}
