import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    // Disable Lightning CSS optimization to avoid platform binary issues on Vercel
    optimizeCss: false,
  },
};

export default nextConfig;
