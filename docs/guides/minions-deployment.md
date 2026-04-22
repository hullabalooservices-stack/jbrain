# Minions Worker Deployment Guide

## The Problem

The `gbrain jobs work` persistent worker can die silently from:
- Database connection drops (Supabase/Postgres intermittent failures)
- Lock renewal failures → stall detector dead-letters jobs
- Bun process crashes with no automatic restart
- Internal event loop death (PID alive but worker stopped)

When the worker dies, submitted jobs sit in `waiting` forever. No built-in recovery.

## Recommended Deployment Pattern

### Option 1: Watchdog Cron (recommended for persistent workers)

Run a cron every 5 minutes that checks worker health and restarts if needed.

The cleanest way to get env into cron is to set it at the top of the crontab itself. Cron uses `/bin/sh` by default, which does not support bash-style dotfile sourcing, and shell dotfiles typically short-circuit for non-interactive shells anyway. Put what the worker needs directly in crontab:

```
# /etc/crontab (or `crontab -e`)
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
DATABASE_URL=postgresql://user:pass@host:6543/db?prepare=false
GBRAIN_ALLOW_SHELL_JOBS=1

*/5 * * * * user bash /path/to/minion-watchdog.sh
```

Then the watchdog script:

```bash
#!/bin/bash
# minion-watchdog.sh
PID_FILE="/tmp/gbrain-worker.pid"
LOG_FILE="/tmp/gbrain-worker.log"
GBRAIN=/usr/local/bin/gbrain  # absolute path; set via `which gbrain`

start_worker() {
  # 2>&1 merges stderr into LOG_FILE so the grep at the bottom catches
  # stderr-only log lines like "[minion worker] shell handler enabled".
  nohup "$GBRAIN" jobs work --concurrency 2 > "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
}

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    # Internal shutdown: process alive but worker stopped.
    if tail -20 "$LOG_FILE" 2>/dev/null | grep -q "worker stopped\|worker shutting down"; then
      kill "$PID" 2>/dev/null
      # Grace window for the worker to flush in-flight jobs and for the
      # shell-job handler to clean up child processes. Shell handler uses
      # a 5s SIGTERM→SIGKILL grace on children (KILL_GRACE_MS), worker
      # graceful shutdown allows up to 30s for in-flight jobs. 10s is the
      # minimum that doesn't orphan shell children; bump to 30 to match
      # worker grace if your jobs run long.
      sleep 10
      kill -9 "$PID" 2>/dev/null
      start_worker
    fi
  else
    start_worker
  fi
else
  start_worker
fi
```

For complex setups that need more env than fits in crontab, use a `#!/bin/bash` wrapper that `cd`s into your repo and exports from a `.env` file before calling `gbrain`.

### Option 2: Inline `--follow` (recommended for cron-only workloads)

Skip the persistent worker entirely. Each cron run brings its own temporary worker:

```bash
# In your cron:
GBRAIN_ALLOW_SHELL_JOBS=1 gbrain jobs submit shell \
  --params '{"cmd":"node my-script.mjs","cwd":"/my/workspace"}' \
  --follow \
  --timeout-ms 120000
```

`--follow` starts a temporary worker on the queue and blocks until the just-submitted job reaches a terminal state (`completed` / `failed` / `dead` / `cancelled`). Important: if other jobs are already waiting on the same queue with higher priority or earlier `created_at`, the worker will process those first before reaching yours. `--follow` still exits only when YOUR job finishes. For strict single-job semantics on shared queues, use a dedicated queue:

```bash
gbrain jobs submit shell --queue my-cron \
  --params '{"cmd":"..."}' --follow --timeout-ms 120000
```

2-3 second startup overhead per job.

**Use this when:** Jobs run on a schedule (every 3h, daily, weekly). The startup overhead is negligible compared to the job duration.

**Don't use this when:** You need sub-second job pickup latency (rare).

## Known Issues

### Supabase connection drops

The worker uses a single Postgres connection. If Supabase drops it (maintenance, connection limits, network blip), lock renewal fails silently. The stall detector then dead-letters the job after `max_stalled` misses.

**Current defaults that make this worse:**
- `lockDuration: 30000` (30s) — too short for long jobs during connection blips.
- `max_stalled: 5` (schema column default on master — see `src/schema.sql` and `src/core/pglite-schema.ts`). Five missed heartbeats before dead-letter. Worth knowing: `MinionWorkerOpts.maxStalledCount` exists in `src/core/minions/worker.ts:74` with a default of `1`, but `handleStalled()` in `src/core/minions/queue.ts` reads the row's `max_stalled` column, not the opt. Setting the worker opt has no effect today.
- `stalledInterval: 30000` (30s) — checks too aggressively.

**Proposed CLI flags (not yet implemented):**
```
gbrain jobs work --lock-duration 120000    # 2 min
                 --max-stalled 8            # 8 strikes (written to column on submit)
                 --stall-interval 60000     # check every 60s
```

Because `handleStalled()` reads the column, a proper fix needs to plumb these values onto newly-submitted rows, not just onto worker opts.

### Zombie processes

When the Bun worker crashes, child processes (shell jobs) may become zombies. The watchdog cron's 10s SIGTERM → SIGKILL window covers the shell handler's 5s child-kill grace. For long-running shell jobs, bump to 30s to let the worker flush.

## Smoke Test

```bash
# Verify worker process is alive
kill -0 $(cat /tmp/gbrain-worker.pid) 2>/dev/null && echo "ALIVE" || echo "DEAD"

# Aggregate queue health (surfaces stalled counts without listing IDs)
gbrain jobs stats

# List actively-stalled jobs (active status with expired lock_until).
# Note: --status waiting is WRONG — stalled jobs stay `active` until handleStalled()
# requeues them. `waiting` shows you requeued-after-stall, not currently-stalled.
gbrain jobs list --status active --limit 10

# Dead-lettered jobs (terminal failure)
gbrain jobs list --status dead --limit 10

# Verify shell handler is enabled (log message writes to stderr;
# start_worker() redirects 2>&1 so the grep sees it)
grep "shell handler enabled" /tmp/gbrain-worker.log
```
