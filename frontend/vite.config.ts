// vite.config.ts

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite' // <-- Make sure this line exists

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // <-- And make sure it's called here
  ],
})