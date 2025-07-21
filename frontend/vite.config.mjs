import { svelte } from '@sveltejs/vite-plugin-svelte';

export default {
  plugins: [svelte()],
  server: {
    port: 5173,
    strictPort: true
  }
};
