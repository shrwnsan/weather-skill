/** Tests for the Bun UK Met Office provider port. */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { UKMetOfficeProvider } from "../../src/providers/uk_metoffice.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("UKMetOfficeProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const london = parseLocation("London");

  test("supports UK locations only when API key is present", () => {
    const provider = new UKMetOfficeProvider("test-key");
    expect(provider.supportsLocation(london)).toBe(true);
    expect(provider.supportsLocation(parseLocation("uk"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Paris"))).toBe(false);
    expect(new UKMetOfficeProvider("").supportsLocation(london)).toBe(false);
  });

  test("getCurrent parses hourly GeoJSON fixture", async () => {
    const provider = new UKMetOfficeProvider("test-key");
    const result = await provider.getCurrent(london);

    expect(result.location).toBe("London");
    expect(result.provider_name).toBe("metoffice");
    expect(result.temperature).toBe(14.2);
    expect(result.feels_like).toBe(13.1);
    expect(result.humidity).toBe(76);
    expect(result.wind_speed).toBe(18);
    expect(result.wind_direction).toBe("SW");
    expect(result.condition).toBe(WeatherCondition.Cloudy);
    expect(result.visibility).toBe(12);
    expect(result.uv_index).toBe(3);
    expect(result.precipitation_chance).toBe(40);
    expect(result.observed_at?.toISOString()).toBe("2026-05-18T10:00:00.000Z");
  });

  test("getForecast parses daily GeoJSON fixture", async () => {
    const provider = new UKMetOfficeProvider("test-key");
    const days = await provider.getForecast(london, 2);

    expect(days).toHaveLength(2);
    expect(days[0]!.temp_high).toBe(18);
    expect(days[0]!.temp_low).toBe(9);
    expect(days[0]!.humidity).toBe(70);
    expect(days[0]!.wind_speed).toBe(21.6);
    expect(days[0]!.wind_direction).toBe("SW");
    expect(days[0]!.condition).toBe(WeatherCondition.Showers);
    expect(days[0]!.precipitation_chance).toBe(55);
    expect(days[0]!.forecast_date?.toISOString()).toBe("2026-05-18T00:00:00.000Z");
    expect(days[1]!.condition).toBe(WeatherCondition.Sunny);
  });

  test("getCurrent throws LocationNotSupportedError for unsupported location", async () => {
    const provider = new UKMetOfficeProvider("test-key");
    await expect(
      provider.getCurrent(parseLocation("Paris")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
