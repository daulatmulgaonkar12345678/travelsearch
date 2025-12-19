"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

// Redirect /admin to /admin/reconciliations
export default function AdminPage() {
  const router = useRouter()
  
  useEffect(() => {
    router.push('/admin/reconciliations')
  }, [router])
  
  return null
}
