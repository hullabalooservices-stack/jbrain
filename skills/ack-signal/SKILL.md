---
name: ack-signal
description: Parse Jack's ack DMs ("ack heights demand-surge 2026-04-24 noise") and update the matching signal log's `ack:` field. Enables skillify feedback loop — misgrades surface which eventually inform SKILL.md updates for signal-grade.
triggers:
  - Telegram DM starting with "ack " (exact — case-insensitive OK)
  - "mark signal as {noise|useful|missed|false-alarm}"
status: CONTRACT ONLY — body TBD in Phase 23
---

## Input

```yaml
ack_text: string  # Jack's DM, e.g. "ack heights demand-surge 2026-04-24 noise"
```

## Parse spec

Expected format: `ack {slug} {signal_type} {YYYY-MM-DD} {verdict}`

Where verdict ∈ {noise, useful, missed, false-alarm, wrong-severity, wrong-review}.

Flexible parsing:
- `ack heights demand-surge noise` (no date) → find most recent matching signal
- `ack heights noise` (no signal-type) → find most recent signal for slug; ambiguous if multiple
- `ack 2026-04-24 heights demand-surge noise` (reordered) → OK

If parse is ambiguous, Keith asks clarifying question via Telegram.

## Output

```yaml
matched_signal_log: path  # ~/brain/signals/YYYY-MM-DD/{slug}_{seq}.md
updated_ack_field: { verdict, ts, text_from_jack }
telegram_confirmation: "Marked {slug}/{signal-type}/{date} as {verdict}. Logged."
```

## Side effects

- Edit matched signal log: set `ack.verdict`, `ack.ts`, `ack.raw_text` in frontmatter
- If verdict is `wrong-severity` or `wrong-review`: add a row to `~/brain/signals/misgrades.md` (weekly rollup input)
- Telegram confirmation back to Jack

## Skillify trigger

Weekly (Sunday) — Keith scans signals/misgrades.md + recent signal logs where verdict=noise but severity≥3, OR verdict=missed but severity≤1. Writes `~/brain/signals/weekly-skill-review-{date}.md` with suggested SKILL.md edits for signal-grade.

Jack reviews weekly report, approves edits manually.

## Body TBD

Exact grammar, edge cases (plural signals, typos, non-existent slugs), and weekly-rollup procedure in Phase 23.
