---
name: migrate
description: Universal migration from Obsidian, Notion, Logseq, markdown, CSV, JSON, Roam
triggers:
  - "migrate from"
  - "import from obsidian"
  - "import from notion"
  - "move docs into brain"
  - "canonicalize docs"
  - "source-of-truth migration"
tools:
  - put_page
  - search
  - add_link
  - add_tag
  - sync_brain
mutating: true
---

# Migrate Skill

Universal migration from any wiki, note tool, or brain system into GBrain.

## Contract

- Source data is never modified or deleted; migration is additive only.
- Every migrated page is verified round-trip: written to gbrain, read back, spot-checked.
- Cross-references from the source system (wikilinks, block refs, tags) are converted to gbrain equivalents.
- Migration is tested on a sample (5-10 files) before bulk execution.
- Post-migration health check confirms page count, link integrity, and embedding coverage.

## Supported Sources

| Source | Format | Strategy |
|--------|--------|----------|
| Obsidian | Markdown + `[[wikilinks]]` | Direct import, convert wikilinks to gbrain links |
| Notion | Exported markdown or CSV | Parse Notion's export structure |
| Logseq | Markdown with `((block refs))` | Convert block refs to page links |
| Plain markdown | Any .md directory | Import directory into gbrain directly |
| CSV | Tabular data | Map columns to frontmatter fields |
| JSON | Structured data | Map keys to page fields |
| Roam | JSON export | Convert block structure to pages |

## Phases

1. **Assess the source.** What format? How many files? What structure?
2. **Plan the mapping.** How do source fields map to gbrain fields (type, title, tags, compiled_truth, timeline)?
3. **Test with a sample.** Import 5-10 files, verify by reading them back from gbrain and exporting.
4. **Bulk import.** Import the full directory into gbrain.
5. **Verify.** Check gbrain health and statistics, spot-check pages.
6. **Build links.** Extract cross-references from content and create typed links in gbrain.

## Obsidian Migration

1. Import the vault directory into gbrain (Obsidian vaults are markdown directories)
2. Wire the graph with native wikilink support (v0.12.1+):

   ```bash
   gbrain extract links --source db --dry-run | head -20    # preview
   gbrain extract links --source db                         # commit
   ```

   `extract links` natively parses `[[relative/path]]` and `[[relative/path|Display Text]]`
   alongside standard `[text](page.md)` markdown syntax. Ancestor-search resolution handles
   wiki KBs where authors omit one or more leading `../` prefixes. The `.md` suffix is
   inferred automatically for wikilinks.

Obsidian-specific:
- Tags (`#tag`) become gbrain tags
- Frontmatter properties map to gbrain frontmatter
- Attachments (images, PDFs) are noted but handled separately via file storage

## Notion Migration

1. Export from Notion: Settings > Export > Markdown & CSV
2. Notion exports nested directories with UUIDs in filenames
3. Strip UUIDs from filenames for clean slugs
4. Map Notion's database properties to frontmatter
5. Import the cleaned directory into gbrain

## CSV Migration

For tabular data (e.g., CRM exports, contact lists):
1. For each row in the CSV, create a page with column values as frontmatter
2. Use a designated column as the slug (e.g., name)
3. Use another column as compiled_truth (e.g., notes)
4. Store each page in gbrain

## Canonical Repository / Docs Migration

Use this path when existing project docs, reports, or operational markdown already exist somewhere else and need to become canonical inside the brain repo rather than remain in an app/project-specific folder.

1. **Classify the source before moving.** For every source folder/file, decide whether it is upstream-canonical, live-used, user-valued, or entropy. A reference in a prompt is not enough; verify actual usage or user value.
2. **Inspect both sides read-only first.** Check source path, target brain repo, git status, remotes, latest commits, and expected file list before writing. Do not overwrite or pull into a dirty repo blindly.
3. **Handle cross-machine auth explicitly.** If source and target are on different Macs, test SSH with `BatchMode=yes` and the intended key. On macOS, `Operation not permitted` under `~/Documents` is often privacy/TCC, not path absence; ask the user to run the local copy command from Terminal rather than weakening permissions. If SSH can prove a source file exists (`ls`/`stat`) but cannot read/hash it, have the user copy it locally into `~/brain/inbox/<source-name>.md` first, then compare/merge from the brain clone.
4. **Prefer copy + verify before retire.** Copy into the target brain path, then verify exact file set and hashes (`shasum -a 256`) on source and target. Only after parity is proven should old paths be marked retired/pointer-only.
5. **For duplicate trackers / logs, merge deltas, not authority.** If an old project folder contains a larger tracker, copy it into `~/brain/inbox/` via local Terminal if needed, compare against the canonical brain file, merge only unique live/history rows, and keep the canonical file’s role explicit (for example: historical/open-asks scratch, not current-state authority). Remove the temporary inbox copy after merging so it does not become a second tracker.
6. **Patch contracts after truth exists.** Update `CLAUDE.md`, agent persona files, runbooks, resolver docs, and decisions logs only after the files actually live at the new canonical path. Do not create a new lie by changing docs ahead of the move.
7. **Leave tripwires at retired paths.** Add a README/pointer or archive marker at the old folder when possible. If macOS privacy blocks SSH writes to `~/Documents`, give the user a local Terminal command to create the pointer. Treat the user’s local Terminal confirmation as the source when SSH cannot verify the TCC-protected path.
8. **Sweep migrated content for stale authority claims.** After files move, grep the new canonical docs for old source-of-truth language (`source of truth`, old repo paths, old registry names, old tracker links, `drafts/`, `macbook-pending`, etc.). Patch live contracts such as `ARCHITECTURE.md`, `STATUS.md`, `DATA.md`, and `CHANGELOG.md`; do not rewrite historical evidence packs wholesale. Add a supersession/status note to the current index or ledger so old findings do not masquerade as live state.
9. **Align reader/writer directory contracts without fake files.** If a pipeline claims it writes a file that has never existed, patch the directory contract and downstream reader skill to say who owns the filename and what absence means. Do not create an empty placeholder merely to satisfy a path check; first write should come from a synthetic end-to-end test of the writer path.
10. **Reconcile secondary clones only after proof.** If another machine has the same migrated files dirty because they were copied there before the canonical commit, fetch the pushed commit, check the dirty files against `origin/main` via a temporary work-tree (`git --work-tree=/tmp/check checkout -f origin/main -- <paths>` + `cmp`/hashes), and only then use `git reset --hard origin/main` to clean that clone. Never reset a dirty clone until every affected path is proven identical or intentionally disposable.
11. **Let live runtime state supersede pending doc-sync rows.** When migrated docs contain `macbook-pending`, `doc-sync`, or scheduler/health claims, verify the live source (`launchctl list/print`, generated `pipeline-status.md`, current JSON status files) before patching docs. If a pending decision row is wrong, do not rewrite append-only history; append a correction/supersession row and patch only the canonical docs/ledger.
12. **Do not commit/push by default.** Report dirty state and ask before committing, especially if other sessions already modified the repo.
13. **When commit/push is approved, stage by ownership boundary.** Stage only files that belong to the migration/source-of-truth lane; leave unrelated handoff, phase, or other-session files dirty. Run `git diff --cached --check`, review `git diff --cached --stat` / `--name-only`, scan the staged diff for secret values or unsafe additions, commit with a migration-scoped message, then verify `git status -sb`. Push only after separate approval, and after push verify any secondary clone with `git pull --ff-only && git status -sb` rather than assuming sync.

Verification checklist for this subcase:

- Source and target file lists match the expected migration set.
- Source and target SHA-256 hashes match for every migrated file.
- New canonical path is referenced by live contracts.
- Migrated docs no longer describe old folders, old trackers, old registry files, or old review locations as canonical.
- Directory/reader/writer contracts agree on any generated files; missing generated files are interpreted explicitly rather than masked by placeholders.
- Pending doc-sync rows have been checked against live runtime state; wrong append-only rows are superseded by correction entries, not edited in place.
- Old path is explicitly retired as canonical.
- Git status is reported; no unrelated dirty files are clobbered.

## Verification

After any migration:
1. Check gbrain statistics to verify page count matches source
2. Check gbrain health for orphans and missing embeddings
3. Export pages from gbrain for round-trip verification
4. Spot-check 5-10 pages by reading them from gbrain
5. Test search: search gbrain for "someone you know is in the data"

## Anti-Patterns

- **Bulk import without sample test.** Never import the full dataset before verifying with 5-10 files. The cost of cleaning up hundreds of bad pages is enormous.
- **Destroying source data.** Migration is additive. Never modify, move, or delete the source files.
- **Ignoring cross-references.** Wikilinks, block refs, and tags from the source system must be converted to gbrain equivalents. Dropping them loses the knowledge graph.
- **Skipping verification.** A migration without post-import health check, page count comparison, and spot-check reads is incomplete.

## Output Format

```
MIGRATION REPORT -- [source] -> GBrain
=======================================

Source: [format] ([file count] files, [size])
Mapping: [field mapping summary]

Sample Test (N files):
- Imported: N/N
- Round-trip verified: N/N
- Cross-refs converted: N

Bulk Import:
- Total imported: N
- Skipped (duplicates/errors): N
- Links created: N
- Tags migrated: N

Verification:
- Page count match: [yes/no]
- Health check: [pass/fail]
- Search test: [query] -> [result count] hits
```

## Tools Used

- Store/update pages in gbrain (put_page)
- Read pages from gbrain (get_page)
- Link entities in gbrain (add_link)
- Tag pages in gbrain (add_tag)
- Get gbrain statistics (get_stats)
- Check gbrain health (get_health)
- Search gbrain (query)
