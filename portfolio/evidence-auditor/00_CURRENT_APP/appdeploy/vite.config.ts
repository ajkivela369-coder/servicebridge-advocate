import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
    plugins: [react()],
  resolve: process.env.APPDEPLOY_VITE_OUT_DIR ? undefined : {
    alias: { '@appdeploy/client': fileURLToPath(new URL('./src/appdeploy-local.ts', import.meta.url)) },
  },
    base: './',
    build: {
        outDir: process.env.APPDEPLOY_VITE_OUT_DIR || 'dist',
        sourcemap: process.env.APPDEPLOY_VITE_SOURCEMAP === 'hidden' ? 'hidden' : false,
        rollupOptions: {
            maxParallelFileOps: 128,
        },
    },
});
