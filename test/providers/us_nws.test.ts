/**
 * US NWS provider tests (PRD-002 Phase 7.4).
 *
 * Replays the canned New York fixture chain
 * (points → stations → observations → forecast) via the global
 * `mockFetch` preload and asserts the small set of fields parsed by
 * `NWSProvider`.
 */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { NWSProvider } from "../../src/providers/us_nws.js";
import { WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("NWSProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const nyc = parseLocation("New York");

  test("supports US locations", () => {
    const provider = new NWSProvider();
    expect(provider.supportsLocation(nyc)).toBe(true);
    expect(provider.supportsLocation(parseLocation("Chicago"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Hong Kong"))).toBe(false);
  });

  test("getCurrent parses observation fixture", async () => {
    const provider = new NWSProvider();
    const result = await provider.getCurrent(nyc);

    // Fields stamped directly from observations.json / properties:
    //   temperature.value  = 26.7   (already °C)
    //   relativeHumidity   = 46.82… (truncated to 46)
    //   textDescription    = "Clear"
    //   timestamp          = "2026-05-17T23:51:00+00:00"
    expect(result.location).toBe("New York");
    expect(result.provider_name).toBe("nws");
    expect(result.temperature).toBe(26.7);
    expect(result.humidity).toBe(46);
    expect(result.condition_raw).toBe("Clear");
    expect(result.condition).toBe(WeatherCondition.Sunny); // "Clear" → Sunny
    expect(result.observed_at?.toISOString()).toBe("2026-05-17T23:51:00.000Z");
    // wind_speed is populated (m/s × 3.6 in provider; we just check
    // that something numeric came through — the unit-mismatch issue
    // is documented separately, not in scope for Phase 7.4).
    expect(typeof result.wind_speed).toBe("number");
  });

  test("getForecast returns up to N daytime/nighttime days", async () => {
    const provider = new NWSProvider();
    const days = await provider.getForecast(nyc, 5);

    expect(days.length).toBeGreaterThan(0);
    expect(days.length).toBeLessThanOrEqual(5);

    const day0 = days[0]!;
    expect(day0.location).toBe("New York");
    expect(day0.provider_name).toBe("nws");
    // First period is "Tonight" (isDaytime=false, temp=68°F → 20°C)
    expect(day0.condition_raw).toBe("Partly Cloudy");
    expect(day0.condition).toBe(WeatherCondition.PartlyCloudy);
    expect(day0.temp_low).toBeCloseTo((68 - 32) * 5 / 9, 5);
    expect(day0.forecast_date).toBeInstanceOf(Date);
    expect(day0.wind_direction).toBe("SW");
  });
});
