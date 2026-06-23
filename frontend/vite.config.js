import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        },
    },
    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
                // SSE 流式：禁用代理缓冲，保证逐字到达
                configure: function (proxy) {
                    proxy.on('proxyRes', function (proxyRes) {
                        if ((proxyRes.headers['content-type'] || '').includes('text/event-stream')) {
                            proxyRes.headers['cache-control'] = 'no-cache';
                        }
                    });
                },
            },
        },
    },
});
