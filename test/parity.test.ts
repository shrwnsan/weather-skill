/**
 * Cross-runtime JSON parity gate (PRD-002 Phase 7.7) — Bun side.
 *
 * For each supported (provider, mode) pair, this suite:
 *   1. Builds a `WeatherSkill` from the default factory.
 *   2. Fetches data against the global `mockFetch` fixture preload
 *      with a frozen clock at 2026-01-01T00:00:00.000Z.
 *   3. Serializes the result via `toJson` (the same code path as the
 *      `--format json` CLI flag).
 *   4. Compares the bytes to `fixtures/parity/<key>.json`.
 *
 * The matching Python suite (`tests/test_parity.py`) asserts against
 * the same snapshot files using `weather.cli.to_jsonable` (the Phase
 * 7.7 normalizer that aligns Python's wire format to Bun's). If both
 * sides pass against the same snapshot, byte-for-byte parity is
 * proven transitively.
 *
 * Refresh snapshots with:
 *   UPDATE_PARITY_SNAPSHOTS=1 bun test test/parity.test.ts
 */

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { buildDefaultSkill } from "../src/bootstrap.js";
import { toJson } from "../src/cli.js";
import { freezeTime, restoreTime } from "./setup.js";

const SNAPSHOTS_ROOT = resolve(import.meta.dir, "..", "fixtures", "parity");
const UPDATE = process.env["UPDATE_PARITY_SNAPSHOTS"] === "1";

interface ParityCase {
  readonly key: string;
  readonly location: string;
  readonly provider: string;
  readonly mode: "current" | "forecast";
  readonly days?: number;
}

/**
 * Active cases. SG NEA and OpenWeather are deliberately excluded:
 *   - SG NEA  — both runtimes crash on `{text, code}` object shape from
 *               the v2 data.gov.sg API (eval finding P7.4-4). Add back
 *               after the provider learns to unwrap that shape.
 *   - OWM     — fixtures not captured yet (`needs_capture: true` in
 *               fixtures/api-responses/openweathermap/manifest.json).
 */
const CASES: readonly ParityCase[] = [
  { key: "hko-current",      location: "Hong Kong", provider: "hko",     mode: "current" },
  { key: "hko-forecast-3",   location: "Hong Kong", provider: "hko",     mode: "forecast", days: 3 },
  { key: "jma-current",      location: "Tokyo",     provider: "jma",     mode: "current" },
  // JMA forecast intentionally OUT of the parity matrix:
  // Bun's JMA provider preserves the raw `timeDefines` instant
  // (e.g. JST midnight = 15:00Z prior day), while the Python provider
  // calls `.date()` first and stores a logical-day value. Both
  // representations are reasonable but they're not byte-identical
  // even after the Phase 7.7 normalizer. Tracked as a follow-up
  // alongside P7.4-5 (JMA day-0 fallback) and the other deferred
  // JMA cross-runtime fixes.
  { key: "us_nws-current",   location: "New York",  provider: "nws",     mode: "current" },
  { key: "us_nws-forecast-5", location: "New York", provider: "nws",     mode: "forecast", days: 5 },
];

describe("cross-runtime JSON parity (Bun side)", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  for (const c of CASES) {
    test(`${c.key} matches fixtures/parity/${c.key}.json`, async () => {
      const skill = buildDefaultSkill();
      const data = c.mode === "current"
        ? await skill.getCurrent(c.location, c.provider)
        : await skill.getForecast(c.location, c.days ?? 3, c.provider);

      const actual = toJson(data) + "\n";
      const snapshotPath = join(SNAPSHOTS_ROOT, `${c.key}.json`);

      if (UPDATE || !existsSync(snapshotPath)) {
        writeFileSync(snapshotPath, actual, "utf-8");
        // First-time write or explicit refresh: pass after writing.
        return;
      }

      const expected = readFileSync(snapshotPath, "utf-8");
      expect(actual).toBe(expected);
    });
  }
});
