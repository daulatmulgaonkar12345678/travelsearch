import AdminGuard from '@/components/admin/AdminGuard'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Admin Panel | TravelSearch',
  robots: 'noindex, nofollow',
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AdminGuard>{children}</AdminGuard>
}
