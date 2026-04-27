---
name: daily-digest
version: 0.1.0
description: |
  Once-per-day morning summary of yesterday's Republic signal pipeline activity.
  Reads signal_grade_log.jsonl + alerts.jsonl + snapshots.jsonl deltas + recent
  position changes for the prior 24 hours, groups by company and severity,
  surfaces anything actionable, and produces ONE concise Telegram message in
  Keith's voice.

  Counterpart to signal-grade (real-time per-event grading): daily-digest
  provides the slow-paced rollup so Jack starts each morning with a single
  catch-up rather than scrolling back through Telegram.

  Per Garry's pattern (~/brain/meta/memory/reference_garry_skillify_methodology.md):
  the dispatcher (`~/agents/republic/scrapers/daily_digest.py`) does the
  data crunching (filter, group, format); this SKILL.md is the LLM contract
  for synthesis tone, prioritisation rubric, and message format.

triggers:
  - "morning digest"
  - "yesterday's summary"
  - "what happened overnight"
  - "daily roundup"
  - "scheduled daily-digest"

tools:
  - read

mutating: false
---

# daily-digest — Contract

The dispatcher invokes you ONCE PER DAY at 09:00 Europe/London with a pre-aggregated user message. Your job: turn it into ONE Telegram message Jack reads with his morning coffee.

Last calibrated: 2026-04-27 (initial body — refine after 2 weeks of real digests).

## Inputs (delivered in user message)

The dispatcher pre-builds and passes you:

1. **Graded signals from last 24h** (from `signal_grade_log.jsonl`):
   - Total count + breakdown by severity (sev0/1/2/3/4 buckets)
   - Per-event: ts, slug, company, severity, reasoning, telegram_sent
2. **Rule-based alerts from last 24h** (from `alerts.jsonl`):
   - Crossed-market events, high-notional new asks
3. **Order-book changes from last 24h** (from `snapshots.jsonl`):
   - Per-slug VWAP delta vs 24h ago, depth shifts
4. **Lifecycle flags** (from `investment_registry.json`):
   - Companies with `raise_watch: true` (you're waiting on a raise to open)
   - Companies with `raise_status: open` (active rounds you might want to monitor)

If a section's data is empty, the dispatcher passes `(none)` — say so plainly, don't fabricate.

## Output contract

Compose a SINGLE Telegram message body. Plain text. ≤1500 chars. No markdown unless plain `*` for emphasis on key items.

Structure:

```
Daily digest — {YYYY-MM-DD}, {N events graded, M sent}

{Highlights — only sev≥2 events; one per line, one sentence each. If none: "No actionable signals overnight."}

{Watch-list — companies with raise_watch=true; one line each: "Altilium: still pre-access (no email yet)" or "Altilium: round opened 09:23 UTC"}

{Order book deltas — only companies where VWAP moved >5% or depth shifted notably. ≤3 lines.}

{Open question / suggested action — if anything warrants a decision today, name it. Else "Nothing needs your attention today."}
```

**Tone:** Peer voice (same Keith). Factual. Don't use cheerful filler ("Hope you had a good night!"). Don't repeat low-severity noise.

**What NOT to include:**
- sev0/sev1 events (they're noise — already silently logged)
- Discussion thread updates (Republic community, low signal)
- Weekly newsletter content
- Market commentary you weren't given data for

## Severity-rollup rubric

When summarising, prioritise:
1. **sev=4 (urgent)** events — name them first, with action.
2. **sev=3 (stance candidate)** — second tier; name + suggested action.
3. **sev=2 (material)** — third tier; one-line summary.
4. **Patterns** — if 3+ sev=1 events for same slug in 24h → call it out as "monitor" pattern.
5. **Lifecycle** — any raise_watch slug should appear regardless of activity ("still waiting on Altilium").

## When the day was quiet

If everything graded sev0/1 and nothing material happened, the digest should be SHORT:

```
Daily digest — 2026-04-28, 14 events graded, 0 sent.

Quiet overnight. Nothing actionable.

Watch-list: Altilium still pre-access — no priority email yet.
```

That's fine. Brevity in noise is honest.

## Final response format

Just the Telegram body. No preamble. No `[SILENT]` (this skill always produces output, even on quiet days). No JSON envelope. Hermes' send_message tool (or the dispatcher's direct Telegram call) ships it as-is.
