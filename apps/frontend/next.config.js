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
  // In production: routes to travelsearch-backend.onrender.com
  // In development: routes to localhost:8001
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8001'
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
