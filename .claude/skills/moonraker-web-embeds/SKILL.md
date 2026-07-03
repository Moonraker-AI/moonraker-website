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
user_invocable: true
disable_model_invocation: false
allowed-tools: [Read, Edit, Write, Bash, Grep, Glob]
---

# Adding embeds to the Moonraker marketing site

Add a third-party media embed to moonraker.ai, including the Cloudflare-worker
CSP allowlist change without which the iframe renders blank.

Repo: `moonraker-website` (Astro, served in prod by the Cloudflare worker in
`worker/` reading the built site from R2). Operator-machine example path:
`~/Desktop/Moonraker/Biz/Dev/moonraker-website`. Embeds live mostly in
`src/pages/knowledge-hub.astro`.

## Gotchas (read before touching anything)

- **The worker CSP silently blocks unlisted iframe origins.** `frame-src` in
  `worker/src/index.js` is an allowlist: an iframe whose origin is NOT listed
  shows a blank frame plus a CSP error in the browser console, nothing else.
  This is the single most common embed bug here. The CSP once allowed only
  Loom, which blocked every other embed.
- **A CSP change takes effect only after a worker redeploy** (`wrangler deploy`
  from `worker/`). That is a separate step from the site content rebuild;
  shipping only the content leaves the new embed blocked.
- **Gamma: the per-doc title is rendered client-side.** A plain fetch of a
  `gamma.app/docs/...` URL returns the generic "Gamma" app shell
  (`og:title = "Gamma"`), not the deck title. Get the title from the Share >
  Embed snippet's `title` attr, or ask the operator.
- **Gamma: the deck must be published for embed** (Share > Publish/Embed,
  anyone-with-link). An unpublished deck returns HTTP 403 with
  `x-frame-options: SAMEORIGIN`, so it will not frame anywhere off gamma.app.
- **Gamma: the embed id is the trailing token** of the normal
  `gamma.app/docs/...-<id>` URL, so plain doc links are enough once embedding
  is enabled.
- **No em-dashes (U+2014) in anything you write** (project rule); scan before
  committing (see Verify).

## Procedure

### Step 1 (ALWAYS FIRST): extend the CSP frame-src

Check the worker file exists before editing (a repo reorg must fail loudly):
`test -f worker/src/index.js || stop and report`.

Open `worker/src/index.js` and add the platform's embed origin to the
`frame-src` directive inside the `Content-Security-Policy` header value (the
`SECURITY_HEADERS` map). Current allowed origins:

```
frame-src 'self' https://www.youtube-nocookie.com https://www.youtube.com https://player.vimeo.com https://open.spotify.com https://embed.podcasts.apple.com https://gamma.app https://www.loom.com;
```

New platform? Add its embed origin here too, or the embed will not render.
Remember (gotchas above): the change is live only after the worker redeploy in
Step 4.

### Step 2: build the embed URL + card

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
  trailing token of the `gamma.app/docs/...-<id>` URL. See the Gamma gotchas above.
- **Loom**: `https://www.loom.com/embed/<VIDEO_ID>`

Always set a descriptive `title="..."` on the iframe (accessibility) and
`loading="lazy"`.

### Step 3: Knowledge Hub layout

Check the page exists: `test -f src/pages/knowledge-hub.astro || stop and report`.

Tabs are a hand-rolled accessible tablist (click + arrow-key + `#hash`
deep-link), JS at the bottom of `src/pages/knowledge-hub.astro`. Layout rules:

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

### Step 4: ship it (GATED: needs plain go-ahead)

Both halves are outward-facing; stop and get an explicit yes before either.

1. Commit and push the content change to `moonraker-website` main (stage with
   explicit paths, never `git add -A`).
2. If Step 1 touched the CSP, redeploy the worker: `wrangler deploy` from
   `worker/`. Without this the new embed stays blocked regardless of the
   content deploy.

## Verify

1. Syntax-check the worker after the CSP edit:

   ```
   $ node --check worker/src/index.js
   $ echo $?
   0
   ```

   (No output on success; any output is a syntax error, fix before shipping.)

2. Em-dash scan on the staged diff, must print nothing (grep exits 1):

   ```
   $ git diff --cached -U0 | grep '^+' | grep -nP '\x{2014}'
   $ echo $?
   1
   ```

3. After the worker deploy, confirm the new origin is in the served CSP header:

   ```
   $ curl -sI https://moonraker.ai/ | grep -i content-security-policy
   content-security-policy: ...; frame-src 'self' ... https://<new-embed-origin> ...; ...
   ```

4. Load the page in a browser and confirm each iframe actually frames (player
   chrome visible, not a blank box). A blank frame almost always means the
   origin is missing from `frame-src` (Step 1) or the worker was not redeployed.

## Failure modes

- **Blank iframe + CSP error in the browser console**: the embed origin is not
  in `frame-src`, or the worker redeploy was skipped. Fix Step 1, redeploy the
  worker, hard-reload.
- **Gamma deck frames on gamma.app but nowhere else (HTTP 403,
  `x-frame-options: SAMEORIGIN`)**: the deck is not published for embed. Ask
  the operator to enable Share > Publish/Embed (anyone-with-link); no code
  change fixes this.
- **Wrong or generic "Gamma" title on the card**: the title was scraped from
  the doc URL, which returns the app shell. Take the title from the Share >
  Embed snippet or the operator.
- **`wrangler deploy` fails (auth or config error)**: nothing shipped; the old
  CSP is still live. Resolve credentials/wrangler.toml and rerun; do not
  declare the embed live until Verify step 3 passes.
- **`node --check` reports a syntax error**: the CSP edit broke the worker
  source. Fix before any deploy; a broken worker takes down the whole site,
  not just the embed.

## Rollback

- **Worker (CSP)**: `git revert` the CSP commit in `moonraker-website`, then
  `wrangler deploy` from `worker/` again. The worker serves whatever was
  deployed last, so redeploying the reverted source restores the prior CSP.
- **Site content**: `git revert` the content commit and push; the normal
  build/deploy path republishes the previous page.
- Nothing in this skill is unrecoverable: both surfaces redeploy from git
  history.
