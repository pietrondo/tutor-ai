/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8001',
        pathname: '/**',
      },
    ],
  },
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8001/:path*',
      },
      {
        source: '/uploads/:path*',
        destination: 'http://backend:8001/uploads/:path*',
      },
    ]
  },
  transpilePackages: ['react-markdown', 'remark-gfm'],
  // Configure for both webpack and turbopack compatibility
  turbopack: {},  // Empty turbopack config to silence the error
  // Configure webpack to handle polyfills properly
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Ensure polyfills are available in client-side bundles
      config.resolve.fallback = {
        ...config.resolve.fallback,
      };
    }
    return config;
  },
}

module.exports = nextConfig
