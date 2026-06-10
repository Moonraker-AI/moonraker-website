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
