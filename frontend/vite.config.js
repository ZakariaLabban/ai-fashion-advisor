const { defineConfig } = require('vite');
const react = require('@vitejs/plugin-react');

// https://vitejs.dev/config/
module.exports = defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/analyze': {
        target: 'http://localhost:7000',
        changeOrigin: true,
        timeout: 120000 // 2 minutes
      },
      '/tryon': {
        target: 'http://localhost:7000',
        changeOrigin: true,
        timeout: 120000 // 2 minutes
      },
      '/api/text-search': {
        target: 'http://localhost:7002', // text2image service
        changeOrigin: true,
        timeout: 60000 // 1 minute
      },
      '/api/check-query': {
        target: 'http://localhost:7002', // text2image service
        changeOrigin: true,
        timeout: 30000 // 30 seconds
      },
      '/api': {
        target: 'http://localhost:7000',
        changeOrigin: true,
        timeout: 120000, // 2 minutes
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        }
      },
      '/static': 'http://localhost:7000'
    }
  },
}); 