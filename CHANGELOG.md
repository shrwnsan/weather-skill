# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
