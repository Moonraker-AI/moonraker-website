---
name: moonraker-web-embeds
description: >
  Add or update a third-party media embed (YouTube, Vimeo, Spotify, Apple
  Podcasts, Gamma slide decks, Loom) on the Moonraker marketing site
  (the moonraker-website repo, the static HTML site served at moonraker.ai),
  especially the Knowledge Hub page. Covers the MANDATORY Cloudflare-worker CSP
  update (worker/src/index.js: the site CSP is allowlist-only and silently blocks any
  iframe whose origin is not listed), the per-platform embed-URL and card-markup
  patterns, and the Gamma publish-for-embed / client-side-title gotchas. Use when
  the operator says "add a video / podcast / webinar / slide deck to the site",
  "add an embed", "the embed is blank / not showing / blocked", "add it to the
  Knowledge Hub", or hands over YouTube / Vimeo / Spotify / Apple / Gamma links
  for moonraker.ai. Do NOT use for: client managed sites (moonraker-site-template
  / sites.moonraker.ai, a different repo with a Cloudflare-worker CSP), the
  client-hq app, or non-embed content edits.
---

# Adding embeds to the Moonraker marketing site

Repo: `~/Desktop/Moonraker/Biz/Dev/moonraker-website` (Astro, served in prod by
the Cloudflare worker in `worker/` reading the built site from R2). Embeds live
mostly in `src/pages/knowledge-hub.astro`.

## Step 1 (ALWAYS FIRST): extend the CSP frame-src

The site ships a strict Content-Security-Policy in the Cloudflare worker
(`worker/src/index.js`, the `SECURITY_HEADERS` map). `frame-src`
is an allowlist: an iframe whose origin is NOT listed is blocked silently (blank
frame + a CSP error in the browser console). This is the single most common
embed bug here. The CSP once allowed only Loom, which blocked every other embed.

Before adding any iframe, open `worker/src/index.js` and add the platform origin
to the `frame-src` directive inside the `Content-Security-Policy` header value.
A CSP change takes effect only after the worker is redeployed (`wrangler deploy`
from `worker/`), which is a separate step from the site content rebuild. Current
allowed origins:

```
frame-src 'self' https://www.youtube-nocookie.com https://www.youtube.com https://player.vimeo.com https://open.spotify.com https://embed.podcasts.apple.com https://gamma.app https://www.loom.com;
```

New platform? Add its embed origin here too, or the embed will not render.

## Step 2: build the embed URL + card

Per-platform embed URL forms and recommended iframe attributes:

- **YouTube** (use the privacy domain): `https://www.youtube-nocookie.com/embed/<VIDEO_ID>`
  16:9. `allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen`
- **Vimeo**: `https://player.vimeo.com/video/<ID>?h=<HASH>&title=0&byline=0&portrait=0`
  (the `h=` hash is in the share URL). 16:9. `allow="autoplay; fullscreen; picture-in-picture" allowfullscreen`
- **Spotify** (episode): `https://open.spotify.com/embed/episode/<ID>?utm_source=generator`
  fixed `height="152"`. `allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"`
- **Apple Podcasts**: `https://embed.podcasts.apple.com/us/podcast/<slug>/id<showId>?i=<episodeId>`
  fixed `height="175"` + `sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation"`
- **Gamma** (slide decks): `https://gamma.app/embed/<id>` where `<id>` is the
  trailing token of the `gamma.app/docs/...-<id>` URL. See Gamma gotchas below.
- **Loom**: `https://www.loom.com/embed/<VIDEO_ID>`

Always set a descriptive `title="..."` on the iframe (accessibility) and
`loading="lazy"`.

## Step 3: Knowledge Hub layout

Tabs are a hand-rolled accessible tablist (click + arrow-key + `#hash` deep-link),
JS at the bottom of `src/pages/knowledge-hub.astro`. Layout rules:

- **Videos & Webinars**: 2 columns, `.kh-grid.two`, 16:9 (`.kh-embed`).
- **Podcasts**: 1 column, `.kh-stack`, native embed height (`.kh-audio`).
- **Slide Decks**: 1 column, `.kh-stack`, `.kh-embed.deck` (14/9), grouped under
  `.kh-year` headings, newest year first.

Card pattern:

```html
<article class="kh-card">
  <div class="kh-embed deck"><iframe src="https://gamma.app/embed/<id>" loading="lazy" allow="fullscreen" title="EXACT TITLE"></iframe></div>
  <div class="kh-card-body"><div class="kh-card-eyebrow">SERIES OR SOURCE</div><h3>SPECIFIC TITLE</h3></div>
</article>
```

Update the tab `<span class="kh-count">N</span>` when the item count changes.

## Gamma gotchas

- The per-doc **title is rendered client-side**. A plain fetch of a
  `gamma.app/docs/...` URL returns the generic "Gamma" app shell
  (`og:title = "Gamma"`), not the deck title. Get the title from the Share >
  Embed snippet's `title` attr, or ask the operator.
- The deck must be **published for embed** in Gamma (Share > Publish/Embed,
  anyone-with-link). An unpublished deck returns HTTP 403 with
  `x-frame-options: SAMEORIGIN`, so it will not frame anywhere off gamma.app.
- The embed id is just the trailing token of the normal doc URL, so plain doc
  links are enough once embedding is enabled.

## Verify before commit

- `node --check worker/src/index.js` (valid JS after the CSP edit).
- Em-dash scan: `git diff --cached -U0 | grep '^+' | grep -nP '\x{2014}'` must be
  empty (no em-dashes anywhere, project rule).
- After deploy, load the page and confirm each iframe actually frames. A blank
  frame almost always means the origin is missing from `frame-src` (Step 1).
