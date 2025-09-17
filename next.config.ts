import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      // Redirect HTTP to HTTPS for all requests
      {
        source: '/(.*)',
        has: [
          {
            type: 'header',
            key: 'x-forwarded-proto',
            value: 'http',
          },
        ],
        destination: 'https://www.showmeyourtds.com/:path*',
        permanent: true,
      },
      // Redirect non-www to www
      {
        source: '/(.*)',
        has: [
          {
            type: 'host',
            value: 'showmeyourtds.com',
          },
        ],
        destination: 'https://www.showmeyourtds.com/:path*',
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
