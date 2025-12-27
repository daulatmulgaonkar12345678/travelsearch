import { redirect } from 'next/navigation'

export default function TrainsPage() {
  // Redirect to homepage with trains tab active
  // The homepage will show the search form with trains tab selected
  redirect('/?tab=trains')
}
