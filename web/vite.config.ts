import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

const GATEWAY = process.env.VITE_GATEWAY_URL ?? 'http://localhost:8080';

const apiPaths = ['/auth', '/accounts', '/transfers', '/history', '/.well-known', '/market'];

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      apiPaths.map((p) => [p, { target: GATEWAY, changeOrigin: true }]),
    ),
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 800,
  },
});
