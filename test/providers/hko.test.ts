/**
 * HKO provider tests (PRD-002 Phase 7.4).
 *
 * Replays the canned `one_json.xml` fixture via the global `mockFetch`
 * preload and asserts a small stable set of fields parsed by the
 * `HKOProvider` for Hong Kong.
 */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { HKO_ICON_MAP } from "../../src/data-loader.js";
import { aqhiStr, makeWeatherData, parseLocation } from "../../src/models.js";
import { HKOProvider } from "../../src/providers/hko.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("HKOProvider", () => {
  // freezeTime is safe again now that P7.4-3 fixed the Date.UTC
  // partial-arg polyfill in test/setup.ts.
  beforeEach(freezeTime);
  afterEach(restoreTime);

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
    // P7.4-6: pin the specific WeatherCondition mapping.
    // rhrread.Icon1 = "62" → "pic62.png" → HKO_ICON_MAP → "rain"
    expect(result.condition).toBe(WeatherCondition.Rain);
    // Issue #15: HKO reports UV as a fractional string (fixture "0.2")
    // Regression guard against int(float()) / Math.trunc() truncating to 0.
    expect(result.uv_index).toBe(0.2);
  });

  test("HKO_ICON_MAP includes nighttime icons (70-85 series)", () => {
    // Issue #14: HKO uses 70-85 series for nighttime conditions.
    // Without these mappings, every night observation falls through to Unknown.
    expect(HKO_ICON_MAP["pic70.png"]).toBe(WeatherCondition.Sunny);
    expect(HKO_ICON_MAP["pic72.png"]).toBe(WeatherCondition.PartlyCloudy);
    expect(HKO_ICON_MAP["pic77.png"]).toBe(WeatherCondition.Fog);
    expect(HKO_ICON_MAP["pic80.png"]).toBe(WeatherCondition.Cloudy);
    expect(HKO_ICON_MAP["pic85.png"]).toBe(WeatherCondition.Thunderstorm);
  });

  test("aqhiStr matches Telegram formatter wording (Issue #16)", () => {
    // Drift fix: models.aqhiStr previously returned "High"/"Very High"
    // while utils.aqhiQuality (used by Telegram) returned "High Risk"/"Very High Risk".
    expect(aqhiStr(makeWeatherData({ location: "test", provider_name: "test", aqhi: 7 }))).toBe("7 (High Risk)");
    expect(aqhiStr(makeWeatherData({ location: "test", provider_name: "test", aqhi: 9 }))).toBe("9 (Very High Risk)");
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
    // P7.4-6: pin the specific WeatherCondition mapping.
    // F9D.WeatherForecast[0].ForecastIcon = "pic62.png" → HKO_ICON_MAP → "rain"
    expect(today.condition).toBe(WeatherCondition.Rain);
  });

  test("getCurrent throws LocationNotSupportedError for non-HK location", async () => {
    // P7.4-9: cover the throw guard at the top of getCurrent.
    const provider = new HKOProvider();
    await expect(
      provider.getCurrent(parseLocation("Paris")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });

  test("getForecast throws LocationNotSupportedError for non-HK location", async () => {
    // P7.4-9: cover the throw guard at the top of getForecast.
    const provider = new HKOProvider();
    await expect(
      provider.getForecast(parseLocation("Paris"), 3),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
