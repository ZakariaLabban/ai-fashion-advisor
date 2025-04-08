const { defineConfig } = require('vite');
const react = require('@vitejs/plugin-react');

// https://vitejs.dev/config/
module.exports = defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/analyze': 'http://localhost:7000',
      '/tryon': 'http://localhost:7000',
      '/api': 'http://localhost:7000',
      '/static': 'http://localhost:7000'
    }
  },
}); 