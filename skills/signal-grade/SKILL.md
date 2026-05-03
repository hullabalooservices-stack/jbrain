---
name: signal-grade
version: 0.4.1
description: |
  Process all new events emitted by the Republic signal pipeline (email-watcher,
  order-book scraper, company-news, notifications). For each event, grade severity
  (0-4) + decide review-needed (binary), and — for severity >= 2 — synthesise an
  opinionated Telegram message in Keith's voice using brain context (latest review
  of the company, latest order-book snapshot). User-facing Telegram is now reserved
  for immediate/actionable items; monitor-only severity-2 output is logged for the
  daily digest rather than pushed as a live ping.

  This is the canonical "daemon-emitted event → LLM processing" skill per Garry's
  pattern (`~/brain/meta/memory/reference_garry_skillify_methodology.md`). Replaces
  Phase 21 v1's `republic_event_synth.py` daemon, which embedded an LLM call inside
  Python infrastructure (off-pattern).

  Output: ~/agents/republic/.watcher/signal_grade_log.jsonl (graded log; separate
  from `alerts.jsonl` which is the order-book daemon's rule-based alerts file
  read by router_lite/digest) + Telegram message via the `send_message` tool
  when severity >= 2.

triggers:
  - "process new signals"
  - "grade pending events"
  - "what's new in the watcher"
  - "run signal-grade"
  - "scheduled tick"

tools:
  - read
  - write
  - bash
  - send_message

mutating: true
---

# signal-grade — Contract

Single skill that handles every flavour of daemon-emitted Republic event. The agent invoking this skill (typically via scheduled trigger every 60s, but also callable from chat) processes ALL new entries across the watcher's input streams in one pass.

Last calibrated: 2026-04-26 (initial body — 2 weeks of real-signal data not yet accumulated; rubric will be refined as feedback comes in via the `ack-signal` skill, currently a Phase 23 skeleton).

---

## Inputs

Three jsonl streams (read incrementally from saved positions):

| Stream | Path | Source daemon |
|---|---|---|
| Notifications (emails + Updates posts) | `~/agents/republic/.watcher/events/notifications.jsonl` | email-watcher (every 2 min), notifications-watcher (every 30 min) |
| Order-book snapshots | `~/agents/republic/.watcher/snapshots.jsonl` | order-book daemon (4×/day) |
| Companies-House + Google News | `~/agents/republic/.watcher/events/news.jsonl` | company-news daemon (hourly working hrs) |

State file: `~/agents/republic/.watcher/signal_grade_position.json` — JSON `{notifications: int, snapshots: int, news: int, saved_at: int}`. On first run (no state file), initialise all positions to current EOF of each stream — do NOT replay history.

Brain context (read-only, for grading):
- `~/brain/companies/investment_registry.json` — registry (slug, fairValue, holding, cost_basis, raises[])
- `~/brain/companies/{folderSlug}/*_review_v*.md` and `*_evaluation_v*.md` — pick highest by `(date_in_filename, version)` descending. Resolve `folderSlug` via the registry's `folderSlug` field (NOT the legacy `slug` field, which may be a Republic URL slug). Cap reading at first 4000 chars per review file. Drafts subfolder retired 2026-04-29 — flat structure only.

The dispatcher (`signal_grade_dispatcher.py`) injects structured fields into the
LLM prompt directly from `investment_registry.json`:

| Field | From registry | Purpose |
|---|---|---|
| `holding {shares, avgCost, totalCost, currency}` | `entry.holding` | Holdings-aware grading: a SH01 on a £23K position grades differently from a SH01 on a watch-only |
| `fairValue {low, high, asOf, basis}` | `entry.fairValue` | Numeric anchor — no prose-parsing of Section 10g |
| `targetEntryPrice` | `entry.latestReview.targetEntryPrice` | TEP-cross detection without LLM prose parse |
| `fundamentalsScore` | `entry.latestReview.fundamentalsScore` | 0-100 score for severity calibration |
| `signalState`, `action` | `entry.latestReview.{signalState,action}` | Current stance |

LLM-extracted prose-parsing of these fields is now a fallback only.

---

## Phases (in order)

### Phase 1 — Idempotency check & state load

1. Read `signal_grade_position.json`. If absent or unparseable → first run: stat each input jsonl, write the current size into the state file as the starting position for each stream, exit cleanly with a one-line summary "first run — initialised positions, no events processed". Don't replay history.
2. Otherwise load positions for all three streams. Validate each: if `position > current_size`, the file was rotated/truncated → reset that stream's position to 0 and log a warning.

### Phase 2 — Discover new events

For each of the three streams:
1. Open the file, seek to the saved position, read line-by-line (use `readline()` not iteration — `tell()` is unreliable after `for line in f`).
2. Parse each line as JSON. Collect into a working set, tagged by stream.
3. Track per-line byte offsets so position can be advanced after each successful processing.

If the working set is empty across all streams → exit cleanly: "no new events".

### Phase 3 — For each event, build context and grade

Process events in chronological order (`ts` ascending). For each event:

**3a-prelude — TEST event short-circuit (safety guard, added 2026-04-26 after the synthetic-Heights-Series-B incident):**

If the event's `slug` starts with `TEST_` (case-insensitive) OR the event's `title`/`summary`/body contains the literal string `[TEST EVENT — BOT CONSOLIDATION VALIDATION]` or `[SIGNAL-GRADE PLUMBING TEST]`:
- Treat this as a synthetic plumbing test — never grade against real brain context, never imply real news.
- Send a Telegram with target=`telegram` containing the literal text:
  `[TEST] signal-grade end-to-end OK — slug={slug} uid={raw.uid or ts} cron_ran_at={now}`
- Append a log entry with `severity=0`, `review=false`, `telegram_sent=true`, `reasoning="synthetic plumbing test"`, `confidence=1.0`.
- Advance position. Do NOT proceed to 3a/b/c/d/e for this event.

This guard exists because LLM-graded test payloads on real slugs (e.g. `slug=heights` with fabricated Series-B news) are dangerous — if delivery succeeds, they look like real news on real holdings. **Synthetic events MUST use TEST_-prefixed slugs.**

**3a-prelude2 — RAISE LIFECYCLE TRANSITION DETECTOR (added 2026-04-27, Phase 21.8 Component A):**

Before applying the normal severity rubric, scan the email subject + body (or Updates post body) for lifecycle-transition signals. These are MUCH more time-critical than ordinary news because they imply Jack must act fast (priority-access windows can close in minutes).

**OPEN signals — a new raise has just opened (or is about to open):**
- "round opens" / "round is open" / "round is now open" / "round goes live"
- "now open" / "live now" / "live to invest" / "open for investment"
- "priority access" / "early access" granted/active
- "investment opportunity" + a deadline or timeframe (Q2, this week, etc.)
- "fundraise commencing" / "raising £X" with an actionable URL

When matched on a `republic-email` event:
- Grade **severity 4** + `review=true`
- Telegram message MUST start with `🚨 NEW RAISE — {company}` and include:
  - The matched signal phrase
  - An explicit suggested action: e.g. "Check Republic now. If new raise slug, update `~/brain/companies/investment_registry.json` raises[] (prepend new slug) + raiseLifecycle.status=open + asOf=today. Then trigger fundamentals-review on the new round."
- Append to `signal_grade_log.jsonl` with `lifecycle_signal: "open"` and the matched phrase.

**CLOSED / TRANSITION-TO-SECONDARY signals — most-recent raise is wrapping up:**
- "round has closed" / "round is closed" / "investment window closed"
- "fully subscribed" / "oversubscribed"
- "thank you to all investors" + past-tense raise references
- "secondary market only" / "trading on secondary"

When matched:
- Grade **severity 3** + `review=true`
- Telegram message must start with `⚠️ RAISE CLOSED — {company}` and suggest action: "Update registry raiseLifecycle.status=closed_secondary_only, asOf=today. Future updates flow through Updates tab + secondary order book — most recent raise's per-raise content is now frozen, can be cached forever."
- Append log with `lifecycle_signal: "closed"`.

**Why this elevates above ordinary grading:** lifecycle transitions are the events the registry must be updated for, otherwise the gather + historical_context + reviews go silently stale. They are the highest-value signal class. Bias toward false positives is acceptable — Jack would rather get one unnecessary "new raise?" Telegram than miss a real one.

After this prelude check fires (or doesn't), continue to Phase 3a flavour identification below.

**3a-prelude3 — GOOGLE NEWS FRESHNESS GUARD (added 2026-05-03 after TransferGo/Mastercard old-article resurfacing):**

For `source == "google-news"`, do **not** treat the Google News discovery timestamp as the publisher/article date.

Before grading a Google News event severity ≥2:
- Check whether the event title/summary/body or resolved article metadata includes an article publication date.
- If the resolved publisher date is older than 30 days before `event.ts`, grade at most **severity 1** unless the item is explicitly a current re-announcement or new filing-backed update.
- If the resolved publisher date is older than 90 days, grade **severity 0** and reason: `stale article resurfaced by Google News`.
- If no publisher date is available and the item is a generic PR headline (partnership, funding, product launch, interview, “welcomes investors”, “launches accounts”), grade conservatively at **0–1** unless another current source corroborates freshness.
- The Telegram/digest reasoning must distinguish: `fresh article` vs `publication date unknown` vs `stale article resurfaced`.

Example calibration: `TransferGo and Mastercard Partnership to Allow Real-Time Cross-Border Payment Transfer` surfaced by Google News on 2026-05-03 but The Fintech Times article date was 2020-12-08. Correct grade: **0**, no review, no “real product-distribution move” language.

**3a — Identify event flavour:**
- `source == "republic-email"` (notifications.jsonl): investor email forwarded from Republic. Body is in `raw.body_full` (preferred) or `summary` (fallback, truncated). Strip Gmail forward preamble (`---------- Forwarded message ----------` block) and Republic risk-warning boilerplate (`Don't invest unless you're prepared...`) before reading.
- `source == "republic-updates"` (notifications.jsonl): new post on Republic Updates tab. Body in `summary`, URL in `url`.
- order-book event (snapshots.jsonl, has `bestAsk`, `bestBid`, `slug`, `vwap`, etc.): a routine snapshot. NEW since v0.2.0: ALSO check whether `bestAsk` is below the company's TEP (extracted from the latest review's Section 10 — see Phase 3c). If yes, this snapshot is a **TEP-cross signal** and grades higher than a routine snapshot.
- `source == "companies-house"` (news.jsonl): a new CH filing. Includes accession_id, filing_type, filing_date.
- `source == "google-news"` (news.jsonl): a news article surfaced for one of the registry companies.

**3b — Resolve company:** every event has (or should have) a `slug`. If slug is null and the event is a `republic-email`, attempt to resolve from subject/body via registry name match (case-insensitive substring). If still unresolved → grade 0, skip downstream; log to signal_grade_log.jsonl with a `unresolved_slug` flag.

**3c — Load brain context:**
- Registry entry for the slug (fairValue, holding, cost_basis).
- Latest review file as described in "Inputs" — picked by `(date_in_filename, version)` descending at `~/brain/companies/{folderSlug}/`. Read first 4000 chars.
- From the review, extract — best-effort — the **TEP / target entry price** if present (typically Section 10 / 10g or "TEP" mentioned in Decision Dashboard). If you can find a numerical TEP in £/share, retain it. If not, set TEP=null.
- Latest order-book snapshot for the slug from snapshots.jsonl (last entry where `slug == event.slug`).

**3d — Apply the grading rubric (severity 0–4):**

- **0 — noise.** Routine snapshot within recent volatility band; admin email; non-material news; CH filing of routine type (CS01 confirmation statement, AA filleted accounts). Log to signal_grade_log.jsonl, no Telegram.
- **1 — informational, no stance change.** Minor update worth seeing in a digest but not a single ping. Empty/boilerplate emails grade here unless slug is unresolved (then 0). Log; no Telegram unless review-needed flag fires.
- **2 — material, monitor closely.** Genuine new info that doesn't yet shift stance. Send Telegram (one message, peer-voice, citing context). New CH filing of substantive type (SH01 share allotments, AR01 annual return with new directors, RES* resolutions). Order-book snapshot showing notable spread widening or new deep-discount offers without crossing TEP.
- **3 — stance candidate.** Crossed TEP, material funding round news, leadership change, partial-fill on a buy request that takes Jack's holding past a portfolio threshold, news article citing material competitive shift. Send Telegram with explicit "stance review warranted" framing + suggested next step (typically "trigger fundamentals-review" or "review section X"). Set review=true.
- **4 — urgent, stop-the-line.** Exit signal (acquisition, IPO), new C-suite departure for a high-conviction holding, regulatory action, severe trading disruption (crossed market both sides), enforcement notice. Send Telegram immediately with explicit "URGENT" framing.

**3e — Decide review flag (independent of severity):**

Set review=true when ANY of these hold:
- Signal hints fundamentals may have changed (new material filing, leadership news, product/market signal, M&A chatter).
- Latest review file is older than 14 days AND signal is non-trivial (severity ≥ 1).
- Multiple non-trivial signals (severity ≥ 1) for same slug in last 7 days, per signal_grade_log.jsonl history.
- News item references undisclosed/unclear context that warrants investigation.

Set review=false when:
- Signal is mechanical (TEP-cross is grade-3 + review=false: action is just "consider buy", not "re-evaluate fundamentals").
- Signal is noise.
- Latest review is from last 7 days and already covers the scenario.

### Phase 4 — Synthesise & dispatch

For each event, produce a concise message candidate for severity ≥2, but only send immediate Telegram when the dispatcher classifies it as `telegram_priority=immediate`.

Priority rules:
- `immediate`: severity 4; priority-access/new-raise/open-round email; actionable severity-3 item with a concrete next step; material stance-review trigger.
- `digest`: severity-2 monitor-only signals; no-thesis-change signals; false-positive-adjacent context; thin book/no TEP-cross; routine CH/admin/news items that are useful but not urgent.
- `silent`: severity 0/1 and true noise.

**4a — Compose the Telegram candidate** (Keith voice, plain text, ≤350 chars, no markdown, no JSON):
1. Name the company and what's actually new — strip Republic filler.
2. Say explicitly whether this changes anything in Jack's existing thesis (cite review's stance/decision when relevant).
3. Suggest one concrete next action: "monitor only" / "read full email body" / "trigger fundamentals-review" / "consider partial sell" / "buy at TEP" — pick what fits, don't list options.

Tone: factual, grounded, no hype. Peer, not assistant. If context is sparse (no review on file, slug unresolved, body uninformative), say so plainly and grade conservatively. Never invent details.

For severity 4, prepend the text "🚨 URGENT — " to the message. For severity 3, prepend "⚠️ ".

**4b — Dispatch**:
The Python dispatcher sends only `telegram_priority=immediate`; `digest` candidates are recorded in `signal_grade_log.jsonl` for the daily digest. Do not include model names, Codex/GPT labels, source plumbing, or footer provenance in the user-facing body.

**4c — On send failure** — if dispatch returns an error for an immediate item, do NOT advance position past this event. Log the error to signal_grade_log.jsonl with `dispatch_error` flag; the next scheduled tick will retry.

### Phase 5 — Append to signal_grade_log.jsonl

For EVERY event processed (regardless of severity), append one line to `~/agents/republic/.watcher/signal_grade_log.jsonl`:

```json
{
  "ts": "2026-04-29T12:34:56Z",          # processing time, not event time
  "event_ts": "<event.ts>",
  "stream": "notifications" | "snapshots" | "news",
  "source": "<event.source>",
  "slug": "<slug or null>",
  "company": "<company name or null>",
  "severity": 0-4,
  "review": true/false,
  "telegram_sent": true/false,
  "reasoning": "<1-2 sentences>",
  "confidence": 0.0-1.0,
  "event_uid_or_id": "<raw.uid for emails, ts+slug for snapshots, accession_id for CH>",

  // Provenance fields (T1.4 — added 2026-04-29) — record what context the
  // grader actually saw, so ack-signal + weekly-self-eval can audit each call.
  "review_path": "companies/heights/2026-04-25_heights_review_v12.md",
  "review_version": "12",
  "review_date": "2026-04-25",
  "review_age_days": 4,
  "review_chars_loaded": 4000,
  "holding_active": true,
  "cost_basis_gbp": 23178.67,
  // Optional cap fields if dispatch suppression triggered
  "dispatch_suppressed_by_cap": true|false,
  "dispatch_suppressed_by_dry_run": "cli"|"event"|null
}
```

This is the durable record — the source-of-truth for what was graded and why. Used by Phase 23's `ack-signal` skill to learn from Jack's manual feedback.

### Phase 5b — Auto-review-trigger (T2.1, added 2026-04-29)

After Phase 5 logs the row, if the graded severity is ≥3 AND the loaded review
is older than 90 days (or null), the dispatcher appends a row to
`~/brain/signals/auto_review_triggers.md` flagging the slug for refresh. This
file is read by `weekly-self-eval` on Sundays to surface stale-review
candidates, and is purely additive — no Telegram, no behaviour change to the
graded event itself. Disable by removing the `append_auto_review_trigger`
call in `signal_grade_dispatcher.py` if needed.

### Phase 6 — Advance positions, save state

After successful processing of all events in a stream, atomically update the position for that stream in `signal_grade_position.json` (write to `.tmp` + rename). If processing failed mid-stream (Phase 4c), save the position UP TO the last successful event so the failure retries on next tick.

---

## Anti-patterns (do not do these)

- ❌ Embed an Anthropic API call in Python code outside this SKILL. The SKILL is the LLM contract; daemons stay infrastructure.
- ❌ Re-process events by ignoring position state. Idempotency is non-negotiable per `~/gbrain/skills/cron-scheduler/SKILL.md`.
- ❌ Use `for line in f:` after `f.seek()`. The buffered iterator disables `tell()`. Use `readline()` in a loop.
- ❌ Fire Telegram for severity ≤ 1. Those are silent (signal_grade_log.jsonl only) until grouped into the daily digest (future skill).
- ❌ Invent TEP values. If you can't extract a numerical TEP from the review, set TEP=null and grade conservatively.
- ❌ Grade an event without checking whether a review on file exists. "No prior review" is a real signal — say so explicitly in the Telegram message.

## Calibration & evolution

The rubric above is v0.2.0 — initial calibration. Real-signal-data calibration follows after 2 weeks of operation. The `ack-signal` skill (Phase 23, not yet built) will let Jack DM Keith feedback like "that should have been a 3" / "noise — too sensitive on TEP-cross" — those acks update a calibration log this skill reads on startup.

Edge cases to watch as data accumulates:
- TEP-cross: how close is "close enough" — exact match? Within 5%? Sustained for N snapshots?
- Email volume from one company in a week — does multi-event throttling matter (don't ping Jack 5× in a day for one slug)?
- News classification: which `companies-house` filing types are genuinely material vs accounting noise?

## Output to caller

Final stdout (one-line JSON, not markdown — for cron-scheduler integration):
```json
{"processed": <int>, "telegrams_sent": <int>, "alerts_logged": <int>, "errors": <int>}
```
