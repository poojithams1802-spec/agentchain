
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// AgentChain frontend — Person 1
// Dev server proxies /api requests to Person 2's FastAPI backend
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8000,
    proxy: {
      '/api': {
        target: 'http://10.0.26.28:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})