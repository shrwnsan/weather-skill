/**
 * Snapshot tests for the WhatsApp formatter (PRD-002 Phase 7.5).
 *
 * WhatsApp uses `*bold*` and `_italic_` syntax. No escaping required;
 * the long-message limit is 65 536 chars (vs Telegram's 4 096).
 */

import { describe, expect, test } from "bun:test";

import { WhatsAppFormatter } from "../../src/formatters/whatsapp.js";
import { aqiOnlyCurrent, forecastDays, fullyPopulatedCurrent } from "./fixtures.js";

describe("WhatsAppFormatter", () => {
  const fmt = new WhatsAppFormatter();

  test("platform is 'whatsapp'", () => {
    expect(fmt.platform).toBe("whatsapp");
  });

  test("formats a fully-populated current snapshot", () => {
    const out = fmt.format(fullyPopulatedCurrent);
    expect(out).toBe(
      [
        "*🌧️ Hong Kong Weather — Thursday, January 1*",
        "",
        "🌡️ 25°C (feels 28°C) • High 27° / Low 24°",
        "🌧️ Light rain with occasional showers.",
        "💧 Humidity: 84%",
        "💨 Wind: East-southeast force 4",
        "🌧️ Rain chance: 70%",
        "🌬️ Air Quality: Moderate (AQHI 4)",
        "☀️ UV Index: 7.0 (High)",
        "🌅 Sunrise: 06:30 | 🌇 Sunset: 19:45",
        "",
        "_Warm humid with rain expected — perfect weather for a cozy day indoors_",
      ].join("\n"),
    );
  });

  test("renders the AQI (non-AQHI) air-quality branch", () => {
    // P7.5-3: separate branch from the AQHI line above.
    const out = fmt.format(aqiOnlyCurrent);
    expect(out).toContain("🌬️ Air Quality: Unhealthy (AQI 180)");
    expect(out).not.toContain("AQHI");
  });

  test("formats a 2-day forecast snapshot", () => {
    const out = fmt.format(forecastDays);
    expect(out).toBe(
      [
        "*📊 Hong Kong 2-Day Forecast*",
        "",
        "Fri Jan 2: 🌧️ 27° / 24° — Showers",
        "Sat Jan 3: ☁️ 27° / 24° — Cloudy",
      ].join("\n"),
    );
  });

  test("does NOT escape any characters (asymmetry with Telegram)", () => {
    // Mirrors Python's whatsapp.py — `.` and `!` and parens render as-is.
    const out = fmt.format(fullyPopulatedCurrent);
    expect(out).not.toContain("\\");
  });
});
