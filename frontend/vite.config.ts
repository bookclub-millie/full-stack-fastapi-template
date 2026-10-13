import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import react from '@vitejs/plugin-react-swc'
import { defineConfig, loadEnv } from 'vite'
import { parsePublicEnv } from './src/lib/env.ts'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, import.meta.dirname, 'VITE_API_URL')
  parsePublicEnv({ VITE_API_URL: environment.VITE_API_URL })

  return {
    build: {
      outDir: '../backend/app/frontend',
      emptyOutDir: true
    },
    resolve: {
      alias: {
        '@': path.resolve(import.meta.dirname, './src')
      }
    },
    plugins: [
      tanstackRouter({
        target: 'react',
        autoCodeSplitting: true
      }),
      react(),
      tailwindcss()
    ]
  }
})
