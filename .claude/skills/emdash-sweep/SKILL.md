---
name: emdash-sweep
description: >-
  Sweep em-dash characters (U+2014) out of a repo surface safely: inventory
  every occurrence, CLASSIFY each hit (display copy vs functional string vs
  vendored code vs frozen record) before touching anything, reword only the
  safe classes per house style, and prove the result with syntax checks and
  the staged-diff gate. Use when the operator says "sweep em-dashes",
  "em-dash sweep <dir or repo>", "any em-dashes left in X", "clean the
  em-dashes from the client-facing surfaces", "the pre-commit hook keeps
  tripping on U+2014", or after any agent fan-out produced content that must
  be committed (Convention 6: subagents routinely emit the glyph). Do NOT use
  for: retired TERMINOLOGY (words, not glyphs; that is retired-term-sweep),
  a single known hit (just edit it), DB-stored content (code sweep only;
  stored rows need their own pass), or frozen legal snapshots (signed
  guarantee/CSA records are append-only and stay untouched).
user_invocable: true
disable_model_invocation: false
allowed-tools: [Read, Grep, Glob, Edit, Bash]
---

# emdash-sweep: remove U+2014 from a code surface without breaking it

Convention 1 bans the em-dash everywhere we generate text, but a blind
find-and-replace is dangerous: the glyph can sit inside a JS string used for
comparison or parsing, a regex, a data attribute, vendored third-party code,
or copy that mirrors a DB-stored string (rewording only the code side breaks
the match). This skill is the classify-first sweep that shipped clean on
client-hq twice (admin surfaces, then _templates/ + shared/, 156 hits, zero
regressions).

## Gotchas

- A functional string (compared, parsed, keyed, regexed, or mirrored in a DB
  row) that gets reworded on the code side only breaks the match silently.
  Classify before touching anything; never reword a hit you have not traced.
- When agents draft the sweep as structured patches, the find strings MUST
  contain the exact em-dash bytes being removed; verify replaces carry zero
  U+2014 before applying (count the glyph separately in finds vs replaces).
- En-dashes (U+2013) are allowed; do not sweep them. Only flag one when it
  sits in the same string you are already rewording.
- DB-stored copy (page sections, proposals, newsletters) is out of scope for
  a code sweep; if stored rows carry the glyph, plan a separate data pass
  with its own backup and verification.
- The per-repo `.githooks/pre-commit` blocks U+2014 in staged additions; this
  skill is how you clear a surface proactively instead of fighting the hook
  hit by hit.
- `node --check` cannot parse HTML; inline `<script>` blocks need the
  extract-and-vm.Script validation in step 4.

## Steps

1. **Inventory.** From the repo root, list every hit with byte context:

   ```
   grep -rnP '\x{2014}' <dirs...>
   ```

   Expected output: one line per hit in the shape

   ```
   <path>:<line>:<line text containing the em-dash>
   ```

   No output at all means the surface is already clean; report that and stop.
   Count first; a sweep with hundreds of hits across many files is a good
   fan-out candidate (one drafting agent per surface, patches-as-data, then
   use the `apply-reviewed-patches` skill). A handful of hits: edit directly.

2. **Classify EVERY hit before changing any.** Four classes:
   - **Display copy** (HTML text, UI strings, comments): safe to reword.
   - **Functional strings** (compared, parsed, keyed, regexed, or mirrored in
     DB rows): trace every consumer before touching; if the string round-trips
     to stored data, leave it and record the coupling as a follow-up.
   - **Vendored third-party code**: leave it, note it.
   - **Frozen records** (signed agreement snapshots, append-only logs stored
     in the DB): never touch, they are legal history.

3. **Reword the safe classes** per house style: comma, colon, period,
   parentheses, or restructure the sentence. Keep meaning and tone (client
   audience is therapists: warm, non-technical). Blank-value placeholder
   glyphs (a lone dash rendered when data is missing) become an en-dash
   (U+2013) or a plain hyphen, NOT a comma; check what the surrounding
   surfaces already use so placeholders stay consistent.

4. **Validate the syntax of everything touched.**
   - Pure JS: `node --check <file>` per file. Expected output on success:

     ```
     (no output, exit code 0; a failure prints SyntaxError with <file>:<line>)
     ```

   - Inline scripts in HTML: extract each `<script>` block and parse with
     `new (require('vm').Script)(blockText)` (node --check cannot parse HTML).
     Success is the same invariant: no throw, no output.

5. **Stage with explicit paths** (never `git add -A`; it sweeps pre-existing
   untracked files into the commit). Confirm the staged set with
   `git diff --cached --name-only` before moving to Verify.

## Verify

Both probes must come back empty before the sweep is done.

1. Re-run the inventory grep over the swept dirs:

   ```
   grep -rnP '\x{2014}' <dirs...>
   ```

   Expected output:

   ```
   (no output, exit code 1: the surface is clean)
   ```

2. Run the staged-diff gate (the same scan the pre-commit hook applies):

   ```
   git diff --cached -U0 | grep '^+' | grep -nP '\x{2014}'
   ```

   Expected output:

   ```
   (no output: staged additions carry zero U+2014)
   ```

If either probe prints a hit, go back to step 2 and classify it; do not
commit until both are empty.
