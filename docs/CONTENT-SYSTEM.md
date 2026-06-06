# Moonraker Content System: design + build plan

Status: DRAFT for operator review (2026-06-07)
Owner: chris@moonraker.ai
Scope: a repeatable engine that turns weekly raw inputs (Fathom prospect calls,
the client-hq newsletter, anonymized client results) into a canonical content
record, gates it through human review (with redaction where required), publishes
it to a real blog on moonraker.ai, and emits per-channel text variants for
LinkedIn / Quora / X.

## 1. Core principle

Write once, in a structured canonical form. Generate every channel output FROM
that record. Never author per-channel by hand. Redaction is a hard, human-signed
gate that sits before anything leaves the building.

Three layers:

1. Canonical store + review UI: **client-hq** (Supabase + `/admin`).
2. Generation + redaction + build/deploy workers: **moonraker-agent** (VPS).
3. Render target: **moonraker.ai**, converted from static HTML to **Astro**,
   blog pulled from the canonical store at build time.

## 2. Locked decisions (operator, 2026-06-07)

- Blog renders from a full **Astro conversion** of moonraker-website (also kills
  the hand-duplicated nav/footer maintenance pain).
- Canonical content lives in **client-hq Supabase**.
- Phase 1 syndication = **blog + text exports** (LinkedIn / Quora / X drafts for
  manual paste). No auto-posting and no YouTube video yet.
- Blog URL = dedicated **/blog/** (Knowledge Hub stays the curated embeds page).
- Fathom ingest = **Fathom API** (chris + scott keys live in client-hq env), not
  manual paste. The API calls run server-side in client-hq.
- Client case studies = **anonymized by default** (vertical + relative metrics,
  no brand); upgrade individual ones to named-with-logo later if a client agrees.
- Management UI lives **entirely in client-hq /admin**, under a new **Marketing**
  left-nav section. The website is a dumb render target only; no authed admin on
  the static R2 site. The existing standalone Newsletter tab relocates into
  Marketing alongside the new Content Studio.

## 3. Content sources and their pipelines

| Source | Input | Generated output | Redaction |
|---|---|---|---|
| Fathom prospect call | transcript | generalized "what we'd do" case report | REQUIRED (brand, names, location, $, competitors) |
| client-hq newsletter | `newsletters` row | blog repurpose + "from the newsletter" series | none (already public-facing) |
| Client results | `contacts` + `deliverables` + `task_completion_entries` + GSC | anonymized case study with real relative metrics | REQUIRED (domain, vertical specifics); keep numbers |

GEO note: Fathom case reports are naturally Q&A shaped ("what would you do about
[problem]?"), which is exactly what ChatGPT / Perplexity / Gemini surface. Every
piece emits Article + FAQPage schema, a `.md` sibling (worker markdown
negotiation already does this), an `llms.txt` entry, and a sitemap entry. The
blog doubles as AI-search bait and feeds the isitagentready Level 3 posture.

## 4. Data model (client-hq Supabase, new tables)

### `content_pieces` (canonical record)
- `id`, `created_at`, `updated_at`
- `type`: `case_report` | `case_study` | `newsletter` | `guide`
- `source_type`: `fathom` | `newsletter` | `client` | `manual`
- `source_ref`: text (fathom transcript id, `newsletters.id`, `contacts.id`)
- `title`, `slug`, `excerpt`
- `problem`, `approach`, `outcome` (text), `metrics` (jsonb) -- the structured spine
- `body_md` (text) -- canonical long-form markdown (REDACTED content only)
- `seo` (jsonb): `keywords[]`, `meta_description`, `og_image`, `faq[]` (for FAQPage)
- `redaction_status`: `n_a` | `needs_redaction` | `redacted` | `approved`
- `redaction_notes` (text)
- `status`: `draft` | `review` | `approved` | `scheduled` | `published`
- `author`: `ai` | `human`, `reviewed_by` (admin id), `review_notes`
- `publish_at` (timestamptz, nullable), `published_at`, `publish_url`

### `content_source_raw` (restricted, never read by the build)
- `id`, `content_piece_id` (fk), `raw_text` (the un-redacted transcript/source)
- RLS: admin-only. This row is the side-by-side "original" in the review diff.
- The blog build query NEVER touches this table. Only `content_pieces` with
  `status='published'` (and, for case_report/case_study, `redaction_status='approved'`).

### `content_variants` (per-channel outputs)
- `id`, `content_piece_id` (fk)
- `channel`: `blog` | `linkedin` | `quora` | `x` | `youtube_script`
- `body` (text), `meta` (jsonb: char count, hook, hashtags, question-target)
- `status`: `draft` | `approved`, `exported_at`

Register `content_pieces` + `content_variants` in `api/_lib/action-schema.js`
allowlist. Do NOT allowlist `content_source_raw` for generic mutation; it gets a
dedicated, auth-gated read route only.

## 5. Generation workers (moonraker-agent VPS)

New tasks following the existing `tasks/<name>.py` async pattern (params dict +
status_callback), calling Claude via the already-installed Anthropic SDK, reading
and writing client-hq Supabase via the existing client:

- `generate_case_report` (Fathom): redact pass FIRST (strict entity-stripping +
  generalization prompt) -> then problem/approach/outcome + body_md + seo + faq.
  Writes draft `content_pieces` (redaction_status=`redacted`) + `content_source_raw`.
  NOTE: the Fathom API calls (list calls across chris + scott, fetch a transcript)
  run in client-hq `/api/fathom-*` routes because the Fathom keys live in the
  client-hq env. That route stores the raw transcript into `content_source_raw`,
  then triggers this agent task with the raw text. Fathom creds are never copied
  to the VPS.
- `repurpose_newsletter`: read a `newsletters` row, reformat to blog + series.
- `generate_case_study`: pull `deliverables` + `task_completion_entries` + GSC
  (report_snapshots / GSC domain-wide-delegation service account), anonymize
  domain/vertical, KEEP real relative deltas ("+240% impressions, 90 days").
- `generate_variants`: from an approved piece, emit channel drafts into
  `content_variants` (LinkedIn 1300-char hook+post no body links; Quora
  question-targeted answer; X thread).

Triggered from the admin UI (button -> `/api/...` -> agent task endpoint) and on
a weekly cron for the always-on inputs.

## 6. Management UI: client-hq /admin "Marketing" section

All management lives in client-hq, grouped under a new **Marketing** left-nav
section. The website never gets an authed admin. Plain HTML pages importing
`admin-base.css`, mutations via new `/api/*.js` routes, `requireAdmin` auth,
`mr-modal-veil` + `toast.js` for UX, consistent with every other admin surface.

Marketing left-nav items:

- **Newsletter** (relocated from the current standalone top-level tab, unchanged
  flow: `newsletters` + `newsletter_stories` + Resend send cron).
- **Content Studio** (new): the `content_pieces` pipeline, one surface:
  - "New from Fathom call" picker (lists recent calls across chris + scott via
    the client-hq Fathom API route), "New from client" (case study), "New from
    newsletter" (repurpose), "New blank".
  - Status board: Draft / Review / Approved / Scheduled / Published.
  - Review modal: for redacted types, **side-by-side original
    (`content_source_raw`, admin-only) vs redacted (`body_md`)** so a human
    verifies nothing leaked. Edit inline, approve (sets `status=approved`,
    `redaction_status=approved`, records reviewer).
  - Schedule: set `status=scheduled` + `publish_at`.
  - Variants: review/edit per-channel drafts, "copy" to export (Phase 2).

Publish guard (server-side): refuse to publish a `case_report`/`case_study` whose
`redaction_status != approved`.

## 7. Render target: moonraker.ai Astro conversion

### Phase 0 conversion (foundation, ships before any pipeline)
- Scaffold Astro in moonraker-website. Port the 17 pages into `src/pages/`
  mirroring exact URL structure (incl. `/core-marketing-system/*` and the
  `/index.html` -> clean-URL routes the worker expects).
- Extract the hand-duplicated `<nav>` + `<footer>` into one `BaseLayout.astro`;
  compute active link from `Astro.url.pathname` (today there is NO active state).
- Move `styles/globals.css` to a global import; move each page's inline `<style>`
  into its `.astro` component (scoped). Keep the inline pre-paint theme script
  via `<script is:inline>` in the layout head (no theme flash).
- Port `assets/site.js` (nav dropdowns, auto-hide nav, FAQ accordion, theme
  toggle, embed facade, reveal observer) as-is; `public/assets/` keeps exact
  `/assets/...` paths so nothing rebreaks.
- Keep the **Cloudflare worker authoritative** for redirects + CSP + markdown
  negotiation. Astro must NOT emit competing redirects. Retire the legacy
  (unused) `vercel.json`.
- Port AI-file generation (robots/sitemap/llms.txt) into the Astro build so they
  stay correct as the blog grows (today they are hand-static). Reuse the
  materialize.mjs helper shapes from moonraker-site-template.
- Acceptance: parity check (all existing routes resolve, 3 worker redirects hold,
  llms/sitemap/robots present, embeds still load), then deploy to R2.

### Blog (Phase 1)
- `src/pages/blog/index.html` (listing) + `src/pages/blog/[slug].astro` (post),
  mirroring the proven ITR/Full Tilt content-collection pattern.
- A pre-build step (small Supabase fetch, materialize-style) pulls
  `content_pieces` where `status='published'` into `src/content/blog/*.md` (or a
  data json), then `astro build`. Emits per-post Article + FAQPage JSON-LD, `.md`
  sibling, llms.txt + sitemap entries.

## 8. Build + deploy integration

The blog is DB-driven, so a git-push build will not see new content. The build
must be event/cron triggered by the pipeline. Reuse, do not reinvent:

- New agent task `moonraker_site_build`: fetch published `content_pieces` ->
  write blog collection -> `_run_build()` (npm install + astro build) ->
  `_deploy_dist()` to R2 with the existing cache-control rules -> patch status.
- Triggers: (a) on publish/approve from admin, (b) a cron that flips
  `status=scheduled` + `publish_at<=now()` to `published` then fires the build.
- `scripts/publish_r2.sh` stays as the manual fallback for the static pages.

Note: this is the company's own marketing site, not a per-client site, so the
"no GitHub Actions for client deploys" rule does not directly apply, but the
DB-driven nature makes the VPS task the right home anyway (it already has the
Anthropic SDK, Supabase, and R2 helpers in one place).

## 9. Syndication (Phase 1 = export only)

`generate_variants` writes channel drafts; admin reviews + copies. No platform
APIs yet. Phase 3 adds LinkedIn API auto-post once the flow is proven (platforms
penalize raw automation; prove quality first). YouTube in Phase 3 is script +
description + chapters only; video production is the real cost and is deferred.

## 10. Phasing

- **Phase 0**: Astro conversion of moonraker.ai (parity, deploy). No pipeline.
- **Phase 1**: `content_pieces` (+ raw + variants) tables; admin review UI w/
  redaction diff; `generate_case_report` + `repurpose_newsletter`; blog render;
  `moonraker_site_build` task + schedule cron. End-to-end on one Fathom report.
- **Phase 2**: `generate_case_study` (GSC integration); `generate_variants` +
  export UI for LinkedIn / Quora / X.
- **Phase 3**: YouTube scripts; LinkedIn (etc.) API auto-post.

## 11. Resolved + still open

Resolved 2026-06-07: blog at /blog/; Fathom via API (client-hq env keys, chris +
scott); case studies anonymized by default; management consolidated in client-hq
under a Marketing section (Newsletter + Content Studio).

Still open:
- Cadence target (posts/week) so the cron + review load is sized right.
- Fathom: pull on a cron into a "calls inbox", or only fetch on demand when the
  operator picks a call? (Leaning on-demand for v1, simpler.)
- Whether a published piece auto-fires a site rebuild immediately, or batches
  into a scheduled daily build window.
