---
name: initial-company-research
version: 1.0.1
description: |
  First-contact investment research for a company before it deserves a full
  fundamentals review. Builds a baseline dossier, evidence/source manifest,
  edge map, data-gap list, and monitoring handoff. It is deliberately NOT a
  canonical valuation/action review: it may reject, monitor, or promote to
  fundamentals-review, but it must not issue BUY/ADD/HOLD/SELL, fair value, or
  target entry price.
triggers:
  - "research {company} as a potential investment"
  - "initial research on {company}"
  - "first pass on {company}"
  - "look into {company}"
  - "is {company} worth diligence"
  - "triage this Republic raise"
  - "research this Republic page"
  - "triage this URL"
  - "new company: {company}"
  - "should we add {company} to the watchlist"
tools:
  - read
  - write
  - bash
  - web_search
mutating: true
---

# Initial Company Research

## Contract

This skill guarantees:

- A first-contact company dossier that separates fact, hypothesis, stale signal, and data gap.
- Entity resolution before synthesis: company name, legal entity, domain, platform slug, aliases, false-positive exclusions.
- A source manifest with source class, URL/path, capture/discovery date, publisher date where relevant, freshness, and reliability.
- An edge map: what the pitch/market may be missing, what filings/platform data contradict, and what future signals would prove/disprove the thesis.
- A monitoring handoff for `signal-grade`, reports, and future `fundamentals-review`.
- A promotion decision: `REJECT`, `MONITOR`, `FULL REVIEW CANDIDATE`, or `URGENT FULL REVIEW`.

It does NOT produce canonical investment action, fair value, target entry price, or registry `latestReview` state. Those belong to `fundamentals-review`.

## Boundary with adjacent skills

Use this skill when the company is new, under-triaged, or Jack asks whether it is worth diligence.

Use `fundamentals-review` when Jack asks for a full investment review, valuation, action, fair value, target entry price, or refresh of a canonical company stance.

Use `signal-recontext` when a company already has a review and the question is whether one new signal changes the stance.

Use `signal-grade` only for watcher/daemon events.

## Phases

### Phase 0 — Route and scope

Accepted inputs:

- company name;
- Republic/Seedrs/company page URL;
- company website URL;
- article/press-release URL with a named company.

If the user sends a bare URL and says “research this”, “look into this”, “triage this”, or similar, resolve it here rather than generic link ingest. A bare URL with no investment intent may still route to `idea-ingest`.

1. Check `~/brain/companies/investment_registry.json` for an existing entry.
2. Check `~/brain/companies/{slug}/` for existing `_review_v*.md`, `_evaluation_v*.md`, and `_initial_research_v*.md` files.
3. If a current full review exists and Jack is reacting to a narrow event, route to `signal-recontext`.
4. If Jack explicitly asks for valuation/action, route to `fundamentals-review`.
5. Otherwise continue.

### Phase 1 — Entity resolution gate

Resolve before synthesis:

- canonical company name;
- registered/legal entity and company number where applicable;
- verified operating domain from a company-owned source;
- Republic/Seedrs/current raise/historical raise URLs where applicable;
- subsidiaries, trading names, and aliases;
- false-positive exclusions for news/RSS matching.

Stop and label a blocking data gap if identity remains ambiguous.

### Phase 2 — Evidence acquisition and source manifest

Build a source inventory. Minimum useful source set, where applicable:

- company website / owned domain;
- Republic/Seedrs page or raise page;
- Companies House profile and key filings;
- latest accounts, CS01, SH01, Articles / resolutions;
- founder/team sources;
- product/customer proof;
- market/competitor sources;
- news/press with publisher dates distinguished from discovery dates;
- existing brain evidence packets if present.

Every material source gets a row:

| Source | Class | URL/path | Captured/discovered | Publisher/filing date | Freshness | Reliability | Notes |
|---|---|---|---:|---:|---|---|---|

Source class:

- `primary-company`
- `primary-platform`
- `regulatory/filing`
- `independent-publisher`
- `market-data`
- `user-provided`
- `google-news-rss-only`
- `unknown`

### Phase 3 — Material-news freshness gate

Apply `fundamentals-review` Rule 26 even at first pass.

For funding, exit, major partnership, major customer/retailer, license/regulatory approval, leadership, litigation, or insolvency claims:

- Google News discovery date is not article date.
- Missing publisher date means the claim is not current fact.
- Google News RSS alone is never enough for a thesis-changing fact.
- Current primary source or two fresh independent sources are required before treating the claim as current.
- Stale or unverified material items go to Data Gaps / Watchlist, not thesis.

### Phase 4 — Business baseline

Summarise:

- product/service;
- customer and buyer;
- revenue model;
- maturity stage;
- market category;
- competitive set;
- distribution proof;
- moat hypothesis;
- regulatory dependencies;
- unit-economics clues.

Keep this factual. Do not pad thin evidence with generic market prose.

### Phase 5 — People, ownership, governance

Check:

- founders/operators;
- prior exits/failures;
- PSC/founder ownership;
- institutional investors and named GPs/principals where visible;
- share classes and Articles availability;
- board changes;
- governance red flags.

Do not call something “institutional backing” without identifying what/who sits behind the entity when that matters.

### Phase 6 — Financial / filings sanity check

Summarise available evidence:

- latest revenue/profit/loss/cash/debt where public;
- filing timeliness;
- dilution trail;
- raise history;
- management growth claims vs audited accounts;
- rough runway only where evidence supports it.

No precise fair value or TEP here. If valuation is needed, promote to `fundamentals-review`.

### Phase 7 — Edge map

This is the core output.

Write:

- consensus/pitch narrative;
- possible variant perception;
- evidence conflicts;
- what retail investors are likely missing;
- hidden upside/hard-to-see risk;
- 3–7 falsifiable confirmers;
- 3–7 falsifiable breakers;
- what a full review must resolve.

### Phase 8 — Monitoring handoff

Produce machine-readable monitoring spec in the dossier:

```yaml
monitoring:
  aliases: []
  exclude_phrases: []
  watch_flags:
    ch_stream: true
    google_news: true
    rss: true
    republic_updates: true
    snapshot: false
  material_signals: []
  thesis_confirmers: []
  thesis_breakers: []
  full_review_triggers: []
```

If a registry candidate is useful, write it as a candidate patch only. Do not update `latestReview` as if this were a full review.

### Phase 8.5 — Live pipeline handoff boundary

Initial research may recommend ongoing monitoring, but it must not silently wire a new company into live scraping.

Write a proposed registry/watchlist patch with:

```yaml
registry_candidate:
  display_name: "..."
  folderSlug: "..."
  slug: "republic-or-seedrs-slug-or-null"
  businessUrl: "..."
  companyNumber: "..."
  registeredName: "..."
  owned: false
  status: "watchlist_candidate"
  secondaryMarket: false
  matchConfig:
    aliases: []
    match_mode: word_boundary
    exclude_phrases: []
  watchFlags:
    rss: true
    ch_stream: true
    google_news: true
    snapshot: false
```

Current runtime caveat (2026-05-03): adding an approved registry entry with `companyNumber` makes Companies House stream matching possible; `watchFlags.rss` feeds registry-sourced RSS matching; Republic updates / Browser Owner market snapshots are currently owned/secondary-market biased; Google News still has owned-company bias in `sources/google_news.py`. If Jack wants non-owned watchlist monitoring, either patch those producers or label the dossier `monitoring_recommended_but_not_live`.

Approval boundary: modifying `investment_registry.json` to add a new live watch target is a control-plane change. Do it only when Jack has asked to add the company to monitoring/watchlist, and then verify registry JSON plus the relevant producer path.

### Phase 9 — Triage verdict

Allowed verdicts:

- `REJECT` — structurally unattractive or evidence too weak for further time.
- `MONITOR` — worth watchlist, not yet worth full review.
- `FULL REVIEW CANDIDATE` — plausible edge; run `fundamentals-review` before capital.
- `URGENT FULL REVIEW` — action window / raise / price move means full review should happen now.

Positive capital allocation language is forbidden. Use “promote to full review”, not “buy”.

## Output Format

Write the dossier to:

`~/brain/companies/{slug}/{YYYY-MM-DD}_{slug}_initial_research_v{N}.md`

Recommended frontmatter:

```yaml
---
type: initial_company_research
slug: {slug}
date: {YYYY-MM-DD}
version: {N}
company: {Company}
legal_entity: {Legal entity or unknown}
company_number: {number or null}
status: reject | monitor | full_review_candidate | urgent_full_review
confidence: low | medium | high
evidence_quality: weak | adequate | strong
full_review_recommended: true | false
watchlist_recommended: true | false
---
```

Recommended body:

1. Triage verdict
2. Entity resolution
3. Evidence inventory
4. Business baseline
5. Financial / filings sanity check
6. Team / ownership / governance
7. Market and competitive context
8. Edge map
9. Monitoring handoff
10. Data gaps ranked by investment importance
11. Recommendation and next step
12. Self-check

## Self-check gates

Before finalising, verify:

- Identity is unambiguous or explicitly blocked.
- Domain is verified from a company-owned source.
- Legal entity is found or explicitly unavailable.
- Every material claim has source attribution.
- News freshness is checked for material external claims.
- Management claims are labelled verified / partly verified / management claim only.
- Recommendation is one of the four allowed triage verdicts.
- No canonical FV, TEP, or BUY/ADD/HOLD/SELL action is issued.
- Monitoring handoff includes aliases, false-positive exclusions, and full-review triggers.
- If monitoring is recommended, dossier says whether it is `proposed_only`, `approved_for_registry`, or `monitoring_recommended_but_not_live`.
- No new live registry/watchlist target is added unless Jack explicitly asks for monitoring/watchlist wiring.

## Anti-Patterns

- Turning first-pass research into a fake full investment review.
- Issuing BUY/ADD/HOLD/SELL, fair value, or TEP without `fundamentals-review`.
- Trusting Republic/company pitch without filings or external triangulation.
- Treating Google News discovery date as publisher date.
- Using stale/resurfaced funding or partnership articles as current facts.
- Creating broad watch aliases without false-positive exclusions.
- Updating `investment_registry.latestReview` from an initial dossier.
- Silently adding a new company to live scraping from an initial dossier without Jack's monitoring/watchlist approval.
- Treating lack of evidence as neutral rather than a data gap.

## Tools Used

- `read` — inspect registry, existing reviews, brain pages, and evidence packets.
- `write` — save initial dossier and optional monitoring spec.
- `bash` — run deterministic local checks where needed.
- `web_search` — external source discovery after brain-first lookup.
