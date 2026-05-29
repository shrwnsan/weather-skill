/**
 * Open-Meteo provider tests (PRD-003).
 *
 * Replays the canned shenzhen-current.json fixture via the global mockFetch
 * preload and asserts parsed fields from the Open-Meteo API response.
 */

import { describe, expect, test } from "bun:test";

import { OpenMeteoProvider } from "../../src/providers/open_meteo.js";
import { parseLocation } from "../../src/models.js";
import { LocationNotSupportedError, WeatherCondition } from "../../src/types.js";

describe("OpenMeteoProvider", () => {
  const provider = new OpenMeteoProvider();

  describe("supportsLocation", () => {
    test("returns true for Chinese city in CN_CITIES", () => {
      expect(provider.supportsLocation(parseLocation("Shenzhen"))).toBe(true);
    });

    test("returns true for US city in US_NWS_CITIES", () => {
      expect(provider.supportsLocation(parseLocation("New York"))).toBe(true);
    });

    test("returns true for German city in DE_DWD_CITIES", () => {
      expect(provider.supportsLocation(parseLocation("Berlin"))).toBe(true);
    });

    test("returns false for unknown location", () => {
      expect(provider.supportsLocation(parseLocation("Atlantis"))).toBe(false);
    });

    test("returns true for country-level 'china' key", () => {
      expect(provider.supportsLocation(parseLocation("China"))).toBe(true);
    });
  });

  describe("getCurrent (Shenzhen fixture)", () => {
    test("parses fixture into WeatherData", async () => {
      const result = await provider.getCurrent(parseLocation("Shenzhen"));

      expect(result.location).toBe("Shenzhen");
      expect(result.provider_name).toBe("open-meteo");
      expect(result.temperature).toBe(18.4);
      expect(result.condition).toBe(WeatherCondition.PartlyCloudy);
      expect(result.condition_raw).toBe("wmo:2");
      expect(result.humidity).toBe(72);
      expect(result.feels_like).toBe(17.1);
      expect(result.temp_high).toBe(22.1);
      expect(result.temp_low).toBe(14.3);
      expect(result.precipitation_chance).toBe(10);
      expect(result.sunrise).toBe("2026-01-01T06:52");
      expect(result.sunset).toBe("2026-01-01T17:58");
      expect(result.wind_speed).toBe(11.2);
      expect(result.observed_at).toBeInstanceOf(Date);
    });
  });

  describe("alias resolution", () => {
    test("'sz' alias resolves to Shenzhen", () => {
      const loc = parseLocation("sz");
      expect(loc.normalized).toBe("shenzhen");
      expect(provider.supportsLocation(loc)).toBe(true);
    });

    test("'bj' alias resolves to Beijing", () => {
      const loc = parseLocation("bj");
      expect(loc.normalized).toBe("beijing");
      expect(provider.supportsLocation(loc)).toBe(true);
    });

    test("'sh' alias resolves to Shanghai", () => {
      const loc = parseLocation("sh");
      expect(loc.normalized).toBe("shanghai");
      expect(provider.supportsLocation(loc)).toBe(true);
    });
  });

  describe("error paths", () => {
    test("getCurrent throws LocationNotSupportedError for unknown location", async () => {
      await expect(
        provider.getCurrent(parseLocation("Atlantis")),
      ).rejects.toBeInstanceOf(LocationNotSupportedError);
    });

    test("getForecast throws LocationNotSupportedError for unknown location", async () => {
      await expect(
        provider.getForecast(parseLocation("Atlantis")),
      ).rejects.toBeInstanceOf(LocationNotSupportedError);
    });
  });
});
