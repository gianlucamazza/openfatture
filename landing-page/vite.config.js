import { defineConfig } from 'vite'

export default defineConfig({
  base: '/', // Changed to root for custom domain
  build: {
    outDir: 'dist',
  },
})
