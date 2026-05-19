/* eslint-disable @typescript-eslint/naming-convention */
/**
 * Shared `WeatherData` payloads for formatter tests.
 *
 * Two payloads:
 *  - `fullyPopulatedCurrent` exercises every optional field the formatters
 *    can render so a single snapshot catches accidental drops.
 *  - `forecastDays` is a two-day forecast list with different conditions
 *    so day-label, emoji, and condition-string handling are covered.
 *
 * Dates use UTC midnight values; combined with `freezeTime()` in
 * `test/setup.ts` (Thu 2026-01-01T00:00:00Z) the formatter day-of-week
 * labels are deterministic.
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
  provider_name: "hko",
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
