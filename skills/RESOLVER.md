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
| "What do we know about", "tell me about", "search for", "who is", "background on", "notes on" | `skills/query/SKILL.md` |
| "Who knows who", "relationship between", "connections", "graph query" | `skills/query/SKILL.md` (use graph-query) |
| Creating/enriching a person or company page | `skills/enrich/SKILL.md` |
| Where does a new file go? Filing rules | `skills/repo-architecture/SKILL.md` |
| Fix broken citations in brain pages | `skills/citation-fixer/SKILL.md` |
| "citation audit", "check citations", "fix citations" | `skills/citation-fixer/SKILL.md` (focused fix). For broader brain health, chain into `skills/maintain/SKILL.md` |
| "Research", "track", "extract from email", "investor updates", "donations" | `skills/data-research/SKILL.md` |
| Share a brain page as a link | `skills/publish/SKILL.md` |
| "validate frontmatter", "check frontmatter", "fix frontmatter", "frontmatter audit", "brain lint" | `skills/frontmatter-guard/SKILL.md` |

## Content & media ingestion

| Trigger | Skill |
|---------|-------|
| User shares a link, article, tweet, or idea | `skills/idea-ingest/SKILL.md` |
| Video, audio, PDF, book, YouTube, screenshot | `skills/media-ingest/SKILL.md` |
| Meeting transcript received | `skills/meeting-ingestion/SKILL.md` |
| Generic "ingest this" (auto-routes to above) | `skills/ingest/SKILL.md` |

## GStack thinking and implementation workflow

| Trigger | Skill |
|---------|-------|
| "Brainstorm", "I have an idea", "office hours", "help me think through", "is this worth building" | GStack: office-hours |
| Complex build / new tool / new automation / new pipeline / "make this happen" / "build me a tool" / "set up a workflow" / "connect X to my brain" | GStack: office-hours first if problem or scope is unclear; then GStack: plan-eng-review before implementation |
| "Review this plan", "CEO review", "poke holes", "think bigger", "strategy review", "rethink this plan" | GStack: plan-ceo-review |
| Architecture / implementation plan / data flow / edge cases / tests / "before we build" / "lock the plan" / "is this the right structure" | GStack: plan-eng-review |
| Design plan / UX plan / UI direction / visual hierarchy before implementation | GStack: plan-design-review |
| Developer experience / onboarding / docs flow / CLI help / time-to-hello-world before implementation | GStack: plan-devex-review |
| "Debug", "fix", "broken", "investigate", "why is this failing", root-cause analysis | GStack: investigate |
| Code review / diff review / PR review / pre-landing review / "check my changes" | GStack: review |
| "Ship", "create a PR", "commit and push", "push this", "deploy this" | GStack: ship (respect Jack's approval gates for production, public remotes, destructive actions, and launchd changes) |
| "Merge", "land it", "deploy to production", "verify deploy" | GStack: land-and-deploy; chain to GStack: canary for post-deploy monitoring |
| Post-deploy check / watch production / canary / monitor after deploy | GStack: canary |
| QA / browser test / "test this site" / "find bugs" / "try this flow" | GStack: qa; use GStack: qa-only when Jack asks for report-only |
| Authenticated browser testing / import cookies / login to test site | GStack: setup-browser-cookies before QA/browser workflows |
| Security audit / secrets / credentials / token handling / threat model / OWASP / supply chain | GStack: cso |
| Risky shared-state work / destructive commands / production / cleanup / broad refactor / "be careful" | GStack: guard, careful, or freeze depending on scope |
| Design system / brand / landing page / mockup / UI polish / visual options | GStack design chain: design-consultation, design-shotgun, design-html, design-review |
| Codebase health / quality dashboard / lint-type-test overview / technical debt | GStack: health |
| Performance benchmark / page speed / Core Web Vitals / regression | GStack: benchmark |
| Model choice / compare Claude vs GPT vs Gemini / which model should do this | GStack: benchmark-models |
| Save progress / checkpoint / handoff / resume / where were we / context restore | GStack: checkpoint, context-save, or context-restore |
| Repeated issue / "didn't we fix this before" / show or prune project learnings | GStack: learn |
| Post-ship docs / update README / changelog / release notes / document what changed | GStack: document-release |
| Retro / what shipped / retrospective | GStack: retro |

> These skills come from GStack. If GStack is installed, read the matching `~/.claude/skills/gstack/.gbrain/skills/gstack-*/SKILL.md` file directly before acting.
> If GStack is not installed, brain-only mode still works; approximate the workflow using the closest GBrain skill and state the fallback.

## Operational

| Trigger | Skill |
|---------|-------|
| Task add/remove/complete/defer/review for active Keith/Hermes operating work | `skills/plane-operating-board/SKILL.md` |
| Legacy/non-Plane daily task list maintenance only | `skills/daily-task-manager/SKILL.md` |
| Morning prep, meeting context, day planning | `skills/daily-task-prep/SKILL.md` |
| Morning digest, yesterday's summary, what happened overnight, daily roundup | `skills/daily-digest/SKILL.md` |
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
| "Run dream", "process today's session", "synthesize my conversations", "consolidate yesterday's conversations", "what patterns did you see", "did the dream cycle run" | `skills/maintain/SKILL.md` (dream cycle section) |
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

- ✓ fundamentals-review v1.4.2 — Gates A/B/C, drafts/ subfolder retired entirely (2026-04-29), extended YAML/cap-table Rule 24, material-news freshness Rule 26, current CDP/long-lived Chrome auth recovery, 16-item Gate C checklist. Prior: registry write Rule 25, historical_context.md, manifest caching for closed raises.
- ✓ signal-grade v0.4.0 — Phase 21.8 lifecycle transition detector + LLM-based news-disambiguation in production.
- ✓ daily-digest v0.1.0 — Phase 21.10 morning rollup of signal pipeline.
- ✓ weekly-self-eval v0.1.0 — Sunday autonomous reflection (shipped 2026-04-28).
- ✓ ack-signal v0.1.0 — human-in-the-loop calibration primitive (shipped 2026-04-28); writes to `~/brain/signals/misgrades.md`; complementary to weekly-self-eval.

Deferred (skeleton, body bundled with downstream phase):

- order-book-interpretation — Phase 21 deferred until order-book cookies fix (Top-15 #1) AND observed snapshot grading degradation. May not be needed; signal-grade currently handles snapshots when they flow.
- news-classification — Phase 21 deferred. signal-grade's in-prompt LLM disambiguation already produces correct false-positive flagging in production (e.g. Heights → Golan Heights, Twickets, Yonder all sev 0 with reasoning "false-positive news match (LLM disambiguation)"). Drop unless evidence shows degradation.
- signal-recontext — Phase 24 deferred. Bundle with auto-review-trigger plan.
