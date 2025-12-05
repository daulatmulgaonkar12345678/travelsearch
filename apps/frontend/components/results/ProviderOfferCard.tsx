'use client'

import { Shield, CheckCircle, Star } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

export type ProviderOffer = {
  name: string
  price: number
  deep_link: string
  rating?: number
  promo?: string
  trust_bullets?: string[]
}

interface ProviderOfferCardProps {
  provider: ProviderOffer
  currency?: string
  onSelect: () => void
}

export default function ProviderOfferCard({
  provider,
  currency = 'INR',
  onSelect
}: ProviderOfferCardProps) {
  const defaultTrustBullets = ['Secure payments', '24/7 support']
  const trustBullets = provider.trust_bullets || defaultTrustBullets

  return (
    <div
      data-testid={`provider-card-${provider.name}`}
      className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all"
    >
      <div className="flex items-start justify-between">
        {/* Provider Info */}
        <div className="flex items-start space-x-3 flex-1">
          {/* Provider Logo */}
          <div className="h-10 w-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-bold">
              {provider.name.slice(0, 2).toUpperCase()}
            </span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h4 className="font-semibold text-gray-900 truncate">{provider.name}</h4>
              {provider.rating && provider.rating >= 80 && (
                <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
              )}
            </div>

            {/* Rating */}
            {provider.rating && (
              <div className="text-xs text-gray-600 mt-1">
                {provider.rating}% positive reviews
              </div>
            )}

            {/* Trust Bullets */}
            <div className="mt-2 space-y-1">
              {trustBullets.slice(0, 2).map((bullet, idx) => (
                <div key={idx} className="flex items-center space-x-1 text-xs text-gray-600">
                  {idx === 0 ? (
                    <Shield className="h-3 w-3 text-green-600" />
                  ) : (
                    <CheckCircle className="h-3 w-3 text-blue-600" />
                  )}
                  <span>{bullet}</span>
                </div>
              ))}
            </div>

            {/* Promo */}
            {provider.promo && (
              <div className="mt-2 inline-block px-2 py-1 bg-green-50 text-green-700 text-xs font-medium rounded">
                {provider.promo}
              </div>
            )}
          </div>
        </div>

        {/* Price & CTA */}
        <div className="text-right ml-4">
          <div className="text-xl font-bold text-gray-900">
            {formatCurrency(provider.price, currency)}
          </div>
          <button
            data-testid={`select-provider-${provider.name}`}
            onClick={onSelect}
            className="mt-3 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            aria-label={`Select ${provider.name} for ${formatCurrency(provider.price, currency)}`}
          >
            Select
          </button>
        </div>
      </div>
    </div>
  )
}
