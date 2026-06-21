import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // @ts-ignore: Next.js 15+ allows this to bypass CORS blocking on local network testing
  allowedDevOrigins: ['192.168.0.41'],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8001/api/:path*', // Proxy to Backend
      },
    ]
  },
};

export default nextConfig;
