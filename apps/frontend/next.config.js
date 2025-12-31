/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['via.placeholder.com', 'images.unsplash.com'],
  },
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Proxy API calls to backend server
  // Production: https://travelsearch-backend.onrender.com
  // Development: http://localhost:8001
  async rewrites() {
    // Use BACKEND_URL from environment, fallback to production URL, then localhost
    const backendUrl = process.env.BACKEND_URL 
      || (process.env.NODE_ENV === 'production' 
          ? 'https://travelsearch-backend.onrender.com' 
          : 'http://localhost:8001')
    
    console.log(`[next.config.js] API rewrite destination: ${backendUrl}`)
    
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
