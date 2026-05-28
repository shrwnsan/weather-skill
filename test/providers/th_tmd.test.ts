/** Tests for the Bun Thailand TMD provider port. */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { TMDProvider } from "../../src/providers/th_tmd.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("TMDProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const bangkok = parseLocation("Bangkok");

  test("supports Thai locations only when API key is present", () => {
    const provider = new TMDProvider("test-key");
    expect(provider.supportsLocation(bangkok)).toBe(true);
    expect(provider.supportsLocation(parseLocation("ภูเก็ต"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Singapore"))).toBe(false);
    expect(new TMDProvider("").supportsLocation(bangkok)).toBe(false);
  });

  test("getCurrent parses station observation fixture", async () => {
    const provider = new TMDProvider("test-key");
    const result = await provider.getCurrent(bangkok);

    expect(result.location).toBe("Bangkok");
    expect(result.provider_name).toBe("tmd");
    expect(result.temperature).toBe(32.5);
    expect(result.temp_high).toBe(35);
    expect(result.temp_low).toBe(27);
    expect(result.humidity).toBe(72);
    expect(result.condition).toBe(WeatherCondition.Unknown);
  });

  test("getForecast parses daily province forecast fixture", async () => {
    const provider = new TMDProvider("test-key");
    const days = await provider.getForecast(bangkok, 2);

    expect(days).toHaveLength(2);
    expect(days[0]!.condition).toBe(WeatherCondition.PartlyCloudy);
    expect(days[0]!.temp_high).toBe(35);
    expect(days[0]!.temp_low).toBe(27);
    expect(days[0]!.precipitation_chance).toBe(10);
    expect(days[0]!.forecast_date?.toISOString()).toBe("2026-04-15T00:00:00.000Z");
    expect(days[1]!.condition).toBe(WeatherCondition.Thunderstorm);
    expect(days[1]!.precipitation_chance).toBe(60);
  });

  test("getCurrent throws LocationNotSupportedError for unsupported location", async () => {
    const provider = new TMDProvider("test-key");
    await expect(
      provider.getCurrent(parseLocation("Singapore")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
