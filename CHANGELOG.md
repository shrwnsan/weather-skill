# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
