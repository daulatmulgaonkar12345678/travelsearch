'use client'

import { Shield, DollarSign, Zap } from 'lucide-react'

export default function TrustStrip() {
  const features = [
    {
      icon: Shield,
      text: 'Compare prices across trusted partners',
    },
    {
      icon: DollarSign,
      text: 'No hidden fees',
    },
    {
      icon: Zap,
      text: 'Fast & secure redirection',
    },
  ]

  return (
    <div className="bg-blue-50 border-y border-blue-100 py-3">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-center space-x-8 md:space-x-12">
          {features.map((feature, index) => (
            <div key={index} className="flex items-center space-x-2">
              <feature.icon className="h-4 w-4 text-blue-600 flex-shrink-0" />
              <span className="text-sm text-gray-700 whitespace-nowrap hidden sm:inline">
                {feature.text}
              </span>
              <span className="text-xs text-gray-700 sm:hidden">
                {feature.text.split(' ').slice(0, 2).join(' ')}...
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
