---
name: fundamentals-review
version: 1.1.0
description: |
  Single-pass fundamental review of a Republic portfolio company using
  the Gates A/B/C framework. Enforces drafter/auditor separation,
  evidence-before-synthesis discipline, and probability-calibrated stance
  recommendations.
  Output: ~/brain/companies/{slug}/{YYYY-MM-DD}_{slug}_review_v{N}.md (auto-versioned at root; flat structure — drafts/ subfolder retired 2026-04-29).
  Requires manifest from `~/agents/republic/scrapers.republic_review_gather` first.
triggers:
  - "review {company}"
  - "do a review of {company}"
  - "do a fundamentals review of {company}"
  - "fundamental review {company}"
  - "investment review {company}"
  - "evaluate {company} as an investment"
tools:
  - read
  - write
  - bash
mutating: true
---

# Review Skill — Contract

Canonical operational contract for every Republic portfolio fundamental review. This is the "hard behavioural rules" layer referenced at the top of `ways_of_working.md`. If anything here contradicts `ways_of_working.md`, **this skill wins** — it encodes the more recent correction.

Last updated: 2026-04-29 (v1.4.0: drafts/ subfolder concept retired entirely — every review file at company root regardless of Gate-C state; Rule 24 added requiring extended YAML frontmatter with cap-table block per T2.3). Prior 2026-04-27 (v1.3.0: Phase 21.7 — gather now caches closed raises from prior manifests, only the active raise (raises[-1] in oldest→newest order) gets a fresh Playwright walk. Cached tabs carry `extra.cached_from = <prior_date>` flag and rewritten attachment paths pointing at prior date's evidence dir. Disable with `republic_review_gather --no-cache` if KIIS PDFs change or you need fresh comments on closed-raise threads). Prior 2026-04-27 (v1.2.0: Phase 21.5 — Rule 2b for `historical_context.md`). Prior 2026-04-23 (Rules 18–22 added). Initial 2026-04-17.

---

## Repo layout note (read first)

This skill spans two repositories that **must not be confused**:

- **READS** (manifest + evidence): `~/agents/republic/research/{slug}/evidence/{YYYY-MM-DD}/manifest.json` and the OCR'd PDFs alongside it. Created by the gather (`~/agents/republic/scrapers/republic_review_gather.py`). This is in the agent runtime tree, not in brain.
- **WRITES** (review draft): `~/brain/companies/{slug}/{YYYY-MM-DD}_{slug}_review_v{N}.md`. This is in the Obsidian/git-synced brain tree.

Two separate repos, two separate purposes. Don't write reviews into `~/agents/`; don't expect manifests to live in `~/brain/`.

The internal helper `~/agents/republic/scrapers/review_common.py` is invoked by the gather (legacy URL fallback, manifest aggregation). You do not call it directly.

## Pre-flight: pick the version number

Before drafting, list existing reviews for the company:

```bash
ls ~/brain/companies/{slug}/*_review_v*.md ~/brain/companies/{slug}/*_evaluation_v*.md 2>/dev/null
```

- **None exist** → this is OG → write `_v1.md`.
- **At least one exists** → this is an UPDATE → take the highest `v{N}`, increment, write `_v{N+1}.md` next to the others at root.

Example: `2026-04-13_heights_evaluation_v8.md` is the latest → today writes `{today}_heights_review_v9.md`. Filename always begins with date, then slug, then `review` (or `evaluation` for legacy compatibility), then `_v{N}.md`. All reviews — drafts and finalised — live at company root. There is no `drafts/` subfolder; the concept was retired 2026-04-29. Gate-C audit absence does not relegate a review; Gate C is a quality enhancer, not a validity gate.

## The non-negotiables

### 1. No synthesis before today's manifest exists on disk

Before writing a single line of a review dated `YYYY-MM-DD`, verify that:

```
~/agents/republic/research/{company-slug}/evidence/{YYYY-MM-DD}/manifest.json
```

exists and was produced by `~/agents/republic/scrapers/republic_review_gather.py`. If absent, you **run the gather** (or ask the user to, if auth is the blocker) **before** any review body is written.

**Violation example** — TransferGo v1 (2026-04-17): wrote the full 19-section review from Companies House + external triangulation only. No Republic tabs walked. No manifest on disk. No evidence gate. v1 must never be repeated.

### 2. Read the manifest before reading anything else

The manifest is the index into the evidence folder. Read it first. It tells you:

- Which tabs were walked, and their `status` (`ok | skipped | error | partial`)
- Every attachment's path + sha256 + source URL + OCR sibling
- Per-raise structure when the company has historical raises (`/{slug}1`, `/{slug}2`, etc.)
- Investor/comment/thread/update counts that feed the review's Section 5 and Section 12 claims

### 2b. Read `historical_context.md` BEFORE drafting Sections 2, 12, 13, 15

Added 2026-04-27 (Phase 21.5). Alongside the manifest, the gather writes:

```
~/agents/republic/research/{slug}/evidence/{YYYY-MM-DD}/historical_context.md
```

This file is a deterministic markdown summary built by `scrapers.historical_context`. It aggregates 30/90 days of watcher data filtered to the company:

- **Order-book history** (last 90d): VWAP trajectory + delta %, bid-ask spread (median + range), depth evolution (buy/sell counts over time), all crossed-market events with timestamps + crossing %.
- **Investor emails** (last 30d): every Republic email subject + date that the email-watcher daemon caught.
- **News + filings** (last 90d): all Companies House filings (with type) + all Google News articles for this slug.
- **Recent graded signals** (last 30d): every signal-grade output for this company by severity, with reasoning + Telegram-sent flag.
- **Rule-based alerts** (last 30d): order-book daemon's Crossed-market / High-notional alert log.

Synthetic test events (slug starts with `TEST_`, body contains `[SIGNAL-GRADE PLUMBING TEST]`, or sender is non-Republic) are filtered OUT of this file by `historical_context.py`.

**You MUST read this file before drafting:**
- **Section 2 (Market Dynamics — Order Book)** — cite VWAP trajectory, spread evolution, crossing density. Do NOT just describe the latest snapshot.
- **Section 12 (Discussion & Investor Sentiment)** — incorporate the email cadence + content drift from `historical_context.md`'s investor email log.
- **Section 13 (Risks ranked)** — reference recent graded signals (sev≥2 patterns, repeated sev=1 around a theme) as risk evidence.
- **Section 15 (Monitoring — Weighted Factors)** — set monitoring thresholds anchored to OBSERVED ranges (median spread, VWAP range, crossing frequency), not abstract numbers.

If `historical_context.md` is missing, the gather failed to produce it OR you're reviewing a company that wasn't yet in the watcher when reviews started. Note in Section 16 (Data Gaps): `historical_context: not available — review based on today-snapshot only`. Do NOT invent trajectory.

If `historical_context.md` exists but is sparse (e.g. "No order-book snapshots in window"), say so plainly in the relevant section. Sparse history is a real signal — it means the company has been quiet OR has only recently entered the watcher.

### 3. Every attachment must be read — or explicitly skipped with a reason

Every PDF listed in `attachments[]` has a `.txt` OCR sibling. You read the sibling. Every significant attachment cited or referenced in the review body must trace back to an attachment in the manifest.

If you deliberately skip an attachment (redundant KIIS copy in a non-English language, duplicate investor deck older than the authoritative current one), note it in the review's Section 16 (Data Gaps) with a `skipped — reason: {...}` line. No silent skips.

**Cached attachments (Phase 21.7, added 2026-04-27):** Manifest entries with `extra.cached_from = <YYYY-MM-DD>` indicate the gather copied this raise's tabs forward from a prior manifest (closed raises are immutable; re-walking wastes cycles). Their `path` and `ocr` fields are rewritten to point at the prior date's evidence directory (e.g. `../2026-04-25/heights2/kiis.pdf`). Read the file at that resolved path — content is identical to the original. Do NOT report the cached_from date as the document's true date in the review; cited dates should come from the document's own headers (filing dates, KIIS publication dates, etc.). If a cached attachment's resolved path 404s on disk, treat it as a Data Gap (Section 16) and note the cache-pointer staleness.

### 4. Gather covers every raise slug, not just the live one

Historical raises carry the original KIIS, the pre-uplift team bios, the old share-class disclosures, and the earlier Updates thread. The gather walks every slug in the registry's `raises` array by default (newest→oldest). For Section 7 (Cap Table & Raise History), the **prior-round KIIS is mandatory** — it's where the old share-class and liquidation-preference terms are written down.

### 5. Authentication failure is stop-the-line

If the gather exits with code 3 / `AuthExpiredError`:

- **Do not** route around it by using `WebFetch` on `europe.republic.com` — that endpoint returns 403 via Cloudflare regardless of stealth patches. `WebFetch europe.republic.com.*` is a forbidden operation throughout the review workflow.
- **Do not** try to infer Republic content from Google cache or external fetches.
- **Do** ask the user to run:
  ```
  python -m scrapers.import_cookies
  ```
  and halt. Their Chrome cookies get imported into the Playwright persistent profile and the gather resumes.

### 6. You do not edit the manifest

The manifest is the script's output. It is Claude-readable, not Claude-writable. Mutations go through rerunning the gather. If you see a fact in the review that contradicts the manifest, that's either a selector bug (re-run with `--tabs {name}` after fixing the tab module) or a Republic DOM change worth flagging.

### 7. Event-driven refreshes rerun the gather

A new investor update, a re-opened raise, a Series D announcement — all of these trigger `republic_review_gather --company "{name}"` on the day of the refresh. The gather is idempotent (sha256 short-circuits unchanged artefacts), so rerunning same-day is cheap (<30 s).

Never paste a rumour or news headline into the review without a manifest refresh that confirms the update is on-platform.

### 8. Read the comment bodies, not just the thread titles

Discussion comments are fetched by the gather via in-browser `fetch()` (not `page.context.request.get()` — Cloudflare blocks that on same-origin Republic HTML). The gather populates each thread's `comments` array with `{author, date, body, role, attachment_hrefs}` for every reply. **These are not metadata — they're primary sources.** Shareholders routinely:

- Cite Companies House filings by number (e.g. Alexander Hands, TransferGo, Oct 2025 → pointed at UK operating entity 07914165 accounts, which reframed the v2 bear case)
- Summarise group P&L accurately (e.g. Karim Chelala Ziade, same thread)
- Call out valuation froth with analysis that matches independent work
- Post buy/sell offers in-thread with prices that bracket the actual clearing VWAP

If a review's Section 12 paraphrases thread titles only, it has missed what the manifest actually holds. Reference specific comments by author + date. If a shareholder names a Companies House entity or filing that isn't yet in the review's evidence folder, **pull it** before finalising.

### 9. Active-M&A-process companies require a precedent-triangulation sweep

When a company has a disclosed M&A / sale process (advisor hired, "exit or liquidity event" flagged in updates, sale-exploration announced in trade press), the review **must** include a specific triangulation pass before synthesising Section 10 valuation. This is the rule Rheal v1 violated (2026-04-21) — v1 used generic "2-3× revenue" sector multiples, missing that Spayne Lindsay's own most recent UK wellness exits (Deliciously Ella at 1.1-1.4×, Rude Health undisclosed, Symprove at ~9×) spanned an 8× range.

**Mandatory sweep (do ALL four before writing Section 10):**

1. **Advisor precedent table.** For the advisor named in the sale process, list every transaction they advised in the same sector in the last 24 months. Source: advisor's own transactions page + `The Grocer` + `Food Manufacture` + `Just Food` + `Dealroom.co`. Extract revenue, EBITDA, price, multiple for each.

2. **Peer brand exit sweep.** For every peer brand cited in the target's marketing (Alantra Fast 50 neighbours, FEBE G100 neighbours, retailer shelf comparators), search: "[peer brand] acquired OR sold OR raised 2024 2025 2026". Log rev multiple + EBITDA multiple for each exit.

3. **Margin-driven multiple band.** Multiples vary 8× across UK wellness exits (1.1× DE → 9× Symprove). The dominant driver is EBITDA margin (not category). Build a band: target's inferred EBITDA margin → implied multiple range → implied valuation range.

4. **Market-vs-precedent pricing test.** Compare the secondary-market implied cap to the precedent-based fair-value band. If secondary > precedent high end → flag retail market is over-pricing. If secondary < precedent low end → flag retail market is under-pricing. Either finding is material to the Action.

**Violation examples logged:**
- Rheal v1 (2026-04-21): wrote scenarios from generic 2-3× revenue sector multiples. Missed Spayne Lindsay's own DE comp at 1.1-1.4× → v1 Base case was ~2× over-priced. Same-day v2 corrected after user prompt.
- Risk: on future reviews, without this rule, any active-M&A company gets valued against generic sector multiples that may diverge 8× from the actual advisor's realised prices.

### 10. Founder cap-table celebrity/angel check — including institutional GPs

The check has TWO triggers, not one:

**(a) TV/media-celebrity trigger.** When a company has received TV/media exposure (Dragons' Den, Shark Tank, etc.) or positioning around a named figure (celebrity endorser, sector veteran), **search for private follow-on investment** before trusting the "walked away from the deal" narrative.

Mandatory searches:
- `"[Dragon name / celebrity]" [company name] invest OR investor`
- Check the celebrity's own TikTok/LinkedIn/personal-investments page (they routinely list portfolio companies there, often with testimonials)
- Search the company's press release archive for "investor announcement" mentions

**(b) Institutional-investor-GP trigger.** When the cap table or share register lists an institutional investor (VC, family office, fund) by entity name only, **identify the named GP / managing partner / principal** before describing it as "institutional backing." Many institutional investor names are vehicles for individual serial entrepreneurs whose other-portfolio links materially affect: (i) exit-route plausibility (their other companies are strategic acquirers), (ii) governance read (their own track record matters more than the fund's brand), and (iii) celebrity-endorsement signal (they bring the same external-credibility halo as a TV celebrity, just less visibly).

Mandatory searches when an institutional name appears in CS01 / Articles / pitch-investor list:
- `"[Fund name]" GP OR partner OR principal OR founder` — identify who's actually behind it
- For any identified individual: their LinkedIn / Wikipedia / personal investment page — surface other portfolio companies + prior exits
- Cross-check against the subject company's exit-route candidates (Section 10e) — their portfolio may include obvious strategic acquirers

**Violation examples:**
- Rheal v1 (2026-04-21) said "notably turned down the Dragons' offer". Reality per Tej Lalvani's own TikTok, LinkedIn, and investments page: he invested privately *after* Rheal walked from the televised deal. (Trigger (a))
- Laundryheap backtest (2026-04-21) listed "VERB VC SCSP" as institutional A Preferred holder. Canonical v2 surfaced that **Verb Ventures = Alex Chesterman + Alexander Chikunov** — Chesterman is the Cazoo + Zoopla serial-founder. The backtest's Gate C agent N/A'd the celebrity test on the basis of "no TV exposure" and missed this. Material for People score and exit-route plausibility (Chesterman's network = obvious strategic acquirers + IPO advisors). (Trigger (b))

### 11. Retail distribution sweep across ALL major UK chains

For DTC-to-retail consumer brands, the review cannot rely on trade-press surface coverage for the retail distribution list. Systematically check 7-8 major UK chains:

- Holland & Barrett
- Boots
- Tesco
- Sainsbury's
- Waitrose
- M&S Food
- Asda
- Ocado

Method: visit the brand's own website "find a store" / "where to buy" page first (brands advertise comprehensive stockist lists). Cross-check each retailer's online product page for availability + rating + review count.

**Violation example:** Rheal v1 (2026-04-21) cited H&B + Tesco + Boots only. Sainsbury's was confirmed via external search in v2 same-day. Missing retailers = under-stated market-position score.

### 12. Domain verification before external triangulation

For SimilarWeb / Trustpilot / any external-domain research, first **visit the brand's own website** to confirm the canonical domain. Don't assume `[brand].com` is the operating domain — many UK brands use `.co.uk`, `[brand]superfoods.com`, `[brand]app.com`, etc.

**Violation example:** Rheal v1 used `rheal.com` → SimilarWeb returned an Indian IT firm's data (wrong company). Correct domain was `rhealsuperfoods.com`. Cost ~15 min of bad data before correction.

### 13. Share-class inventory is mandatory

Every review must list all share classes sourced from the **Articles of Association** on Companies House, with per-class:
- Voting rights (one-vote / supervoting / non-voting)
- Dividend entitlement (pari passu / preference / participating)
- Liquidation preference (1× non-participating / 1× participating / none)
- Anti-dilution protection (none / broad-based weighted / narrow-based / full-ratchet)

No "cap-table is complex, we'll skip" or "management withheld" handwaving. **Articles are public on CH** (most companies file an MA every 12-24 months; search filing history for "MA" or "RESOLUTIONS" entries). If the MA is genuinely not filed (pre-incorporation-only companies, newly formed subsidiaries), say so explicitly with the CH filing-history URL.

**Violation example:** OnBuy v1 (2026-04-21) — accepted Cas Paton's "strict confidentiality" line. The MA had been public on CH since 1 Mar 2024 (55pp, disclosing 4 share classes + 1× non-participating preference waterfall + EIS caps + Investor Director regime).

### 14. Preference waterfall modelled in £

If any Preferred class exists (Series A, Series B, Convertible Preferred, etc.), Section 10 scenarios **must deduct the preference stack from exit proceeds before calculating Ordinary/retail returns.**

Required:
- Aggregate preference stack quantified in £ (Preference Amount per class × shares in class)
- Each scenario in the exit table shows: Gross Exit Value → Less Preference Stack → Net to Ordinary → Per-share Ordinary → Net after Republic fees
- Do not quote "2× return on the Base case" if that's the gross exit multiple; Republic retail only sees the residual after Preferred is paid

**Violation example:** Laundryheap v1 (2026-04-21) — modelled exit scenarios at gross valuation levels without deducting the ~£6M of B Preferred + A Preferred preference stack. v2 correction reduced probability-weighted return on £160 cost from +73% to +37% over 5yr (from "beats S&P" to "misses S&P").

### 15. Management-claim cross-check

Any headline revenue / customer / growth claim by management in Sections 4-5 must be EITHER:
- **(a) Cross-checked against CH audited figures** (statutory accounts, SH01 allotment dates/prices, CS01 confirmation statements) with the reconciliation shown inline, OR
- **(b) Explicitly marked "unverified — management claim only"** in the narrative

Do not present management claims as data. If the claim is directional only (no number), say so.

**Violation example (avoided):** Cheeky Panda / Currensea / Heights v1s have largely complied via "management guidance — not yet audited" phrasing. This rule codifies the pattern.

### 16. Mandatory two-phase synthesis — Gate B + Gate C

No review is finalised without documented passes through:

**Gate B (pre-Section-10, drafter-checked) — Primary-source depth before valuation:**
- [ ] Share-class inventory complete per Rule 13
- [ ] Preference waterfall modelled in £ per Rule 14 (or "N/A — no Preferred class" with evidence)
- [ ] Rule 9 precedent table populated with ≥3 specific dated transactions (advisor-specific where known; else sector; else geography)
- [ ] Management headline claims cross-checked per Rule 15
- [ ] Ongoing dilution trajectory modelled in scenarios (staff options, anti-dilution, future rounds)
- [ ] **Retail share-class allocation identified** — when a pre-emption / pre-IPO round mixes Ordinary + Preferred classes (e.g. "Ordinary and B preferred shares" stated in the Republic update), explicitly state which class retail received. If unknown, this is a **HIGH-priority Data Gap** that blocks any waterfall-aware Section 10 (because the answer determines whether retail sits inside or outside the preference stack).

No Section 10 is written until all six boxes are ticked. If any box must remain unticked, the specific reason goes into Section 16 (Data Gaps) as a HIGH-priority gap blocking the current valuation.

**Gate C (post-draft, agent-audited) — 10-item red-team by fresh-context agent:**

Spawn a fresh-context agent (Agent tool, subagent_type: `code-reviewer` or `general-purpose`) with:
- The full draft review markdown
- Read access to the evidence folder + CH filings + external tools
- Instructions to be adversarial: re-derive the action from primary sources, challenge every claim

**The 14-item checklist (expanded 2026-04-23 to add Investability-framework tests):**

1. **Preference stack test** — every Section 10 scenario deducts the preference stack?
2. **Multiple inflation test** — specific dated precedent transactions (named company + date + price + multiple), not generic sector ranges?
3. **Dodge test** — every management "we can't share / confidential" claim investigated via public CH filings?
4. **Restatement test** — amended/overdue accounts have root-cause diagnosis (audit transition / PYA / covenant / qualified opinion) in Data Gaps with note references?
5. **Fresh data test** — precedent comps dated within last 24 months, with specific current-year check?
6. **Dilution test** — staff-option / anti-dilution dilution explicitly in scenario exit £/sh, not just flagged?
7. **Celebrity/angel test** — both Rule 10 triggers checked? (a) TV/media-exposure → celebrity portfolio list searched for quiet follow-on; (b) **Institutional investor name in cap table → GP / managing partner identified by name + their other portfolio + prior exits surfaced.** N/A only when both triggers genuinely don't apply (e.g. cap table is 100% disclosed individuals, no fund vehicles).
8. **Scorecard test** — every sub-score cites specific evidence (not gut rating)? Q/A/M decomposition arithmetic matches the sub-score breakdown? **Header-body consistency (Anti-Pattern A13):** do the three-panel Q/A/M block, the Decision Dashboard, and the Decision Output code block all show the SAME Q/A/M/FV/TEP/band values as §10g? Any mismatch is a FIX.
9. **Action test** — non-HOLD action has ≥3 specific falsifiable triggers in Section 14?
10. **Data gap test** — every N/A / N/D / "Not accessed" cell in Section 9 has a documented categorised gap (research / transparency / access)?
11. **FV external-anchoring test (Rule 18)** — every multiple in §10d traces to a named dated precedent in §10b/10b.i or to a documented EBITDA-margin-positioning derivation? The multiple-before-valuation order is visible in the review's narrative?
12. **Probability base-rate test (Rule 19)** — every scenario probability in §10e either (a) cites a named empirical base rate, or (b) is marked `JUDGMENT — no empirical anchor`? For pre-revenue companies, Blockbuster is capped at 3% unless a named 24-month precedent is cited?
13. **Sensitivity band test (Rule 20)** — §10g shows Investability_central, Investability_low, Investability_high with stresses documented? FRAGILE flag applied if band width > 15pp? Upward action gated by low-end?
14. **EIS calibration test (Rule 21)** — if any route is EIS-eligible, §10g shows both (primary+EIS) and (secondary-no-EIS) Investability explicitly? §11 shows per-lot EIS status?
15. **Extended frontmatter test (Rule 24, post 2026-04-29)** — does the review file open with the YAML frontmatter block per Rule 24 (cap-table block, fair_value_low/high_gbp, target_entry_price_gbp, holding_active, action enum)? Required for v2+ post-2026-04-29; absence on a new review fails Gate C.

Agent returns PASS-with-evidence or FIX-with-specific-revision per item. On any FIX, drafter applies the revision and re-spawns the agent with the revised draft + prior findings attached. Loop until agent returns all-PASS.

**Final output:** Audit transcript (all iterations verbatim) written into the review's **Section 20 — Self-Audit Log**. The existence of Section 20 with all-PASS across ALL 15 items is the gate; no Self-Audit Log = review is not finalised. Tests 11–14 are new as of 2026-04-23; test 15 added 2026-04-29; reviews predating this revision that did not run them are flagged for retrofit (see Phase 4 retrofit queue).

### 17. Template header block is mandatory — no "Headline" table variants

Every review MUST open with this exact block order below the title metadata (Date / Author / Workflow / Time spent), using the same heading level the file uses elsewhere (`##` if the body uses `##` for Sections; `###` if the body uses `###`):

1. **★ Entity** — bullet list with Company + CH number, Sector, CEO/Founder + PSC %, Chairman, FY-end. Context-only; not a substitute for the Decision blocks.
2. **⚡ TL;DR** — one-sentence, action-named commitment in blockquote form: `> **{ACTION}** at £{price} because …`. Forces commitment before narrative, per `~/brain/ways_of_working.md` Part 1.
3. **★ Decision Dashboard** — table with every canonical row from `~/brain/ways_of_working.md` → "Part 2 — Output: The Review Structure" → "★ Decision Dashboard" subsection (Main Action, Tactical Move, Fundamentals Score, Signal State, Concentration, Best Ask/Best Bid, 30d VWAP, Price vs 5yr Hurdle, Price vs Target Entry, Data Vintage, Next Refresh Trigger, Open Data Asks). No blank cells — use "N/A — {reason}" if genuinely not applicable.
4. **★ Decision Output** — fenced code block matching the schema in `~/brain/ways_of_working.md` → "Part 2" → "★ Decision Output (machine-readable code block)" subsection (Company, Fundamentals Score, Signal State, Opportunity Rating, Upside Profile, Data Vintage, Action, Tactical Move, Target Entry Price, Position Ceiling, Next refresh, Conviction). Machine-readable for registry backfill.
5. **★ One-paragraph summary** — dense "why this rating" prose, integrating triangulation highlights and iteration-audit corrections.

**Not allowed:** a single `## ★ Headline` table that collapses all five into one metadata+action+target sheet. Cuvva v1 and ManiLife v1 (2026-04-22) both shipped this variant; both were retrofitted on 2026-04-23 to the canonical block. The Headline variant is dense but (a) breaks the commit-before-narrative TL;DR discipline, (b) fails the registry backfill script that expects the code-block schema, (c) hides required Dashboard fields (Concentration, Best Ask/Bid, VWAP, Data Vintage, Next Refresh Trigger, Open Data Asks).

**Enforcement check (runs before Gate C sign-off):**
```
grep -cE '^#{2,3} (⚡ TL;DR|★ Decision Dashboard|★ Decision Output|★ One-paragraph summary)' {review.md}
```
Must return **4**. If it returns less, the review is not template-compliant and must be retrofitted before being registered. Add this to the Content-level verification checklist in `~/brain/ways_of_working.md` → "Section 13 — Risks (ranked)" subsection's surrounding verification block.

### 18. Fair Value must derive from named dated precedent transactions — NOT from scenario back-solve

The anti-circularity defence. Fair Value (FV) is the single most load-bearing number in the Investability calculation. When drafters compute FV from their own scenario probabilities × their own chosen multiples × their own assumed dilution, the number is a self-fulfilling prophecy — drafter picks a multiple because it yields a plausible exit, then cites the plausible exit as justification for the multiple.

**Order of operations (strict):**

1. **Comp precedent table first** (§10b and §10b.i) — list named dated transactions in the subject's sub-sector over the last 24 months. Extract revenue, EBITDA, price, multiple, buyer type. Minimum 3 transactions; for active-M&A companies, ≥3 advisor-specific precedents.
2. **Multiple band is derived from the comp table** — target's EBITDA margin positions it within the band. The drafter cannot invent a multiple outside the band without a documented reason (superior unit economics, category-leader premium, distressed-seller discount).
3. **Exit scenarios use the multiple band** — Bear at low end, Base at median, Bull at high end.
4. **FV is then computed** from the resulting scenario table. Not before.

**Violation pattern (forbidden):**
- Drafter decides Target Entry Price (TEP) based on "20% below VWAP" habit.
- Drafter back-solves what multiple / probability weights yield the TEP.
- Drafter inserts those multiples into §10b and those weights into §10d.
- The comp table exists but doesn't anchor anything — it's decoration.

**Detection in Gate C:**
For every multiple in the exit scenarios, the auditor asks: "Where in the precedent table does this multiple appear? If absent from the table, why?" A multiple that doesn't trace back to a named precedent (or to a documented derivation from an EBITDA-margin positioning) fails the test.

**Cross-reference:** Rule 9 already mandates the precedent sweep for active-M&A companies. Rule 18 generalises it: the precedent-before-multiple-before-FV discipline applies to EVERY review, not just active-M&A ones. Active-M&A just gets the additional advisor-specific requirement on top.

### 19. Scenario probabilities must cite empirical base rates

The second anti-circularity defence. Probabilities in §10d can be moved 5-10 percentage points in either direction to make any desired TEP look "reasonable." Without external anchoring, probabilities become the adjustment variable for whatever verdict the drafter has already reached.

**Rule: every scenario probability must be either (a) anchored to a named empirical base rate with citation, or (b) explicitly marked `JUDGMENT — no empirical anchor`.**

**Base-rate defaults (use when no specific precedent applies):**
- Bear + Base: **77%** (split by drafter's judgment of failure mode, typically 30/47)
- Bull: **20%** (top-quartile exits ~15–25% of completed sales across UK startup sample)
- Blockbuster: **3%** (top-tier exits at >10× revenue are ~3% of the startup population)

**Blockbuster 3% cap for pre-revenue companies (HARD rule, with sector-specific recency window):** Pre-revenue or pre-commercial companies (no recurring revenue, ≤1 customer, deep-tech / biotech pre-Phase-2) MUST cap Blockbuster at 3% unless the drafter cites a named dated precedent in the same sub-sector at similar scale.

**Precedent recency window — sector-adjusted (added 2026-04-24 after Metallobio v3 finding that 4 of 6 antibiotic-biotech precedents fell outside the 24mo window but were still the best available anchors):**

| Sector | Recency window | Rationale |
|---|---|---|
| DTC consumer / FMCG / B2C retail | **24 months** | Short deal cycles; comps age quickly |
| Fintech / SaaS / B2B software | **24 months** | Active M&A; valuations re-price fast |
| Marketplace / platform | **24 months** | Same |
| **Biotech / pharma (pre-clinical or clinical-stage)** | **48 months** | Long deal cycles; comps scarce; same-stage deals within a 4-year window are typically the closest available anchor |
| **Industrial / hardware / deep-tech** | **36 months** | Fewer deals, longer cycles |
| **Climate / energy / battery** | **36 months** | Same |

If a sub-sector has genuinely no named precedent within its window, the Blockbuster cap stays at 3% and the drafter flags the absence as a Data Gap. A stale precedent (outside window) may be cited but should be discounted — e.g. scale haircut, time-decay haircut — and the discount rationale documented.

Post-revenue companies can argue higher than 3% if they have named specific comparables in the appropriate sector window — but must cite them.

**Example citations that satisfy the rule:**
- *"Bull 22% — UK insurtech with FCA Part 4A + UK platform cleared scale-adjusted 10× EBITDAC premium in 22% of completed 2022–2025 deals per MarshBerry FY25 UK M&A tracker."*
- *"Blockbuster 5% — Wellness-FMCG brands with ≥£30M revenue + retail penetration cleared 10× revenue exits in 5% of 2022–2025 sample (Deliciously Ella/Hero Sep 2024 at 1.4×; Rude Health Nov 2024 undisclosed premium; Symprove Feb 2025 ~9×)."*

**Example failing citations (require defaults or JUDGMENT flag):**
- *"Blockbuster 10% — upside is significant given traction"* — no empirical anchor.
- *"Bear 35% — failure is a meaningful risk"* — no empirical anchor.

**JUDGMENT flag is allowed but penalised:** A `JUDGMENT — no empirical anchor` flag means the probability cannot be defended by base rates. The review's sensitivity band (Rule 20) will naturally widen as a result — which is the correct outcome: action conviction drops when probabilities are guesses.

**Cross-reference:** Rule 19 is enforced at Gate B (documented citation check) and Gate C (fresh-context agent verifies citations trace to real sources).

**Sense-check reference — `~/brain/concepts/probability-calibration/probability_calibration_2026-04-23_v3.md`:** a standing companion doc with UK base rates (primary-sourced), distribution percentiles with CIs (N=8 FMCG; broker medians), margin→multiple regression (R²=0.68 robust), horizon-conversion math, and a disputed-claims log flagging fabricated anchors (e.g. the v1 Trowers 71% close rate). Use it as a **sense check** — cross-reference citations against it at Gate B. **Do NOT import numbers from its §5 chain templates or §9 update-rule structure** — those are deliberately structure-only. If a review's base-rate citation contradicts a T1 entry in §2–4 of the calibration doc, the reviewer must reconcile before Gate C sign-off.

**Violation examples:**
- Stampfree v1 (2026-04-22) — Blockbuster probability set at 10% for a pre-revenue company (Mar 2026 turnover: £0). No named precedent cited. Drafter's own §10f acknowledged "Blockbuster dominates 51% of total weighted entry price." Under Rule 19, Blockbuster 10% → 3% (hard cap for pre-revenue), Investability drops 63 → 33.
- Thermify v1 — Blockbuster 5% for a pre-commercial hardware company (n=1 SHIELD install, £81k FY25 turnover). No 24-month precedent within ±1 sub-sector cited. Under Rule 19, 5% → 3% default, reducing A from 51.4 to 35.4.

### 20. Sensitivity band mandatory on review header

The third anti-circularity defence. Even with empirical probabilities, the point-estimate Investability hides how fragile the call is. A review where shifting any one probability ±10pp swings Investability by 30 points is NOT the same as a review where the same shift moves Investability 4 points. The difference matters to the action.

**Computation (runs before Gate C sign-off):**

1. Compute Investability at central estimate (drafter's best inputs).
2. For each scenario probability, shift ±10pp (reallocating symmetrically among other scenarios proportionally). Recompute Investability.
3. For each multiple in §10d, shift ±30%. Recompute Investability.
4. For each FV-input (dilution, horizon): stress per documented uncertainty (±5pp dilution, ±1yr horizon).
5. **Investability_low = minimum across all stresses. Investability_high = maximum.**

**Header display (MANDATORY):**
```
INVESTABILITY  97  [69 – 118]   sensitivity ±24 points
```

**FRAGILE flag (revised 2026-04-24 — threshold relaxed from 15pp to 30pp after A13 batch exposed that most Republic portfolio reviews carry genuine uncertainty and "FRAGILE-everything" defeats the discriminating purpose of the flag):**

| Band width | Label | Action constraint |
|---|---|---|
| ≤ 15pp | **TIGHT** | Any action based on central Investability |
| 15–30pp | **MODERATE** | Upward actions (BUY/ADD) gated by low-end of band; downward actions (PASS/EXIT) gated by high-end. Standard discipline — not a flag. |
| > 30pp | **FRAGILE** | Action requires explicit override paragraph in Section 17 explaining why the wide band is acceptable given the conviction. Default action moves one band more conservative than central suggests (e.g. central HOLD → WATCH) until band tightens (via full accounts filing, named precedent landing, scenario probabilities re-anchored). |

**Rationale for relaxation:** Every Republic portfolio review sits on genuinely uncertain primary-source inputs (filleted accounts, judgement-based probabilities, pre-IND commercial assumptions). A 15pp threshold flagged 5 of 6 rebuilds in the 2026-04-23 batch — which told the reader nothing differentiating. Moving to 30pp reserves the FRAGILE label for reviews where the uncertainty genuinely dominates the central estimate (e.g. Heights v11 at 63pp, Yonder v4.1 at 51pp) vs reviews with ordinary portfolio-level uncertainty (e.g. TransferGo v4 at 28pp, AltoVita v2 at 8pp).

**Why this matters:** a FRAGILE review with Investability 97 central but [69–118] band should NOT trigger HOLD based on the central alone — the low-end (69) sits below the WATCH threshold (70). Margin-of-safety logic: if the number can plausibly be that low, don't act as though it's definitely that high.

**Cross-reference:** Rule 20 is enforced at Gate C. The sensitivity sweep is the single most important new output of the Gate C pass — more important than any individual red-team finding, because it's what stops a point estimate from being over-read.

### 21. EIS calibration mandatory for UK-eligible primary raises

EIS (Enterprise Investment Scheme) provides 30% income tax relief on qualifying primary share subscriptions, plus CGT exemption after 3-year hold for EIS-compliant companies. For UK taxpayers with sufficient income tax liability, this is a ~30% effective discount on entry price and a further ~24% CGT saving on realised gains. The canonical framework has historically ignored this in TEP derivation, treating EIS as a "Light positive" footnote. Under Rule 21, EIS becomes a first-class input to Investability.

**Rule:**

1. **Every review must state EIS status explicitly**, per route:
   - Primary (current raise): EIS-eligible / not eligible / pending HMRC assurance — check the KIIS or Republic raise page; eligibility is clearly stated by the issuer
   - Secondary (post-raise purchases): **EIS NOT available — ever**. EIS attaches at primary subscription only. It does NOT carry forward to subsequent secondary buyers, regardless of whether HMRC certificates were issued to the original primary-round subscribers.
   - Existing lots in user's portfolio: per-lot EIS status. **The question is "was this lot bought in the primary Republic/Seedrs raise, or on the secondary market?"** — NOT "did the company have EIS certificates?" Only primary-bought lots are EIS-eligible. If the purchase route is unknown, it's a HIGH-priority Data Gap requiring portfolio-ledger check. Default assumption: if the user bought well after the original raise closed, it is secondary, not EIS.

**Anti-Pattern A14 (2026-04-24):** AKT London iter-3 Gate C incorrectly asserted Jack's lot "likely qualifies for EIS CGT exemption on exit" based on (a) HMRC certificates issued to the primary raise in Mar 2024 and (b) an assumed £3.60 (2022) or £5.00 (2023) acquisition price. User clarified Jack's lot was bought on secondary — EIS does NOT apply. Correction applied. **Guardrail:** any EIS claim on a user's existing lot must trace to a specific primary-round subscription date, not to the company's EIS certificate status. "The company was EIS-approved" does not mean "this holder's lot is EIS-eligible."

2. **Effective Cost computation** for EIS-eligible primary purchases:
   ```
   Effective Cost = Market Price × (1 − EIS_rebate)
   where EIS_rebate = 0.30 if primary + EIS-eligible + user has tax capacity
                    = 0    otherwise
   ```

3. **CGT exemption** on exit (3+ year hold, company still EIS-compliant at disposal):
   ```
   Net £/sh (EIS-adjusted) = Exit £/sh × 0.98  (no carry; no CGT)
   vs
   Net £/sh (non-EIS)     = Exit £/sh × 0.98 − 0.075 × max(0, Exit − Cost)
   ```
   *Note: Republic's 7.5% carry is NOT the same as CGT. Carry applies regardless of EIS status; CGT is the UK personal tax layer on top.*

4. **Dual-route disclosure when both primary and secondary are available:** Show Investability for BOTH (primary+EIS) and (secondary-no-EIS) paths. Neither path dominates automatically — primary+EIS has EIS uplift but may be locked until 3-year clock, while secondary may clear below effective EIS price.

5. **Tax capacity caveat:** The 30% rebate assumes the user has enough income tax liability to absorb the relief. If user's tax capacity is insufficient, the effective rebate is proportional. For Jack's portfolio specifically: tax capacity is assumed sufficient per user confirmation 2026-04-23.

**Template requirement:** Section 10 must include explicit EIS adjustment working when EIS is available. §11 (My Position) must include per-lot EIS status. The header Investability shows (primary+EIS) route when applicable, with secondary-route Investability shown in a sub-line.

**Violation examples:**
- Ignota Labs v1 line 344: *"all-in cost of £9.10 (pre-EIS relief) is used per the canonical spec"* — the canonical spec was wrong. Under Rule 21, Ignota's Investability should be 42 not 34.
- Thermify v1 — EIS listed as "Light positive" in §15; not computed in §10. Under Rule 21, primary+EIS Investability is 58 vs 45 raw.
- Albotherm v1 — primary £6.60 EIS-eligible; TEP £6.00 is a −9% discount raw but +32% discount on effective EIS cost. Under Rule 21, this flips WATCH to HOLD on the primary route.

### 22. Investability scoring (Q × A × M framework)

The unified scoring metric. Replaces the old 0–100 Fundamentals Score as the single action-determining number.

**Formula:**
```
Investability = Q × (1 + A/100) × (0.25 + 0.75 × M)

  where:
    Q = rescaled quality score (0–100)
    A = asymmetry score (0–100)
    M = mispricing ratio, capped [0.5, 2.0]
```

Anchor: **Investability = 100 when Q=100, A=0, M=1** (a perfect franchise at fair price with no asymmetric upside). Most reviews will score 30–150.

**Q — Quality score (0–100):**

Rescaled from the previous 6-factor scorecard by dropping Risk (10) and Liquidity (10) — those concerns now live in the sensitivity band and the Action Matrix. The remaining four factors rescale:

| Factor | Old weight | New weight | Filleted cap |
|---|---|---|---|
| Business Model & Moat | 25 | 31 | — |
| Unit Economics & Financial Health | 25 | 31 | 16 (cap binds when P&L is filleted) |
| People | 15 | 19 | — |
| Market Position & Traction | 15 | 19 | — |
| **Q total** | — | **100** | — |

The old Risk (10) and Liquidity (10) sub-scores are still written in Section 1 for diagnostic visibility — but they do NOT feed Q. Risk shows up in sensitivity band width; Liquidity shows up in Action constraints (can you actually buy/sell?).

**A — Asymmetry score (0–100):**

Captures upside optionality from Bull + Blockbuster scenarios only. Lower-tail scenarios (Bear, Base) do NOT contribute — those feed Fair Value via M.

```
A = min(100, 25 × Σ(P_scenario × Multiple_on_cost))  for Bull + Blockbuster only
where Multiple_on_cost = Net £/sh at exit (after fees/carry) ÷ Effective Cost basis
```

- A = 0 when there's no Bull/Blockbuster upside.
- A = 50 when prob-weighted upside returns are 2× effective cost.
- A = 100 (capped) when prob-weighted upside returns are ≥4× effective cost.

**M — Mispricing ratio (capped [0.5, 2.0]):**

```
M = Fair Value / Market Price anchor
```

Where Market Price anchor = **30d VWAP** (smoothed market-clearing price) for companies with secondary trading, else **primary raise price** (for pre-secondary companies or paused-secondary cases).

And Fair Value is computed from Bear + Base + Bull scenarios only (Rule 18 + 19 + 23 below, with Blockbuster explicitly excluded to avoid double-counting):

```
FV = (Σ(P_scenario × Net £/sh) / Σ(P_scenario)) × 1/(1 + r)^horizon

  over Bear + Base + Bull scenarios only
  where Σ(P_scenario) for Bear+Base+Bull typically ≈ 0.95–0.97 (renormalised)
  r = 10%/yr (S&P hurdle)
  horizon = stated in years per review (§10d)
  Net £/sh already includes dilution, Republic fees, and carry
```

M capped at 2.0 (extreme cheapness likely signals modeling error, not opportunity). Capped at 0.5 at the low end for the same reason (extreme expense likely signals stale price data or modeling error).

**Action thresholds:**

| Investability (low-end of band for upward actions; high-end for downward) | Action |
|---|---|
| ≥ 130 | **BUY** |
| 110 – 129 | **ADD** |
| 90 – 109 | **HOLD** |
| 70 – 89 | **WATCH** |
| < 70 | **PASS** / **EXIT** |

**Upward action (BUY/ADD/HOLD) is gated by the low-end of the sensitivity band.** Downward action (WATCH/PASS/EXIT) is gated by the high-end. Central estimate drives diagnostic presentation but not the Action.

**The three-panel header presentation (MANDATORY):**

```
┌──────────────────────────────────────────────────────────────────────┐
│ {Company} — {date} (v{N})                                            │
├───────────────────┬───────────────────┬──────────────────────────────┤
│ Q — QUALITY   NN  │ A — ASYMMETRY NN  │ M — MISPRICING   N.NN        │
│ Business  NN/31   │ Bull  NN% × N.NN× │ FV £N.NN / Market £N.NN      │
│ UnitEcon  NN/31   │ Block NN% × N.NN× │ EIS? (Effective Cost £N.NN)  │
│ People    NN/19   │                   │                              │
│ Market    NN/19   │ ProbWtd upside    │ Horizon: NN years            │
├───────────────────┴───────────────────┴──────────────────────────────┤
│ INVESTABILITY   NNN   [NN – NNN]    sensitivity ±NN    [FRAGILE]     │
│ Action: {BUY/ADD/HOLD/WATCH/PASS}  — gated by low-end / central      │
└──────────────────────────────────────────────────────────────────────┘
```

**Enforcement:**
- Every review must display Q, A, M individually before the Investability composite.
- Sensitivity band is mandatory (Rule 20).
- EIS-adjusted Investability is a separate line when applicable (Rule 21).
- The old 0–100 Score can remain in §1 for diagnostic continuity during the transition period but does NOT drive action.

### 23. Blockbuster scenario is excluded from Fair Value (anti-double-counting)

The fourth anti-circularity defence. Blockbuster probability and multiple feed A (the asymmetry score, which rewards tail optionality). The same Blockbuster contribution MUST NOT also feed Fair Value — otherwise the speculative tail inflates the Investability score twice: once via A, once via M.

**Rule:** Fair Value is computed from Bear + Base + Bull scenarios only. Blockbuster is explicitly excluded from the FV prob-weighted exit average.

Mechanically, sum probabilities over Bear + Base + Bull (typically 95–97% of total mass) and renormalise so they sum to 100% before weighting the exit £/sh. The Blockbuster scenario is preserved in the review for narrative purposes (§10d exit table) and feeds A directly, but does not touch FV.

**Why:**
- A rational buyer pays for expected earnings (Bear/Base/Bull territory). Tail outcomes at acquisition are captured by warrants, ratchets, contingent consideration — not headline price.
- A already captures Blockbuster upside as optionality premium. Including it in FV would double-count the same uncertain tail.
- Empirically: reviews with aggressive Blockbuster weights (Thermify 5%, Stampfree 10%) had inflated both A and M under the old double-counting formula. Moving Blockbuster to A-only halved M for Thermify and dropped Investability 97 → 44.

**Exception:** Blockbuster can be included in FV only when the Blockbuster scenario is backed by a named dated precedent within 24 months that has *already closed* (not a hypothetical) AND the drafter argues the specific subject company has demonstrable pathway to the same outcome. This is the rare case and requires Gate C explicit challenge. Default: exclude.

---

### 24. Extended YAML frontmatter — machine-readable cap-table block (T2.3, added 2026-04-29)

Every new review MUST open with extended YAML frontmatter that downstream
consumers (signal-grade dispatcher, registry sync, weekly-self-eval) can
parse without re-extracting from prose. Format:

```yaml
---
type: review
slug: hunter-gather                      # canonical brain folder slug (matches investment_registry.folderSlug)
date: 2026-04-22
version: 1
fundamentals_score: 61                   # 0-100
signal_state: "Mixed (leaning positive)"
action: HOLD                             # HOLD | WATCH | PASS | SELL | BUY-AT-TEP
fair_value_low_gbp: 18.0
fair_value_high_gbp: 21.5
target_entry_price_gbp: 9.45             # TEP per share
holding_active: true                     # has Jack a position?
cap_table:
  preference_stack_gbp: 0                # aggregate preference £; 0 if no Preferred
  founder_pct_fully_diluted: 30.4
  options_outstanding: 6733283
  dilution_to_liquidity_pct: 14.6
  share_classes:                         # one entry per class on AoA
    - name: Ordinary
      voting: standard                   # standard | super | non_voting
      preference: pari_passu             # pari_passu | 1x_non_participating | 1x_participating | 1x_participating_capped
    - name: "Series A Preferred"
      voting: standard
      preference: 1x_non_participating
last_review_action_was: HOLD             # registry-pointer style; lets registry diff
---
```

**Why structured:** signal-grade dispatcher reads the `holding`, `fairValue`,
`targetEntryPrice`, `fundamentalsScore`, `action` fields directly from the
investment_registry.json (which mirrors these). Future bid-tracker, weekly
auto-review-trigger, and ack-signal calibration all benefit from the same
machine-readable surface. Avoids the prose-parse-every-event tax.

**What it does NOT replace:** the full prose review remains the source of
truth for thesis, scoring rationale, M&A precedents, Section 20 audit log.
The YAML is a derived summary — if YAML and prose disagree, prose wins.

**Scope:** applies to v2+ reviews dated post-2026-04-29. Existing reviews
not retro-fitted; they remain valid via prose extraction. Cap-table block
extracted at review-write time during Section 9 / 13 work — no extra effort.

**Violation (added to Gate C as item #15):** any review at v2+ post-2026-04-29
without the extended frontmatter fails Gate C and must be revised.

---

## How to invoke

Cold-start baseline for a new review:

```
cd ~/agents/republic && ./scrapers/.venv/bin/python -m scrapers.republic_review_gather --company "TransferGo"
```

Live re-walk for an event-driven refresh (idempotent; unchanged artefacts reused):

```
cd ~/agents/republic && ./scrapers/.venv/bin/python -m scrapers.republic_review_gather --company "Heights"
```

Dry run — enumerate attachment hrefs without downloading, for debugging or when network bandwidth matters:

```
cd ~/agents/republic && ./scrapers/.venv/bin/python -m scrapers.republic_review_gather --company "TransferGo" --dry-run
```

Single-tab focus — when only one tab needs refreshing:

```
cd ~/agents/republic && ./scrapers/.venv/bin/python -m scrapers.republic_review_gather --company "Heights" --tabs updates,discussion
```

Single-raise focus — when history is already captured and only the live raise has changed:

```
cd ~/agents/republic && ./scrapers/.venv/bin/python -m scrapers.republic_review_gather --company "TransferGo" --raise /transfergo
```

---

## Anti-Patterns — prior specific failures

These are the concrete incidents this skill exists to prevent. Adding to this list is part of the review's own improvement loop.

### A1. TransferGo v1 (2026-04-17) — "CH-only under 403"

**What happened:** Claude (me) attempted `WebFetch https://europe.republic.com/businesses/transfergo`, got a 403 from Cloudflare, and silently fell back to Companies House + external triangulation for the entire v1 review. No Republic tab was walked. No manifest existed.

**Why it was possible:** the Republic gather was a *memory-dependent checklist* inside `ways_of_working.md` Step 2, not a *structural gate*. A skipped checklist item is invisible to the reviewer.

**The fix this skill enforces:** Rule #1 — no manifest, no synthesis. The manifest is now a file-on-disk gate. You can't "forget" to produce it the way you can forget a checkbox.

### A2. Metallobio (2026-04-11) — "evidence without provenance"

**What happened:** The Metallobio KIIS and pitch-deck PDFs were manually dropped into `~/agents/republic/research/metallobio/evidence/` with filenames like `metallobio_kiis_en.pdf` — no date prefix, no manifest, no OCR sibling. A later rerun would silently overwrite; no audit trail links the PDF to which raise it was extracted from.

**The fix this skill enforces:** every gather writes to `evidence/{YYYY-MM-DD}/` with a manifest. PDFs carry `source_href`, `sha256`, and dated filenames. OCR siblings are written automatically.

### A3. `WebFetch europe.republic.com.*` drift

**What happened (recurring):** under time pressure, I've historically tried `WebFetch` on Republic pages hoping the block was transient. It never is. The block is Cloudflare fingerprinting the request signature — only the Playwright persistent profile (with stealth patches + imported cookies) passes.

**The fix this skill enforces:** Rule #5. `WebFetch https://europe.republic.com.*` is a forbidden operation. No workarounds. If the persistent-profile pathway is broken, fix it via `import_cookies.py` — don't detour around it.

### A5. Republic URL pattern drift — historical raises at root-level Seedrs URL

**What happened (2026-04-20, surfaced during Currensea v1 baseline):** the gather walked `/businesses/currensea1`, `/businesses/currensea2`, `/businesses/currensea3` and got `section_not_available_on_this_raise` on every tab. The reason string implied "the section isn't present on this older raise". The truth was worse: the **URLs themselves 404**. Republic migrated `/{slug}` → `/businesses/{slug}` for the *current* raise of each company, but historical raises still only resolve at the **pre-migration Seedrs-style root URL** `https://europe.republic.com/{slug}/sections/{tab}` (no `/businesses/` prefix).

Evidence:
- `https://europe.republic.com/businesses/currensea3` → `Page Not Found | Republic Europe`
- `https://europe.republic.com/currensea3/sections/key-information` → live, 10 KIIS PDFs (multi-lingual) from `assets.seedrs.com/uploads/kiis/pdf/file/...`

**Impact:** every prior review with multiple raises silently lost historical-raise content — and therefore the **prior-round KIIS** required by Rule #4 above. Likely affected: Heights (5 raises), TransferGo (3), AltoVita (3), Altilium (2). No review caught this because the `section_not_available_on_this_raise` reason-string looked "expected" for older raises.

**The fix `~/agents/republic/scrapers/review_common.py` enforces:**
- `navigate_to_tab` detects the Republic 404 title (`"Page Not Found | Republic Europe"`) and falls back to `legacy_tab_url(slug, tab)` — `{origin}/{slug}/sections/{tab}`.
- Successful fallback sets `meta["legacy_url_used"] = True`, which per-tab handlers merge into `TabResult.extra`. The raise-level `legacy_url_used` flag is aggregated into the manifest `raises[].legacy_url_used` so a scan of the manifest surfaces the fallback immediately.
- A distinct `"not_found"` status distinguishes "both URLs 404" from "section genuinely missing on a page that loaded" — the manifest reason becomes `raise_url_not_found`, not `section_not_available_on_this_raise`.
- Legacy-URL pages render as static HTML without Republic's `section[data-section=X].rendered` marker, so the fallback branch skips `wait_for_section_rendered` and instead waits for any anchor/main/article as a readiness signal.

**Why this rule stays relevant** even after the fix:
1. The KIIS extraction JS (`review_kiis.js`) scans all anchors for `/kiis/i` and works on both URL patterns — but other extractors (pitch, team, key_info, investors, updates, discussion, documents) were written against Republic's SPA DOM. On legacy pages they may return empty or partial data. A `status: partial` on a `legacy_url_used: true` tab is a predictable outcome, not a bug — but the review SHOULD state so in Section 16 rather than silently treating the tab as uninformative.
2. **If Republic migrates again** (or a new platform takeover happens), expect this same pattern: a new canonical URL + a legacy URL that older raises still cling to. The detection pattern (title-check + URL-fallback) and the manifest-level `legacy_url_used` flag generalise to any future URL drift.
3. Running the `scripts/backfill_historical_raises.py` is the right move any time you suspect an affected review — it re-gathers without overwriting the current-dated manifest.

### A4. "Indicative price is the current valuation"

**What happened (recurring):** the Republic raise's indicative price is often months-stale relative to the secondary VWAP. Framing reviews around the indicative (TransferGo: £20.61) when the market-clearing price is VWAP (£10.63) overstates fair value by 40-50%.

**The fix this skill enforces:** Section 2 of the review (Market Dynamics) flags `indicative` as a "static raise anchor, not a live signal." The gather's `secondary.json` artefact carries VWAP + order-book depth alongside the indicative so the two can be compared inline.

### A6. Rheal v1 (2026-04-21) — generic sector multiples in lieu of advisor precedent

**What happened:** Rheal v1 Section 10 used "2-3× revenue" as the UK wellness FMCG sector comparable, treating it as a reasonable default. Same-day v2 surfaced Spayne Lindsay's (the actual advisor Rheal hired) most recent wellness exit: **Deliciously Ella sold to Hero Group Sep 2024 at 1.1-1.4× revenue** ($35M for ~£24M revenue). v1 Base case was ~2× over-priced.

**The fix this skill enforces:** Rule 9 (active-M&A precedent triangulation). Now reinforced by Gate B — no Section 10 writing until Rule 9 precedent table has ≥3 transactions including advisor-specific where known.

### A7. OnBuy v1 (2026-04-21) — accepted "cap-table confidential"

**What happened:** CEO Cas Paton told Republic investors that the cap table couldn't be disclosed due to "strict confidentiality clauses". v1 accepted this at face value. Same-day v2 downloaded OnBuy's Articles of Association (1 Mar 2024, 55pp) — **fully public on CH** — which disclosed 4 share classes (A Ordinary, Ordinary, B Shares non-voting, Deferred), full 1× non-participating liquidation preference waterfall, EIS voting + surplus-assets caps at 29.99%/30%, and Investor Director / Investor Majority Consent regime.

**The fix this skill enforces:** Rule 13 (share-class inventory mandatory). Management's confidentiality claim ≠ information being confidential. Articles are nearly always public; claim the opposite only after checking CH filing history.

### A8. Laundryheap v1 (2026-04-21) — flagged overdue accounts as risk without diagnosis

**What happened:** v1 Risk section noted "FY24 accounts overdue" as a certainty-high-impact risk but did not investigate the cause. Same-day v2 read the 15-Apr-2026 amended FY23 accounts, identified Note 9 Prior Year Adjustment disclosing **two audit findings**: (a) £398k intragroup loan classification error (parent BS only); (b) missing amortisation policy on capitalised development costs — now applied at 5-year useful life, structurally increasing annual operating loss by ~£400k. The "overdue" status is a **transition from s477 audit-exempt (incorrectly claimed at £17.7M turnover above £10.2M threshold) to fully audited by Azets**. Less-bad interpretation than v1 implied but diagnostic information that reframes the risk.

**The fix this skill enforces:** Rule 14 Gate B requires "amended or overdue accounts have diagnosed cause" in Data Gaps; Rule 16 Gate C #4 (Restatement test) verifies this. Never flag "amended" as a risk without stating WHAT was amended.

### A10. Laundryheap backtest (2026-04-21) — celebrity-test scope too narrow + retail share-class allocation never explicitly asked

**What happened:** The integrated Gate A/B/C workflow was validated end-to-end against the canonical Laundryheap v2 review. The workflow caught all three of v2's headline findings (preference waterfall, FY23 amendment cause, Rule 9 precedent sweep) **plus five additional findings v2 missed** (Claret £828k drawn balance, EMI option pool 34,696 @ £32.76, cash-vs-operating-loss distinction, share-options PYA #3, subsidiary/market gap). But the workflow also **missed two findings v2 caught**:

(1) **Verb VC = Alex Chesterman** (Cazoo / Zoopla serial-founder). The cap table listed "VERB VC SCSP" as institutional A Preferred holder; the Gate C agent N/A'd Test 7 (celebrity/angel) on the basis of "no TV/media exposure." Chesterman is a textbook celebrity-grade UK serial founder whose other portfolio is materially relevant to exit-route plausibility — Test 7 should have been triggered by the institutional-name pattern, not just by TV exposure.

(2) **Republic retail share-class allocation question** — Feb 2025 pre-emption update said the round was "Ordinary and B preferred shares". Whether retail received Ordinary (subordinated) or B Preferred (with £193.06 preference) is the single largest waterfall sensitivity for Republic investors. v2 raised it as a critical open data ask. Backtest assumed Ordinary throughout without flagging the question, which is structurally wrong — the assumption may be right but it must be explicit and challengeable.

**The fix this skill enforces:**
- **Rule 10 broadened**: now covers both (a) TV/media celebrities AND (b) institutional investor GPs / managing partners. Test 7 in Rule 16 Gate C updated to reflect both triggers; N/A only when neither applies.
- **Rule 16 Gate B**: new 6th item — when a pre-emption round mixes Ordinary + Preferred classes, retail allocation must be explicitly identified or recorded as a HIGH-priority Data Gap.

**What this teaches about the workflow itself:** The Gate C agent did genuinely substantive adversarial work (7 FIXes, 2 PASS, 1 N/A on first iteration), but the N/A was on a test the agent applied too literally. Agents will follow the checklist as written; the checklist needs to anticipate the failure mode, not the human reviewer. The Laundryheap miss is not a workflow failure — it's a checklist sharpening signal, which is how a healthy quality system is supposed to evolve.

### A11. Portfolio sweep (2026-04-23) — Blockbuster-probability double-counting across 5 pre-revenue reviews

**What happened:** The Q/A/M methodology sweep across all 23 reviews exposed systematic tail-inflation in pre-revenue deep-tech reviews. Five reviews (Thermify, Stampfree, Metallobio, Albotherm, Ignota) carried Blockbuster probabilities of 5–10% without any named 24-month precedent for a >10× revenue exit in the relevant sub-sector. Under default base rates (Blockbuster 3%), Investability dropped 21–59% for these reviews.

Further, the old scoring formula fed Blockbuster into BOTH A (asymmetry premium) AND FV (central value), producing a double-count. Thermify at Investability 97 under the old formula dropped to 44 under the corrected formula (Rule 23: Blockbuster excluded from FV).

**The fix this skill enforces:**
- Rule 19: Blockbuster 3% cap for pre-revenue companies (hard) unless named precedent within 24 months.
- Rule 23: Blockbuster is excluded from Fair Value — feeds A only.
- Gate C Tests 11, 12, 13: auditor verifies precedent anchoring, probability citations, and sensitivity band.

### A13. Header-body consistency failure (2026-04-23) — arithmetic corrections in §10g not propagated to header blocks

**What happened:** Fresh-context Gate C iter-3 audit on AltoVita v2, TransferGo v4, and Cheeky Panda v2 (2026-04-23) revealed that mid-document arithmetic corrections made during in-session self-audit had been applied to §10g but NOT propagated back to:
- the three-panel Q/A/M header block,
- the Decision Dashboard table,
- the Decision Output code block.

Three of four reviews carried two completely different number sets for the same company — a "header version" a reader sees first, and a "body version" buried in §10g.

**Most severe case:** TransferGo v4 header showed Investability 72 [56–96] FRAGILE WATCH; corrected body showed Investability 49 [38–66] FRAGILE PASS (new money). Different action entirely.

**Other examples:**
- AltoVita v2: header I=41 [26–63] FRAGILE WATCH; body I=36 [34–42] TIGHT PASS. Drafter also invoked "Rule 20 FRAGILE discipline" for the WATCH override when the corrected band is TIGHT, not FRAGILE — override was preserved but re-anchored to de-minimis exit cost.
- Cheeky Panda v2: six header values wrong (Q, A, M, FV, TEP, band high). Central Investability 57 was correct by coincidence; underlying Q/A/M decomposition materially different (Q=50.2 vs corrected 61.3).

**The fix this skill enforces:**
1. **Any revision to §10g MUST cascade to all header blocks.** Specifically: three-panel Q/A/M, Decision Dashboard rows (Investability, Q/A/M, FV, TEP), and Decision Output code block. A §10g change is not complete until the three downstream blocks match.
2. **Gate C Test 8 (Scorecard test) MUST verify header-body consistency** — the auditor does not just check that §10g arithmetic is internally correct, but that Q/A/M/FV/TEP/band values in the header match the §10g body. Any mismatch is a FIX.
3. **In-session self-correction is NOT equivalent to fresh-context Gate C** — this is why the rebuild reviews (Heights v11, Yonder v4, AltoVita v2, TransferGo v4, Cheeky Panda v2) were all flagged for proper fresh-context re-audit. The in-session pass catches arithmetic drift but not presentational drift, because the drafter who made the correction is too close to the header to notice it's stale.

**Discipline:** the moment a §10g value changes (post-Gate-B or mid-Gate-C), update the three header blocks in the same edit. Rule 22's three-panel header is a display of §10g inputs — it is NOT an independent source of truth.

**Confirmation-bias lesson (added after 4-of-5 recurrence rate on rebuilds 2026-04-23/24):** In-session Gate C does NOT reliably catch A13 because the drafter who made the §10g correction and wrote the headers shares context across both — confirmation bias suppresses the inconsistency. **A fresh-context Gate C (spawned via `Agent` tool from the main session, not from within a sub-agent) is structurally required to catch A13.** If the Agent tool is unavailable at sub-agent runtime (e.g. during a rebuild-agent's own Gate C attempt), the rebuild's Gate C is provisional and must be followed by a fresh-context audit from the main session before the review is considered finalised. This is why all 2026-04-23 rebuilds were queued for "fresh-context Gate C re-run" after initial in-session Gate C was flagged as limitation.

### A12. EIS-hidden-return pattern (2026-04-23) — canonical spec ignored EIS across 5 primary-eligible reviews

**What happened:** The canonical spec historically computed Target Entry Price on a pre-EIS-relief basis (explicitly stated in Ignota v1 line 344: *"all-in cost of £9.10 (pre-EIS relief) is used per the canonical spec"*). For primary + EIS-eligible raises, this under-priced the investment by the 30% tax rebate. Five current reviews (Albotherm, Ignota, Metallobio, Stampfree, Thermify) listed EIS as "Light positive" in §15 without computing the effective cost. Albotherm specifically was miscalibrated: primary £6.60 effective cost £4.62 under EIS makes M = 1.32 (cheap) vs M = 0.92 (fair) raw — flipping the primary route from WATCH to HOLD.

**The fix this skill enforces:**
- Rule 21: EIS calibration mandatory. Effective Cost = Market Price × (1 − EIS_rebate). Dual-route disclosure when primary+secondary both available.
- Gate C Test 14: auditor verifies EIS computation in §10g and per-lot EIS status in §11.

### A9. Creditspring v1 (2026-04-21) — missed Rule 9 despite "exit or liquidity event" flagged by management

**What happened:** Neil Kadagathur's 8 Mar 2024 investor update said "soon we will be thinking about an exit or liquidity event." This is the textbook Rule 9 trigger. v1 ignored it — Section 10 used generic "5-10× net income" without any peer-transaction research. Same-day v2 sweep found: Zopa Dec 2024 raise at $1B+ / £226M rev = 4.5× revenue; Lendable Jun 2024 at £3.5B (Ontario Teachers); Klarna 2024 at 5.4× rev. Creditspring at VWAP is 2.3× rev — materially below peer benchmarks.

**The fix this skill enforces:** Rule 9 + Rule 16 Gate C #1 (Preference stack test) and #2 (Multiple inflation test). Rule 9 trigger detection is part of Gate A: any management "exit/liquidity" language MUST trigger the precedent sweep before Section 10.

---

## What this skill is NOT responsible for

- **Companies House research** — filings, PSC, charges, officers. These live outside Republic and are fetched via `find-and-update.company-information.service.gov.uk` (static HTML, no auth, no Cloudflare). `WebFetch` is fine for CH.
- **External triangulation** — SimilarWeb, Trustpilot, app stores, trade press, World Bank stats. `WebFetch` / `WebSearch` are the right tools here.
- **The synthesis itself** — scoring, narrative, valuation math, Section 10 exit scenarios. That's the review workflow, which consumes the manifest. This skill is only the gate, not the writer.

---

## Escalation

If the gather produces a manifest with `status: error` on more than 2 tabs for the same raise, the script is probably chasing stale selectors (Republic's DOM changed). Do not paper over by writing around the gaps. Instead:

1. Re-run with `--visible` to see what the browser sees.
2. Inspect the DOM; update the relevant `review_*.js` selector file.
3. Re-run the gather. If errors persist, ask the user before proceeding — we'd rather skip the review than synthesise on a broken gather.
