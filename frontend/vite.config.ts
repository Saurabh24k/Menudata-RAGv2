import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // Your backend server address
        changeOrigin: true, // For CORS if needed (usually recommended)
      },
    },
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
})