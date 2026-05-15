/**
 * Public package entry point for `@shrwnsan/weather-skill`.
 *
 * Re-exports the orchestrator, factory, types, providers, and
 * model helpers so consumers can import everything they need from
 * a single module.
 */

export { WeatherSkill, type WeatherSkillInit } from "./skill.js";
export { buildDefaultSkill } from "./bootstrap.js";

export type {
  IWeatherFormatter,
  IWeatherProvider,
  IWeatherSender,
  Location,
  SendOptions,
  SendResult,
  WeatherData,
} from "./types.js";

export {
  LocationNotSupportedError,
  NoProviderError,
  ProviderError,
  WeatherCondition,
} from "./types.js";

export {
  aqhiStr,
  aqiStr,
  calculateFeelsLike,
  effectiveFeelsLike,
  getEmoji,
  humidityStr,
  makeWeatherData,
  normalizeLocation,
  parseLocation,
  tempRangeStr,
  windStr,
} from "./models.js";

export { HKOProvider } from "./providers/hko.js";
export { JMAProvider } from "./providers/jma.js";
export { OpenWeatherMapProvider } from "./providers/openweathermap.js";
export { SGNEAProvider } from "./providers/sg_nea.js";
export { NWSProvider } from "./providers/us_nws.js";
