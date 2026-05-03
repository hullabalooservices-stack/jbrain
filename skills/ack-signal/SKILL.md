---
name: ack-signal
version: 0.1.0
description: |
  Parse Jack's Telegram ack DMs ("ack heights demand-surge 2026-04-24 noise") and
  mutate the matching entry in `~/agents/republic/.watcher/signal_grade_log.jsonl`
  by setting its `.ack` field. On verdicts that flag a misgrade, append a row to
  `~/brain/signals/misgrades.md` for the weekly skillify rollup AND for
  weekly-self-eval Phase 1 question 5 to read.

  This is the human-in-the-loop calibration primitive — complementary to
  weekly-self-eval (autonomous reflection). ack-signal is reactive (per-signal,
  immediate); weekly-self-eval is structured (weekly, autonomous). They layer.

triggers:
  - Telegram DM starting with "ack " (case-insensitive)
  - "ack list"  — browse last 10 signal log entries
  - "ack undo"  — revert the most recent ack (single level)
  - "mark signal as {noise|useful|missed|false-alarm|wrong-severity|wrong-review}"

tools:
  - read
  - write
  - bash
  - send_message

mutating: true
last_calibrated: 2026-04-28
---

# ack-signal

## Contract

When Jack sends an ack DM, find the matching signal_grade_log entry, mutate its
`.ack` field, and — for misgrade verdicts — append to misgrades.md.

A vacuous ack response is failure. Each ack must produce: matched entry path,
mutation receipt, conditional misgrades.md row, Telegram confirmation. If any
step fails, halt and report the failure rather than partial success.

## Inputs

| Source | Path | Format |
|---|---|---|
| Telegram DM body | (live, via Hermes inbound) | Plain text starting with "ack " |
| Signal log | `~/agents/republic/.watcher/signal_grade_log.jsonl` | JSON Lines, one entry per graded event |
| Misgrades log | `~/brain/signals/misgrades.md` | Markdown with table — append-only |

Each signal log entry has these load-bearing fields used by ack-signal:

```json
{
  "ts": "2026-04-28T19:50:25Z",
  "event_ts": "2026-04-28T19:50:25Z",
  "stream": "news",
  "source": "google-news",
  "slug": "hunter-gather-foods-ltd",
  "company": "Hunter & Gather",
  "severity": 2,
  "review": false,
  "telegram_sent": true,
  "reasoning": "...",
  "confidence": 0.8,
  "event_uid_or_id": "2026-04-28T19:50:25Z",
  "llm_source": "codex:gpt-5.4-mini"
}
```

`event_uid_or_id` is the canonical join key. `slug` and `event_ts` are the
practical match keys when Jack types an ack from memory.

## Phases

### Phase 0: Parse ack text

Strip the leading "ack " (case-insensitive). Tokenise the rest. Recognise the
sub-commands `list` and `undo` first; otherwise extract:

- `slug` — token matching a known portfolio slug (fuzzy match: case-insensitive,
  alias-aware via `~/agents/republic/config/watchlist.yaml` companies block).
- `signal_type` — short-name from the alerts vocabulary
  (e.g. `demand-surge`, `crossed-market`, `news-article`, `ch-filing`,
  `investor-email`, `republic-update`). Optional.
- `date` — `YYYY-MM-DD`. Optional. Defaults to today (Europe/London).
- `verdict` — last token; must be one of the six allowed verdicts.

The order is flexible: `ack 2026-04-24 heights demand-surge noise` parses the
same as `ack heights demand-surge 2026-04-24 noise`.

If the verdict is missing or unrecognised, run the verdict-typo fuzzy match
(see Edge cases) before giving up.

### Phase 1: Match signal_grade_log entry

Read `~/agents/republic/.watcher/signal_grade_log.jsonl`. Filter:

1. By slug if provided (fuzzy: try the literal token, then aliases from
   watchlist.yaml, then the registered name from `~/brain/companies/investment_registry.json`).
2. By signal_type if provided. Map common short-names to log fields:
   - `news-article` / `news` → `source ∈ ("google-news", "rss-*")`
   - `ch-filing` / `filing` → `source ∈ ("companies-house", "companies-house-stream")`
   - `investor-email` / `email` → `source == "republic-email"`
   - `demand-surge`, `crossed-market`, etc. → `stream == "snapshots"` AND
     reasoning/extra contains the pattern name (best-effort).
3. By date if provided (match against `event_ts` date in Europe/London).

Capped events (`dispatch_suppressed_by_cap: true`) and old events (`severity: 0`,
reasoning starting "event too old") are matchable. Don't filter them out.

If the filter returns multiple entries, pick the most recent by `event_ts`.

If the filter returns zero entries, abort with the "no match" path (see Edge cases).

### Phase 2: Mutate the signal log entry

Read the JSONL file in full. Locate the matched entry. Add or replace the
`ack` field:

```json
"ack": {
  "verdict": "noise",
  "ts": "2026-04-28T21:18:42Z",
  "raw_text": "ack heights demand-surge 2026-04-24 noise"
}
```

Atomic write: write the full file to a tempfile in the same directory, then
`os.replace` to the canonical path. Never edit in place. On any error, halt
without writing and report the failure.

### Phase 3: Conditional misgrades.md append

If `verdict ∈ {wrong-severity, wrong-review, missed, false-alarm}`, append one
row to `~/brain/signals/misgrades.md`. Schema:

| ts | slug | signal_type | verdict | given_severity | given_review | suggested_severity | suggested_review | jack_text |

`suggested_severity` and `suggested_review` are heuristic:
- `wrong-severity` → suggested = given ± 1 (direction inferred from context;
  default down if given ≥ 2, up if given ≤ 1).
- `wrong-review` → suggested_review = NOT given_review.
- `missed` → suggested = max(given+1, 2); suggested_review = true.
- `false-alarm` → suggested_severity = 0; suggested_review = false.

Append only — never edit prior rows. Atomic write.

For verdicts `noise` and `useful`, do not append. The signal log mutation alone
is the record.

### Phase 4: Telegram confirmation

Send one short message back to Jack via Keith. Format:

```
Logged: {slug}/{signal_type} {date} → {verdict}.
{conditional sub-line}
```

Sub-line content:
- Misgrade verdict → "Misgrades.md row appended."
- Capped-on-dispatch event → "(was capped on dispatch — log only.)"
- Old-event ack → "(event was too-old-skipped; ack still recorded.)"
- `noise` / `useful` → no sub-line.

Keep under 250 chars. No markdown. Plain text.

## Grammar

Canonical:

```
ack <slug> <signal_type> <YYYY-MM-DD> <verdict>
```

Flexible accepts:

```
ack <slug> <signal_type> <verdict>           # date defaults to today
ack <slug> <verdict>                          # signal-type inferred (most recent for slug)
ack <verdict>                                 # most recent signal across all slugs
ack <YYYY-MM-DD> <slug> <signal_type> <verdict>   # any field order
```

Sub-commands:

```
ack list                                      # last 10 entries with brief context
ack undo                                      # revert most recent ack (single level)
```

`<verdict> ∈ {noise, useful, missed, false-alarm, wrong-severity, wrong-review}`

## Verdict semantics

- **`noise`** — system fired but the signal was meaningless to me. Calibrate down
  next time this pattern appears for this slug/sector.
- **`useful`** — system fired correctly. Calibration neutral; helps confirm the
  rubric is well-tuned for this case.
- **`missed`** — I noticed something signal-grade should have caught and didn't,
  or graded too low. The ack is for a related event in the log; misgrades row
  flags upward calibration.
- **`false-alarm`** — system fired with confidence on something that was wrong
  (e.g. severity 4 on a name-collision Heights → Golan Heights that slipped
  through). Stronger than `noise` — implies signal-grade actively misjudged.
- **`wrong-severity`** — verdict on the right event but the severity number was
  off. Most common case in practice.
- **`wrong-review`** — verdict on the right event with right severity but the
  review-needed flag was off (true when should be false, or vice versa).

## Anti-patterns

- ❌ Don't mutate the signal log without an atomic write — partial writes can
  corrupt JSONL parsing.
- ❌ Don't add misgrades.md rows for `noise` or `useful` verdicts — the volume
  would drown calibration signal.
- ❌ Don't try to apply calibration changes here. ack-signal records; skillify
  proposes; Jack hand-applies. Three roles, separate.
- ❌ Don't silently ignore unmatched acks. If you can't match, say so explicitly
  and offer `ack list`.
- ❌ Don't let a Telegram-confirmation send failure roll back the log mutation.
  The mutation is the source of truth; the Telegram is a courtesy receipt.
- ❌ Don't send long confirmations. One line, sub-line if needed.

## Worked dialogues

### 1. Full-grammar ack

> Jack: `ack hunter-and-gather news-article 2026-04-28 useful`

Match: most recent `slug=hunter-gather-foods-ltd` (alias match) `source=google-news`
event with `event_ts` on 2026-04-28. Mutates `.ack`. No misgrades.md append
(verdict=useful). Confirms:

> Keith: `Logged: hunter-and-gather/news-article 2026-04-28 → useful.`

### 2. Slug + verdict only (most-recent inference)

> Jack: `ack heights noise`

Match: most recent log entry with slug=heights (or alias). For Heights, the
recent entries are Google News false-positives — match the most recent timestamp.
No append (noise). Confirms:

> Keith: `Logged: heights/news-article 2026-04-28 → noise.`

### 3. Verdict only

> Jack: `ack wrong-severity`

Match: most recent log entry overall (regardless of slug). Mutates. Appends
misgrades row with suggested_severity = given_severity − 1 (heuristic: most
graded events are sev 2-3; "wrong-severity" usually means "too high"). Confirms:

> Keith: `Logged: hunter-and-gather/news-article 2026-04-28 → wrong-severity (you marked sev 2; misgrade suggests sev 1).`

### 4. Ambiguous match (multiple recent same slug+date)

> Jack: `ack heights wrong-severity`

If multiple Heights entries today (likely — Google News produces multiple),
pick most recent. If timestamps are within seconds of each other, reply:

> Keith: `Multiple heights events today within 5s of each other — try 'ack list' to disambiguate.`

### 5. ack list

> Jack: `ack list`

Reply with last 10 log entries:

> Keith:
> ```
> 1. 2026-04-28T19:51:38Z yonder google-news sev 0 (capped)
> 2. 2026-04-28T19:51:37Z twickets google-news sev 0 (sent)
> 3. 2026-04-28T19:50:25Z hunter-and-gather google-news sev 2 (sent)
> 4. 2026-04-28T19:50:24Z heights google-news sev 0 (sent)
> 5. 2026-04-28T19:50:24Z heights google-news sev 0 (sent)
> ...
> Reply 'ack {n} {verdict}' to ack by index.
> ```

(Index-based ack accepted as variant: `ack 3 wrong-severity` → matches entry 3
from the most recent `ack list` for that chat.)

### 6. ack undo

> Jack: `ack undo`

Find the most recently mutated entry (highest `.ack.ts`). Remove the `.ack`
field. If a misgrades.md row was added, mark it `(reverted)` rather than delete
(preserve history). Confirms:

> Keith: `Reverted: heights/news-article 2026-04-28 ack (was wrong-severity).`

Single level only — no `ack undo undo`.

### 7. Verdict typo

> Jack: `ack heights noiseee`

Fuzzy-match against the six verdicts. "noiseee" → "noise" at >80% confidence
(Levenshtein 2; or token prefix match). Apply silently with:

> Keith: `Logged: heights/news-article 2026-04-28 → noise. (parsed "noiseee" as noise.)`

If fuzzy confidence <80%, ask:

> Keith: `Did you mean: noise / wrong-severity?`

### 8. Capped event ack

Capped events (`dispatch_suppressed_by_cap: true`) didn't reach Jack via Telegram.
He's likely ack'ing because he saw it in `pipeline-status.md` or `ack list`.

> Jack: `ack altilium news-article 2026-04-28 useful`

If the matched entry has `dispatch_suppressed_by_cap: true`, append confirmation
sub-line:

> Keith: `Logged: altilium/news-article 2026-04-28 → useful. (was capped on dispatch — log only.)`

### 9. Old-event ack

Events skipped by `MAX_EVENT_AGE_HOURS` are in the log with severity 0 and
reasoning starting "event too old". When ack'd, default to noise:

> Jack: `ack ch-filing 2026-04-25`

If matched entry has reasoning starting "event too old" and Jack didn't specify
verdict, default to noise. Confirms:

> Keith: `Logged: TEST_AGE_GUARD/ch-filing 2026-04-25 → noise (auto: event was too-old-skipped).`

### 10. No match

> Jack: `ack metallobio funding-round 2026-04-26 useful`

If no log entry matches (e.g. Metallobio hasn't fired any signals; or the date
is wrong):

> Keith: `Couldn't match: no log entry for metallobio/funding-round near 2026-04-26. Try 'ack list' to browse recent.`

## Output schema

```json
{
  "matched_signal_log_path": "~/agents/republic/.watcher/signal_grade_log.jsonl",
  "matched_event_uid_or_id": "2026-04-28T19:50:25Z",
  "matched_slug": "hunter-gather-foods-ltd",
  "matched_signal_type": "news-article",
  "matched_event_ts": "2026-04-28T19:50:25Z",
  "ack": {
    "verdict": "wrong-severity",
    "ts": "2026-04-28T21:18:42Z",
    "raw_text": "ack hunter-and-gather news-article 2026-04-28 wrong-severity"
  },
  "side_effects": [
    "updated signal_grade_log entry .ack field (atomic write)",
    "appended misgrades.md row (verdict=wrong-severity, given=2, suggested=1)"
  ],
  "telegram_confirmation": "Logged: hunter-and-gather/news-article 2026-04-28 → wrong-severity (you marked sev 2; misgrade suggests sev 1)."
}
```

For sub-commands, the schema differs:

```json
// ack list
{
  "subcommand": "list",
  "entries": [{"index": 1, "uid": "...", "slug": "...", "signal_type": "...", "date": "...", "severity": 0, "telegram_sent": true}, ...],
  "telegram_response": "1. 2026-04-28T19:51:38Z yonder ... \n2. ...\nReply 'ack {n} {verdict}' to ack by index."
}

// ack undo
{
  "subcommand": "undo",
  "reverted_event_uid_or_id": "...",
  "previous_verdict": "wrong-severity",
  "side_effects": ["removed .ack field", "marked misgrades.md row as (reverted)"],
  "telegram_response": "Reverted: heights/news-article 2026-04-28 ack (was wrong-severity)."
}
```

## Integration with weekly-self-eval

Both skills read the same calibration substrate (`signal_grade_log.jsonl` and
`~/brain/signals/`) but at different cadence and granularity:

- **ack-signal** — reactive, per-signal, immediate. Captures the user's verdict
  on individual events as they happen.
- **weekly-self-eval** — autonomous, structured, weekly. Phase 1 question 5
  ("what rule failed this week that I should propose?") reads
  `~/brain/signals/misgrades.md` since last rollup and looks for patterns.

Sample weekly-self-eval flow that consumes ack-signal output:

1. Sunday 09:00 BST, weekly-self-eval fires.
2. Reads misgrades.md rows since last Sunday.
3. Identifies pattern: "5 demand-surge events ack'd as noise on FMCG companies".
4. Writes recommendation to `~/brain/meta/weekly-self-eval/{date}.md`:
   "Suggest demand-surge default severity 3 → 2 for sector=fmcg".
5. Jack reads the eval, decides, hand-applies edit to `signal-grade.SKILL.md`,
   bumps version + last_calibrated.

Neither replaces the other. ack-signal feeds weekly-self-eval. Together they
form the calibration loop.

## Smoke test (one-shot, after install)

```
ack hunter-and-gather news-article 2026-04-28 useful
```

Expected:
- signal_grade_log.jsonl entry for hunter-and-gather/2026-04-28 has `.ack`.
- misgrades.md unchanged (verdict=useful skips append).
- Telegram confirmation arrives within ~5s.

Then:

```
ack heights news-article 2026-04-28 wrong-severity
```

Expected:
- signal_grade_log.jsonl entry for heights/2026-04-28 has `.ack`.
- misgrades.md gains one row.
- Telegram confirmation arrives.

## Calibration

`last_calibrated: 2026-04-28` — initial ship. Iterate based on real-world ack
fidelity over the first 14 days. Specifically watch for:

- Verdict-typo fuzzy match too lenient or too strict.
- Slug fuzzy match collisions (e.g. "heights" vs "hunter-and-gather" — both 1-word).
- Ambiguous match frequency (if >10% of acks need disambiguation, the grammar
  should default to most-recent more aggressively).

Bump version when calibration shifts; record the change rationale in commit message.

## Anti-Patterns

- Do not bypass the documented phases.
- Do not invent side effects not described by the skill.
- Do not treat this skill as complete without the relevant verification evidence.

## Output Format

Return a concise status summary with files touched, evidence collected, blockers, and next action.
