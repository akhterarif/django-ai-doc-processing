/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://web:8000/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
