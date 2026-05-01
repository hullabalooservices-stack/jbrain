# Plane Operating Board

## Purpose

Use this skill whenever Jack asks Keith/Hermes to capture, review, migrate, summarize, or operate task and planning state through Plane.

Plane is the execution source of truth. The brain remains the source of context, evidence, reasoning, decisions, and historical plans.

Canonical local Plane board:
- App URL: `http://localhost:8080`
- Workspace: `Agent`
- Workspace slug: `agent`
- Project: `Operating Board`
- Project identifier: `OPS`
- Board URL for summaries: `http://localhost:8080/agent/projects`

Local MCP bridge notes:
- Hermes MCP server: `plane`
- Bridge: `/Users/agentfolder/.hermes/scripts/plane_mcp_server.py`
- Smoke: `/Users/agentfolder/.hermes/hermes-agent/venv/bin/python /Users/agentfolder/.hermes/scripts/plane_mcp_server.py --smoke`
- Snapshot: `/Users/agentfolder/.hermes/hermes-agent/venv/bin/python /Users/agentfolder/.hermes/scripts/plane_mcp_server.py --snapshot`

## Contract

This skill guarantees:

- Backlog contains only accepted-but-unscheduled work.
- Non-committed ideas are treated as effective no and placed in `Parked`, not `Backlog`.
- Every actionable Plane card links back to the source brain file/report/session where possible.
- Daily board stress-test checks stale, duplicate, blocked, completed, dependency-sensitive, and source-link-missing cards.
- Morning Telegram brief summarizes yesterday, overnight, and this morning's priorities, with the Plane board link.

## Board Semantics

States, preferred left-to-right order:

- `In Progress`: actively being worked after explicit or obvious start approval.
- `Todo`: committed next / soon after a light challenge pass, and only after an execution plan exists.
- `Backlog`: accepted work, unscheduled. Real work, not maybe work, but not automatic approval to start.
- `Done`: completed.
- `Parked`: non-committed placeholder bucket. Effective no. Review only if Jack explicitly asks or if a dated resurfacing trigger exists.
- `Cancelled`: deliberately dropped.

Labels:

- Commitment/status labels: `accepted`, `parked`, `blocked`, `decision-needed`, `needs-scoping`, `recurring`, `needs-plan`, `plan-ready`.
- Domain labels: `agent-stack`, `republic`, `writing`, `x-bookmarks`, `brain`, `cleanup`, `research`, `decorum`, `visa`.

Do not use a `maybe` label. If tempted to tag something maybe, move it to `Parked` or do not create a Plane card.

## Backlog Planning Gate

Backlog is a tracking state, not start approval. `Backlog` → `Todo` requires an execution plan before any work starts.

Before moving a card from `Backlog` to `Todo`:

1. Create or link an execution plan in `~/brain`.
2. Apply Jack's standard planning methodology: plan/no-plan decision, prerequisite checks, red-team for non-trivial/shared-state work, clear acceptance criteria, exact next steps, verification, and safety gates.
3. If the work is too unclear to plan, write a plan to make a plan. The planning card may then move to `Todo`; the underlying execution stays in `Backlog`.
4. Add or keep the `needs-plan` label until a plan exists; replace it with `plan-ready` only after the plan is created/linked.
5. Confirm whether Jack needs to answer a decision question before execution.

Before moving a card from `Todo` to `In Progress`, verify the execution plan still matches reality and record the start decision. No work starts from `Backlog` or `Todo` without this planning gate.

Completion pressure does not bypass this gate. If Jack says to avoid deferring or to "do it now," complete the current authorised step now: create/link the execution plan, update labels truthfully (`needs-plan` until a plan exists; `plan-ready` only after one exists), and leave execution unstarted unless the start decision is explicit or already obvious under this skill.

Light formal gate questions:

1. Why now?
2. What is the concrete acceptance test?
3. What is the main way this could be wrong or wasted effort?
4. What dependencies or user decisions exist?
5. Should it instead remain Backlog, move to Parked, or be Cancelled?

## Capture Rules

When a task or idea comes up:

1. Decide whether it is actionable.
   - Concrete next action or Jack explicitly wants it done: create/update a card.
   - Vague but potentially useful: Parked, not Backlog.
   - Just context/knowledge: write or leave it in the brain, not Plane.

2. Decide commitment level.
   - Accepted unscheduled work → `Backlog`.
   - Committed next/soon with execution plan linked/created → `Todo`.
   - Accepted but no execution plan yet → stay in `Backlog` with `needs-plan`.
   - Currently being worked → `In Progress`.
   - Effective no / speculative / someday → `Parked`.

3. Card description must include:
   - Why it matters.
   - Source path or source note.
   - Acceptance criteria.
   - Next action.
   - Owner: Jack / Keith / both.
   - Due date or review date where relevant.
   - Execution plan link/status when moving beyond Backlog.

4. Avoid duplicate cards.
   - Search existing Plane cards by title/topic before creating.
   - If a card exists, update it rather than creating a second card.

5. Do not import completed historical tasks as active Plane work.
   - Completed tasks stay in the brain/history unless needed as evidence.

## Recurring Work

Recurring jobs are not automatically shown as live Kanban cards. Runtime schedule truth lives in Hermes cron. The board should show recurring work only when there is a human-actionable card, such as:

- a setup/maintenance card for the recurring job;
- an investigation card when a recurring job fails;
- a recurring review card if Jack wants human review on a cadence.

Use the `recurring` label for those cards. Do not create one new Plane card every time a cron job runs.

Current recurring task jobs:
- `e64023b6abeb` — Plane backlog stress-test — daily 07:45.
- `2df054dadd73` — Keith morning brief to Telegram — daily 08:10.

## Daily Backlog Stress-Test Job

Run once each morning before the morning brief.

Inputs:
- Plane `Operating Board` cards.
- Recent Hermes sessions if available.
- `~/brain/ops/tasks.md` only as the pointer/archive during migration.
- Relevant current plan files under `~/brain/reports/` when linked from open cards.

Actions:

1. Verify board access and expected workspace/project/state order.
2. Check `In Progress`, `Todo`, and `Backlog` cards for acceptance criteria, next action, source link, stale status, vague scope, and explicit dependencies.
3. Ask how yesterday's work changed the board: created, completed, invalidated, unblocked, duplicated, or made stale.
4. Identify improvement opportunities that make cards more executable without bloating them.
5. Check `Parked` cards without promoting them automatically; flag any item masquerading as actionable work.
6. Enforce the brain/Plane split: reasoning, evidence, and full plans stay in `~/brain`; executable accepted work goes in Plane.
7. For `Backlog` cards, identify the execution plan needed before `Todo`; do not move them automatically.
8. Create a concise stress-test report for the morning brief: board state, yesterday changed, key dependencies, fixes applied, ranked 1-3 attention items, watchouts, board link.

Idempotency:
- May update missing labels/source links/stale flags.
- Must not create duplicate cards.
- Must not promote Parked to Backlog without explicit instruction.
- Must not delete cards; use `Cancelled` for deliberate drops.

## Morning Telegram Brief

Run after the daily backlog stress-test job.

Format:

```text
Morning, Jack.

Yesterday:
- ...

Overnight:
- ...

This morning:
1. ...
2. ...
3. ...

Board: http://localhost:8080/agent/projects

Watchouts:
- ...
```

Rules:
- Keep it short.
- Include Plane board link every time.
- Distinguish completed work from configured-but-unverified work.
- Mention Parked only when a parked item has a due review date or Jack asked to revisit it.
- If Plane access fails, say so and fall back to brain/session evidence without pretending the board was checked.

## Migration from Brain Tasks

During migration:

1. Read `~/brain/ops/tasks.md`.
2. Import only unchecked tasks.
3. Map accepted work without an execution plan → Backlog, accepted work with an execution plan → Todo, speculative/non-committed → Parked.
4. Keep completed history in archive/session history.
5. After verified import, replace the live task file with a pointer saying Plane is canonical for active tasks.

Current migrated active cards:
- `OPS-1` — Draft LinkedIn post 1 — AI brains are infrastructure.
- `OPS-2` — Legacy Claude Project cleanup — verify old Project/staging copies before archive/delete.

## Anti-Patterns

- Treating Parked as Backlog.
- Creating a Plane card for every thought, note, or historical plan line.
- Using `maybe` as a label or status.
- Auto-promoting parked ideas during daily review.
- Moving Backlog to Todo without an execution plan.
- Starting work from Todo/In Progress without checking that the plan still fits.
- Treating "finish now" or "don't defer" as permission to skip Backlog→Todo planning or Todo→In Progress start checks.
- Letting Backlog contain vague cards with no next action.
- Sending a morning brief that claims Plane was checked when API/MCP access failed.
- Making the daily brief a long audit report.
