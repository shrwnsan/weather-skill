/**
 * CLI integration tests (PRD-002 Phase 7.6).
 *
 * Drives the exported `run()` function from `src/cli.ts` against the
 * fixture-backed fetch mock and asserts exit code, stdout, and stderr
 * for the four parity-critical paths called out in Task 7.6:
 *
 *   1. `--location "Hong Kong"`           → text output, exit 0
 *   2. `--format json`                    → sorted-key JSON, exit 0
 *   3. `--send --format json`             → exit 2 (incompatible flags)
 *   4. `--provider <unknown>`             → exit 1 + provider list
 *
 * Plus a handful of regression cases (help flag, strict-int parsing
 * from the P6-1 fix, default location).
 */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { run } from "../src/cli.js";
import { freezeTime, restoreTime } from "./setup.js";

interface CapturedIO {
  stdout: string;
  stderr: string;
  restore: () => void;
}

/** Replace `process.stdout.write` and `process.stderr.write` with collectors. */
function captureIO(): CapturedIO {
  const buf = { stdout: "", stderr: "" };
  const origOut = process.stdout.write.bind(process.stdout);
  const origErr = process.stderr.write.bind(process.stderr);
  process.stdout.write = (chunk: string | Uint8Array): boolean => {
    buf.stdout += typeof chunk === "string" ? chunk : Buffer.from(chunk).toString();
    return true;
  };
  process.stderr.write = (chunk: string | Uint8Array): boolean => {
    buf.stderr += typeof chunk === "string" ? chunk : Buffer.from(chunk).toString();
    return true;
  };
  return {
    get stdout() { return buf.stdout; },
    get stderr() { return buf.stderr; },
    restore: () => {
      process.stdout.write = origOut;
      process.stderr.write = origErr;
    },
  };
}

let io: CapturedIO;
beforeEach(() => {
  io = captureIO();
  freezeTime();
});
afterEach(() => {
  io.restore();
  restoreTime();
});

describe("CLI integration", () => {
  describe("text output", () => {
    test("--location 'Hong Kong' produces emoji-prefixed text", async () => {
      const code = await run(["--location", "Hong Kong"]);
      expect(code).toBe(0);
      expect(io.stdout).toContain("Weather for Hong Kong");
      expect(io.stdout).toContain("Temperature:");
      expect(io.stdout).toContain("Provider: hko");
      expect(io.stderr).toBe("");
    });

    test("default location is Hong Kong", async () => {
      const code = await run([]);
      expect(code).toBe(0);
      expect(io.stdout).toContain("Weather for Hong Kong");
    });

    test("location alias --location 'hk' routes through HKO (P7.6-2)", async () => {
      // P3-1 fix: `parseLocation` applies `normalizeLocation` so the
      // alias map kicks in. End-to-end CLI integration coverage for
      // alias resolution → provider routing → data emission.
      const code = await run(["--location", "hk", "--format", "json"]);
      expect(code).toBe(0);
      const parsed = JSON.parse(io.stdout);
      expect(parsed.location).toBe("Hong Kong");
      expect(parsed.provider_name).toBe("hko");
    });

    test("--provider hko explicitly selects HKO", async () => {
      // Non-default provider selection — pairs with the alias test
      // above to cover both the auto-chain and explicit-name paths.
      const code = await run([
        "--location", "Hong Kong",
        "--provider", "hko",
        "--format", "json",
      ]);
      expect(code).toBe(0);
      const parsed = JSON.parse(io.stdout);
      expect(parsed.provider_name).toBe("hko");
    });
  });

  describe("json output", () => {
    test("--format json produces sorted-key JSON with the expected key set", async () => {
      const code = await run(["--location", "Hong Kong", "--format", "json"]);
      expect(code).toBe(0);

      const parsed = JSON.parse(io.stdout);

      // P7.6-3: pin the exact key sequence the HKO fixture produces.
      // Sorted alphabetical: catches both unsorted output AND key-spelling
      // regressions (e.g. `wind_speed` vs `windspeed`).
      expect(Object.keys(parsed)).toEqual([
        "condition",
        "condition_raw",
        "description",
        "fetched_at",
        "humidity",
        "location",
        "observed_at",
        "precipitation_chance",
        "provider_name",
        "temp_high",
        "temp_low",
        "temperature",
        "uv_index",
        "wind_description",
      ]);

      expect(parsed.location).toBe("Hong Kong");
      expect(parsed.provider_name).toBe("hko");
      // Frozen clock: fetched_at must be exactly the freeze instant.
      expect(parsed.fetched_at).toBe("2026-01-01T00:00:00.000Z");
    });

    test("--format json --forecast --days 2 produces a JSON array", async () => {
      const code = await run([
        "--location", "Hong Kong",
        "--format", "json",
        "--forecast",
        "--days", "2",
      ]);
      expect(code).toBe(0);
      const parsed = JSON.parse(io.stdout);
      expect(Array.isArray(parsed)).toBe(true);
      expect(parsed.length).toBeGreaterThan(0);
      expect(parsed[0].provider_name).toBe("hko");
    });
  });

  describe("incompatible flags", () => {
    test("--send --format json exits 2", async () => {
      const code = await run(["--send", "--format", "json"]);
      expect(code).toBe(2);
      expect(io.stderr).toContain("Error:");
      expect(io.stderr).toContain("--send");
      expect(io.stderr).toContain("--format json");
      expect(io.stdout).toBe("");
    });
  });

  describe("unknown provider", () => {
    test("--provider nonexistent exits 1 and lists available providers", async () => {
      const code = await run(["--provider", "nonexistent"]);
      expect(code).toBe(1);
      expect(io.stderr).toContain("Error: Provider not found: nonexistent");
      expect(io.stderr).toContain("Available providers:");
      // Sorted alphabetically per src/cli.ts → run()
      expect(io.stderr).toContain("hko, jma, nws, sg_nea");
      expect(io.stdout).toBe("");
    });
  });

  describe("argparse parity", () => {
    test("--help prints usage to stdout and exits 0", async () => {
      const code = await run(["--help"]);
      expect(code).toBe(0);
      expect(io.stdout).toContain("usage: weather");
      expect(io.stdout).toContain("--format {text,telegram,whatsapp,json}");
      expect(io.stderr).toBe("");
    });

    test("--days 3.5 errors (P6-1: strict int parsing)", async () => {
      const code = await run(["--days", "3.5"]);
      expect(code).toBe(1);
      expect(io.stderr).toContain("argument --days: invalid int value: '3.5'");
    });

    test("--format xml errors with choices list", async () => {
      const code = await run(["--format", "xml"]);
      expect(code).toBe(1);
      expect(io.stderr).toContain("argument --format: invalid choice");
      expect(io.stderr).toContain("'text', 'telegram', 'whatsapp', 'json'");
    });

    test("--bogus errors with unrecognized argument", async () => {
      const code = await run(["--bogus"]);
      expect(code).toBe(1);
      expect(io.stderr).toContain("unrecognized argument: --bogus");
    });
  });
});
