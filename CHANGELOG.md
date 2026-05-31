# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2026-05-30

### Added

- **AGENTS.md** — agent orientation file auto-loaded by pi/CLAUDE.md-aware agents on project entry.

### Changed

- Bumped version to 0.3.0.

## [Unreleased]

### Added

- **Nanshan district (Shenzhen)** (#43) — added `nanshan` to `weather/data/cities/cn.json` with coords (22.5333, 113.9333). Covers the major tech district west of Shenzhen city centre, distinct from the default `shenzhen` coords near Luohu/Futian.
- **Nanshan test coverage** (#43) — added `supportsLocation`/`supports_location` tests for Nanshan in both Bun (`test/providers/open_meteo.test.ts`) and Python (`tests/test_open_meteo.py`).

### Fixed

- **Chongqing longitude** (#43) — corrected from 106.9123 to 106.9233.

- **HKO nighttime icon mappings** (#14) — added 14 nighttime entries (pic70-85 series) to the shared `weather/data/condition_maps/hko-icons.json`. Both Bun and Python runtimes now resolve nighttime icons instead of falling through to `Unknown`.
- **HKO UV index precision** (#15) — both runtimes now preserve the fractional UV value from HKO (e.g. `0.2`) instead of truncating to an integer via `Math.trunc()` / `int(float())`.
- **AQHI wording alignment** (#16) — `aqhiStr` / `aqhi_str` in both runtimes now returns "High Risk" / "Very High Risk" for AQHI 7 and 8-10, matching the Telegram and WhatsApp formatters.

### Added

- **Open-Meteo provider** (`open-meteo`, priority 11) — zero-config global fallback below
  OpenWeatherMap. Free, no API key required. Resolves coordinates from the merged city
  lookup (`cn.json`, `us-nws.json`, `de-dwd.json`, `metoffice.json`). Backed by
  ECMWF/GFS models via `api.open-meteo.com/v1/forecast`. Activates only when all
  higher-priority providers have declined or failed (priority 10 = OWM). Implemented in
  both Bun (`src/providers/open_meteo.ts`) and Python (`weather/providers/open_meteo.py`).
  Registered unconditionally in `buildDefaultSkill()` / `build_default_skill()`. Provider
  count: 13 → 14.
- **`weather/data/cities/cn.json`** — coordinates for 10 major Chinese cities (Beijing,
  Shanghai, Guangzhou, Shenzhen, Chengdu, Hangzhou, Wuhan, Xi'an, Nanjing, Chongqing)
  plus a `"china"` country-level key (→ Beijing). Both runtimes read this file.
- **Chinese city aliases** — 29 new entries in `weather/data/location-aliases.json`
  covering Latin (`sz`, `gz`, `sh`, `bj`, `cn`, full city names), CJK script (e.g. `深圳`,
  `北京`, `中国`), and romanisation variants (`xi'an`). Running `--location sz` now
  resolves to Shenzhen via Open-Meteo.
- **`weather/data/condition_maps/wmo-codes.json`** — WMO 4680 weather code → `WeatherCondition`
  mapping (28 codes, shared by both runtimes).
- **PRD-002b Bun provider parity** — ported the remaining 8 Python-only providers to the Bun/TypeScript runtime, bringing Bun and standalone binaries to the full 13-provider chain:
  - `src/providers/tw_cwa.ts` — Taiwan CWA (key-required, current + 7-day forecast)
  - `src/providers/uk_metoffice.ts` — UK Met Office DataHub (key-required, current + 7-day forecast)
  - `src/providers/au_bom.ts` — Australia BOM (free, current + 7-day forecast)
  - `src/providers/nz_metservice.ts` — New Zealand MetService (free, current observations)
  - `src/providers/id_bmkg.ts` — Indonesia BMKG (free, current + 3-day forecast)
  - `src/providers/de_dwd.ts` — Germany DWD/Bright Sky (free, current + forecast)
  - `src/providers/kr_kma.ts` — South Korea KMA (key-required, current + 3-day forecast)
  - `src/providers/th_tmd.ts` — Thailand TMD (key-required, current + 7-day forecast)
- **Batch-2 Bun fixture tests** — added canned API responses and provider tests for all 8 PRD-002b providers under `fixtures/api-responses/{tw_cwa,uk_metoffice,au_bom,nz_metservice,id_bmkg,de_dwd,kr_kma,th_tmd}/` and `test/providers/*.test.ts`.
- **Bun bootstrap/export coverage** — `buildDefaultSkill()` now registers all free providers by default and registers key-required providers when their environment variables are present (`CWA_API_KEY`, `METOFFICE_API_KEY`, `KMA_SERVICE_KEY`, `TMD_API_TOKEN`, `OPENWEATHERMAP_API_KEY`).

### Changed

- README and `SKILL.md` now document Bun/compiled-binary support for all 13 providers. npm publication remains optional; GitHub release binaries and direct agent-skill installation are the default distribution path.

## [0.1.0-bun] - 2026-05-25

**Cross-runtime release.** Adds a Bun/TypeScript implementation of the weather skill alongside the existing Python package, with a shared JSON data layer, byte-for-byte parity-tested CLI output, and a standalone Linux/macOS binary distribution that needs no runtime install. The Python package itself continues at its own version line; this tag covers the new Bun runtime and the supporting cross-runtime infrastructure produced under PRD-002.

Highlights:

- **`@shrwnsan/weather-skill` Bun package scaffold** — new package metadata/source distribution shape (ESM, Bun ≥ 1.1.30). 5 providers (HKO, JMA, SG NEA, US NWS, OpenWeatherMap), 3 formatters (cli_text, telegram, whatsapp), 1 sender (Telegram via built-in `fetch`). Same `WeatherSkill` orchestrator surface as the Python package. Public npm publication was deferred; direct repository/skill installation and GitHub release binaries are the default distribution paths.
- **Compiled binary** — `weather-linux-x64` (~90 MB) and `weather-darwin-arm64` (~61 MB) built by `bun build --compile`. Bundles the Bun runtime + every shared JSON data file so the binary runs anywhere with `glibc` / arm64 macOS, no `pip install`, no `npm install`.
- **Shared data layer** — all condition maps, location aliases, and city tables moved out of Python source into `weather/data/*.json` so both runtimes consume the same source of truth.
- **Cross-runtime parity gate** — new CI workflow asserts that Python's `weather --format json` output is byte-identical to Bun's for every (provider, mode) pair in the matrix (5 cases today: HKO ×2, JMA current, US NWS ×2). Snapshots committed under `fixtures/parity/`.
- **Python `--format json` wire shape** — normalized via the new public `weather.cli.to_jsonable` helper to match the Bun wire shape (drops `None` fields, UTC `…Z` millisecond ISO datetimes, integral floats → int, `ensure_ascii=False`). **Breaking change** for callers that grepped the previous null-heavy / `+00:00` Python output. The previous shape was never released — it was added under `[Unreleased]` alongside the Bun port and reshaped before the first cross-runtime tag.

Full per-phase detail follows.

### Changed

- **Shared data layer** (PRD-002 Phase 1) — moved all hardcoded condition maps, location aliases, and city tables out of Python source into `weather/data/*.json`. Providers now load via `importlib.resources` so the data ships in the wheel and can be consumed by future runtimes (Bun port). Zero behavioral changes; all 69 tests pass.
- **CLI JSON output** — switched `--format json` to use `sort_keys=True` and ISO-8601 datetime format (T-separated) for deterministic, cross-runtime-friendly output. `WeatherCondition` enum values now serialize as their `.value` (e.g., `"sunny"`) instead of `"WeatherCondition.SUNNY"`.
- **Python `--format json` wire shape now matches Bun** (PRD-002 Phase 7.7) — `weather.cli.to_jsonable` normalizes the dataclass payload before `json.dumps`: drops `None`-valued keys (matches Bun's conditional-spread pattern), renders datetimes as UTC `…Z` with millisecond precision (matches `Date.prototype.toISOString`), renders bare `date` values as midnight-UTC in the same Bun ISO form, and coerces integral `float` values to `int` (Bun's `JSON.stringify` has no float/int distinction). Also passes `ensure_ascii=False` so CJK descriptions (e.g. JMA) emit raw UTF-8 like Bun does. This is what unlocks the byte-for-byte parity gate. **Breaking change for any consumer that grepped the previous null-heavy Python `--format json` output.**

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
- **Parity test fixtures + capture script** (PRD-002 Phase 7.1) — canned HTTP responses for the cross-runtime JSON parity test, plus the script that captures them:
  - `fixtures/api-responses/{hko,jma,sg_nea,us_nws,openweathermap}/` — per-provider directories with a `manifest.json` mapping URLs → relative response filenames and captured live responses for the four free providers (14 response files total: 1 HKO, 2 JMA, 7 SG NEA, 4 US NWS). OpenWeatherMap's manifest uses `<API_KEY>` placeholders; the responses still need capture once a key is available (`needs_capture: true` in the manifest).
  - `fixtures/README.md` — documents the layout, distribution exclusion (not shipped in the wheel or npm package), capture/refresh workflow, manifest format, and when to refresh.
  - `scripts/capture-fixtures.sh` — idempotent bash script that fetches each provider's canonical endpoints with the `WeatherSkill/1.0 (support@weather-skill.io)` User-Agent and pretty-prints the JSON for clean diffs. Sleeps 1 s between SG NEA requests to avoid the data.gov.sg HTTP 429 burst limit. Selective by provider name (e.g. `bash scripts/capture-fixtures.sh hko jma`). Captures the dynamic US NWS chain (`/points` → `observationStations` URL → `/observations/latest` + `/forecast`) by parsing each response with Python.
  - Verified: `python -m build --wheel` produces a wheel that excludes `fixtures/` (only `weather/*` packages listed in `pyproject.toml`); `package.json` `files` whitelist already excludes everything outside `src/` and `weather/data/`, so npm distributions don't ship the fixtures either.
- **Python + Bun test mock infrastructure** (PRD-002 Phase 7.2 + 7.3) — fixture-backed HTTP mocks and frozen-clock helpers so provider/CLI/parity tests can run hermetically against the canned responses from Phase 7.1:
  - `tests/conftest.py` — `mock_http` pytest fixture patches `urllib.request.urlopen` to return a `_FakeResponse(BytesIO(canned_bytes))` for every URL listed across all per-provider `manifest.json` files; OWM `<API_KEY>` placeholders are normalized to `test-key` so the mock matches whatever key the test bootstrap injects. Unknown URLs raise `FileNotFoundError` so accidental network access surfaces immediately. `frozen_clock` fixture uses `freezegun` to pin time to `2026-01-01T00:00:00+00:00` (the PRD-mandated frozen-clock value).
  - `.github/workflows/python-ci.yml` — added `freezegun` to the CI install line so `from freezegun import freeze_time` in `tests/conftest.py` resolves on every Python version in the matrix.
  - `test/setup.ts` — `mockFetch()` / `restoreFetch()` swap `globalThis.fetch` for a fixture-backed replay (same manifest format / `<API_KEY>` normalization as the Python side); `freezeTime()` / `restoreTime()` replace `globalThis.Date` with a subclass that freezes `Date.now()` and parameter-less `new Date()` to the same `2026-01-01T00:00:00.000Z`. Auto-installs the fetch mock via `beforeAll`/`afterAll` hooks under `bunfig.toml`'s `[test] preload`, so every test file sees the mock by default — tests that need real network call `restoreFetch()` explicitly.
  - `test/setup.test.ts` — 8 smoke tests covering HKO / JMA / SG NEA / US NWS fixture replay, 404 for unknown URLs, and `freezeTime` correctness (`Date.now()`, parameter-less `new Date()`, and that explicit `new Date(string)` is still unfrozen so providers can parse `observed_at` timestamps from canned responses).
  - `bunfig.toml` — updated the `[test] preload` comment to reflect that the global fetch mock is now active by default.
  - `fixtures/api-responses/us_nws/manifest.json` + `scripts/capture-fixtures.sh` — fixed the points URL from `40.7128,-74.0060` (literal capture-script string) to `40.7128,-74.006` to match what both Python's `f"{lon}"` and JS template literals actually produce for `-74.006` (the lat/lon in `weather/data/cities/us-nws.json`). Without this both mock infrastructures would 404 every NWS request.
  - Verified: `pytest` 69/69 pass (no regressions; freezegun import resolves locally); `bun test test/setup.test.ts` 8/8 pass; `bun run typecheck` 0 errors.
- **Bun provider tests** (PRD-002 Phase 7.4) — first end-to-end Bun coverage of all five providers, each replaying its canned fixture chain via the `mockFetch` preload from Phase 7.3:
  - `test/providers/hko.test.ts` — 3 tests: alias matching, `getCurrent` (temperature 25.2 / humidity 89 / observed_at 2026-05-18T08:20Z parsed from `hko.BulletinTime`), and 3-day `getForecast` shape + first-day high/low/date. Does not call `freezeTime()` because HKO uses `Date.UTC(y, mo, d, hh, mm)` and the current `freezeTime()` polyfill in `test/setup.ts` mishandles `Date.UTC` calls with fewer than 7 arguments (the override forwards `undefined` for omitted args, which returns `NaN`); all assertions compare against fixture-derived constants rather than wall-clock "now", so freezing isn't required.
  - `test/providers/jma.test.ts` — 3 active + 1 skipped: alias matching, `getCurrent` parsing of short-term `timeSeries` (tempLow=18, tempHigh=29, temperature=23.5, precip=0, overview description present), and weekly `getForecast` (5-day slice, day 0 date 2026-05-17T15:00Z, day 1 tempLow=17 / tempHigh=28 / pops=10). Skipped: `forecast[0] has temp_high / temp_low / precipitation_chance` — scout finding: in the canned `forecast-130000.json` the weekly `tempsMin[0]`/`tempsMax[0]`/`pops[0]` are empty strings (today is covered by the short-term block instead) and `JMAProvider.parseForecast` parses them as `NaN` → `undefined`. Provider not fixed in this task.
  - `test/providers/sg_nea.test.ts` — 2 active + 2 skipped: alias matching, plus an explicit assertion that `getCurrent` currently throws `ProviderError(/NEA API error/)` against the canned fixture. Skipped: `getCurrent parses temperature + humidity` and `getForecast returns 4 days` — scout finding: the live data.gov.sg v2 API now returns `general.forecast` and `forecasts[].forecast` as `{text, code}` objects rather than bare strings; the provider's `textToCondition()` calls `.toLowerCase()` on that and crashes. Provider not fixed in this task.
  - `test/providers/us_nws.test.ts` — 3 tests: alias matching, `getCurrent` parsing the New York `points` → `stations` → `observations/latest` chain (temperature 26.7, humidity 46, condition_raw "Clear" → `Sunny`, observed_at 2026-05-17T23:51Z), and 5-day `getForecast` first-period parsing ("Partly Cloudy" → `PartlyCloudy`, 68 °F → ~20 °C, wind direction SW).
  - `test/providers/openweathermap.test.ts` — 1 active + 2 skipped: instantiation + `supportsLocation` returns true for London/Hong Kong/Tokyo. Skipped: `getCurrent parses London weather fixture` and `getForecast returns N daily entries` — `fixtures/api-responses/openweathermap/manifest.json` has `needs_capture: true`; capturing real responses is blocked on `OPENWEATHERMAP_API_KEY` and `bash scripts/capture-fixtures.sh openweathermap`.
  - Provider bugs surfaced (NOT fixed in this PR — see scout findings above): (a) SG NEA `forecast` object-shape crash, (b) JMA weekly day-0 missing-temp/pops parsing, (c) latent test-infra bug in `freezeTime()` where `Date.UTC` with <7 args returns `NaN` (works around in HKO test by not calling `freezeTime`), (d) US NWS observation parser treats `windSpeed.value` as m/s and multiplies by 3.6, but the canned fixture's `unitCode` is `wmoUnit:km_h-1` — test does not assert the numeric km/h value, only that one is set.
  - Verified: `bun test` → 50/55 pass, 5 skipped (0 failures); `bun run typecheck` → 0 errors; `pytest` → 69/69 pass (no Python regressions).
- **Bun formatter + CLI integration tests** (PRD-002 Phase 7.5 + 7.6) — first end-to-end Bun test coverage of the rendered output and CLI entry point:
  - `test/formatters/fixtures.ts` — shared `fullyPopulatedCurrent` and two-day `forecastDays` `WeatherData` payloads. UTC-midnight forecast dates combined with the `freezeTime()` helper (Thu 2026-01-01T00:00:00Z) give deterministic day-of-week labels (`Fri Jan 2`, `Sat Jan 3`) across runtimes.
  - `test/formatters/cli_text.test.ts` — 4 tests: platform identifier, full-snapshot current + 2-day forecast assertions, and verification that the formatter skips rows whose data is `null`/`undefined` instead of emitting `N/A` placeholders (mirrors `weather/formatters/cli_text.py`).
  - `test/formatters/telegram.test.ts` — 8 tests: platform identifier, full-snapshot current + 2-day forecast, plus a focused suite on `escapeMdv2` that pins the exact 18-char Telegram-reserved set, asserts every reserved char gets a single backslash, leaves non-reserved chars untouched, and documents the (deliberate) lack of idempotency.
  - `test/formatters/whatsapp.test.ts` — 4 tests: platform identifier, full-snapshot current + 2-day forecast, and explicit assertion that no `\` characters appear (mirrors the Python asymmetry — Telegram escapes, WhatsApp doesn't).
  - `test/cli.test.ts` — 10 integration tests driving `src/cli.ts` `run()` directly with `process.stdout/stderr.write` capture: text output for `--location "Hong Kong"`, sorted-key JSON shape + frozen `fetched_at`, JSON-array forecast, `--send --format json` → exit 2, `--provider nonexistent` → exit 1 with sorted-provider list, plus argparse-parity regressions for `--help`, `--days 3.5` (P6-1 strict-int), `--format xml` (invalid choice), and `--bogus` (unknown flag).
  - `test/setup.ts` was already auto-installing the fetch mock at `beforeAll`; the CLI test additionally opts into `freezeTime()` per `beforeEach`/`afterEach` so frozen-clock assertions on `fetched_at` are deterministic without affecting other test files.
  - Verified: `bun test` → 34/34 pass (8 setup + 16 formatter + 10 CLI); `bun run typecheck` → 0 errors; `pytest` → 69/69 pass (no Python regressions).
- **Cross-runtime JSON parity gate** (PRD-002 Phase 7.7) — proves byte-for-byte equality of `--format json` output between the Python and Bun runtimes for every (provider, mode) pair in the parity matrix:
  - `fixtures/parity/<key>.json` — 5 committed snapshots (`hko-current`, `hko-forecast-3`, `jma-current`, `us_nws-current`, `us_nws-forecast-5`). Generated from the Bun runtime (the canonical reference shape per PRD-002).
  - `test/parity.test.ts` — Bun-side gate: builds `WeatherSkill`, fetches via `mockFetch` fixture preload + `freezeTime(2026-01-01T00:00:00.000Z)`, serializes through `toJson` from `src/cli.ts`, asserts byte-equality against the committed snapshot. Honours `UPDATE_PARITY_SNAPSHOTS=1` to refresh.
  - `tests/test_parity.py` — Python-side mirror: same matrix, uses `mock_http` + `frozen_clock` from `conftest.py`, serializes through `weather.cli.to_jsonable` + `json.dumps(sort_keys=True, ensure_ascii=False, indent=2)`, asserts byte-equality against the same snapshot. Honours the same env var.
  - `weather/cli.py:to_jsonable` — the wire-shape normalizer described above; exposed as a public helper so the parity test imports it instead of duplicating logic.
  - `.github/workflows/parity.yml` — new CI workflow running both gates on `push` to `main` + `pull_request`. Bun job uses `oven-sh/setup-bun@v2`; Python job matrices over 3.11 and 3.13. `TZ=UTC` set on both. Either side failing fails the workflow.
  - Coverage matrix: HKO current + forecast (3), JMA current, US NWS current + forecast (5). Deliberate exclusions: **SG NEA** — both runtimes crash on the data.gov.sg v2 `{text, code}` object shape (eval P7.4-4), reinstate after the provider fix lands. **OpenWeatherMap** — fixtures `needs_capture: true`. **JMA forecast** — Bun preserves raw `timeDefines` instant (JST midnight = 15:00Z prior day) while Python's provider calls `.date()` first and stores a logical-day value; a real cross-runtime JMA divergence to fix alongside P7.4-5, not a normalizer issue.
  - Verified: `bun test test/parity.test.ts` → 5/5 pass; `pytest tests/test_parity.py` → 5/5 pass; full `bun test` → 63/68 pass + 5 skipped (0 failures); full `pytest` → 74/74 pass; `bun run typecheck` → 0 errors.
- **Docs + release** (PRD-002 Phase 8) — updated user-facing docs for the cross-runtime release:
  - `SKILL.md` — frontmatter `compatibility:` now lists Python + Bun + compiled binary; providers table gains a `Bun` column marking the 5 Bun-available entries vs the 8 Python-only ones; Integration section adds a Bun/TypeScript snippet (`buildDefaultSkill` + manual provider chain) and a Compiled-binary section; Agent Execution lists all three invocation styles; File Structure expanded to show `src/`, `test/`, `fixtures/`, and the docs/PRD layout.
  - `README.md` — adds a distribution-formats table at the top (Python / Bun / standalone binary), Install section with curl-download commands for the binaries, Bun/TypeScript API examples (matching the Python ones), explicit note on the snake_case-data + camelCase-method interface convention.
  - This `CHANGELOG.md` entry — first cross-runtime tag `[0.1.0-bun] - 2026-05-25`.

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
