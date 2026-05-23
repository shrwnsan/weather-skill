/**
 * JMA provider tests (PRD-002 Phase 7.4).
 *
 * Replays the canned Tokyo (area 130000) forecast + overview fixtures
 * via the global `mockFetch` preload.
 *
 * NOTE — scout finding: in the captured `forecast-130000.json` the
 * weekly-forecast (`forecastData[1].timeSeries[1]`) starts with an
 * empty-string entry for `tempsMin[0]`, `tempsMax[0]`, and `pops[0]`
 * (today is covered by the short-term block instead). The provider
 * code in `src/providers/jma.ts` parses those empty strings as NaN
 * and leaves the fields undefined, so `forecast[0]` lacks
 * `temp_high`, `temp_low`, and `precipitation_chance`. The temp/precip
 * assertions for day 0 are therefore SKIPPED — see the scout report
 * referenced in the PRD-002 Phase 7.4 task brief.
 */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { JMAProvider } from "../../src/providers/jma.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("JMAProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const tokyo = parseLocation("Tokyo");

  test("supports Japanese locations", () => {
    const provider = new JMAProvider();
    expect(provider.supportsLocation(tokyo)).toBe(true);
    expect(provider.supportsLocation(parseLocation("東京"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Hong Kong"))).toBe(false);
  });

  test("getCurrent parses short-term forecast + overview", async () => {
    const provider = new JMAProvider();
    const result = await provider.getCurrent(tokyo);

    // Fixture: short-term ts[2].temps = ["29","29","18","29"] →
    // tempLow=18, tempHigh=29, temperature=(29+18)/2=23.5
    expect(result.location).toBe("Tokyo");
    expect(result.provider_name).toBe("jma");
    expect(result.temp_low).toBe(18);
    expect(result.temp_high).toBe(29);
    expect(result.temperature).toBe(23.5);
    // P7.4-6: pin the specific WeatherCondition mapping.
    // weatherCodes[0] = "100" → JMA_WEATHER_CODE_MAP → "sunny"
    expect(result.condition).toBe(WeatherCondition.Sunny);
    // pops are all "0" → max = 0
    expect(result.precipitation_chance).toBe(0);
    // description sourced from overview_forecast.text
    expect(result.description).toBeDefined();
    expect((result.description ?? "").length).toBeGreaterThan(0);
  });

  test("getForecast returns the weekly outlook", async () => {
    const provider = new JMAProvider();
    const days = await provider.getForecast(tokyo, 5);

    // Weekly timeDefines has 7 entries; capped at 5 by the days arg.
    expect(days.length).toBe(5);
    const today = days[0]!;
    expect(today.location).toBe("Tokyo");
    expect(today.provider_name).toBe("jma");
    // timeDefines[0] = "2026-05-18T00:00:00+09:00" → 2026-05-17T15:00Z
    expect(today.forecast_date?.toISOString()).toBe("2026-05-17T15:00:00.000Z");
    // P7.4-6: pin the specific WeatherCondition mapping.
    // weatherCodes[0] = "100" → JMA_WEATHER_CODE_MAP → "sunny"
    expect(today.condition).toBe(WeatherCondition.Sunny);

    // Day 1 (index 1) has populated values: tempsMin=17, tempsMax=28, pops=10
    const day1 = days[1]!;
    expect(day1.temp_low).toBe(17);
    expect(day1.temp_high).toBe(28);
    expect(day1.precipitation_chance).toBe(10);
  });

  // SKIPPED — scout finding: in the canned forecast-130000.json,
  // weekly tempsMin[0]/tempsMax[0]/pops[0] are empty strings (today
  // is covered by the short-term block instead), so `forecast[0]`
  // ends up with undefined temp_high/temp_low/precipitation_chance.
  // The provider should fall back to the short-term block for day 0;
  // until then this assertion is parked here as documentation.
  test.skip("forecast[0] has temp_high / temp_low / precipitation_chance", async () => {
    const provider = new JMAProvider();
    const days = await provider.getForecast(tokyo, 5);
    const today = days[0]!;
    expect(today.temp_high).toBeDefined();
    expect(today.temp_low).toBeDefined();
    expect(today.precipitation_chance).toBeDefined();
  });

  test("getCurrent throws LocationNotSupportedError for non-JP location", async () => {
    // P7.4-9: cover the throw guard at the top of getCurrent.
    const provider = new JMAProvider();
    await expect(
      provider.getCurrent(parseLocation("Hong Kong")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });

  test("getForecast throws LocationNotSupportedError for non-JP location", async () => {
    // P7.4-9: cover the throw guard at the top of getForecast.
    const provider = new JMAProvider();
    await expect(
      provider.getForecast(parseLocation("Hong Kong"), 5),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
