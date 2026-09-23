import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const standalone = process.env.CI === 'true' || process.env.GRIMFORGE_STANDALONE === '1';

export default defineConfig({
    plugins: [react()],
    resolve: standalone ? {
        alias: {
            '@appdeploy/client': new URL('./src/appdeploy-client-shim.ts', import.meta.url).pathname,
        },
    } : undefined,
    base: './',
    build: {
        outDir: process.env.APPDEPLOY_VITE_OUT_DIR || 'dist',
        sourcemap: process.env.APPDEPLOY_VITE_SOURCEMAP === 'hidden' ? 'hidden' : false,
        rollupOptions: {
            maxParallelFileOps: 128,
        },
    },
});
