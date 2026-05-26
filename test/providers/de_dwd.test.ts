/** Tests for the Bun DWD/Bright Sky provider port. */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { DWDProvider } from "../../src/providers/de_dwd.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("DWDProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const berlin = parseLocation("Berlin");

  test("supports German locations", () => {
    const provider = new DWDProvider();
    expect(provider.supportsLocation(berlin)).toBe(true);
    expect(provider.supportsLocation(parseLocation("de"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Paris"))).toBe(false);
  });

  test("getCurrent parses Bright Sky current weather", async () => {
    const provider = new DWDProvider();
    const result = await provider.getCurrent(berlin);

    expect(result.location).toBe("Berlin");
    expect(result.provider_name).toBe("dwd");
    expect(result.temperature).toBe(18.4);
    expect(result.humidity).toBe(67);
    expect(result.wind_speed).toBe(12.3);
    expect(result.wind_direction).toBe("SW");
    expect(result.pressure).toBe(1014.2);
    expect(result.visibility).toBe(20);
    expect(result.condition).toBe(WeatherCondition.PartlyCloudy);
    expect(result.observed_at?.toISOString()).toBe("2026-05-18T10:00:00.000Z");
  });

  test("getForecast aggregates hourly Bright Sky weather by day", async () => {
    const provider = new DWDProvider();
    const days = await provider.getForecast(berlin, 2);

    expect(days).toHaveLength(2);

    expect(days[0]!.location).toBe("Berlin");
    expect(days[0]!.provider_name).toBe("dwd");
    expect(days[0]!.temp_low).toBe(12);
    expect(days[0]!.temp_high).toBe(20);
    expect(days[0]!.humidity).toBe(65);
    expect(days[0]!.precipitation_chance).toBe(10);
    expect(days[0]!.condition).toBe(WeatherCondition.Rain);
    expect(days[0]!.forecast_date?.toISOString()).toBe("2026-05-18T00:00:00.000Z");

    expect(days[1]!.temp_low).toBe(11);
    expect(days[1]!.temp_high).toBe(17);
    expect(days[1]!.condition).toBe(WeatherCondition.Sunny);
  });

  test("getCurrent throws LocationNotSupportedError for non-German location", async () => {
    const provider = new DWDProvider();
    await expect(
      provider.getCurrent(parseLocation("Paris")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
