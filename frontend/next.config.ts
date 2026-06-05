import type { NextConfig } from "next";

// Внутри сети Docker бэкенд доступен по имени сервиса 'app'
const BACKEND_URL = "http://app:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    proxyClientMaxBodySize: "100mb",
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
