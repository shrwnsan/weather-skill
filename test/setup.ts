/**
 * Bun test setup — loaded via bunfig.toml `[test] preload`.
 *
 * Provides fixture-backed fetch mock and clock freezing for
 * deterministic cross-runtime parity tests (Phase 7.3).
 *
 * Usage in test files:
 *   import { mockFetch, restoreFetch, freezeTime, restoreTime } from "./setup";
 *
 *   // In beforeEach / beforeAll:
 *   mockFetch();
 *   freezeTime();
 *
 *   // In afterEach / afterAll:
 *   restoreFetch();
 *   restoreTime();
 */

import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { beforeAll, afterAll } from "bun:test";

// ── Constants ───────────────────────────────────────────────────────────

const FIXTURES_ROOT = resolve(import.meta.dir, "..", "fixtures", "api-responses");
const FROZEN_ISO = "2026-01-01T00:00:00.000Z";
const FROZEN_MS = new Date(FROZEN_ISO).getTime();

const PROVIDERS = [
  "hko",
  "jma",
  "sg_nea",
  "us_nws",
  "openweathermap",
  "de_dwd",
  "nz_metservice",
  "id_bmkg",
  "au_bom",
] as const;

// ── Fixture loading ─────────────────────────────────────────────────────

let _fixtureCache: Map<string, string> | null = null;

function loadFixtures(): Map<string, string> {
  if (_fixtureCache) return _fixtureCache;

  const map = new Map<string, string>();

  for (const provider of PROVIDERS) {
    const manifestPath = join(FIXTURES_ROOT, provider, "manifest.json");
    let manifestRaw: string;
    try {
      manifestRaw = readFileSync(manifestPath, "utf-8");
    } catch {
      continue;
    }

    const manifest: { urls: Record<string, string> } = JSON.parse(manifestRaw);
    for (const [url, relPath] of Object.entries(manifest.urls)) {
      const normalized = url.replace(/<API_KEY>/g, "test-key");
      const bodyPath = join(FIXTURES_ROOT, provider, relPath);
      try {
        const body = readFileSync(bodyPath, "utf-8");
        map.set(normalized, body);
      } catch {
        // Fixture file doesn't exist yet — skip
      }
    }
  }

  _fixtureCache = map;
  return map;
}

// ── Fetch mock ──────────────────────────────────────────────────────────

const _originalFetch = globalThis.fetch;

function mockedFetch(fixtures: Map<string, string>, input: Request | string | URL, _init?: RequestInit): Promise<Response> {
  const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  const normalized = url.replace(/<API_KEY>/g, "test-key");

  const body = fixtures.get(normalized);
  if (body != null) {
    return Promise.resolve(new Response(body, {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }));
  }

  return Promise.resolve(new Response(`No fixture for URL: ${url}`, { status: 404 }));
}

/** Mock `globalThis.fetch` to replay fixture responses. */
export function mockFetch(): void {
  const fixtures = loadFixtures();
  // @ts-expect-error — assigning narrower mock to global fetch type
  globalThis.fetch = (input: Request | string | URL, init?: RequestInit) =>
    mockedFetch(fixtures, input, init);
}

/** Restore original `globalThis.fetch`. */
export function restoreFetch(): void {
  globalThis.fetch = _originalFetch;
}

// ── Clock freezing ──────────────────────────────────────────────────────

const _OriginalDate = globalThis.Date;

type DateConstructorArgs = [value?: number | string | Date];

/** Freeze `Date` to 2026-01-01T00:00:00.000Z. */
export function freezeTime(): void {
  const Origin = _OriginalDate;

  class FrozenDate extends Origin {
    constructor(...args: DateConstructorArgs | []) {
      if (args.length === 0) {
        super(FROZEN_MS);
      } else {
        super(args[0]!);
      }
    }

    static override now(): number {
      return FROZEN_MS;
    }

    static override parse(str: string): number {
      return Origin.parse(str);
    }

    static override UTC(...args: Parameters<typeof Date.UTC>): number {
      // P7.4-3 fix: forward only the args actually passed in. Earlier
      // versions of this override declared 7 named params and forwarded
      // them all, which caused Date.UTC with <7 args to receive
      // `undefined` for the trailing slots and return `NaN`
      // (e.g. providers calling Date.UTC(y, mo, d, hh, mm)).
      return Origin.UTC(...args);
    }
  }

  Object.setPrototypeOf(FrozenDate.prototype, Origin.prototype);

  // @ts-expect-error — replacing global Date with subclass
  globalThis.Date = FrozenDate;
}

/** Restore original `Date`. */
export function restoreTime(): void {
  globalThis.Date = _OriginalDate;
}

// ── Global hooks ────────────────────────────────────────────────────────

let _fetchMocked = false;

function setup(): void {
  mockFetch();
  _fetchMocked = true;
}

function teardown(): void {
  if (_fetchMocked) {
    restoreFetch();
    _fetchMocked = false;
  }
}

beforeAll(setup);
afterAll(teardown);
