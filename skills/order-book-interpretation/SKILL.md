---
name: order-book-interpretation
description: Given an order-book movement pattern (e.g., crossed market, demand surge, book thinning, new high bid), explain what it semantically means and what action implications it carries. Called by signal-grade as a chained sub-skill when the signal is an order-book type and grading needs interpretation.
triggers:
  - "interpret order book {pattern}"
  - "what does {pattern} mean on {slug}"
status: CONTRACT ONLY — body TBD in Phase 21
---

## Input

```yaml
pattern: string  # e.g. "crossed-market", "demand-surge", "new-low-ask", "book-thinning", "new-high-bid", "high-notional-new-ask"
slug: string
snapshot_context:
  current: object  # current snapshot fields
  prior: object    # prior snapshot
  rollups_14d: object
  registry: { fairValue, holding, cost_basis }
```

## Output

```yaml
interpretation: string    # 1-2 sentences: what this pattern likely means mechanically
market_reading: string    # 1 sentence: what market participants are probably doing
action_implications:      # list of actionable insights
  - string
severity_hint: 0 | 1 | 2 | 3 | 4  # suggested severity (signal-grade can override)
review_hint: true | false
```

## Pattern catalogue (starter — to be expanded in Phase 21)

- **crossed-market:** bid ≥ ask. Mechanical arb opportunity. Usually resolves in next scrape. Severity hint: 4.
- **demand-surge:** buySum rose >150% vs prior. Growing buy-side appetite. Severity hint: 2-3. Check if top-bid is new or just bigger.
- **book-thinning (ask-side):** sellSum <70% of prior. Supply drying up. Severity hint: 2 (buy opp developing).
- **new-low-ask:** bestAsk dropped to new low with <2% spread. Fresh seller accepting lower. Severity hint: 3 (buy opp).
- **new-high-bid:** bestBid rose to new high with <2% spread. Fresh buyer accepting higher. Severity hint: 3 (sell opp).

## Body TBD

Full catalogue + edge cases + relation to FV distance in Phase 21.

## Contract

This skill follows its purpose/frontmatter and the phases documented above. Preserve existing behaviour; this section exists to satisfy the shared skill conformance contract.

## Anti-Patterns

- Do not bypass the documented phases.
- Do not invent side effects not described by the skill.
- Do not treat this skill as complete without the relevant verification evidence.

## Output Format

Return a concise status summary with files touched, evidence collected, blockers, and next action.
