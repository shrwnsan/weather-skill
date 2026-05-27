/** Tests for the Bun Taiwan CWA provider port. */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { CWAProvider } from "../../src/providers/tw_cwa.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("CWAProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const taipei = parseLocation("Taipei");

  test("supports Taiwanese locations only when API key is present", () => {
    const provider = new CWAProvider("test-key");
    expect(provider.supportsLocation(taipei)).toBe(true);
    expect(provider.supportsLocation(parseLocation("台北"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Hong Kong"))).toBe(false);
    expect(new CWAProvider("").supportsLocation(taipei)).toBe(false);
  });

  test("getCurrent parses observation and 36-hour forecast fixtures", async () => {
    const provider = new CWAProvider("test-key");
    const result = await provider.getCurrent(taipei);

    expect(result.location).toBe("臺北市");
    expect(result.provider_name).toBe("cwa");
    expect(result.temperature).toBe(28.4);
    expect(result.humidity).toBe(70);
    expect(result.wind_speed).toBe(3.2);
    expect(result.wind_direction).toBe("NE");
    expect(result.condition).toBe(WeatherCondition.Rain);
    expect(result.description).toBe("多雲短暫雨");
    expect(result.precipitation_chance).toBe(40);
    expect(result.observed_at?.toISOString()).toBe("2026-05-18T10:00:00.000Z");
  });

  test("getForecast parses weekly forecast fixture", async () => {
    const provider = new CWAProvider("test-key");
    const days = await provider.getForecast(taipei, 2);

    expect(days).toHaveLength(2);
    expect(days[0]!.temp_low).toBe(24);
    expect(days[0]!.temp_high).toBe(30);
    expect(days[0]!.condition).toBe(WeatherCondition.Rain);
    expect(days[0]!.description).toBe("多雲短暫雨");
    expect(days[0]!.precipitation_chance).toBe(40);
    expect(days[0]!.forecast_date?.toISOString()).toBe("2026-05-18T00:00:00.000Z");
    expect(days[1]!.condition).toBe(WeatherCondition.Sunny);
  });

  test("getCurrent throws LocationNotSupportedError for unsupported location", async () => {
    const provider = new CWAProvider("test-key");
    await expect(
      provider.getCurrent(parseLocation("Hong Kong")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
