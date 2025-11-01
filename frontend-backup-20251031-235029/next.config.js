/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ]
  },
  experimental: {
    esmExternals: 'loose',
  },
  transpilePackages: ['react-markdown', 'remark-gfm'],
}

module.exports = nextConfig