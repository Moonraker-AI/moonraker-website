/**
 * Generate display-sized AVIF twins for the partner logos and testimonial
 * headshots (oi-178).
 *
 * The originals are 3 to 6 times larger than the box they render in: partner
 * logos are up to 2048px wide for an 80px-tall slot, headshots are 500px wide
 * for an 88px circle. Every page that shows the partner band pays for that.
 *
 * Output filenames carry the target size (-h160, -w176) rather than replacing
 * the original in place. That is not cosmetic: moonraker.ai assets are served
 * `immutable` for a year and the worker's cache key drops the query string, so
 * an in-place replacement never reaches a browser that has seen the old bytes.
 * A new path is the only cache-bust available.
 *
 * Idempotent: skips an output that already exists and is newer than its source.
 *
 *   node scripts/resize_display_assets.mjs [--force]
 */
import { readdir, stat, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ASSETS = path.join(ROOT, 'public', 'assets');
const FORCE = process.argv.includes('--force');

// [dir, output suffix, resize options]. Partner logos are constrained by
// HEIGHT (the band sets height: 56-80px, max-width 180-200px), headshots by
// WIDTH (an 88px square). Both targets are 2x for retina.
const JOBS = [
  { dir: 'partners', suffix: '-h160', resize: { height: 160, fit: 'inside', withoutEnlargement: true } },
  { dir: 'headshots', suffix: '-w176', resize: { width: 176, fit: 'inside', withoutEnlargement: true } },
];

const SOURCE_EXT = new Set(['.png', '.jpg', '.jpeg', '.webp']);

async function newer(a, b) {
  const [sa, sb] = await Promise.all([stat(a), stat(b)]);
  return sa.mtimeMs > sb.mtimeMs;
}

let saved = 0, made = 0, skipped = 0;

for (const job of JOBS) {
  const dir = path.join(ASSETS, job.dir);
  if (!existsSync(dir)) continue;
  for (const name of (await readdir(dir)).sort()) {
    const ext = path.extname(name).toLowerCase();
    if (!SOURCE_EXT.has(ext)) continue;
    const base = path.basename(name, ext);
    if (base.endsWith(job.suffix)) continue;
    const src = path.join(dir, name);
    const out = path.join(dir, `${base}${job.suffix}.avif`);
    if (existsSync(out) && !FORCE && !(await newer(src, out))) { skipped++; continue; }
    // Logos are flat art with hard edges: chroma subsampling smears them, and
    // a high effort pass is cheap at this size.
    await sharp(src)
      .resize(job.resize)
      .avif({ quality: 62, effort: 6, chromaSubsampling: '4:4:4' })
      .toFile(out);
    const [before, after] = await Promise.all([stat(src), stat(out)]);
    saved += before.size - after.size;
    made++;
    const meta = await sharp(out).metadata();
    console.log(
      `${job.dir}/${name}  ${before.size} -> ${after.size} bytes  (${meta.width}x${meta.height})`
    );
  }
}

console.log(`\n${made} written, ${skipped} up to date, ${(saved / 1024).toFixed(1)} KB saved at source`);
