/**
 * moonraker.ai static-site worker.
 * Serves the hand-built marketing site from R2 (client-sites bucket) under the
 * SITE_PREFIX key prefix, with cleanUrls, the vercel.json redirects, the site
 * CSP/security headers, agent markdown negotiation (Accept: text/markdown ->
 * serve the .md sibling), and www -> apex canonicalization.
 */

const SECURITY_HEADERS = {
  "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
  "Content-Security-Policy":
    "default-src 'self'; script-src 'self' 'unsafe-inline' https://www.loom.com; " +
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
    "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; " +
    "connect-src 'self' https://clients.moonraker.ai; " +
    "frame-src 'self' https://www.youtube-nocookie.com https://www.youtube.com " +
    "https://player.vimeo.com https://open.spotify.com https://embed.podcasts.apple.com " +
    "https://gamma.app https://www.loom.com; frame-ancestors 'none'; base-uri 'self'; " +
    "form-action 'self'; upgrade-insecure-requests",
};

// permanent (308) redirects ported from vercel.json
const REDIRECTS = {
  "/contact": "/book-a-call",
  "/privacy-policy": "/privacy",
  "/terms-of-service": "/terms",
};

const CT = {
  html: "text/html; charset=utf-8", md: "text/markdown; charset=utf-8",
  css: "text/css; charset=utf-8", js: "text/javascript; charset=utf-8",
  png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", webp: "image/webp",
  avif: "image/avif", svg: "image/svg+xml", ico: "image/x-icon", gif: "image/gif",
  txt: "text/plain; charset=utf-8", xml: "application/xml; charset=utf-8",
  json: "application/json; charset=utf-8", woff2: "font/woff2", woff: "font/woff",
  mp4: "video/mp4", webm: "video/webm", pdf: "application/pdf",
};
function extOf(k) { const i = k.lastIndexOf("."); return i < 0 ? "" : k.slice(i + 1).toLowerCase(); }
function contentTypeFor(key, obj) {
  const meta = obj && obj.httpMetadata && obj.httpMetadata.contentType;
  if (meta && meta.toLowerCase() !== "application/octet-stream") return meta;
  return CT[extOf(key)] || "application/octet-stream";
}
function cacheControlFor(key, env) {
  const ext = extOf(key);
  const htmlTtl = parseInt(env.DEFAULT_HTML_TTL || "300", 10);
  const assetTtl = parseInt(env.DEFAULT_ASSET_TTL || "31536000", 10);
  if (ext === "html" || ext === "md" || ext === "xml" || ext === "txt" ||
      key.endsWith("robots.txt") || key.endsWith("sitemap.xml") || key.endsWith("llms.txt")) {
    return `public, max-age=${htmlTtl}, s-maxage=86400, stale-while-revalidate=604800`;
  }
  return `public, max-age=${assetTtl}, immutable`;
}

function wantsMarkdown(request) {
  return (request.headers.get("Accept") || "").toLowerCase()
    .split(",").map((p) => p.trim().split(";")[0]).includes("text/markdown");
}

function redirect(to, status = 308) {
  return new Response(null, { status, headers: { Location: to } });
}
function notFound() {
  return new Response("Not found", { status: 404, headers: { "Content-Type": "text/plain; charset=utf-8" } });
}

// path -> R2 key (relative, before prefix). null => caller handles redirect/special.
function keyForPath(pathname) {
  let rest = pathname.replace(/^\/+/, "").replace(/\/+$/, "");
  if (rest === "") return "index.html";
  const last = rest.split("/").pop() || "";
  if (last.includes(".")) return rest;        // explicit file (asset, llms.txt, ...)
  return `${rest}/index.html`;                 // clean URL -> directory index
}

async function handle(request, env) {
    const url = new URL(request.url);
    const host = url.hostname;
    const apex = env.APEX_HOST || "moonraker.ai";
    const prefix = env.SITE_PREFIX || "moonraker-website";

    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405 });
    }

    // www / other moonraker.ai subdomain -> apex, preserve path + query.
    // workers.dev passes through so the site can be tested on its own host.
    if (host !== apex && !host.endsWith(".workers.dev")) {
      return redirect(`https://${apex}${url.pathname}${url.search}`, 308);
    }

    // explicit redirects (cleanUrls: match without trailing slash)
    const normalized = url.pathname !== "/" ? url.pathname.replace(/\/+$/, "") : "/";
    if (REDIRECTS[normalized]) return redirect(REDIRECTS[normalized] + url.search, 308);

    // trailingSlash:false -> strip trailing slash (except root)
    if (url.pathname !== "/" && url.pathname.endsWith("/")) {
      return redirect(url.pathname.replace(/\/+$/, "") + url.search, 301);
    }

    // favicon -> logo asset
    let relKey = url.pathname === "/favicon.ico" ? "assets/logo.png" : keyForPath(url.pathname);
    const head = request.method === "HEAD";

    // markdown negotiation for HTML pages
    if (wantsMarkdown(request) && relKey.endsWith(".html")) {
      const mdRel = relKey.replace(/\.html$/, ".md");
      const mdObj = head ? await env.SITE_R2.head(`${prefix}/${mdRel}`) : await env.SITE_R2.get(`${prefix}/${mdRel}`);
      if (mdObj) {
        const h = new Headers(SECURITY_HEADERS);
        h.set("Content-Type", CT.md);
        h.set("Cache-Control", cacheControlFor(mdRel, env));
        h.set("Vary", "Accept");
        if (typeof mdObj.size === "number") {
          h.set("Content-Length", String(mdObj.size));
          h.set("x-markdown-tokens", String(Math.max(1, Math.round(mdObj.size / 4))));
        }
        if (mdObj.httpEtag) h.set("ETag", mdObj.httpEtag);
        return new Response(head ? null : mdObj.body, { status: 200, headers: h });
      }
    }

    let key = `${prefix}/${relKey}`;
    let obj = head ? await env.SITE_R2.head(key) : await env.SITE_R2.get(key);
    if (!obj) return notFound();

    const h = new Headers(SECURITY_HEADERS);
    h.set("Content-Type", contentTypeFor(key, obj));
    h.set("Cache-Control", obj.httpMetadata?.cacheControl || cacheControlFor(key, env));
    if (obj.httpEtag) h.set("ETag", obj.httpEtag);
    if (typeof obj.size === "number") h.set("Content-Length", String(obj.size));
    if (key.endsWith(".html")) {
      h.set("Link", '</llms.txt>; rel="describedby", </sitemap.xml>; rel="sitemap"');
      h.set("Vary", "Accept");
    }
    return new Response(head ? null : obj.body, { status: 200, headers: h });
}

export default {
  // Edge-cache GET responses (like CF auto-caches static origins) so we are not
  // hitting R2 on every request. Markdown variants cache under a distinct key.
  async fetch(request, env, ctx) {
    if (request.method !== "GET") return handle(request, env);
    const cache = caches.default;
    const u = new URL(request.url);
    const md = (request.headers.get("Accept") || "").toLowerCase().includes("text/markdown");
    const cacheKey = new Request(`${u.origin}${u.pathname}${md ? "__md" : ""}`, { method: "GET" });
    const hit = await cache.match(cacheKey);
    if (hit) return hit;
    const resp = await handle(request, env);
    const cc = resp.headers.get("Cache-Control") || "";
    if (resp.status === 200 && cc.includes("max-age")) {
      ctx.waitUntil(cache.put(cacheKey, resp.clone()));
    }
    return resp;
  },
};
