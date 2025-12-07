import { redirect } from 'next/navigation'

// Redirect /flights to homepage (main flight search)
export default function FlightsPage() {
  redirect('/')
}
