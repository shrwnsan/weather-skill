# weather-skill — Agent Guidelines

## Project Overview

A platform-agnostic weather skill for AI agents. Fetches current weather and forecasts from 14 providers, formats output for Telegram / WhatsApp / CLI text, and optionally sends directly to Telegram.

Ships in three byte-identical-output runtimes — **Python**, **Bun/TypeScript**, and **standalone binary**.

## Quick Reference

| Runtime | Entry point | Install / Run |
|---------|-------------|---------------|
| Python 3.10+ (reference) | `weather/cli.py` | `pip install weather-skill` then `weather --location "Hong Kong"` |
| Bun ≥1.1.30 | `src/cli.ts` | `bun run src/cli.ts --location "Hong Kong"` |
| Standalone binary | `weather-linux-x64` / `weather-darwin-arm64` | `./weather-linux-x64 --location "Hong Kong"` |

## File Copy Guide (Agent Local Install)

If your agent copies files to its local workspace instead of using `pip install` or `git clone`, copy **only** the files for your target runtime:

### Python agent

```bash
cp -r weather/ pyproject.toml your-agent-workspace/
```

No other files are needed. The Python package is fully self-contained — all shared JSON data lives inside `weather/data/` and is loaded via `importlib.resources`.

### Bun / TypeScript agent

```bash
cp -r src/ weather/data/ your-agent-workspace/
cp package.json tsconfig.json bunfig.toml bun.lock your-agent-workspace/
```

**⚠️ `weather/data/` is required** — Bun's `src/data-loader.ts` imports from `../weather/data/*.json` at build time. Do NOT omit this directory or the compiled binary will have no city tables, condition maps, or location aliases.

You do **not** need: `weather/*.py`, `weather/providers/`, `weather/formatters/`, `weather/senders/`, `tests/`, `test/`, `fixtures/`, `docs/`.

### Standalone binary agent

No files to copy. Download the binary from [GitHub Releases](https://github.com/shrwnsan/weather-skill/releases) — it bundles the Bun runtime + all `weather/data/*.json`.

```bash
curl -L -o weather https://github.com/shrwnsan/weather-skill/releases/latest/download/weather-linux-x64
chmod +x weather
```

All three produce **byte-identical** `--format json` output for the same input — verified by parity snapshots in CI.

**No external Python dependencies.** Network calls use `urllib.request` + `asyncio.run_in_executor`.

## Testing

```bash
# Python (pytest, all mocked — no network / API keys needed)
python -m pytest tests/ -v

# Bun (bun:test, also mocked)
bun test

# Typecheck TypeScript
bun run typecheck
```

- `tests/` — Python test suite (pytest)
- `test/` — Bun test suite (bun:test)
- `fixtures/api-responses/` — Canned provider responses shared by both suites
- `fixtures/parity/` — Cross-runtime byte-equality snapshots (**do not break these**)

## Key Files & Roles

| File / Directory | Role |
|-----------------|------|
| `weather/` | Python package (reference implementation) |
| `weather/cli.py` | Python CLI entry point |
| `weather/skill.py` | Python `WeatherSkill` orchestrator |
| `weather/models.py` | Data models, location normalization, feels-like calculation |
| `weather/bootstrap.py` | Factory: registers all providers conditionally |
| `weather/data/` | **Shared JSON data** — cities, condition maps, location aliases. Loaded by both runtimes. |
| `weather/providers/` | 14 Python providers |
| `weather/formatters/` | Python formatters (telegram, whatsapp, cli_text) |
| `weather/senders/` | Python senders (telegram) |
| `src/` | Bun/TypeScript package (mirrors `weather/`) |
| `src/cli.ts` | Bun CLI entry point |
| `src/skill.ts` | Bun `WeatherSkill` orchestrator |
| `src/index.ts` | Public package re-exports (`@shrwnsan/weather-skill`) |
| `src/bootstrap.ts` | Factory: `buildDefaultSkill()` |
| `src/data-loader.ts` | JSON-module imports of `weather/data/*` (the cross-runtime bridge) |
| `src/providers/` | 14 Bun provider ports |
| `src/types.ts` | All interfaces: `WeatherData`, `Location`, `SendResult`, etc. |
| `SKILL.md` | Skill definition for agent platforms (triggers, instructions, integration examples) |
| `README.md` | Full documentation (install, providers, output formats, env vars) |
| `CONTRIBUTING.md` | Human contributor guide |
| `pyproject.toml` | Python packaging (`setuptools`, zero dependencies) |
| `package.json` | Bun packaging (`@shrwnsan/weather-skill`, zero dependencies) |

## Providers (14 total)

| # | Provider | File prefix | Coverage | API Key | Priority |
|---|----------|------------|----------|---------|----------|
| 1 | HKO | `hko` | Hong Kong | Free | 1 |
| 2 | SG NEA | `sg_nea` | Singapore | Free | 2 |
| 3 | JMA | `jma` | Japan | Free | 3 |
| 4 | CWA | `tw_cwa` | Taiwan | Required | 4 |
| 5 | UK Met Office | `uk_metoffice` | UK | Required | 5 |
| 6 | BOM | `au_bom` | Australia | Free | 6 |
| 7 | MetService | `nz_metservice` | New Zealand | Free | 7 |
| 8 | NWS | `us_nws` | USA | Free | 7 |
| 9 | BMKG | `id_bmkg` | Indonesia | Free | 8 |
| 10 | DWD | `de_dwd` | Germany | Free | 8 |
| 11 | KMA | `kr_kma` | South Korea | Required | 9 |
| 12 | TMD | `th_tmd` | Thailand | Required | 9 |
| 13 | OpenWeatherMap | `openweathermap` | Global | Required | 10 |
| 14 | Open-Meteo | `open_meteo` | Global | Free | 11 |

Provider selection is automatic by location matching. Falls back down the chain on failure.

## Shared Data Boundary

`weather/data/` is the **critical cross-runtime contract**:
- Python reads it via `weather/data/loader.py`
- Bun reads it via `src/data-loader.ts` (JSON module imports)
- Both runtimes must see the **same** data for parity to hold

**⚠️ When editing files in `weather/data/`, update both `tests/` and `test/` fixtures and regenerate parity snapshots in `fixtures/parity/`.**

## Naming Conventions

| Aspect | Python | Bun / TypeScript |
|--------|--------|-----------------|
| Methods | `get_current()`, `add_provider()` | `getCurrent()`, `addProvider()` |
| Data fields | snake_case (`temp_current`) | snake_case (`temp_current`) — matches Python `dataclasses.asdict()` shape |
| File naming | `sg_nea.py` | `sg_nea.ts` (same prefix) |
| Error classes | PascalCase in `weather/providers/base.py` | PascalCase in `src/types.ts` |
| Condition enum | `weather/models.py` | `src/models.ts` |

## Adding a New Provider

Must be added to **both runtimes** to maintain parity:

1. **Python:** Create `weather/providers/<name>.py` subclassing `WeatherProvider`. Implement `get_current()`, `get_forecast()`, `supports_location()`. Add city/station lookup tables.
2. **Bun:** Create `src/providers/<name>.ts` implementing `IWeatherProvider`. Mirror the Python logic.
3. **Register:** Add imports to both `weather/providers/__init__.py` and `src/index.ts`.
4. **Data:** Add any city/station mappings to `weather/data/cities/` and `weather/data/location-aliases.json`.
5. **Tests:** Add mocked tests in both `tests/` (pytest) and `test/providers/` (bun:test). Add fixture JSON to `fixtures/api-responses/`.
6. **Parity:** Generate/update snapshots in `fixtures/parity/`.
7. **Docs:** Update `SKILL.md`, `README.md`, and this file's provider table.

See any existing provider as a template. `sg_nea` is simple; `jma` is more complex with multi-endpoint fetching.

## Agent Execution Patterns

```bash
# Current weather
python -m weather.cli --location "<location>"
bun run src/cli.ts --location "<location>"
./weather-linux-x64 --location "<location>"

# Forecast
python -m weather.cli --location "<location>" --forecast --days 3
bun run src/cli.ts --location "<location>" --forecast --days 3

# JSON output (for programmatic use)
python -m weather.cli --location "<location>" --format json

# Send to Telegram (requires TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
python -m weather.cli --location "<location>" --format telegram --send
```

## Safety Guardrails

1. Default to read-only weather retrieval.
2. Execute outbound actions (`--send`) only when the user explicitly asks.
3. Confirm destination details if not explicitly provided.
4. Never print, log, or echo secrets (API keys, bot tokens, chat IDs).

## Things to Avoid

- **Do not add third-party Python dependencies.** The project uses only stdlib.
- **Do not modify `weather/data/` without updating both test suites and parity snapshots.**
- **Do not add a provider to only one runtime.** Both Python and Bun must stay in sync.
- **Do not change data field names.** Downstream agents depend on the snake_case JSON shape.
- **Do not commit compiled binaries** (`weather-linux-x64`, etc.) — they are gitignored; built in CI.
