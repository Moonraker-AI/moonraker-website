// Generated sitemap: the static marketing routes (ported from the old
// public/sitemap.xml) plus /blog and every published blog post. Built statically
// at build time, so it ships as dist/sitemap.xml exactly like the old file.
import { getPublishedPieces } from '../lib/content.js';

const BASE = 'https://moonraker.ai';

const STATIC: Array<{ path: string; priority: string }> = [
  { path: '/', priority: '1.0' },
  { path: '/services', priority: '0.9' },
  { path: '/core-marketing-system', priority: '0.9' },
  { path: '/core-marketing-system/credibility', priority: '0.8' },
  { path: '/core-marketing-system/optimization', priority: '0.8' },
  { path: '/core-marketing-system/reputation', priority: '0.8' },
  { path: '/core-marketing-system/engagement', priority: '0.8' },
  { path: '/results', priority: '0.9' },
  { path: '/knowledge-hub', priority: '0.8' },
  { path: '/blog', priority: '0.8' },
  { path: '/process', priority: '0.7' },
  { path: '/scope', priority: '0.7' },
  { path: '/team', priority: '0.6' },
  { path: '/free-strategy-call', priority: '0.8' },
  { path: '/privacy', priority: '0.4' },
  { path: '/terms', priority: '0.4' },
];

export async function GET() {
  const pieces = await getPublishedPieces();

  const staticUrls = STATIC.map(
    (u) => `  <url><loc>${BASE}${u.path}</loc><priority>${u.priority}</priority></url>`,
  );

  const postUrls = pieces.map((p) => {
    const lastmod = p.published_at ? `<lastmod>${new Date(p.published_at).toISOString().slice(0, 10)}</lastmod>` : '';
    return `  <url><loc>${BASE}/blog/${p.slug}</loc>${lastmod}<priority>0.7</priority></url>`;
  });

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${[...staticUrls, ...postUrls].join('\n')}
</urlset>
`;

  return new Response(body, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
}
