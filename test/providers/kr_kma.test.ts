/** Tests for the Bun South Korea KMA provider port. */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { KMAProvider } from "../../src/providers/kr_kma.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("KMAProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const seoul = parseLocation("Seoul");

  test("supports Korean locations only when API key is present", () => {
    const provider = new KMAProvider("test-key");
    expect(provider.supportsLocation(seoul)).toBe(true);
    expect(provider.supportsLocation(parseLocation("서울"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Tokyo"))).toBe(false);
    expect(new KMAProvider("").supportsLocation(seoul)).toBe(false);
  });

  test("getCurrent parses ultra-short nowcast fixture", async () => {
    const provider = new KMAProvider("test-key");
    const result = await provider.getCurrent(seoul);

    expect(result.location).toBe("Seoul");
    expect(result.provider_name).toBe("kma");
    expect(result.temperature).toBe(22.5);
    expect(result.humidity).toBe(65);
    expect(result.wind_speed).toBe(11.5);
    expect(result.condition).toBe(WeatherCondition.Unknown);
  });

  test("getForecast parses daily KMA forecast fixture", async () => {
    const provider = new KMAProvider("test-key");
    const days = await provider.getForecast(seoul, 2);

    expect(days).toHaveLength(2);
    expect(days[0]!.condition).toBe(WeatherCondition.Sunny);
    expect(days[0]!.temp_high).toBe(24);
    expect(days[0]!.temp_low).toBe(14);
    expect(days[0]!.precipitation_chance).toBe(10);
    expect(days[0]!.forecast_date?.toISOString()).toBe("2026-04-15T00:00:00.000Z");

    expect(days[1]!.condition).toBe(WeatherCondition.Rain);
    expect(days[1]!.humidity).toBe(80);
    expect(days[1]!.precipitation_chance).toBe(70);
  });

  test("getCurrent throws LocationNotSupportedError for unsupported location", async () => {
    const provider = new KMAProvider("test-key");
    await expect(
      provider.getCurrent(parseLocation("Tokyo")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
