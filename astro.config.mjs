// @ts-check
import { defineConfig } from 'astro/config';

// moonraker.ai is served from Cloudflare R2 + a worker that expects clean URLs
// (each route at <route>/index.html) and owns redirects/CSP/markdown-negotiation.
// So: directory output, no trailing slash, no Astro-side redirects.
export default defineConfig({
  site: 'https://moonraker.ai',
  trailingSlash: 'never',
  build: {
    format: 'directory',
  },
  devToolbar: { enabled: false },
});
