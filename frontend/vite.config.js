import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// AgentChain frontend — Person 1
// Dev server proxies /api to Person 2's FastAPI backend, matching
// the shared API contract in AGENTCHAIN_TEAM_IMPLEMENTATION.md
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
