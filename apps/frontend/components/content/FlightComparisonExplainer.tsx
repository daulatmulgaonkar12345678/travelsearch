/**
 * Dynamic Flight Comparison Explainer
 * Appears below search results to educate users
 */

interface ExplainerProps {
  originCity: string
  destinationCity: string
}

export function FlightComparisonExplainer({ originCity, destinationCity }: ExplainerProps) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-lg p-6 my-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Why compare flights from {originCity} to {destinationCity}?
      </h3>
      <p className="text-gray-700 leading-relaxed">
        Flight prices, departure times, and seat availability vary significantly 
        across airlines and booking platforms. By comparing options side-by-side, 
        you can identify flights that best match your schedule, budget, and preferences. 
        Our platform aggregates real-time data from multiple sources, helping you make 
        informed decisions without visiting dozens of websites. Whether you prioritize 
        price, duration, or departure time, comparison ensures you see all available choices.
      </p>
    </div>
  )
}
