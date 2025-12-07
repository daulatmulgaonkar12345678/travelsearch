import { redirect } from 'next/navigation'

// Redirect /admin to /admin/reconciliations
export default function AdminPage() {
  redirect('/admin/reconciliations')
}
