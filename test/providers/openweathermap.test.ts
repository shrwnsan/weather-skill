/**
 * OpenWeatherMap provider tests (PRD-002 Phase 7.4).
 *
 * The `fixtures/api-responses/openweathermap/` directory currently has
 * `manifest.json` only — `needs_capture: true` (capturing real
 * responses requires `OPENWEATHERMAP_API_KEY`). Until those response
 * files are populated via
 *   `bash scripts/capture-fixtures.sh openweathermap`
 * the full request/response replay tests are TODO. We still cover the
 * class-instantiation + `supportsLocation` contract so this file has
 * at least one passing assertion.
 */

import { describe, expect, test } from "bun:test";

import { parseLocation } from "../../src/models.js";
import { OpenWeatherMapProvider } from "../../src/providers/openweathermap.js";

describe("OpenWeatherMapProvider", () => {
  test("instantiates with API key and supports any global location", () => {
    const provider = new OpenWeatherMapProvider("test-key");
    expect(provider.name).toBe("openweathermap");
    expect(provider.requiresApiKey).toBe(true);
    expect(provider.supportsLocation(parseLocation("London"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Hong Kong"))).toBe(true);
    expect(provider.supportsLocation(parseLocation("Tokyo"))).toBe(true);
  });

  // SKIPPED — `fixtures/api-responses/openweathermap/manifest.json`
  // has `needs_capture: true`; weather.json / forecast.json /
  // air-pollution.json have not been captured yet because a real
  // OPENWEATHERMAP_API_KEY is required. Re-enable after running
  // `bash scripts/capture-fixtures.sh openweathermap`.
  test.skip("getCurrent parses London weather fixture", async () => {
    const provider = new OpenWeatherMapProvider("test-key");
    const result = await provider.getCurrent(parseLocation("London"));
    expect(result.location).toBeDefined();
    expect(result.provider_name).toBe("openweathermap");
  });

  // SKIPPED — same reason as above (needs_capture: true).
  test.skip("getForecast returns N daily entries", async () => {
    const provider = new OpenWeatherMapProvider("test-key");
    const days = await provider.getForecast(parseLocation("London"), 3);
    expect(days.length).toBeGreaterThan(0);
  });
});
