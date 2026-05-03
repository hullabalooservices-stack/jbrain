---
name: news-classification
description: Given a news item (article, CH filing, RSS entry, tweet) about a held company, classify its materiality and whether it suggests fundamentals have changed. Called by signal-grade as a chained sub-skill when the signal is a news type.
triggers:
  - "classify this news"
  - "is this material for {slug}"
status: CONTRACT ONLY — body TBD in Phase 21
---

## Input

```yaml
news_item:
  source: string       # "companies-house" | "google-news" | "sector-rss" | "twitter"
  slug: string
  title: string
  url: string
  summary: string      # excerpt or lede
  published_at: ISO8601
  raw: object          # source-specific
brain_context:
  latest_eval_summary: string  # from context_bundle
  fair_value: object
  holding: object
```

## Output

```yaml
materiality: "high" | "med" | "low"
fundamentals_change: true | false
change_type: list[string]  # e.g. ["new-funding", "leadership-change", "regulatory", "product-launch", "m&a", "noise"]
reasoning: string
severity_hint: 0 | 1 | 2 | 3 | 4
review_hint: true | false
```

## Materiality rubric (starter — refine per Phase 21)

**High:**
- New funding round announced
- Acquisition / M&A activity
- CEO/founder departure
- Regulatory action
- Significant new filing (e.g., strike-off notice)

**Medium:**
- New product launch or major update
- Partnership announcement
- Hiring a senior exec
- Sector-wide regulatory news
- Competitor major event

**Low:**
- Minor press mention
- Sector news not directly relevant
- Incidental social-media mention
- Noise

## Fundamentals-change flag

Set `fundamentals_change: true` when the news would plausibly change the eval's core thesis — growth trajectory, unit economics, moat, or governance. Otherwise false.

## Body TBD

Jack-calibrated examples from actual news history added in Phase 21.

## Contract

This skill follows its purpose/frontmatter and the phases documented above. Preserve existing behaviour; this section exists to satisfy the shared skill conformance contract.

## Anti-Patterns

- Do not bypass the documented phases.
- Do not invent side effects not described by the skill.
- Do not treat this skill as complete without the relevant verification evidence.

## Output Format

Return a concise status summary with files touched, evidence collected, blockers, and next action.
