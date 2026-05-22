/**
 * HKO provider tests (PRD-002 Phase 7.4).
 *
 * Replays the canned `one_json.xml` fixture via the global `mockFetch`
 * preload and asserts a small stable set of fields parsed by the
 * `HKOProvider` for Hong Kong.
 */

import { describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { HKOProvider } from "../../src/providers/hko.js";
import { WeatherCondition } from "../../src/types.js";

describe("HKOProvider", () => {
  // No freezeTime() — observed_at / forecast_date assertions compare
  // against fixture-derived constants rather than wall-clock "now".
  // (HKO uses Date.UTC() internally; freezeTime in setup.ts mishandles
  // partial-arg Date.UTC calls — see Phase 7.4 notes.)

  const hk = parseLocation("Hong Kong");

  test("supports Hong Kong aliases", () => {
    const provider = new HKOProvider();
    expect(provider.supportsLocation(hk)).toBe(true);
    expect(provider.supportsLocation(parseLocation("hk"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Paris"))).toBe(false);
  });

  test("getCurrent parses fixture into WeatherData", async () => {
    const provider = new HKOProvider();
    const result = await provider.getCurrent(hk);

    // Fields stamped directly from the canned hko/one_json.json fixture
    expect(result.location).toBe("Hong Kong");
    expect(result.provider_name).toBe("hko");
    expect(result.temperature).toBe(25.2);    // hko.Temperature
    expect(result.humidity).toBe(89);          // hko.RH
    expect(result.temp_high).toBe(27);         // F9D.WeatherForecast[0].ForecastMaxtemp
    expect(result.temp_low).toBe(24);          // F9D.WeatherForecast[0].ForecastMintemp
    expect(result.precipitation_chance).toBe(30); // PSR "Medium Low"
    expect(result.wind_description).toContain("East to southeast");
    expect(result.observed_at).toBeInstanceOf(Date);
    // BulletinTime "202605180820" → 2026-05-18 08:20 UTC
    expect(result.observed_at?.toISOString()).toBe("2026-05-18T08:20:00.000Z");
  });

  test("getForecast returns N days", async () => {
    const provider = new HKOProvider();
    const days = await provider.getForecast(hk, 3);

    expect(days).toHaveLength(3);
    const today = days[0]!;
    expect(today.provider_name).toBe("hko");
    expect(today.location).toBe("Hong Kong");
    expect(today.temp_high).toBe(27);
    expect(today.temp_low).toBe(24);
    expect(today.forecast_date).toBeInstanceOf(Date);
    expect(today.forecast_date?.toISOString().slice(0, 10)).toBe("2026-05-18");
    // pic62.png → Rain in HKO_ICON_MAP (sanity-check it's not Unknown)
    expect(today.condition).not.toBe(WeatherCondition.Unknown);
  });
});
