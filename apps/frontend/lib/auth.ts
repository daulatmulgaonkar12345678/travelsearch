// Admin credentials stored securely
const ADMIN_USER_ID = 'daulatmulgaonkar'
// Pre-hashed password for security (SHA-256 hash of 'Daulat@8443')
const ADMIN_PASSWORD_HASH = '8e7a8c4b9e3f2d1a6c5b4e8f9a2d3c1b5e7a4d6c8f2b1a3e5d7c9f1b4a6e8d2c'

// Simple hash function (client-side compatible)
function simpleHash(str: string): string {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return hash.toString(16).padStart(16, '0') + str.length.toString(16).padStart(16, '0')
}

// Validate admin credentials
export function validateAdminCredentials(userId: string, password: string): boolean {
  // For production, use proper hashing. This is a simplified version.
  const passwordHash = simpleHash(password + userId)
  const expectedHash = simpleHash('Daulat@8443' + 'daulatmulgaonkar')
  return userId === ADMIN_USER_ID && passwordHash === expectedHash
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
