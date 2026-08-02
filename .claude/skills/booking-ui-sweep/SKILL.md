---
name: booking-ui-sweep
description: >-
  Sweep-checklist for any change to Moonraker's own strategy-call booking
  surfaces (assignee identity, assignee/attendee time zones, booking copy,
  links). The booking UI is intentionally duplicated across moonraker-website
  (BookingWidget.astro plus two pages that carry their OWN diverged copies)
  and client-hq (email templates, calendar event, ICS, assignee defaults), so
  a one-place edit silently ships inconsistent copy. This skill enumerates
  every copy with scoped greps, applies the change everywhere, and proves all
  copies agree. Use when the operator says "change the booking assignee",
  "Scott's hours/timezone changed", "update the booking copy", "new person
  taking the strategy calls", "the confirmation email says X but the page
  says Y", "sweep the booking surfaces", or before shipping ANY edit that
  touches assignee name, assignee email, Australia/Perth, the tz select list,
  or attendee-facing booking wording. Do NOT use for booking API LOGIC (slot
  generation, availability, double-book locks live in client-hq
  api/_lib/booking-helpers.js, edit directly with tests); admin calls-page
  features (that is ordinary client-hq work, use the client-hq-feature-workflow
  skill for a sweep); client-practice bookings (that is Engage, a different
  product); or retired-terminology sweeps (that is the retired-term-sweep
  skill).
user_invocable: true
disable_model_invocation: false
---

# booking-ui-sweep: keep every copy of the booking UI in agreement

One booking flow, many copies. Any assignee/timezone/copy change must land in
every copy in the same session, then be proven consistent. History: a 5-place
sweep that bit twice before 2026-07-04 (ledger oi-038); BookingWidget.astro
later absorbed three pages, and on 2026-08-03 (commit bf72312) it absorbed
book-a-call.astro and reschedule.astro too via a `mode` prop, but cancel.astro
and all the email/calendar surfaces still carry their own copies.

## Gotchas

- **BookingWidget.astro is MOST of the story now, but not all of it.** Since
  the 2026-08-03 fold it runs all three flows via `mode`
  ('audit' | 'quick' | 'reschedule') and is the component behind
  free-strategy-call.astro, lp/strategy-call.astro,
  lp/therapist-websites.astro, book-a-call.astro, and reschedule.astro.
  Still OUTSIDE it: `cancel.astro` carries a partial copy (booking summary,
  tz formatting, assignee copy: "Scott's calendar", "Optional note for
  Scott"), every page carries its own header-band and meta assignee copy,
  and the three audit-mode consumer pages carry assignee-name copy AROUND
  the widget (free-strategy-call.astro bio copy, lp/strategy-call.astro team
  cards, lp/therapist-websites.astro CTA band: "Scott walks through your
  current site live"); details in `locations.md`.
- **Do not narrow the name grep to a phrase list.** Copy phrasing varies per
  page ("with Scott", "Scott walks through", "Scott leads every strategy
  call"), so the enumeration grep is a bare case-insensitive `\bscott\b`
  within the booking scope. A curated alternation missed the
  lp/therapist-websites.astro CTA copy in review on 2026-08-03; the scope
  bound is the `$BWEB` / `$BCHQ` file sets, not the pattern.
- **"Change the assignee" is config AND hardcodes.** The availability API
  returns config-driven `assignee_display_name` / `assignee_time_zone` /
  `assignee_location_label` (from the booking config, editable at
  client-hq `admin/calls/settings/`), but the pages, emails, and API files
  also hardcode "Scott", `scott@moonraker.ai`, and `Australia/Perth` in copy,
  defaults, and formatters. Both must move.
- **The assignee's name and email also appear OUTSIDE the booking surfaces,
  and those uses are OUT OF SCOPE.** `scott@moonraker.ai` appears in 33
  files under client-hq `api/` today, and only 6 are booking surfaces; the
  rest are Scott as a RECIPIENT (cron digest recipients, newsletter plumbing,
  ga4 alerts, notify-team) and must NOT be touched by this sweep. Likewise
  "Scott" appears in the moonraker-website team-page bio (team.astro) and in
  client-hq email plumbing. That is why every assignee-name/email grep below
  is scoped to the `$BWEB` / `$BCHQ` file sets; never widen them to whole
  repos and never add a non-booking hit to the known-locations tables.
- **Each email wording exists up to 4 times per type.** booking-emails.js
  forks templates per audience (new prospect vs existing client) and each
  template emits html AND plain text. One sentence change can be 4 strings.
- **The Google Calendar event description is another copy.**
  `createCalendarEvent` in client-hq api/_lib/booking-helpers.js writes its
  own booking summary text, and `sendTeamBookingAlert` in the same file
  formats the assignee-side time with a hardcoded `Australia/Perth`.
- **Two deploy paths.** moonraker-website ships by push to main (VPS
  publishes the static build to R2, no Vercel); client-hq ships by push to
  main (Vercel auto-deploy). A sweep is not live until BOTH are pushed.
- **rtk hook mangles grep pipes on the operator machine.** If a grep below
  errors with a bogus flag (e.g. `--ultra-compact`), wrap it:
  `rtk proxy bash -c '<command>'`.
- **Do not trust the known-locations tables over the greps.** The tables
  (in `locations.md` in this skill's directory) are a snapshot (2026-08-03).
  Within the booking scope defined in step 1, the greps are the authority;
  if they surface a booking file not listed there, the edit goes there too
  AND the master copy of this skill gets the new location added (edit
  `moonraker-skills/skills/booking-ui-sweep/`, never a vendored copy).

## Known locations

The full per-file tables (slot-picker copies, widget consumers with their
own assignee copy, email/calendar/preview surfaces, assignee defaults) and
the fanned-out hardcoded strings live in `locations.md` in this skill's
directory. Read it before step 2; it is the map the step 1 hit lists get
diffed against.

## Steps

### 1. Enumerate every copy (fresh, every time)

Set roots and existence-check them (web sessions and teammate machines lay
repos out differently), then define the two booking-scope file sets. `$BWEB`
and `$BCHQ` must stay UNQUOTED where used so they expand to multiple paths:

```
WEB=<path to moonraker-website>; CHQ=<path to client-hq>
test -d "$WEB/src" && test -d "$CHQ/api" || { echo 'set WEB/CHQ'; exit 2; }
BWEB="$WEB/src/components/BookingWidget.astro $WEB/src/pages/book-a-call.astro $WEB/src/pages/reschedule.astro $WEB/src/pages/cancel.astro $WEB/src/pages/free-strategy-call.astro $WEB/src/pages/lp"
BCHQ="$CHQ/api/booking $CHQ/api/_lib/booking-emails.js $CHQ/api/_lib/booking-helpers.js $CHQ/api/admin/booking-availability.js $CHQ/api/admin/booking-config.js $CHQ/api/admin/booking-email-preview.js $CHQ/admin/calls"
```

`$WEB/src/pages/lp` is in scope as a DIRECTORY because both current lp pages
are booking funnels; judge a future non-booking lp page's hits on content.

Run the enumeration greps (wrap in `rtk proxy bash -c` if the hook mangles
them):

```
grep -rln 'dateStrip' $WEB/src                              # full slot-picker copies
grep -rln 'Australia/Perth' $WEB/src $CHQ/api $CHQ/admin    # tz hardcodes (booking-only string, safe tree-wide)
grep -rliE '\bscott\b' $BWEB $BCHQ                          # assignee-name copy, SCOPED, deliberately bare
grep -rln 'scott@moonraker.ai' $BCHQ                        # assignee default + mailto + alerts + preview, SCOPED
grep -rn  'assignee_' $BCHQ | grep -v node_modules          # config-driven half
grep -rn  "API_ROOT = 'https://clients.moonraker.ai" $WEB/src   # the 4 astro surfaces
```

Expected shape (2026-08-03 baseline, verified):

- `dateStrip`: exactly 3 files (BookingWidget.astro, book-a-call.astro,
  reschedule.astro).
- `Australia/Perth`: exactly 6 files (those 3 astro copies plus
  `$CHQ/api/admin/booking-availability.js`, `$CHQ/api/_lib/booking-helpers.js`,
  `$CHQ/admin/calls/index.html`). This string is unique to booking, so the
  tree-wide sweep is safe; a 7th file means the duplication grew.
- `\bscott\b` (scoped, case-insensitive): exactly 17 files: 15 with
  assignee-NAME copy plus 2 email-only hits (`$CHQ/api/booking/quick-book.js`
  and `$CHQ/api/admin/booking-email-preview.js`, whose only matches are the
  `scott@moonraker.ai` address, already enumerated by the email grep). The
  full 17-file baseline is listed at the bottom of `locations.md`; confirm
  the two email-only files still carry no name copy.
- `scott@moonraker.ai` (scoped): 6 files:
  `$CHQ/api/booking/{create,create-with-audit,quick-book}.js`,
  booking-emails.js, booking-helpers.js, booking-email-preview.js (its
  sample payload hardcodes the mailto reschedule/cancel links). Do NOT run
  this grep repo-wide: across all of `$CHQ/api` it hits 33 files, mostly
  non-booking recipient lists this sweep must never edit.
- `API_ROOT`: 4 astro files (the 3 slot-picker copies plus cancel.astro).

Diff the hit list against the tables in `locations.md`. A new file INSIDE the
scoped sets (or a new tree-wide Perth/dateStrip/API_ROOT hit) = add it to the
sweep AND to this skill's master before finishing. A Scott hit OUTSIDE the
scoped sets (team bio, digest recipients) = ignore, out of scope.

### 2. Classify the change and mark its blast radius

- **Assignee identity** (name, email, location): booking config via the
  `admin/calls/settings/` UI (or `api/admin/booking-config.js`), PLUS every
  hardcode hit from the scoped `\bscott\b` and `scott@moonraker.ai` greps,
  PLUS the emails' FROM/signature lines in `booking-emails.js`.
- **Time zone** (assignee moves, or tz shortlist changes): every
  `Australia/Perth` hit, the tz-select arrays in the 3 astro copies
  (grep `'Australia/Adelaide'` in `$WEB/src` to find them; baseline: the
  same 3 files), `booking-helpers.js` assignee-side formatting,
  `booking-availability.js` default, and the `admin/calls/index.html`
  formatters.
- **Copy/wording** (page text, email text): the 3 astro copies + cancel.astro
  + the consumer pages' own copy around the widget, and in
  `booking-emails.js` BOTH audience variants and BOTH html/text bodies of
  every affected template, plus the `createCalendarEvent` description in
  `booking-helpers.js` if the summary wording changed.

### 3. Apply the edit to EVERY location in one session

Ordinary code edits in both repos. Do not stop halfway: a partial sweep is
worse than no sweep (page and email disagree in front of a prospect). Stage
with explicit paths, never `git add -A`.

### 4. Verify all copies agree, then ship (GATED: needs plain go-ahead)

See `## Verify`. Only after verification passes AND the operator gives a
plain go-ahead: push moonraker-website to main (VPS publishes the static
build) and client-hq to main (Vercel auto-deploys). Two pushes, or the
surfaces disagree in production.

## Failure modes

- A grep returns a booking-scope file not in the `locations.md` tables: the
  duplication grew. Sweep the new file too and update this skill's master,
  or the next sweep misses it silently.
- The name or assignee-email grep is run tree-wide and floods with
  non-booking hits (team.astro bio, cron digest recipients, newsletter
  plumbing): that is the grep escaping its scope, not new duplication. Re-run
  the scoped `$BWEB $BCHQ` form; never edit those files in this sweep.
- The name grep gets "tightened" to a phrase alternation to cut noise: it
  will miss diverged page copy (this exact failure shipped a review miss on
  lp/therapist-websites.astro). Keep it bare; the file sets are the filter.
- `dateStrip` returns fewer than 3 files: a page was refactored onto the
  shared component (good). Update `locations.md`; do not "restore" anything.
- Greps fail with an unknown flag on the operator machine: the rtk hook
  rewrote the command. Re-run wrapped in `rtk proxy bash -c '...'`.
- Old string still hits within scope after the sweep (Verify check 1 fails):
  you missed a copy, usually cancel.astro, booking-email-preview.js, or the
  plain-text twin of an email body. Fix and re-verify; never ship with a
  non-zero in-scope old-string count.
- `npx astro build` fails in moonraker-website: the inline-JS copies define
  globals called by inline onclick handlers; a rename inside one copy must
  rename both definition and handler in THAT file.

## Rollback

All edits are ordinary commits in moonraker-website and client-hq:
`git revert` the sweep commit(s) in each repo and push. The booking-config
change (step 2, assignee identity) is a DB-backed setting: revert it by
setting the previous values back through the same `admin/calls/settings/`
UI; note the old values before changing them.

## Verify

1. Old string is gone from every BOOKING surface (for a replacement change),
   using the same scoped sets from step 1:

```
$ grep -rn '<old string>' $BWEB $BCHQ | wc -l
0
```

   For an assignee-email change, do NOT chase the count to zero across all
   of `$CHQ/api`: the old address legitimately remains in non-booking
   recipient lists (digests, newsletter, ga4 alerts). Only the scoped sets
   must be clean; forcing a repo-wide zero is a failure, not a pass.
2. New string is present in every enumerated location: re-run the step 1
   greps with the new string and check the hit list covers every file you
   classified into the blast radius in step 2. A location missing from the
   hits is an unapplied edit, not a pass.
3. Both repos still build/parse:

```
$ cd $WEB && npx astro build   # exits 0
$ node --check $CHQ/api/_lib/booking-emails.js && node --check $CHQ/api/_lib/booking-helpers.js && echo SYNTAX-OK
SYNTAX-OK
```

4. Read one rendered pair side by side (the confirmation template in
   `booking-emails.js` vs the confirm step in `BookingWidget.astro`) and
   confirm the wording, assignee name, and time-zone label agree.
5. If any location was added or removed this sweep, the master
   `moonraker-skills/skills/booking-ui-sweep/locations.md` tables were
   updated and re-synced; the sweep is not done until the map matches
   reality.
