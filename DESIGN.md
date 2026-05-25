# Moonraker Website Design System

## Source

The public website should align with client-facing Client HQ surfaces, especially strategy call pages, proposal pages, onboarding, diagnosis, reports, results, and campaign summaries.

## Fonts

- Heading: Outfit 800 for all authored h1, h2, h3, and h4 elements.
- Body: Inter, weights 400, 500, 600.

Although these fonts are common, they are already part of the shipped Moonraker identity. Preserve them for consistency across website, proposals, reports, onboarding, and booking surfaces.

## Color Tokens

Use the existing Moonraker token family.

```css
:root {
  --color-primary: #00D47E;
  --color-primary-hover: #00b86c;
  --color-primary-light: #B4EEE0;
  --color-primary-subtle: #DDF8F2;
  --color-bg: #F7FDFB;
  --color-surface: #FFFFFF;
  --color-border: #E2E8F0;
  --color-heading: #1E2A5E;
  --color-body: #333F70;
  --color-muted: #6B7599;
  --color-navy: #141C3A;
}
```

Dark mode can continue using the existing Client HQ palette, but public marketing pages should default to light mode. Dark navy is a structural frame, not the default page theme.

## Color Use

- Navy: top navigation, footer, strong proof bands, CTA bands, table headers, and major framework moments.
- Green: primary CTA, active navigation state, progress indicators, key highlights, bullets, selected states, form focus.
- Light green tint: badges, callouts, low-emphasis active states.
- Background: green-tinted off-white for page body.
- Surface: panels, quotes, proof modules.

Do not flood the page with green gradients. Green should feel like a signal, not wallpaper.

## Layout

- Public pages use a 1120px max-width content rhythm.
- Reading sections should alternate between unframed light sections, proof bands, and selective panels.
- Avoid repeating CTA buttons after every section.
- Avoid identical card grids except where browsing a set of proof items or results.
- Prefer varied structures: proof strips, evidence rows, process diagrams, split copy and artifacts, tables, quote panels, and dark bands.

## Components

- Site nav: dark navy, sticky when useful, compact, logo left, links center/right, green CTA.
- Buttons: 10px radius, Outfit 600 or 700, green primary, navy or outline secondary.
- Supraheadings: green text only, no enclosing pill or badge treatment above section headings.
- Badges: use sparingly for proof assets or state labels, not as section heading decoration.
- Cards: 12-14px radius, light surface, 1px border, restrained shadow at rest. On hover or focus-within, use the Moonraker pop effect: translateY(-4px to -5px), green-tinted border, and soft shadow using `cubic-bezier(.22, 1, .36, 1)`. Do not apply hover lift to CORE tab cards because the tabs already provide the interaction cue.
- Proof tiles: logo or badge first, one concise support line.
- CORE rows: letter, question, deliverables, outcome. Avoid four cloned icon cards as the only presentation.
- Partner logos: use the Client HQ / newsletter 3-3-2 order and shape: Psychology Business School, Private Practice Elevation, Traveling Therapist; Private Practice Academy, TheraSaaS, Intensive Therapy Coach; Prosperous Therapist, McCance Method. Use the original source logo assets when AVIF conversion hurts fidelity. Logos stay unboxed and static, with no hover pop or partner tooltip interaction.
- Footer: navy, simple links, low-contrast copy.

## Typography

- Hero H1: 3.5rem to 4.5rem desktop, clamp down on mobile.
- Section H2: 2rem to 2.75rem.
- All h1, h2, h3, and h4 headings use Outfit 800 unless the text is not semantically a heading.
- Body: default root size is slightly enlarged for readability; keep most body copy between 1rem and 1.125rem with line-height 1.65 to 1.75.
- Max paragraph width: 65 to 75 characters.
- Avoid long all-caps labels. Short badges only.

## Imagery and Proof

Required public proof assets:

- Google Partner badge.
- Google rating badge.
- Partner logos.
- Named testimonials with headshots where available.
- Results screenshots when available.
- Client HQ inspired visual motifs: score rings, report rows, progress markers, evidence tables.

Do not use generic AI illustrations. If imagery is not available, use product-like evidence modules from the actual system.

All pulled marketing images must be stored locally as optimized AVIF assets. Do not hotlink WordPress, Google Drive, or Client HQ image URLs from public pages. Each placed image needs meaningful `alt`, `title`, intrinsic `width` and `height`, `loading` where appropriate, and `decoding="async"`. Keep source, title, alt, usage, dimensions, and byte metadata in `assets/image-manifest.json`.

Audrey Shoen result imagery and testimonial copy are not used on the public homepage or public results page.

## Homepage Interactions

- Homepage hero stays simple: one platform-forward headline, one support paragraph, one primary call to action, and early trust badges.
- CORE pillar sections pair each pillar's problem and solution in the same section, with simple tabs to switch between the two.
- Proof modules: the homepage should show tangible product proof, such as AVIF reporting previews and non-Audrey Google Search Console result images.
- Partner logos remain static and should not get hover tooltips or interaction behavior.

## Motion

- Subtle reveal or hover motion only.
- Use transform and opacity, not layout properties.
- No bounce or elastic motion.
- Respect reduced motion.

## Copy Rules

- Every claim needs a nearby reason, proof point, or mechanism.
- Use therapist-specific language, not generic small business language.
- Keep CTAs direct: "Book a Free Strategy Call", "See the CORE System", "View Results".
- No em dashes in authored copy.

## Page Priorities

1. Home: position Moonraker, establish proof, introduce CORE, show results and testimonials, convert to strategy call.
2. CORE overview: explain the framework as the operating system.
3. Pillar pages: go deep on each pillar with deliverables, why it matters, and examples.
4. Results: proof gallery, partner trust, selected feedback, and clear filters.
5. Strategy call: conversion path with low-pressure framing.
