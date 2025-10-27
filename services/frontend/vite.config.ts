import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/api': {
        // Proxy API requests to backend service
        // Uses VITE_API_URL if set, otherwise falls back to service DNS name
        // In Docker Compose: 'api' resolves via docker network
        // In Kubernetes: 'api' resolves via cluster DNS (same namespace)
        target: process.env.VITE_API_URL || 'http://api:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: true,
    port: 3000,
  },
})
