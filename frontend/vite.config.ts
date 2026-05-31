import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://app:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string): string | undefined {
          // React core
          if (id.includes('node_modules/react') && !id.includes('react-router-dom')) {
            return 'react'
          }
          if (id.includes('node_modules/react-router-dom')) {
            return 'react'
          }
          // MUI UI library
          if (id.includes('node_modules/@mui') || id.includes('node_modules/@emotion')) {
            return 'mui'
          }
          // Data fetching and forms
          if (
            id.includes('node_modules/@tanstack') ||
            id.includes('node_modules/react-hook-form') ||
            id.includes('node_modules/axios') ||
            id.includes('node_modules/zod')
          ) {
            return 'vendor'
          }
          // Plotly for charts
          if (id.includes('node_modules/plotly.js') || id.includes('node_modules/react-plotly.js')) {
            return 'plotly'
          }
          return undefined
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        statements: 50,
        branches: 40,
        functions: 45,
        lines: 50,
      },
    },
  },
})
