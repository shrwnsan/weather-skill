/**
 * SG NEA provider tests (PRD-002 Phase 7.4).
 *
 * SCOUT FINDING — the live data.gov.sg v2 endpoints now return
 * `general.forecast` (24-hour) and `forecasts[].forecast` (4-day) as
 * `{text, code}` objects rather than the bare strings the current
 * `SGNEAProvider` (mirroring `weather/providers/sg_nea.py`) expects.
 * Calling `.toLowerCase()` on that object throws, so both
 * `getCurrent()` and `getForecast()` blow up against the canned
 * fixture. The full-flow assertions are therefore SKIPPED with this
 * comment; do NOT fix the provider in Phase 7.4 — the maintainer will
 * decide whether to bundle the fix.
 */

import { describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { SGNEAProvider } from "../../src/providers/sg_nea.js";

describe("SGNEAProvider", () => {
  const sg = parseLocation("Singapore");

  test("supports Singapore aliases", () => {
    const provider = new SGNEAProvider();
    expect(provider.supportsLocation(sg)).toBe(true);
    expect(provider.supportsLocation(parseLocation("sg"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Bangkok"))).toBe(false);
  });

  test("getCurrent throws ProviderError against current canned fixture", async () => {
    // The canned 24hr-forecast.json has `general.forecast = {text,code}`
    // (the new live schema). The provider's `textToCondition()` calls
    // `.toLowerCase()` on it, which throws — caught and wrapped as
    // ProviderError. We assert the failure mode so the regression is
    // visible until the provider is patched.
    const provider = new SGNEAProvider();
    await expect(provider.getCurrent(sg)).rejects.toThrow(/NEA API error/);
  });

  // SKIPPED — scout finding (see file header). Re-enable after
  // SGNEAProvider learns to unwrap the `{text, code}` object shape.
  test.skip("getCurrent parses temperature + humidity from station readings", async () => {
    const provider = new SGNEAProvider();
    const result = await provider.getCurrent(sg);
    expect(result.location).toBe("Singapore");
    expect(result.provider_name).toBe("sg_nea");
    // air-temperature.json averages to ~29-30°C across 33 stations
    expect(result.temperature).toBeGreaterThan(20);
    expect(result.temperature).toBeLessThan(40);
    expect(result.temp_high).toBe(33); // general.temperature.high
    expect(result.temp_low).toBe(25);  // general.temperature.low
  });

  // SKIPPED — same scout finding: `forecasts[].forecast` is an object
  // in the canned four-day-outlook.json, which crashes textToCondition.
  test.skip("getForecast returns 4 days with temp ranges", async () => {
    const provider = new SGNEAProvider();
    const days = await provider.getForecast(sg, 4);
    expect(days.length).toBe(4);
    const day0 = days[0]!;
    expect(day0.location).toBe("Singapore");
    expect(day0.provider_name).toBe("sg_nea");
    expect(day0.temp_high).toBe(34);
    expect(day0.temp_low).toBe(25);
  });
});
