# moonraker-website: context for AI coding agents

This repo is the public Moonraker marketing site (`moonraker.ai`), an Astro
build. It is NOT a client managed site (those live in `moonraker-site-template`
and serve at `sites.moonraker.ai/<slug>/`).

This file auto-loads every Claude Code session (terminal and web). Read it in
full before editing anything.

## How it is served and deployed

- **Astro** source: pages in `src/pages/`, one `BaseLayout`, chrome in
  `globals.css`.
- **Prod serve:** a Cloudflare Worker in `worker/` (`worker/src/index.js`,
  `worker/wrangler.toml`) reads the built site from R2 and adds the security
  headers, CSP, redirects, and agent markdown negotiation.
- Two deploy halves, each needs tokens not present on the web:
  - **Site content** (the Astro build) publishes to R2 from the VPS.
  - **Worker** (CSP, headers, redirects, routing) deploys via
    `wrangler deploy` from `worker/`.
- **A push to main publishes the STATIC half within about 5 minutes.** The VPS
  cron runs `scripts/publish_watch.py`, which watches both the published
  `content_pieces` set and the tip of `origin/main`, and runs
  `scripts/vps_publish.sh` when either moves. Until 2026-08-02 it watched only
  `content_pieces`, so a plain code commit reached the live site ONLY when
  somebody ran `vps_publish.sh` by hand; the marker and the publish log both
  sat frozen from 2026-06-08.
- **A push to main does NOT deploy the worker.** Anything under `worker/`
  (CSP, security headers, redirects, `cacheControlFor`, markdown negotiation)
  still needs `cd worker && npx wrangler deploy` from a machine holding a
  Cloudflare token with Workers Scripts edit rights. Nothing automates it.
- **There is no `vercel.json` and no Vercel auto-deploy.** Older notes that say
  "static HTML, Vercel auto-deploy" or put the CSP in `vercel.json` are stale.
  The CSP lives in `worker/src/index.js`.

**On Claude Code web** you can do all the authoring token-less (edit `.astro`
pages, `globals.css`, components, and the worker CSP file). You cannot run the
deploys (R2 publish needs the VPS, `wrangler deploy` needs a Cloudflare token).
Make the edits and hand the deploy to the operator, or open it as a follow-up.

## The embed gotcha (most common bug here)

The site CSP is allowlist-only. An iframe whose origin is not in the
`frame-src` directive of the `Content-Security-Policy` in
`worker/src/index.js` is blocked silently (blank frame + a console CSP error).
Adding any new embed platform means adding its origin there AND redeploying the
worker, which is separate from the site content rebuild. The `moonraker-web-embeds`
skill covers the full recipe.

## The asset-cache gotcha (unhashed assets update slowly, hashed never)

`cacheControlFor` in `worker/src/index.js` (since 2026-08-03) splits assets in
two. Content-hashed keys (anything under `_astro/`, or a filename carrying an
8+ hex-char hash segment like
`public/assets/case-studies/revibe-therapy-hero.52d879e6.avif`) serve
`public, max-age=31536000, immutable` and can NEVER be updated in place.
Everything else (the bulk of `public/` under literal names) serves
`public, max-age=86400, stale-while-revalidate=604800`, so an in-place
republish reaches visitors within about a day (returning browsers may see the
stale copy once while revalidating).

The edge cache key is still `origin + pathname` alone, dropping the query
string, so `?v=2` busts nothing. For an immediate flip, or for anything
hashed, **replace the asset by RENAMING it** with a content hash and update
every reference. Anything imported through Vite gets this for free, which is
why `BaseLayout.astro` imports `../scripts/site.js?url` rather than hardcoding
`/assets/site.js`. A Cloudflare purge only clears the edge, not the browsers
that already hold the old bytes.

HTML and the text files (`.md`, `.xml`, `.txt`, `robots.txt`, `sitemap.xml`,
`llms.txt`) sit on a 300s TTL and do self-flip within about five minutes of a
publish. Only assets are the trap.

## The extraction gotcha (page to shared component)

Pulling a chunk of a page into `src/components/*.astro` moves its CSS from
page-scoped to shared, and the same class of bug lands three ways: rules that
were harmless while one page could see them start applying everywhere. Check
all three before committing an extraction.

1. **Astro strips `:global()` only inside a SCOPED `<style>` block.** Widgets
   that build elements at runtime need `<style is:global>`, because scoped
   rules get a `data-astro-cid` stamped at BUILD time and never match a node
   created later. But moving selectors into that global block verbatim ships
   the literal text `:global(...)`, which browsers discard. It cost
   `BookingWidget.astro` 32 dead selectors and every runtime-created date and
   time pill lost its styling. Inside `is:global`, write plain selectors.
2. **A component's own copy of a design-system class now overrides the design
   system.** `.btn-primary` inside the booking widget was fine page-scoped;
   global, it redefined the button on every page hosting the widget and
   reintroduced white-on-green at 2.08:1. Bound every widget rule with the
   component root (`#bookingWorkspace .btn-primary`, see
   `src/styles/booking-widget.css`) and take colour from the tokens in
   `globals.css` rather than restating it.
3. **One class on two surfaces needs two rules, not one compromise colour.**
   `.tier-tag` in `services.astro` sits on a light card and on the navy
   featured card, and no single colour passes on both: the light case takes
   `--color-primary-text`, `.tier-card.featured .tier-tag` takes brand green.
   Resolve contrast against the element's NEAREST background, not from the
   selector name, and against the DARKEST light surface in use, not white.

## Writing conventions (enforced)

1. **No em-dashes (U+2014) anywhere you generate text.** Commit messages, docs,
   comments, copy, everything. Use a comma, colon, period, or parentheses.
2. **No emojis** anywhere unless explicitly requested.
3. **Stage with explicit paths, never `git add -A` / `git add .`** Check
   `git diff --cached --name-only` before committing.

## Skills in this repo

- `moonraker-web-embeds` - add or update a third-party media embed (YouTube,
  Vimeo, Spotify, Apple Podcasts, Gamma, Loom) on the marketing site, including
  the mandatory worker CSP `frame-src` update.
- `impeccable` - design, critique, polish, or harden any UI surface on the
  marketing site (typography, color, spacing, motion, responsive, UX writing).
  Vendored duplicate: the canonical copy lives in
  `client-hq/.claude/skills/impeccable/`; edit there and run its
  `sync-vendored.sh`, never edit the copy here.

The canonical cross-repo agent context (AGENT_LOG, the broader memory library)
lives in the `client-hq` repo's `AGENTS.md`. This file is the self-sufficient
context for working in THIS repo.
