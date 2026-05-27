/** Tests for the Bun Australia BOM provider port. */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { BOMProvider } from "../../src/providers/au_bom.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("BOMProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const sydney = parseLocation("Sydney");

  test("supports Australian locations", () => {
    const provider = new BOMProvider();
    expect(provider.supportsLocation(sydney)).toBe(true);
    expect(provider.supportsLocation(parseLocation("au"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Auckland"))).toBe(false);
  });

  test("getCurrent parses latest observation fixture", async () => {
    const provider = new BOMProvider();
    const result = await provider.getCurrent(sydney);

    expect(result.location).toBe("Sydney");
    expect(result.provider_name).toBe("bom");
    expect(result.temperature).toBe(21.7);
    expect(result.feels_like).toBe(20.9);
    expect(result.humidity).toBe(63);
    expect(result.wind_speed).toBe(19);
    expect(result.wind_direction).toBe("SSE");
    expect(result.pressure).toBe(1018.4);
    expect(result.condition).toBe(WeatherCondition.Unknown);
    expect(result.observed_at?.toISOString()).toBe("2026-05-18T10:30:00.000Z");
  });

  test("getForecast parses BOM daily forecast fixture", async () => {
    const provider = new BOMProvider();
    const days = await provider.getForecast(sydney, 2);

    expect(days).toHaveLength(2);
    expect(days[0]!.location).toBe("Sydney");
    expect(days[0]!.provider_name).toBe("bom");
    expect(days[0]!.temp_high).toBe(23);
    expect(days[0]!.temp_low).toBe(15);
    expect(days[0]!.condition).toBe(WeatherCondition.Showers);
    expect(days[0]!.condition_raw).toBe("shower or two");
    expect(days[0]!.precipitation_chance).toBe(60);
    expect(days[0]!.uv_index).toBe(4);
    expect(days[0]!.forecast_date?.toISOString()).toBe("2026-05-18T00:00:00.000Z");
    expect(days[1]!.condition).toBe(WeatherCondition.Sunny);
  });

  test("getCurrent throws LocationNotSupportedError for unsupported location", async () => {
    const provider = new BOMProvider();
    await expect(
      provider.getCurrent(parseLocation("Auckland")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
