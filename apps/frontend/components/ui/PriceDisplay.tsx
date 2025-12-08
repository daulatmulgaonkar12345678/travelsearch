'use client'

interface PriceDisplayProps {
  price: number
  currency?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  showTrustLabel?: boolean
  className?: string
}

export default function PriceDisplay({
  price,
  currency = 'INR',
  size = 'md',
  showTrustLabel = true,
  className = '',
}: PriceDisplayProps) {
  const formatPrice = (amount: number) => {
    return Math.round(amount).toLocaleString('en-IN')
  }

  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl',
    xl: 'text-4xl',
  }

  const trustLabelSizes = {
    sm: 'text-xs',
    md: 'text-xs',
    lg: 'text-sm',
    xl: 'text-sm',
  }

  return (
    <div className={`flex flex-col ${className}`}>
      {/* Price */}
      <div className={`font-bold text-gray-900 ${sizeClasses[size]}`}>
        {currency === 'INR' && '₹'}
        {currency === 'USD' && '$'}
        {currency === 'EUR' && '€'}
        {formatPrice(price)}
      </div>

      {/* Trust Label */}
      {showTrustLabel && (
        <div className={`${trustLabelSizes[size]} text-gray-600 mt-0.5`}>
          Final price • Taxes included
        </div>
      )}
    </div>
  )
}

interface PriceWithTooltipProps extends PriceDisplayProps {
  showTooltip?: boolean
}

export function PriceWithTooltip({
  showTooltip = true,
  ...props
}: PriceWithTooltipProps) {
  return (
    <div className="relative group">
      <PriceDisplay {...props} />
      
      {/* Tooltip on hover */}
      {showTooltip && (
        <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50">
          <div className="bg-gray-900 text-white text-xs rounded-lg py-2 px-3 whitespace-nowrap shadow-lg">
            <div className="font-medium mb-1">Price Guarantee</div>
            <div className="text-gray-300">
              No markup — prices from official partners
            </div>
            {/* Arrow */}
            <div className="absolute top-full left-4 -mt-1">
              <div className="border-4 border-transparent border-t-gray-900"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
