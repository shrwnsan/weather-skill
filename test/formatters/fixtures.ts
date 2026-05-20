/* eslint-disable @typescript-eslint/naming-convention */
/**
 * Shared `WeatherData` payloads for formatter tests.
 *
 *  - `fullyPopulatedCurrent` exercises every optional field the formatters
 *    can render (incl. astro `sunrise`/`sunset` per P7.5-2) so a single
 *    snapshot catches accidental drops.
 *  - `aqiOnlyCurrent` exercises the `else if (data.aqi != null)` branch
 *    that's distinct from AQHI (per P7.5-3) — the formatters render
 *    "Air Quality: <quality> (AQI N)" instead of the AQHI variant.
 *  - `forecastDays` is a two-day forecast list with different conditions
 *    so day-label, emoji, and condition-string handling are covered.
 *
 * Fixtures pin `observed_at` to fixed Date instances so the day-of-week
 * labels (`Thursday, January 1`, `Fri Jan 2`, `Sat Jan 3`) are
 * deterministic without needing `freezeTime()` in every formatter test.
 */

import { WeatherCondition, type WeatherData } from "../../src/types.js";

export const fullyPopulatedCurrent: WeatherData = {
  location: "Hong Kong",
  temperature: 25.3,
  feels_like: 28.1,
  humidity: 84,
  wind_speed: 12,
  wind_direction: "ESE",
  wind_description: "East-southeast force 4",
  pressure: 1013,
  visibility: 10,
  uv_index: 7,
  condition: WeatherCondition.Rain,
  condition_raw: "Light rain",
  description: "Light rain with occasional showers.",
  observed_at: new Date("2026-01-01T08:00:00.000Z"),
  fetched_at: new Date("2026-01-01T00:00:00.000Z"),
  temp_high: 27,
  temp_low: 24,
  precipitation_chance: 70,
  aqhi: 4,
  sunrise: "06:30",
  sunset: "19:45",
  provider_name: "hko",
};

/**
 * Minimal payload that exercises the `aqi` (US EPA) air-quality branch
 * — distinct from the AQHI branch already covered by
 * `fullyPopulatedCurrent`. Both Telegram and WhatsApp formatters have
 * an `else if (data.aqi != null)` path that renders "Air Quality:
 * <quality> (AQI N)" with `aqiQuality()` instead of `aqhiQuality()`.
 */
export const aqiOnlyCurrent: WeatherData = {
  location: "Beijing",
  temperature: 18,
  condition: WeatherCondition.Cloudy,
  condition_raw: "Cloudy",
  observed_at: new Date("2026-01-01T08:00:00.000Z"),
  fetched_at: new Date("2026-01-01T00:00:00.000Z"),
  aqi: 180,
  provider_name: "owm",
};

export const forecastDays: WeatherData[] = [
  {
    ...fullyPopulatedCurrent,
    forecast_date: new Date("2026-01-02T00:00:00.000Z"),
    description: "Showers",
  },
  {
    ...fullyPopulatedCurrent,
    forecast_date: new Date("2026-01-03T00:00:00.000Z"),
    description: "Cloudy",
    condition: WeatherCondition.Cloudy,
    condition_raw: "Cloudy",
  },
];
