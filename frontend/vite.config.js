import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
        host: true, // Allow external access
        allowedHosts: ['presensi.kitapunya.web.id'], // Allow specific host
        proxy: {
            '/api': {
                target: 'https://back.kitapunya.web.id',
                changeOrigin: true,
            }
        }
    }
})
