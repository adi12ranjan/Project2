/** @type {import('next').NextConfig} */
// BACKEND_URL: in local dev this defaults to your uvicorn server on :8000.
// In production (Vercel), set an environment variable named BACKEND_URL to
// wherever the FastAPI backend is actually deployed (Vercel does not run
// Python/uvicorn processes — the backend needs its own host, e.g. Render).
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
