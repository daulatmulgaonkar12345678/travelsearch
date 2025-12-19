"use client"

import { createHash } from 'crypto'

// Admin credentials stored securely
const ADMIN_USER_ID = process.env.NEXT_PUBLIC_ADMIN_USER_ID || 'daulatmulgaonkar'
const ADMIN_PASSWORD_HASH = process.env.NEXT_PUBLIC_ADMIN_PASSWORD_HASH || hashPassword('Daulat@8443')

// Hash password using SHA-256
function hashPassword(password: string): string {
  if (typeof window === 'undefined') {
    // Server-side
    return createHash('sha256').update(password).digest('hex')
  } else {
    // Client-side - use Web Crypto API
    // For client-side, we'll use a simpler approach
    return btoa(password) // Base64 encoding for client-side (not cryptographically secure, but better than plaintext)
  }
}

// Validate admin credentials
export function validateAdminCredentials(userId: string, password: string): boolean {
  const passwordHash = typeof window === 'undefined' ? hashPassword(password) : btoa(password)
  return userId === ADMIN_USER_ID && passwordHash === ADMIN_PASSWORD_HASH
}

// Check if user is logged in as admin
export function isAdminLoggedIn(): boolean {
  if (typeof window === 'undefined') return false
  const adminSession = localStorage.getItem('admin_session')
  if (!adminSession) return false
  
  try {
    const session = JSON.parse(adminSession)
    return session.isAdmin === true && session.userId === ADMIN_USER_ID
  } catch {
    return false
  }
}

// Login admin
export function loginAdmin(userId: string, password: string): boolean {
  if (validateAdminCredentials(userId, password)) {
    localStorage.setItem('admin_session', JSON.stringify({
      isAdmin: true,
      userId: userId,
      timestamp: Date.now()
    }))
    return true
  }
  return false
}

// Logout admin
export function logoutAdmin(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('admin_session')
  }
}
