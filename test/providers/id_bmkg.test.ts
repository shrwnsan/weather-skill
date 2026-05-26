/** Tests for the Bun Indonesia BMKG provider port. */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { BMKGProvider } from "../../src/providers/id_bmkg.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("BMKGProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const jakarta = parseLocation("Jakarta");

  test("supports Indonesian locations", () => {
    const provider = new BMKGProvider();
    expect(provider.supportsLocation(jakarta)).toBe(true);
    expect(provider.supportsLocation(parseLocation("Bali"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Singapore"))).toBe(false);
  });

  test("getCurrent picks nearest interval from forecast fixture", async () => {
    const provider = new BMKGProvider();
    const result = await provider.getCurrent(jakarta);

    expect(result.location).toBe("Kota Jakarta Pusat");
    expect(result.provider_name).toBe("bmkg");
    expect(result.temperature).toBe(29);
    expect(result.humidity).toBe(78);
    expect(result.wind_speed).toBe(8);
    expect(result.wind_description).toBe("SW 8 km/h");
    expect(result.condition).toBe(WeatherCondition.Rain);
    expect(result.description).toBe("Rain");
    expect(result.observed_at?.toISOString()).toBe("2026-01-01T00:00:00.000Z");
  });

  test("getForecast chooses one representative entry per day", async () => {
    const provider = new BMKGProvider();
    const days = await provider.getForecast(jakarta, 2);

    expect(days).toHaveLength(2);
    expect(days[0]!.temperature).toBe(32);
    expect(days[0]!.condition).toBe(WeatherCondition.PartlyCloudy);
    expect(days[0]!.forecast_date?.toISOString()).toBe("2026-01-01T00:00:00.000Z");
    expect(days[1]!.temperature).toBe(31);
    expect(days[1]!.condition).toBe(WeatherCondition.PartlyCloudy);
  });

  test("getCurrent throws LocationNotSupportedError for unsupported location", async () => {
    const provider = new BMKGProvider();
    await expect(
      provider.getCurrent(parseLocation("Singapore")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
