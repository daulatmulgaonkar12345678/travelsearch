import { redirect } from 'next/navigation'

export default function BusesPage() {
  // Redirect to homepage with buses tab active
  // The homepage will show the search form with buses tab selected
  redirect('/?tab=buses')
}
