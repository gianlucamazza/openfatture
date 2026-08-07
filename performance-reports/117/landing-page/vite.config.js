import { defineConfig } from 'vite'

export default defineConfig({
  base: './', // Changed to relative path for robustness
  build: {
    outDir: 'dist',
  },
})
