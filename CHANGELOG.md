# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- **Shared data layer** (PRD-002 Phase 1) — moved all hardcoded condition maps, location aliases, and city tables out of Python source into `weather/data/*.json`. Providers now load via `importlib.resources` so the data ships in the wheel and can be consumed by future runtimes (Bun port). Zero behavioral changes; all 69 tests pass.
- **CLI JSON output** — switched `--format json` to use `sort_keys=True` and ISO-8601 datetime format (T-separated) for deterministic, cross-runtime-friendly output. `WeatherCondition` enum values now serialize as their `.value` (e.g., `"sunny"`) instead of `"WeatherCondition.SUNNY"`.

### Added

- `weather/data/loader.py` — small helper to load JSON resources via `importlib.resources`.
- `.github/workflows/python-ci.yml` — CI workflow that runs pytest across Python 3.10–3.13 and verifies the built wheel ships all required JSON data files.
- **Bun/TypeScript scaffold** (PRD-002 Phase 2) — `package.json` (`@shrwnsan/weather-skill`, ESM, Bun ≥1.1.30), `tsconfig.json` (strict ESNext, `resolveJsonModule`), `bunfig.toml` (test preload).
- `src/types.ts` — `WeatherCondition` enum (20 values) and snake_case `WeatherData` / `Location` / `IWeatherProvider` / `IWeatherFormatter` / `IWeatherSender` interfaces matching Python's `dataclasses.asdict()` output exactly. Includes `ProviderError`, `LocationNotSupportedError`, `NoProviderError` parity with Python.
- `src/data-loader.ts` — typed accessors for every JSON file under `weather/data/` (3 top-level + 4 city + 14 condition maps). Uses bundled JSON imports so files are embedded into `bun build --compile` output instead of read from disk at runtime.
- `src/models.ts` — helper functions mirroring `WeatherData` properties (`humidityStr`, `windStr`, `tempRangeStr`, `aqhiStr`, `aqiStr`, `effectiveFeelsLike`, `calculateFeelsLike`) and module-level `normalizeLocation`, `parseLocation`, `getEmoji`, `makeWeatherData`.
- **Bun providers — batch 1 + OpenWeatherMap** (PRD-002 Phase 3) — TypeScript ports of the 4 v0.1 regional providers and the global fallback:
  - `src/providers/hko.ts` — Hong Kong Observatory (priority 1, AQHI support, `pic{N}.png` icon → `WeatherCondition` mapping, PSR rain probability map).
  - `src/providers/jma.ts` — Japan Meteorological Agency (priority 3, dual forecast + overview endpoints, parallel `Promise.all`, 3-level nested `timeSeries` traversal, `User-Agent: WeatherSkill/1.0`).
  - `src/providers/sg_nea.ts` — Singapore NEA (priority 2, partial-failure-tolerant parallel fetch via `fetchJsonSafe`, PSI air-quality, 4-day default forecast, `User-Agent: WeatherSkill/1.0`).
  - `src/providers/us_nws.ts` — US National Weather Service (`name = "nws"`, priority 7, multi-step `/points` → forecast/observation flow, F→C and m/s→km/h unit conversions, `User-Agent: WeatherSkill/1.0 (support@weather-skill.io)` required to avoid HTTP 403).
  - `src/providers/openweathermap.ts` — OpenWeatherMap global fallback (priority 10, `q={city}` query path, today's high/low aggregated from 3-hourly forecast, daily forecast aggregation by UTC date with mode-aggregated condition codes, optional air-quality endpoint with US-EPA scale mapping).
- `src/skill.ts` — `WeatherSkill` orchestrator class with `getCurrent` / `getForecast` / `format` / `send`, provider-chain priority routing, `ProviderError` accumulation across retries, plain-text fallback formatter (mirrors `weather/skill.py`).
- `src/bootstrap.ts` — `buildDefaultSkill()` factory that registers the 4 batch-1 providers unconditionally and OpenWeatherMap iff `OPENWEATHERMAP_API_KEY` is set (mirrors `weather/bootstrap.py`). Formatter/sender maps return empty until Phase 5.
- `src/index.ts` — public package entry point; re-exports orchestrator, factory, types, providers, and model helpers from a single module.
- **Bun formatters + Telegram sender** (PRD-002 Phase 5) — TypeScript ports of the three message formatters and the Telegram delivery channel, all verified byte-identical against Python output for a representative `WeatherData` payload:
  - `src/utils.ts` — shared helpers extracted from the duplicated logic in `weather/formatters/telegram.py` and `whatsapp.py`: `aqhiQuality`, `aqiQuality`, `uvDescription`, `generateSummary`, plus locale-free date formatters (`formatLongDate`, `formatShortDate`, `formatIsoDate`) that mirror Python's `strftime("%A, %B %-d")` / `%a %b %-d` / `%Y-%m-%d` without relying on `Intl.DateTimeFormat` (which inserts commas in `en-US` short form). Also exposes `conditionTitle`, `truncateDescription`, `truncateMessage`, and small temperature/UV format helpers.
  - `src/formatters/base.ts` — `BaseFormatter` abstract class providing shared `format()` dispatch and `truncate()` behavior (mirrors `weather/formatters/base.py`).
  - `src/formatters/cli_text.ts` — `CliTextFormatter` with `platform = "text"`; emoji-annotated plain-text reports for terminal display, omitting fields with missing data (matches `weather/formatters/cli_text.py`).
  - `src/formatters/telegram.ts` — `TelegramFormatter` with `platform = "telegram"`; `MDV2_ESCAPE_CHARS` constant copied verbatim from `weather/formatters/telegram.py:15` (`_*[]()~\`>#+-=|{}.!`) and exposed as a `ReadonlySet<string>`; `escapeMdv2()` produces output byte-identical to Python's. Max length 4096.
  - `src/formatters/whatsapp.ts` — `WhatsAppFormatter` with `platform = "whatsapp"`; `*bold*` / `_italic_` syntax, no escaping required, max length 65 536. Preserves the Python asymmetry of omitting the "Data unavailable" air-quality fallback that `telegram.py` has.
  - `src/senders/telegram.ts` — `TelegramSender` with `channel = "telegram"`; uses the runtime's built-in `fetch` with `AbortSignal.timeout(30 s)` for the `POST https://api.telegram.org/bot{token}/sendMessage` call, mirroring the v0.2.0 Python security fix that replaced a `curl` subprocess with `urllib.request`. Supports `chat_id`, `topic_id` (→ `message_thread_id`), and `disable_notification` options; reads `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` from `process.env`; returns `SendResult` with `metadata.chat_id` on success matching Python's shape.
  - `src/types.ts` — added `metadata?: Record<string, unknown>` to `SendResult` for parity with Python's `SendResult.metadata` dataclass field; added `FormatterError` and `SenderError` classes.
  - `src/bootstrap.ts` — wired `buildFormatters()` to register all three formatters unconditionally and `buildSenders()` to register `TelegramSender` only when `TELEGRAM_BOT_TOKEN` is set (mirrors `weather/bootstrap.py:_build_formatters` / `_build_senders` gating).
  - `src/index.ts` — re-exports `CliTextFormatter`, `TelegramFormatter`, `WhatsAppFormatter`, `TelegramSender`, `MDV2_ESCAPE_CHARS`, `escapeMdv2`, `FormatterError`, `SenderError`.
- **Bun CLI + compiled binary** (PRD-002 Phase 6) — single-file `weather` CLI entry point and cross-compiled Linux x86-64 binary distribution:
  - `src/cli.ts` — inline argument parser (zero external deps) implementing the same flags, defaults, and exit codes as `weather/cli.py`: `-l/--location`, `-f/--forecast`, `-d/--days`, `--format {text,telegram,whatsapp,json}`, `--send`, `--chat-id`, `--topic-id`, `--provider`, `-v/--verbose`. Same edge cases: `--send` + `--format json` → exit 2 with stderr error; `--provider <unknown>` → exit 1 listing available providers. JSON output uses a `sortKeys` walker + `JSON.stringify(..., (_k, v) => v instanceof Date ? v.toISOString() : v, 2)` replacer per the PRD "JSON Schema Parity" section; `WeatherCondition` serializes as the underlying snake_case string (e.g. `"sunny"`). `import.meta.main` guard so the file is safe to import without side effects.
  - `package.json` — renamed `build` script output from `weather` to `weather-linux-x64` to avoid colliding with the existing `weather/` Python package directory (the Phase 8 release artifact name is `weather-linux-x64` anyway, so the script now matches it).
  - Verified: `bun build src/cli.ts --compile --target=bun-linux-x64` produces a 90 MB ELF x86-64 executable (well under the 150 MB ceiling), bundling all `weather/data/*.json` via `src/data-loader.ts`. A `bun-darwin-arm64` cross-compile produces a 61 MB Mach-O that runs locally and successfully fetches HKO live data with no network/install dependencies beyond `fetch`.

## [0.2.1] - 2026-04-17

### Fixed

- **CLI entry point** — corrected `pyproject.toml` console script to reference `cli()` instead of `main()`, which requires an `args` parameter. The installed `weather` command now works correctly.

## [0.2.0] - 2026-04-17

### Changed

- **Unified CLI architecture** — CLI now routes through `WeatherSkill` orchestrator instead of a bespoke data path. All 13 providers are accessible from the command line via automatic location routing (previously only HKO worked).
- **Telegram sender security** — replaced `subprocess`/`curl` with `urllib.request`, removing bot token exposure in the process table.
- **CLI flags consolidated** — `--platform` and `--format` merged into a single `--format` flag with choices: `text`, `telegram`, `whatsapp`, `json`.
- **Wind speed unit fix** — corrected `_calculate_feels_like()` which was receiving km/h but expecting m/s, causing incorrect wind chill values.

### Added

- **4 weather providers**: BMKG (Indonesia), DWD (Germany), KMA (South Korea), TMD (Thailand)
- **CliTextFormatter** — plain-text CLI formatter operating on `WeatherData` directly (no dict intermediary)
- **`bootstrap.py`** — `build_default_skill()` factory that wires providers, formatters, and senders based on environment variables
- **29 new tests** (66 total) covering CliTextFormatter, bootstrap, CLI integration, and TelegramSender security
- **`requires-python`** bumped to `>=3.10`

### Removed

- ~300 lines of dead code from `cli.py`: manual dict serialization, HKO-only fetch, curl-based Telegram send, icon-to-condition mapping, PSR conversion

## [0.1.0] - 2026-04-15

### Added
- **9 weather providers** with priority-based automatic selection:
  - HKO (Hong Kong, free, priority 1)
  - SG NEA (Singapore, free, priority 2)
  - JMA (Japan, free, priority 3)
  - CWA (Taiwan, requires API key, priority 4)
  - UK Met Office (United Kingdom, requires API key, priority 5)
  - BOM (Australia, free, priority 6)
  - MetService (New Zealand, free, priority 7)
  - NWS (USA, free, priority 7)
  - OpenWeatherMap (global fallback, requires API key, priority 10)
- **WeatherSkill orchestrator** with provider chain, formatters, and senders
- **Formatters**: Telegram MarkdownV2, WhatsApp
- **Senders**: Telegram Bot API
- **CLI**: `python -m weather.cli` with location, forecast, format, and send options
- **SKILL.md** following the [agentskills.io](https://agentskills.io) open standard
- **Safety guardrails**: read-only default, explicit send intent, no secret logging
- **Location aliases** for 100+ cities across 9 regions (English, Chinese, Japanese)
- **Air quality support**: AQHI (HKO), PSI (SG NEA), AQI (OpenWeatherMap)
- **Feels-like temperature** calculation (heat index + wind chill)
- **17 unit tests** with mocked API responses
