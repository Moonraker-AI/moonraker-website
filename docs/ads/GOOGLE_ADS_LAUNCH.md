# Google Ads Launch: Runbook + Campaign Build Sheet

Companion to the tracking code shipped in this repo (BaseLayout gtag, booking
conversion hooks, /lp/strategy-call landing page, worker CSP + noindex).
Operator does Phase 0 and Phase 3 in the Ads UI; everything else is code.

## Phase 0: Create the sub-account (the right way)

The account picker's "New Google Ads Account" button creates a STANDALONE
account and forces the campaign-creation wizard. Do not use it. Create the
account from inside the Manager account instead:

1. ads.google.com, sign in as chris@moonraker.ai, pick **Moonraker Manager
   (649-085-6586)** from the account selector.
2. Left navigation: **Accounts** (or "Sub-account settings" on some layouts).
3. Click the blue **+** button, choose **Create new account**
   (NOT "Link existing account").
4. Fill in: account name **Moonraker**, country United States, time zone
   **America/New_York** (or Eastern, wherever billing is anchored; time zone is
   permanent), currency **USD**. This flow does NOT force a campaign.
5. Open the new sub-account, then:
   - **Billing > Payment methods**: attach the payment profile.
   - **Settings (Admin) > Recommendations auto-apply: turn everything OFF.**
     Do this before anything else; auto-apply silently adds broad match and
     "enhancements" that wreck a tight account.
6. Conversion action: **Goals > Conversions > New conversion action > Website >
   enter moonraker.ai > add a conversion action manually**:
   - Goal category: **Book appointment**
   - Name: **Booked strategy call**
   - Value: Don't use a value (or 100 if it insists; keep consistent)
   - Count: **One**
   - Click-through window: **30 days**; Engaged-view: 3 days; Attribution: Data-driven
   - Installation: choose "Use Google tag" / manual, you only need the ids.
7. Collect the three ids and hand them to Claude:
   - **AW id** (looks like AW-XXXXXXXXX, on the conversion action's tag setup screen)
   - **Conversion label** (the part after the slash in AW-XXXXXXXXX/YYYYYYYYYY)
   - **GA4 measurement id** (G-XXXXXXX: GA4 Admin > Data streams > moonraker.ai stream)
8. Link GA4: GA4 Admin > Product links > Google Ads links > link the new
   sub-account. In Ads: Tools > Linked accounts, confirm.

## Phase 1 id swap (code, after Phase 0)

`src/layouts/BaseLayout.astro` frontmatter: replace the three `'PENDING'`
consts (GA4_ID, AW_ID, AW_CONV) with the real ids, republish. The tag emits
nothing while any id is PENDING, so shipping the code early is safe.

## Phase 3: Campaign build sheet

Enter in the Ads UI (Expert mode). Every value below is deliberate; when the
UI suggests otherwise, decline.

### Campaign
| Field | Value |
|---|---|
| Objective | Create a campaign without a goal's guidance (avoids forced smart settings) |
| Type | Search |
| Name | MR \| Search \| Therapist Marketing \| US |
| Networks | Google Search only. Search partners OFF. Display Network OFF |
| Locations | United States. Location options: **Presence** (not "Presence or interest") |
| Languages | English |
| Audience segments | none (observation only if it forces one) |
| Bidding | Maximize clicks with **max CPC bid limit $8.00** |
| Budget | **$50/day** |
| Ad rotation | Optimize |
| Start date | on approval |
| Sitelinks/assets | see Assets below |
| Auto-created assets | OFF |
| Broad match keywords setting | OFF (campaign setting "Use broad match" must be off) |

Switch bidding to tCPA (start ~$150) only after 15-30 recorded conversions.

### Ad group 1: Therapist Marketing
Keywords (add BOTH phrase and exact of each):
```
"marketing for therapists"      [marketing for therapists]
"therapist marketing agency"    [therapist marketing agency]
"therapy practice marketing"    [therapy practice marketing]
"private practice marketing"    [private practice marketing]
"marketing for private practice" [marketing for private practice]
```

### Ad group 2: Therapist SEO
```
"seo for therapists"        [seo for therapists]
"therapist seo"             [therapist seo]
"seo for therapy practice"  [seo for therapy practice]
"local seo for therapists"  [local seo for therapists]
"therapy website audit"     [therapy website audit]
```

### Ad group 3: Therapist Websites
```
"therapist website design"        [therapist website design]
"therapy website design"          [therapy website design]
"websites for therapists"         [websites for therapists]
"private practice website design" [private practice website design]
"therapist website redesign"      [therapist website redesign]
```

### Campaign-level negative keywords (one list, "MR negatives")
```
free, cheap, diy, template, templates, job, jobs, salary, career, hiring,
course, training, certification, ceu, degree, school, become a therapist,
betterhelp, talkspace, psychology today, wix, squarespace, godaddy, examples
```
(Add as broad-match negatives; multi-word ones as phrase negatives.)

### RSAs (one per ad group)
Final URL for ALL ads:
`https://moonraker.ai/lp/strategy-call`
Tracking template (campaign level, Settings > Additional settings > Tracking):
`{lpurl}?utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_term={keyword}`

Shared headlines (all ad groups; 30-char limit respected):
1. Marketing for Therapists
2. Get Found on Google and AI
3. **Book a Free Strategy Call** (PIN to position 3)
4. Built Only for Therapy
5. Flat-Rate Projects
6. No Long-Term Contracts
7. 5-Star Rated by Therapists
8. See Where You Rank Today

Ad-group-specific headlines (add to the shared set):
- Therapist Marketing: "Therapy Practice Marketing", "AI Search Visibility"
- Therapist SEO: "SEO for Therapists", "Therapist SEO Experts", "Local SEO for Therapists"
- Therapist Websites: "Therapist Website Design", "Websites for Therapists", "Fast, Secure Practice Sites"

Descriptions (all ad groups; 90-char limit):
1. See exactly how your practice shows up on Google, Maps, and AI tools. Free strategy call.
2. We work only with therapy practices. Flat-rate projects and you own everything we build.
3. Start with a free visibility review. Clear findings, honest next steps, zero pressure.
4. From audit to full rebuild: three clear service steps, scoped on a free 20-minute call.

### Assets (campaign level)
- Sitelinks: Services -> /services, Results -> /results, Our Process -> /process,
  Meet the Team -> /team
- Callouts: Therapy Practices Only; Flat-Rate Projects; No Long-Term Contracts;
  You Own Everything
- Structured snippet: header "Services": Visibility Audit, Platform Upgrade,
  Full Practice Rebuild

## Phase 4 verification (after id swap + republish)

1. `curl -sI https://moonraker.ai/lp/strategy-call` -> X-Robots-Tag: noindex, follow + new CSP.
2. Browser DevTools on any page: gtag/js 200, collect pings, ZERO CSP console errors, incl. a full test booking on /book-a-call (then cancel the booking).
3. GA4 Realtime shows page_view + book_strategy_call on the test booking.
4. Ads conversion action leaves "Unverified" within 24-48h of first tagged conversion; true end-to-end proof needs a real ad click post-launch.
5. sessionStorage check: visit /lp/strategy-call?gclid=TEST123, navigate to /free-strategy-call, `sessionStorage.mr_attrib` persists.

## Post-launch cadence

Weekly: Search terms report -> add negatives; confirm conversions recording.
15-30 conversions: switch to tCPA (~$150 start). Month 2: consider per-ad-group
landing variants under /lp/.

## Flagged follow-up (client-hq repo)

Booking endpoints (/api/booking/create-with-audit, /api/booking/quick-book)
should accept + persist the `mr_attrib` blob (gclid + utm_*), then the site
forwards it in the booking payload. Enables lead-source attribution in CHQ and
future enhanced conversions.
