/* eslint-disable @typescript-eslint/naming-convention */
/**
 * Bootstrap factory for the Bun WeatherSkill.
 *
 * Mirrors `weather/bootstrap.py`. Registers all v0.1 batch-1 providers
 * unconditionally and the OpenWeatherMap fallback if the
 * `OPENWEATHERMAP_API_KEY` environment variable is set.
 *
 * Batch-2 providers (CWA, Met Office, BOM, MetService, BMKG, DWD,
 * KMA, TMD) are deferred to PRD-002b and will be wired here when their
 * Bun ports land.
 *
 * Formatters: CLI text, Telegram (MarkdownV2), and WhatsApp are
 * registered unconditionally. The Telegram sender is registered only
 * when `TELEGRAM_BOT_TOKEN` is present in the environment, matching
 * the gating in `weather/bootstrap.py`.
 */

import { CliTextFormatter } from "./formatters/cli_text.js";
import { TelegramFormatter } from "./formatters/telegram.js";
import { WhatsAppFormatter } from "./formatters/whatsapp.js";
import { HKOProvider } from "./providers/hko.js";
import { JMAProvider } from "./providers/jma.js";
import { OpenWeatherMapProvider } from "./providers/openweathermap.js";
import { SGNEAProvider } from "./providers/sg_nea.js";
import { NWSProvider } from "./providers/us_nws.js";
import { TelegramSender } from "./senders/telegram.js";
import { WeatherSkill, type WeatherSkillInit } from "./skill.js";
import type {
  IWeatherFormatter,
  IWeatherProvider,
  IWeatherSender,
} from "./types.js";

/**
 * Build a fully-configured WeatherSkill instance.
 *
 * Accepts optional overrides for testing or custom configuration.
 */
export function buildDefaultSkill(
  overrides: WeatherSkillInit = {},
): WeatherSkill {
  return new WeatherSkill({
    providers: overrides.providers ?? buildProviders(),
    formatters: overrides.formatters ?? buildFormatters(),
    senders: overrides.senders ?? buildSenders(),
  });
}

/** Construct the default v0.1 provider list from environment. */
function buildProviders(): IWeatherProvider[] {
  const providers: IWeatherProvider[] = [
    new HKOProvider(),
    new SGNEAProvider(),
    new JMAProvider(),
    new NWSProvider(),
  ];

  // Key-required: OpenWeatherMap (global fallback).
  const owmKey = process.env.OPENWEATHERMAP_API_KEY;
  if (owmKey) {
    providers.push(new OpenWeatherMapProvider(owmKey));
  }

  return providers;
}

/**
 * Construct the default formatter map. Mirrors
 * `weather/bootstrap.py:_build_formatters`. All three formatters are
 * registered unconditionally — they have no configuration.
 */
function buildFormatters(): Record<string, IWeatherFormatter> {
  return {
    text: new CliTextFormatter(),
    telegram: new TelegramFormatter(),
    whatsapp: new WhatsAppFormatter(),
  };
}

/**
 * Construct the default sender map from environment. Mirrors
 * `weather/bootstrap.py:_build_senders` — Telegram registers only when
 * `TELEGRAM_BOT_TOKEN` is set so `TelegramSender`'s constructor cannot
 * throw during default bootstrap.
 */
function buildSenders(): Record<string, IWeatherSender> {
  const senders: Record<string, IWeatherSender> = {};
  if (process.env.TELEGRAM_BOT_TOKEN) {
    senders["telegram"] = new TelegramSender();
  }
  return senders;
}
