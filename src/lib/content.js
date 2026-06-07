// Build-time data access for the moonraker.ai blog.
//
// The site is static (built locally, shipped to R2), so these run at BUILD time
// only: the anon key never reaches the shipped HTML. content_pieces has an anon
// SELECT RLS policy, so the anon key is sufficient to read published rows. The
// un-redacted source (content_source_raw) has NO anon policy and is unreachable
// here by design (the redaction firewall).
//
// Env (moonraker-website/.env.local, gitignored): SUPABASE_URL, SUPABASE_ANON_KEY.
// If either is missing the build does not fail: the blog renders empty so every
// other page still builds.

const SUPABASE_URL =
  import.meta.env.SUPABASE_URL || process.env.SUPABASE_URL || '';
const SUPABASE_ANON_KEY =
  import.meta.env.SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY || '';

// Columns that are safe to surface publicly. body_md / problem / approach /
// outcome are REDACTED content only (the schema guarantees this). We never select
// from content_source_raw.
const LIST_COLS = 'id,type,title,slug,excerpt,published_at';
const FULL_COLS =
  'id,type,title,slug,excerpt,problem,approach,outcome,metrics,body_md,seo,published_at,updated_at';

async function query(params) {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    console.warn('[content] SUPABASE_URL / SUPABASE_ANON_KEY missing; blog will render empty.');
    return [];
  }
  const url = `${SUPABASE_URL}/rest/v1/content_pieces?${params}`;
  const res = await fetch(url, {
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    },
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`[content] Supabase ${res.status} ${res.statusText}: ${detail.slice(0, 300)}`);
  }
  return res.json();
}

// Every published piece with a slug, newest first. Used by the listing + sitemap.
export async function getPublishedPieces() {
  return query(
    `status=eq.published&slug=not.is.null&order=published_at.desc.nullslast&select=${LIST_COLS}`,
  );
}

// One published piece by slug (full body). Used by [slug].astro.
export async function getPieceBySlug(slug) {
  const rows = await query(
    `status=eq.published&slug=eq.${encodeURIComponent(slug)}&limit=1&select=${FULL_COLS}`,
  );
  return rows[0] || null;
}

// Human label for a content type.
export const TYPE_LABELS = {
  case_report: 'Case Report',
  case_study: 'Case Study',
  newsletter: 'Newsletter',
  guide: 'Guide',
};

// Date -> "June 7, 2026" (build runs in UTC; pieces store timestamptz).
export function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d)) return '';
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC',
  });
}
