import type { BrainEngine } from './engine.ts';
import { slugifyPath } from './sync.ts';

/**
 * Schema migrations — run automatically on initSchema().
 *
 * Each migration is a version number + idempotent SQL. Migrations are embedded
 * as string constants (Bun's --compile strips the filesystem).
 *
 * Each migration runs in a transaction: if the SQL fails, the version stays
 * where it was and the next run retries cleanly.
 *
 * Migrations can also include a handler function for application-level logic
 * (e.g., data transformations that need TypeScript, not just SQL).
 */

interface Migration {
  version: number;
  name: string;
  sql: string;
  handler?: (engine: BrainEngine) => Promise<void>;
}

// Migrations are embedded here, not loaded from files.
// Add new migrations at the end. Never modify existing ones.
const MIGRATIONS: Migration[] = [
  // Version 1 is the baseline (schema.sql creates everything with IF NOT EXISTS).
  {
    version: 2,
    name: 'slugify_existing_pages',
    sql: '',
    handler: async (engine) => {
      const pages = await engine.listPages();
      let renamed = 0;
      for (const page of pages) {
        const newSlug = slugifyPath(page.slug);
        if (newSlug !== page.slug) {
          try {
            await engine.updateSlug(page.slug, newSlug);
            await engine.rewriteLinks(page.slug, newSlug);
            renamed++;
          } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            console.error(`  Warning: could not rename "${page.slug}" → "${newSlug}": ${msg}`);
          }
        }
      }
      if (renamed > 0) console.log(`  Renamed ${renamed} slugs`);
    },
  },
  {
    version: 3,
    name: 'unique_chunk_index',
    sql: `
      -- Deduplicate any existing duplicate (page_id, chunk_index) rows before adding constraint
      DELETE FROM content_chunks a USING content_chunks b
        WHERE a.page_id = b.page_id AND a.chunk_index = b.chunk_index AND a.id > b.id;
      CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_page_index ON content_chunks(page_id, chunk_index);
    `,
  },
  {
    version: 4,
    name: 'access_tokens_and_mcp_log',
    sql: `
      CREATE TABLE IF NOT EXISTS access_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        scopes TEXT[],
        created_at TIMESTAMPTZ DEFAULT now(),
        last_used_at TIMESTAMPTZ,
        revoked_at TIMESTAMPTZ
      );
      CREATE INDEX IF NOT EXISTS idx_access_tokens_hash ON access_tokens (token_hash) WHERE revoked_at IS NULL;
      CREATE TABLE IF NOT EXISTS mcp_request_log (
        id SERIAL PRIMARY KEY,
        token_name TEXT,
        operation TEXT NOT NULL,
        latency_ms INTEGER,
        status TEXT NOT NULL DEFAULT 'success',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );
    `,
  },
  {
    version: 5,
    name: 'oauth_infrastructure',
    sql: `
      CREATE TABLE IF NOT EXISTS oauth_clients (
        client_id               TEXT PRIMARY KEY,
        client_secret_hash      TEXT,
        client_name             TEXT NOT NULL,
        redirect_uris           TEXT[],
        grant_types             TEXT[] DEFAULT '{"client_credentials"}',
        scope                   TEXT,
        token_endpoint_auth_method TEXT,
        client_id_issued_at     BIGINT,
        client_secret_expires_at BIGINT,
        created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
      );
      CREATE TABLE IF NOT EXISTS oauth_tokens (
        token_hash   TEXT PRIMARY KEY,
        token_type   TEXT NOT NULL,
        client_id    TEXT NOT NULL REFERENCES oauth_clients(client_id) ON DELETE CASCADE,
        scopes       TEXT[],
        expires_at   BIGINT,
        resource     TEXT,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
      );
      CREATE INDEX IF NOT EXISTS idx_oauth_tokens_expiry ON oauth_tokens(expires_at);
      CREATE INDEX IF NOT EXISTS idx_oauth_tokens_client ON oauth_tokens(client_id);
      CREATE TABLE IF NOT EXISTS oauth_codes (
        code_hash              TEXT PRIMARY KEY,
        client_id              TEXT NOT NULL REFERENCES oauth_clients(client_id) ON DELETE CASCADE,
        scopes                 TEXT[],
        code_challenge         TEXT NOT NULL,
        code_challenge_method  TEXT NOT NULL DEFAULT 'S256',
        redirect_uri           TEXT NOT NULL,
        state                  TEXT,
        resource               TEXT,
        expires_at             BIGINT NOT NULL,
        created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
      );
      CREATE INDEX IF NOT EXISTS idx_mcp_log_time_agent ON mcp_request_log(created_at, token_name);
    `,
  },
];

export const LATEST_VERSION = MIGRATIONS.length > 0
  ? MIGRATIONS[MIGRATIONS.length - 1].version
  : 1;

export async function runMigrations(engine: BrainEngine): Promise<{ applied: number; current: number }> {
  const currentStr = await engine.getConfig('version');
  const current = parseInt(currentStr || '1', 10);

  let applied = 0;
  for (const m of MIGRATIONS) {
    if (m.version > current) {
      // SQL migration (transactional)
      if (m.sql) {
        await engine.transaction(async (tx) => {
          await tx.runMigration(m.version, m.sql);
        });
      }

      // Application-level handler (runs outside transaction for flexibility)
      if (m.handler) {
        await m.handler(engine);
      }

      // Update version after both SQL and handler succeed
      await engine.setConfig('version', String(m.version));
      console.log(`  Migration ${m.version} applied: ${m.name}`);
      applied++;
    }
  }

  return { applied, current: applied > 0 ? MIGRATIONS[MIGRATIONS.length - 1].version : current };
}
