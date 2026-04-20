import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { resolvePrepare } from '../src/core/db.ts';

describe('resolvePrepare', () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    // Restore env
    delete process.env.GBRAIN_PREPARE;
    Object.assign(process.env, originalEnv);
  });

  it('returns false for Supabase pooler port 6543', () => {
    expect(resolvePrepare('postgresql://user:pass@host:6543/db')).toBe(false);
  });

  it('returns undefined for direct Postgres port 5432', () => {
    expect(resolvePrepare('postgresql://user:pass@host:5432/db')).toBeUndefined();
  });

  it('returns undefined for default port (no port specified)', () => {
    expect(resolvePrepare('postgresql://user:pass@host/db')).toBeUndefined();
  });

  it('respects ?prepare=false in URL', () => {
    expect(resolvePrepare('postgresql://user:pass@host:5432/db?prepare=false')).toBe(false);
  });

  it('respects ?prepare=true in URL even on port 6543', () => {
    expect(resolvePrepare('postgresql://user:pass@host:6543/db?prepare=true')).toBe(true);
  });

  it('GBRAIN_PREPARE=false overrides everything', () => {
    process.env.GBRAIN_PREPARE = 'false';
    expect(resolvePrepare('postgresql://user:pass@host:5432/db?prepare=true')).toBe(false);
  });

  it('GBRAIN_PREPARE=true overrides auto-detect on 6543', () => {
    process.env.GBRAIN_PREPARE = 'true';
    expect(resolvePrepare('postgresql://user:pass@host:6543/db')).toBe(true);
  });

  it('GBRAIN_PREPARE=0 is falsy', () => {
    process.env.GBRAIN_PREPARE = '0';
    expect(resolvePrepare('postgresql://user:pass@host:6543/db')).toBe(false);
  });

  it('returns undefined for malformed URL', () => {
    expect(resolvePrepare('not-a-url')).toBeUndefined();
  });

  it('handles postgres:// scheme (no ql)', () => {
    expect(resolvePrepare('postgres://user:pass@host:6543/db')).toBe(false);
  });

  it('handles URL with special chars in password', () => {
    expect(resolvePrepare('postgresql://user:p%40ss$word@host:6543/db')).toBe(false);
  });
});
