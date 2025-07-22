import { svelte } from '@sveltejs/vite-plugin-svelte';

export default {
  plugins: [svelte()],
  server: {
    port: 5173,
    strictPort: true,
    host: true,
    allowedHosts: [
      'auction-display-app-tunnel-6k9tntu5.devinapps.com',
      '.devinapps.com'
    ]
  }
};
