import type { NextConfig } from "next";
import path from "path";

/** Backend URL for Next.js rewrites (server-side on Vercel). */
const backendUrl = (
  process.env.API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.NEXT_PUBLIC_BACKEND_URL ??
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

if (process.env.VERCEL && !process.env.API_URL && !process.env.NEXT_PUBLIC_API_URL) {
  console.warn(
    "[Arcus] API_URL is not set on Vercel. Add API_URL=https://your-app.onrender.com and redeploy.",
  );
}

const nextConfig: NextConfig = {
  // Monorepo-style repo has a lockfile at repo root; keep Turbopack scoped to frontend/
  turbopack: {
    root: path.join(__dirname),
  },
  // Proxy /api/* → Render (or local uvicorn). Avoids CORS and NEXT_PUBLIC build issues.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
