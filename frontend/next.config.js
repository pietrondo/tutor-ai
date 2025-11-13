/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV === 'development';
const isProd = process.env.NODE_ENV === 'production';
const normalizeUrl = (url = '') => url.replace(/\/+$/, '');
const internalApiUrl = normalizeUrl(
  process.env.NEXT_INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000'
);

const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/**',
      },
    ],
  },
  output: 'standalone',
  // Development performance optimizations
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['lucide-react', '@heroicons/react'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${internalApiUrl}/:path*`,
      },
      {
        source: '/uploads/:path*',
        destination: `${internalApiUrl}/uploads/:path*`,
      },
      {
        source: '/course-files/:path*',
        destination: `${internalApiUrl}/course-files/:path*`,
      },
      {
        source: '/courses/:id/concepts',
        destination: `${internalApiUrl}/courses/:id/concepts`,
      },
    ]
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "style-src-elem 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "style-src-attr 'self' 'unsafe-inline'",
              "font-src 'self' https://fonts.gstatic.com data:",
              "upgrade-insecure-requests",
              "img-src 'self' data: blob: http: https:",
              // Removed duplicate font-src directive; fonts are served from fonts.gstatic.com
              "connect-src 'self' http://localhost:8000 http://localhost:3000 ws://localhost:3001 ws://localhost:8000 https://my.productfruits.com https://api.z.ai http://localhost:1234 ws://localhost:1234 https://api.openai.com https://openrouter.ai/api https://fonts.googleapis.com https://fonts.gstatic.com https://unpkg.com https://cdnjs.cloudflare.com",
              "media-src 'self'",
              "object-src 'self'",
              // Enhanced worker-src for PDF.js support in both dev and prod
              ...(isDev
                ? ["worker-src 'self' blob: data: http://localhost:3001 http://localhost:8000"]
                : ["worker-src 'self' blob: data: http://localhost:3001 http://localhost:8000"]
              ),
              "frame-src 'self'",
              "child-src 'self' blob:",
              "form-action 'self'"
            ].join('; ')
          }
        ]
      },
      {
        // Special handling for PDF worker file
        source: '/pdf.worker.min.js',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          },
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'require-corp'
          },
          {
            key: 'Cross-Origin-Resource-Policy',
            value: 'cross-origin'
          }
        ]
      },
      {
        // Special handling for all PDF files
        source: '/course-files/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=3600'
          },
          {
            key: 'Cross-Origin-Resource-Policy',
            value: 'cross-origin'
          }
        ]
      }
    ]
  },
  transpilePackages: ['react-markdown', 'remark-gfm'],
  // Configure for both webpack and turbopack compatibility
  turbopack: {},  // Empty turbopack config to silence the error
  // Configure webpack to handle polyfills properly
  webpack: (config, { isServer, dev }) => {
    // Add polyfill for Promise.withResolvers
    if (isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        'promise-withresolvers-polyfill': require.resolve('./polyfills.js'),
      };
    }

    // Development performance optimizations
    if (dev) {
      // Improve development build performance
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              chunks: 'all',
            },
            common: {
              name: 'common',
              minChunks: 2,
              chunks: 'all',
              enforce: true,
            },
          },
        },
      };

      // Reduce bundle analysis overhead in development
      config.stats = 'minimal';
    }

    if (!isServer) {
      // Ensure polyfills are available in client-side bundles
      config.resolve.fallback = {
        ...config.resolve.fallback,
      };

      // Simplified PDF worker handling for production
      if (isProd) {
        config.plugins.push({
          apply: (compiler) => {
            compiler.hooks.afterEmit.tap('CopyPDFWorker', () => {
              const fs = require('fs');
              const path = require('path');

              const sourceWorker = path.join(__dirname, 'public', 'pdf.worker.min.js');

              if (fs.existsSync(sourceWorker)) {
                // Copy to main static directory for backend serving
                const staticDir = path.join(__dirname, '.next', 'static');
                const mainWorkerDest = path.join(staticDir, 'pdf.worker.min.js');

                // Ensure directory exists
                if (!fs.existsSync(staticDir)) {
                  fs.mkdirSync(staticDir, { recursive: true });
                }

                fs.copyFileSync(sourceWorker, mainWorkerDest);
                console.log(`✅ PDF worker copied to: ${mainWorkerDest}`);

                // Also copy to standalone public directory for production
                const standalonePublicDir = path.join(__dirname, '.next', 'standalone', 'public');
                if (!fs.existsSync(standalonePublicDir)) {
                  fs.mkdirSync(standalonePublicDir, { recursive: true });
                }
                const standaloneWorker = path.join(standalonePublicDir, 'pdf.worker.min.js');
                fs.copyFileSync(sourceWorker, standaloneWorker);
                console.log(`✅ PDF worker copied to standalone: ${standaloneWorker}`);
              } else {
                console.warn('⚠️ PDF worker source file not found:', sourceWorker);
              }
            });
          },
        });
      }
    }
    return config;
  },
}

module.exports = nextConfig
