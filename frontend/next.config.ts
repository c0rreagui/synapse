import type { NextConfig } from "next";

// Server-side only: resolve backend URL for rewrites
// In Docker: BACKEND_INTERNAL_URL=http://backend:8000 (Docker DNS)
// Local dev: falls back to http://127.0.0.1:8000
const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
    ],
  },
  turbopack: {},
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${BACKEND_URL}/api/v1/:path*`,
      },
      {
        source: '/api/clipper/:path*',
        destination: `${BACKEND_URL}/api/clipper/:path*`,
      },
      {
        source: '/api/health/:path*',
        destination: `${BACKEND_URL}/api/health/:path*`,
      },
      {
        source: '/health',
        destination: `${BACKEND_URL}/health`,
      },
      // clipper-output still needs proxy (not volume-mounted)
      {
        source: '/clipper-output/:path*',
        destination: `${BACKEND_URL}/clipper-output/:path*`,
      },
    ]
  },
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
        ignored: ['**/node_modules/**', '**/.next/**', '**/.git/**'],
      };
    }
    return config;
  },
};

export default nextConfig;
