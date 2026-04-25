---
name: signal-recontext
description: Given a slug, a triggering signal, and context_bundle, perform a 5-minute recontextualisation. Answer — does the current investment stance need revisiting given this new information? Used by the router when grade has review=true for the quick-assessment case.
triggers:
  - "recontextualise this"
  - "quick recontext of {slug}"
  - "has the stance changed given {signal}"
status: CONTRACT ONLY — body TBD in Phase 24
---

## Input

```yaml
slug: string
signal: { type, source, raw, ts }
context_bundle: (same shape as signal-grade)
```

## Output

```yaml
output_file: ~/brain/companies/{slug}/drafts/{date}_recontext.md
summary_for_telegram: string  # 3 lines max, shown in Telegram
verdict: "unchanged" | "reconsider" | "reconsider-urgently"
```

Output file format:
```markdown
---
slug: {slug}
trigger_signal: {signal.type}
trigger_ts: {signal.ts}
recontext_ts: {now}
verdict: unchanged | reconsider | reconsider-urgently
---

## 1. What changed

(1 paragraph: the new information from the signal + context)

## 2. What's the current stance

(1 paragraph: the most recent eval's position + reasoning, as of {brain_summary date})

## 3. Does anything need updating

(1 paragraph: does the signal change the stance? If yes, what specifically? If no, why is it robust?)

## Verdict

{unchanged / reconsider / reconsider-urgently} — 1-line justification.
```

## Output contract

- **3 paragraphs**, not more. Brevity matters; this is a 5-min task not a full review.
- Always include a verdict (no "it depends").
- Cite specific files from context_bundle's `brain_summary` — don't just paraphrase.

## Body TBD

Full procedure with examples and anti-patterns added in Phase 24. Until then, agents invoking this skill should use the contract above + Jack's integrated review workflow (`reference_integrated_review_workflow.md`) as loose guidance.
