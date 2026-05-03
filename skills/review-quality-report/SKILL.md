---
name: review-quality-report
version: 1.0.0
description: |
  Generate a deterministic quality-debt report for Republic company reviews:
  registry pointer integrity, latest-review status, evidence packet freshness,
  Rule 24 frontmatter conformance, Rule 26 material-news freshness risk, and
  stale/limited-review follow-up. This is a reporting/audit workflow, not a
  company valuation workflow.
triggers:
  - "review quality report"
  - "review quality debt"
  - "audit company reviews"
  - "check review registry"
  - "which reviews are stale"
  - "frontmatter and registry audit for reviews"
  - "quality debt in Republic reviews"
tools:
  - read
  - write
  - bash
mutating: true
---

# Review Quality Report

## Contract

This skill guarantees:

- A deterministic report over the company-review control plane, not an LLM opinion pass.
- Checks `investment_registry.json`, latest company-root review files, evidence packets, review statuses, Rule 24 frontmatter, and Rule 26 material-news freshness risk.
- Flags contaminated / unsafe review state before it feeds investment strategy.
- Saves reports under `~/brain/reports/republic-investing/` with timestamped frontmatter.
- Does not change company actions, fair values, target entry prices, or review content.

## Inputs

Canonical inputs:

- `~/brain/companies/investment_registry.json`
- `~/brain/companies/{slug}/*_review_v*.md`
- `~/brain/companies/{slug}/*_evaluation_v*.md`
- `~/brain/companies/{slug}/evidence/current/manifest.json`
- `~/brain/companies/{slug}/evidence/current/EVIDENCE_INDEX.md`
- `~/brain/companies/{slug}/evidence/current/historical_context.md`
- optional watcher context in `~/agents/republic/.watcher/` for signal-grade counts

Helper script:

- `~/gbrain/skills/review-quality-report/scripts/generate_review_quality_report.py`

## Phases

### Phase 1 — Run deterministic report

From any working directory:

```bash
python3 ~/gbrain/skills/review-quality-report/scripts/generate_review_quality_report.py
```

The script writes:

`~/brain/reports/republic-investing/{YYYY-MM-DD-HHMM}_review_quality_debt.md`

### Phase 2 — Registry pointer integrity

Check:

- registry parses as JSON;
- each entry has `folderSlug` or an inferable folder;
- each `latestReview.path` exists if present;
- latest root-level review by version/date matches or supersedes registry pointer;
- every latest root review has a registry entry;
- status coverage exists (`latestReview.reviewStatus`).

### Phase 3 — Review status and canonicality

Bucket latest reviews by status:

- `canonical_final`
- `limited_update`
- `maintenance_refresh`
- `test_candidate`
- missing / unknown

Flag:

- missing status;
- latest file newer than registry pointer;
- maintenance refresh used as if canonical;
- no explicit data vintage / limitations.

### Phase 4 — Evidence packet coverage

Check per company:

- `evidence/current/manifest.json` exists;
- `EVIDENCE_INDEX.md` exists;
- `historical_context.md` exists;
- evidence index contains warnings/errors;
- review data vintage discloses missing/stale evidence.

### Phase 5 — Rule 24 frontmatter conformance

For post-2026-04-29 v2+ reviews, check frontmatter for required machine-readable keys:

- `type: review`
- `slug:`
- `date:`
- `version:`
- `fundamentals_score:`
- `signal_state:`
- `action:`
- `fair_value_low_gbp:` / `fair_value_high_gbp:` or explicit equivalent
- `target_entry_price_gbp:` or explicit equivalent
- `holding_active:`
- `cap_table:`

Flag nonconforming files. Do not auto-fix; this is a report.

### Phase 6 — Rule 26 material-news freshness risk

Heuristically scan latest reviews for material-news terms:

- funding, raised, new investors, Series A/B/C/D;
- acquisition, IPO, exit, sale process;
- partnership, major customer, retailer, license, regulatory approval;
- litigation, enforcement, insolvency, restatement.

If such terms appear, require evidence of a material-news freshness table or equivalent fields:

- `Discovery date`
- `Publisher date`
- `Resolved URL`
- `Freshness`
- `Confirmation`

Flag reviews that contain material-news terms without a freshness table. Treat this as a quality-debt warning, not proof of error. Known contaminated cases should be escalated manually.

### Phase 7 — Report priorities

Classify findings:

- **P0 contaminated** — known false material fact or review explicitly unsafe for strategy.
- **P1 blocking** — missing registry path, missing evidence, stale/unknown material-news freshness, noncanonical review being used for action.
- **P2 quality debt** — missing reviewStatus, frontmatter nonconformance, no Section 20, data vintage unclear.
- **P3 cleanup** — docs/schema drift, naming legacy, old evaluation naming.

### Phase 8 — Output and action handoff

Report should end with:

- top 5 fixes;
- companies needing review correction;
- companies needing metadata/frontmatter cleanup only;
- safe-to-use canonical reviews;
- recommended next skill/workflow for each issue.

## Output Format

Saved report frontmatter:

```yaml
---
title: Republic review quality debt
category: republic-investing
type: report
date: YYYY-MM-DD
time: HH:MM BST
---
```

Body outline:

1. Summary
2. P0/P1 issues
3. Registry integrity
4. Review status coverage
5. Evidence packet coverage
6. Rule 24 frontmatter debt
7. Rule 26 material-news freshness risk
8. Recommended next actions
9. Source files checked

## Anti-Patterns

- Treating this report as a valuation/review update.
- Auto-editing reviews or registry entries from the report script.
- Ignoring warnings because the registry path exists.
- Treating heuristic material-news flags as proof of error without checking sources.
- Letting a known contaminated review feed strategy just because it is the latest version.

## Tools Used

- `read` — inspect registry, reviews, evidence packets, script output.
- `write` — save timestamped report.
- `bash` — run deterministic helper script and tests.
