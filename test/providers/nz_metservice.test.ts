/** Tests for the Bun New Zealand MetService provider port. */

import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { MetServiceProvider } from "../../src/providers/nz_metservice.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";
import { freezeTime, restoreTime } from "../setup.js";

describe("MetServiceProvider", () => {
  beforeEach(freezeTime);
  afterEach(restoreTime);

  const auckland = parseLocation("Auckland");

  test("supports New Zealand locations", () => {
    const provider = new MetServiceProvider();
    expect(provider.supportsLocation(auckland)).toBe(true);
    expect(provider.supportsLocation(parseLocation("nz"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Sydney"))).toBe(false);
  });

  test("getCurrent parses local observation fixture", async () => {
    const provider = new MetServiceProvider();
    const result = await provider.getCurrent(auckland);

    expect(result.location).toBe("Auckland");
    expect(result.provider_name).toBe("metservice");
    expect(result.temperature).toBe(16.5);
    expect(result.feels_like).toBe(15.8);
    expect(result.humidity).toBe(82);
    expect(result.wind_speed).toBe(18);
    expect(result.wind_direction).toBe("SW");
    expect(result.pressure).toBe(1012.4);
    expect(result.condition).toBe(WeatherCondition.Rain);
    expect(result.condition_raw).toBe("Rain");
    expect(result.observed_at?.toISOString()).toBe("2026-05-18T09:00:00.000Z");
  });

  test("getForecast returns empty list because public API has no multi-day forecast", async () => {
    const provider = new MetServiceProvider();
    expect(await provider.getForecast(auckland, 5)).toEqual([]);
  });

  test("getCurrent throws LocationNotSupportedError for non-New Zealand location", async () => {
    const provider = new MetServiceProvider();
    await expect(
      provider.getCurrent(parseLocation("Sydney")),
    ).rejects.toBeInstanceOf(LocationNotSupportedError);
  });
});
