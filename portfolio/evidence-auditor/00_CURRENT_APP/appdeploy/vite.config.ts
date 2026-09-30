import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
    plugins: [react()],
    resolve: process.env.PORTFOLIO_QC_APPDEPLOY_SHIM === '1'
        ? { alias: { '@appdeploy/client': fileURLToPath(new URL('./src/appdeployClient.ci.ts', import.meta.url)) } }
        : undefined,
    base: './',
    build: {
        outDir: process.env.APPDEPLOY_VITE_OUT_DIR || 'dist',
        sourcemap: process.env.APPDEPLOY_VITE_SOURCEMAP === 'hidden' ? 'hidden' : false,
        rollupOptions: {
            maxParallelFileOps: 128,
        },
    },
});
