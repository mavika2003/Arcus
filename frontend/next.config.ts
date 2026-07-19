import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Monorepo-style repo has a lockfile at repo root; keep Turbopack scoped to frontend/
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
