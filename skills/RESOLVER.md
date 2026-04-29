# GBrain Skill Resolver

This is the dispatcher. Skills are the implementation. **Read the skill file before acting.** If two skills could match, read both. They are designed to chain (e.g., ingest then enrich for each entity).

## Always-on (every message)

| Trigger | Skill |
|---------|-------|
| Every inbound message (spawn parallel, don't block) | `skills/signal-detector/SKILL.md` |
| Any brain read/write/lookup/citation | `skills/brain-ops/SKILL.md` |

## Brain operations

| Trigger | Skill |
|---------|-------|
| "What do we know about", "tell me about", "search for" | `skills/query/SKILL.md` |
| "Who knows who", "relationship between", "connections", "graph query" | `skills/query/SKILL.md` (use graph-query) |
| Creating/enriching a person or company page | `skills/enrich/SKILL.md` |
| Where does a new file go? Filing rules | `skills/repo-architecture/SKILL.md` |
| Fix broken citations in brain pages | `skills/citation-fixer/SKILL.md` |
| "Research", "track", "extract from email", "investor updates", "donations" | `skills/data-research/SKILL.md` |
| Share a brain page as a link | `skills/publish/SKILL.md` |

## Content & media ingestion

| Trigger | Skill |
|---------|-------|
| User shares a link, article, tweet, or idea | `skills/idea-ingest/SKILL.md` |
| Video, audio, PDF, book, YouTube, screenshot | `skills/media-ingest/SKILL.md` |
| Meeting transcript received | `skills/meeting-ingestion/SKILL.md` |
| Generic "ingest this" (auto-routes to above) | `skills/ingest/SKILL.md` |

## Thinking skills (from GStack)

| Trigger | Skill |
|---------|-------|
| "Brainstorm", "I have an idea", "office hours" | GStack: office-hours |
| "Review this plan", "CEO review", "poke holes" | GStack: ceo-review |
| "Debug", "fix", "broken", "investigate" | GStack: investigate |
| "Retro", "what shipped", "retrospective" | GStack: retro |

> These skills come from GStack. If GStack is installed, the agent reads them directly.
> If not, brain-only mode still works (brain skills function without thinking skills).

## Operational

| Trigger | Skill |
|---------|-------|
| Task add/remove/complete/defer/review | `skills/daily-task-manager/SKILL.md` |
| Morning prep, meeting context, day planning | `skills/daily-task-prep/SKILL.md` |
| Daily briefing, "what's happening today" | `skills/briefing/SKILL.md` |
| Cron scheduling, quiet hours, job staggering | `skills/cron-scheduler/SKILL.md` |
| Save or load reports | `skills/reports/SKILL.md` |
| "Create a skill", "improve this skill" | `skills/skill-creator/SKILL.md` |
| "Skillify this", "is this a skill?", "make this proper" | `skills/skillify/SKILL.md` |
| "Is gbrain healthy?", morning health check, skillpack-check | `skills/skillpack-check/SKILL.md` |
| Post-restart health + auto-fix, "did the container restart break anything", smoke test | `skills/smoke-test/SKILL.md` |
| Cross-modal review, second opinion | `skills/cross-modal-review/SKILL.md` |
| "Validate skills", skill health check | `skills/testing/SKILL.md` |
| Webhook setup, external event processing | `skills/webhook-transforms/SKILL.md` |
| "Spawn agent", "background task", "parallel tasks", "steer agent", "pause/resume agent", "gbrain jobs submit", "submit a gbrain job", "submit a shell job", "shell job" | `skills/minion-orchestrator/SKILL.md` |

## Setup & migration

| Trigger | Skill |
|---------|-------|
| "Set up GBrain", first boot | `skills/setup/SKILL.md` |
| "Migrate from Obsidian/Notion/Logseq", "move docs into brain", "canonicalize docs", "source-of-truth migration" | `skills/migrate/SKILL.md` |
| Brain health check, maintenance run | `skills/maintain/SKILL.md` |
| "Extract links", "build link graph", "populate timeline" | `skills/maintain/SKILL.md` (extraction sections) |
| "Brain health", "what features am I missing", "brain score" | Run `gbrain features --json` |
| "Set up autopilot", "run brain maintenance", "keep brain updated" | Run `gbrain autopilot --install --repo ~/brain` |
| Agent identity, "who am I", customize agent | `skills/soul-audit/SKILL.md` |
| "Populate links", "extract links", "backfill graph" | `skills/maintain/SKILL.md` (graph population phase) |
| "Populate timeline", "extract timeline entries" | `skills/maintain/SKILL.md` (graph population phase) |

## Identity & access (always-on)

| Trigger | Skill |
|---------|-------|
| Non-owner sends a message | Check `ACCESS_POLICY.md` before responding |
| Agent needs to know its identity/vibe | Read `SOUL.md` |
| Agent needs user context | Read `USER.md` |
| Operational cadence (what to check and when) | Read `HEARTBEAT.md` |

## Disambiguation rules

When multiple skills could match:
1. Prefer the most specific skill (meeting-ingestion over ingest)
2. If the user mentions a URL, route by content type (link → idea-ingest, video → media-ingest)
3. If the user mentions a person/company, check if enrich or query fits better
4. Chaining is explicit in each skill's Phases section
5. When in doubt, ask the user

## Conventions (cross-cutting)

These apply to ALL brain-writing skills:
- `skills/conventions/quality.md` — citations, back-links, notability gate
- `skills/conventions/brain-first.md` — check brain before external APIs
- `skills/conventions/subagent-routing.md` — when to use Minions vs inline work
- `skills/_brain-filing-rules.md` — where files go
- `skills/_output-rules.md` — output quality standards

## Jack's skills

Custom domain skills. Same shape as upstream skills above; added by Jack rather than Garry. Future upstream merges only touch the sections above this one.

| Trigger | Skill |
|---|---|
| Run a full fundamentals review (Gates A/B/C) — "do a review of {company}", "investment review" | `skills/fundamentals-review/SKILL.md` |
| Recontextualise a company given a new signal (5-min quick assessment) | `skills/signal-recontext/SKILL.md` |
| Grade an ambiguous signal (severity 0-4 + review flag) | `skills/signal-grade/SKILL.md` |
| Interpret an order-book pattern semantically (crossed market, depth surge, etc.) | `skills/order-book-interpretation/SKILL.md` |
| Classify news materiality (does it change fundamentals?) | `skills/news-classification/SKILL.md` |
| Parse Jack's ack DM — update signal log entry | `skills/ack-signal/SKILL.md` |
| Weekly Sunday self-eval — "weekly self-eval", "/self-eval" | `skills/weekly-self-eval/SKILL.md` |

### Skill chaining (Jack-specific)

- order-book-interpretation runs first when an order-book pattern is present, then signal-grade consumes the interpretation.
- news-classification runs first on news items, then signal-grade consumes the materiality output.
- fundamentals-review supersedes signal-recontext only when recontext concludes "stance changed, full re-eval needed."

### Status (2026-04-28)

Filled (production):

- ✓ fundamentals-review v1.4.0 — Gates A/B/C, drafts/ subfolder retired entirely (2026-04-29) — every review at company root, Rule 24 added (extended YAML frontmatter with cap-table block, T2.3), Gate C item 15 (frontmatter test). Prior: Rule 2b historical_context.md, manifest caching for closed raises.
- ✓ signal-grade v0.4.0 — Phase 21.8 lifecycle transition detector + LLM-based news-disambiguation in production.
- ✓ daily-digest v0.1.0 — Phase 21.10 morning rollup of signal pipeline.
- ✓ weekly-self-eval v0.1.0 — Sunday autonomous reflection (shipped 2026-04-28).
- ✓ ack-signal v0.1.0 — human-in-the-loop calibration primitive (shipped 2026-04-28); writes to `~/brain/signals/misgrades.md`; complementary to weekly-self-eval.

Deferred (skeleton, body bundled with downstream phase):

- order-book-interpretation — Phase 21 deferred until order-book cookies fix (Top-15 #1) AND observed snapshot grading degradation. May not be needed; signal-grade currently handles snapshots when they flow.
- news-classification — Phase 21 deferred. signal-grade's in-prompt LLM disambiguation already produces correct false-positive flagging in production (e.g. Heights → Golan Heights, Twickets, Yonder all sev 0 with reasoning "false-positive news match (LLM disambiguation)"). Drop unless evidence shows degradation.
- signal-recontext — Phase 24 deferred. Bundle with auto-review-trigger plan.
