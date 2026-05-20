/**
 * Snapshot tests for the CLI text formatter (PRD-002 Phase 7.5).
 *
 * Asserts the full byte-for-byte rendered output for a fully-populated
 * current `WeatherData` and a two-day forecast so any change to the
 * formatter is forced through an explicit test update.
 */

import { describe, expect, test } from "bun:test";

import { CliTextFormatter } from "../../src/formatters/cli_text.js";
import { fullyPopulatedCurrent, forecastDays } from "./fixtures.js";

describe("CliTextFormatter", () => {
  const fmt = new CliTextFormatter();

  test("platform is 'text'", () => {
    expect(fmt.platform).toBe("text");
  });

  test("formats a fully-populated current snapshot", () => {
    const out = fmt.format(fullyPopulatedCurrent);
    expect(out).toBe(
      [
        "🌧️ Weather for Hong Kong",
        "🌡️ Temperature: 25°C",
        "   Feels like: 28°C",
        "   Range: 24° - 27°",
        "💧 Humidity: 84%",
        "💨 Wind: East-southeast force 4",
        "🌧️ Rain chance: 70%",
        "☀️ UV Index: 7",
        "🌫️ AQHI: 4 (Moderate)",
        "📍 Provider: hko",
      ].join("\n"),
    );
  });

  test("formats a 2-day forecast snapshot", () => {
    const out = fmt.format(forecastDays);
    expect(out).toBe(
      [
        "📊 Weather Forecast",
        "",
        "2026-01-02: 27° / 24° — Showers",
        "2026-01-03: 27° / 24° — Cloudy",
      ].join("\n"),
    );
  });

  test("omits fields with missing data (no 'N/A' placeholders)", () => {
    // Mirrors `weather/formatters/cli_text.py` policy: skip the row entirely
    // when the field is null/undefined. Verified by removing optional fields.
    const minimal = {
      location: "Test",
      temperature: 20,
      condition: fullyPopulatedCurrent.condition,
      condition_raw: "",
      fetched_at: fullyPopulatedCurrent.fetched_at,
      provider_name: "test",
    };
    const out = fmt.format(minimal);
    // No humidity, wind, rain chance, UV, AQHI lines should appear.
    expect(out).not.toContain("Humidity");
    expect(out).not.toContain("Wind");
    expect(out).not.toContain("Rain chance");
    expect(out).not.toContain("UV Index");
    expect(out).not.toContain("AQHI");
    expect(out).not.toContain("N/A");
    // But location, temperature, and provider always render.
    expect(out).toContain("Weather for Test");
    expect(out).toContain("Temperature: 20°C");
    expect(out).toContain("Provider: test");
  });
});
