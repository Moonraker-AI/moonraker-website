# booking-ui-sweep: known locations (snapshot 2026-08-03, post-fold)

Sidecar to SKILL.md. This is the map the step 1 grep hit lists get diffed
against. Within the booking scope the greps are the authority; when they
disagree with these tables, the tables are stale: sweep the new file AND
update this master (edit `moonraker-skills/skills/booking-ui-sweep/`, never
a vendored copy).

Repo roots below: `WEB` = moonraker-website checkout, `CHQ` = client-hq
checkout (siblings in the Dev tree on the operator machine).

## Slot-picker UI (ONE shared component plus one partial, all in `WEB`)

Folded 2026-08-03 (moonraker-website commit bf72312): book-a-call.astro and
reschedule.astro no longer carry their own copies. BookingWidget.astro runs
all three flows via a `mode` prop ('audit' default, 'quick', 'reschedule'),
so a slot-picker/copy change lands ONCE in the component; the two pages own
only their header bands.

| Copy | File | Notes |
|---|---|---|
| 1 | `src/components/BookingWidget.astro` | shared component, all three flows via `mode`; consumed by `src/pages/free-strategy-call.astro`, `src/pages/lp/strategy-call.astro`, `src/pages/lp/therapist-websites.astro` (mode audit), `src/pages/book-a-call.astro` (mode quick), `src/pages/reschedule.astro` (mode reschedule); styles in `src/styles/booking-widget.css`; the three audit consumers ALSO carry their own assignee-name page copy around the widget (see next table) |
| partial | `src/pages/cancel.astro` | booking summary, tz formatting, assignee copy ("Scott's calendar", "Optional note for Scott"); no dateStrip, easy to miss, still its own copy |

## Widget consumers with their own assignee page copy (`WEB`)

| File | Assignee copy of its own |
|---|---|
| `src/pages/free-strategy-call.astro` | meta description + intro bio copy ("A focused 30 minute call with Scott Pope...") |
| `src/pages/lp/strategy-call.astro` | team cards (Scott Pope bio, photo alt text) |
| `src/pages/lp/therapist-websites.astro` | CTA band directly above the widget, line ~286: "Pick a time below. Scott walks through your current site live..." |

## Email / calendar surfaces (all in `CHQ`)

| Copy | File | Notes |
|---|---|---|
| 4 | `api/_lib/booking-emails.js` | every attendee template (confirmation x2 audiences, day-before x2, four-hour x2, ten-minute, cancellation) + team alert; `FROM` display name; "your call with Scott" subjects |
| 5 | `api/_lib/booking-helpers.js` | `sendBookingEmail` (reschedule/cancel links incl. mailto fallbacks to `scott@moonraker.ai`), `sendTeamBookingAlert` (hardcoded `Australia/Perth`, `TEAM_ALERT_RECIPIENTS`), `createCalendarEvent` description, ICS generation |
| 6 | `api/admin/booking-email-preview.js` | preview harness; its sample payload hardcodes the `scott@moonraker.ai` mailto reschedule/cancel links (lines 50-51 as of today); email-only hit, no name copy |

## Assignee defaults and admin surfaces (`CHQ`), swept by the same greps

- `api/booking/create.js`, `api/booking/create-with-audit.js`,
  `api/booking/quick-book.js`: `assignee_email: config.assignee_email || 'scott@moonraker.ai'`
  (quick-book.js is an email-only hit, no name copy)
- `api/booking/availability.js`: assignee-name copy in responses
- `api/admin/booking-availability.js`: attendee tz defaults to `Australia/Perth`,
  plus assignee-name copy
- `admin/calls/index.html`: admin times rendered hardcoded in `Australia/Perth`,
  plus assignee-name copy
- `admin/calls/settings/index.html` + `api/admin/booking-config.js`: the
  booking-config editor (the config-driven half of assignee identity);
  the settings page carries example name copy ("e.g. Scott Pope")

## Hardcoded strings that fan out across the copies

`Australia/Perth` (attendee tz default, assignee-side formatting, and the
tz-select shortlist, all in BookingWidget.astro plus cancel.astro's tz
formatting), `Scott` / `Scott Pope` (page copy, email subjects/signatures,
FROM line), `scott@moonraker.ai` (assignee default, mailto fallbacks, team
alert recipients, preview payload), and `clients.moonraker.ai` (`API_ROOT`
in BookingWidget.astro and cancel.astro).

## Scoped name-grep baseline (17 files, `grep -rliE '\bscott\b' $BWEB $BCHQ`)

15 files with assignee-NAME copy: BookingWidget.astro, book-a-call.astro
(header/meta copy only since the fold), reschedule.astro (same),
cancel.astro, free-strategy-call.astro,
lp/strategy-call.astro, lp/therapist-websites.astro (all `WEB`);
api/booking/create.js, api/booking/create-with-audit.js,
api/booking/availability.js, api/_lib/booking-emails.js,
api/_lib/booking-helpers.js, api/admin/booking-availability.js,
admin/calls/index.html, admin/calls/settings/index.html (all `CHQ`).

2 email-only files (hit only on the `scott@moonraker.ai` address, also
enumerated by the email grep): api/booking/quick-book.js,
api/admin/booking-email-preview.js.
