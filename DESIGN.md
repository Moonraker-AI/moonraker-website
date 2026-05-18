# Moonraker Website Design System

## Source

The public website should align with client-facing Client HQ surfaces, especially strategy call pages, proposal pages, onboarding, diagnosis, reports, results, and campaign summaries.

## Fonts

- Heading: Outfit, weights 600, 700, 800.
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
- Surface: panels, forms, quotes, proof modules.

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
- Badges: small, green-subtle background, uppercase only when short.
- Cards: 12-14px radius, light surface, 1px border, restrained shadow on hover only.
- Proof tiles: logo or badge first, one concise support line.
- CORE rows: letter, question, deliverables, outcome. Avoid four cloned icon cards as the only presentation.
- Footer: navy, simple links, low-contrast copy.

## Typography

- Hero H1: 3.5rem to 4.5rem desktop, clamp down on mobile.
- Section H2: 2rem to 2.75rem.
- Body: 1rem to 1.125rem, line-height 1.65 to 1.75.
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
4. Results: proof gallery, partner trust, reviews, and clear filters.
5. Strategy call: conversion path with low-pressure framing.
