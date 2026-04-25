---
name: signal-grade
description: Given a raw signal (order-book alert, news event, or Republic notification) plus a context_bundle, grade it on two independent dimensions — severity (0–4) and review-needed (binary). Used by the router's LLM-grader tier when rule-based grading is uncertain or the signal is high-stakes.
triggers:
  - "grade this signal"
  - "what severity is this"
  - "should we review this"
status: CONTRACT ONLY — body TBD in Phase 21 (after 2 weeks of real signal data for calibration)
---

## Input

```yaml
signal:
  type: string        # e.g. "demand-surge", "new-low-ask", "ch-filing", "investor-update"
  source: string      # "order-book" | "news" | "notification"
  slug: string        # company slug
  ts: ISO8601
  raw: object         # source-specific payload
context_bundle:
  current_snapshot: object
  prior_snapshot: object | null
  rollups_14d: object | null
  registry: { fairValue, holding, cost_basis }
  recent_events: list[event]
  brain_summary: string | null  # latest eval excerpt
```

## Output

```yaml
severity: 0 | 1 | 2 | 3 | 4
review: true | false
reasoning: string  # 1-2 sentences explaining grade
confidence: 0.0–1.0
```

## Severity rubric (calibration TBD per Phase 21 — use these definitions for now)

- **0 — noise.** Normal market noise, within recent volatility band, no position change warranted. Log silently.
- **1 — interesting, low priority.** Deviates from baseline but not actionable. Include in daily digest.
- **2 — worth knowing.** Should reach Jack today. Single Telegram, headline only. No action implied.
- **3 — action possibly warranted.** Suggests a position change or deeper look. Telegram with trend context + suggested action. Jack decides.
- **4 — urgent.** Immediate attention. Crossed market, major governance event, filing materially changing fundamentals. Multi-message Telegram + escalation if no reply in 30 min.

## Review flag rubric

Set `review: true` when ANY of:
- The signal may have changed fundamentals (new material filing, leadership change, product development)
- The current eval is >14 days old AND the signal is non-trivial
- Multiple signals for the same company in the last 7 days (pattern, not one-off)
- A news item hints at undisclosed context (need to investigate)

Set `review: false` when:
- The signal is obvious and mechanical (crossed market — just trim)
- The signal is noise
- An eval from the last 7 days already covers the scenario

Review is INDEPENDENT of severity. Sev-0 + review=true is valid (minor signal but fundamentals hint); sev-4 + review=false is valid (urgent but mechanical action).

## Body TBD

Actual grading procedure, example-by-example calibration, historical edge cases — all added in Phase 21 after we have 2 weeks of real signals on the mini to ground against.
