/**
 * Snapshot tests for the Telegram (MarkdownV2) formatter
 * (PRD-002 Phase 7.5).
 *
 * MarkdownV2 reserves a specific set of punctuation that must be
 * escaped with a backslash even inside plain text. The escape set is
 * exposed as `MDV2_ESCAPE_CHARS` so the assertions can re-derive it
 * rather than hard-coding.
 */

import { describe, expect, test } from "bun:test";

import {
  MDV2_ESCAPE_CHARS,
  TelegramFormatter,
  escapeMdv2,
} from "../../src/formatters/telegram.js";
import { aqiOnlyCurrent, forecastDays, fullyPopulatedCurrent } from "./fixtures.js";

describe("TelegramFormatter", () => {
  const fmt = new TelegramFormatter();

  test("platform is 'telegram'", () => {
    expect(fmt.platform).toBe("telegram");
  });

  test("formats a fully-populated current snapshot", () => {
    const out = fmt.format(fullyPopulatedCurrent);
    expect(out).toBe(
      [
        "🌧️ Hong Kong Weather — Thursday, January 1",
        "",
        "🌡️ 25°C \\(feels 28°C\\) • High 27° / Low 24°",
        "🌧️ Light rain with occasional showers\\.",
        "💧 Humidity: 84%",
        "💨 Wind: East\\-southeast force 4",
        "🌧️ Rain chance: 70%",
        "🌬️ Air Quality: Moderate \\(AQHI 4\\)",
        "☀️ UV Index: 7.0 \\(High\\)",
        "🌅 Sunrise: 06:30 | 🌇 Sunset: 19:45",
        "",
        "Warm humid with rain expected — perfect weather for a cozy day indoors",
      ].join("\n"),
    );
  });

  test("renders the AQI (non-AQHI) air-quality branch", () => {
    // P7.5-3: separate branch from the AQHI line above.
    const out = fmt.format(aqiOnlyCurrent);
    expect(out).toContain("🌬️ Air Quality: Unhealthy \\(AQI 180\\)");
    expect(out).not.toContain("AQHI");
  });

  test("formats a 2-day forecast snapshot", () => {
    const out = fmt.format(forecastDays);
    expect(out).toBe(
      [
        "📊 Hong Kong 2\\-Day Forecast",
        "",
        "Fri Jan 2: 🌧️ 27° / 24° — Showers",
        "Sat Jan 3: ☁️ 27° / 24° — Cloudy",
      ].join("\n"),
    );
  });
});

describe("escapeMdv2", () => {
  test("MDV2_ESCAPE_CHARS contains exactly Telegram's reserved set", () => {
    // Per https://core.telegram.org/bots/api#markdownv2-style — 18 chars.
    expect(MDV2_ESCAPE_CHARS).toEqual(
      new Set(["_", "*", "[", "]", "(", ")", "~", "`", ">", "#",
              "+", "-", "=", "|", "{", "}", ".", "!"]),
    );
  });

  test("escapes every reserved char with a single backslash", () => {
    for (const ch of MDV2_ESCAPE_CHARS) {
      expect(escapeMdv2(ch)).toBe(`\\${ch}`);
    }
  });

  test("leaves non-reserved chars untouched", () => {
    expect(escapeMdv2("Hello, world 123")).toBe("Hello, world 123");
  });

  test("escapes inside a sentence", () => {
    expect(escapeMdv2("It's 25°C (feels like 28)."))
      .toBe("It's 25°C \\(feels like 28\\)\\.");
  });

  test("double-escape documents non-idempotency (P7.5-1)", () => {
    // `escapeMdv2` is NOT idempotent — Telegram MarkdownV2 requires
    // backslashes themselves be escaped, so a second pass DOES add
    // more slashes. Callers must escape exactly once, never re-feed
    // already-escaped text. This test pins that behavior.
    const once = escapeMdv2("foo. bar!");
    expect(once).toBe("foo\\. bar\\!");
    const twice = escapeMdv2(once);
    expect(twice).not.toBe(once);
  });
});
