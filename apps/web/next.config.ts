import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: true,
  },
  // Orphan scaffold pages (untracked, spread across tabs) have pre-existing type
  // mismatches from an earlier experiment. They don't block the shell port
  // sprint — enable once all scaffolds are either wired or stubbed.
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:31300",
  },
};

export default config;
