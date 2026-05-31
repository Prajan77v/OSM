import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";

const nextConfig: NextConfig = {
  // Static export for production (served by FastAPI)
  ...(isProd ? { output: "export", trailingSlash: true } : {}),
  images: { unoptimized: true },
  // Dev proxy: forward /api/* to FastAPI at :8000
  ...(isProd ? {} : {
    async rewrites() {
      return [
        { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
      ];
    },
  }),
};

export default nextConfig;
