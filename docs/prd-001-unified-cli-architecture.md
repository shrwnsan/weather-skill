# PRD-001: Unified CLI Architecture

**Status:** Phase 1 Complete
**Created:** 2026-04-17
**Priority:** High

## Problem Statement

The CLI (`weather/cli.py`) has grown organically into three parallel data paths that bypass `WeatherSkill`, the project's own orchestrator. This causes:

1. **Only HKO works from CLI** — 12 of 13 providers are unreachable. Non-HK locations silently return Hong Kong weather.
2. **`--provider` flag is dead code** — accepted but never read.
3. **Data loss in text output** — `format_text()` looks for dict key `wind_str`, but fetch paths populate `wind`. Wind is silently dropped.
4. **Telegram parse_mode mismatch** — CLI sends with `"Markdown"`, but `TelegramFormatter` outputs MarkdownV2 syntax. Messages render garbled.
5. **Needless WeatherData→dict→WeatherData round-trip** — fields are lost in each conversion.
6. **Security: bot token in process table** — `subprocess.run(["curl", ... url_with_token])` is visible via `ps aux`.

### Current Data Flow (broken)

```
CLI main()
  → fetch_weather()            # hardcodes HKOProvider only
    → WeatherData → dict       # manual, incomplete serialization
      → format_text(dict)      # reads wrong keys, drops fields
      → _dict_to_weather_data  # dict → WeatherData again (telegram only)
        → TelegramFormatter    # outputs MarkdownV2
          → send_telegram()    # sends with parse_mode: Markdown ← mismatch
```

### Target Data Flow (unified)

```
CLI main()
  → build_default_skill()      # registers all available providers + formatters
  → skill.get_current/forecast # provider chain handles location routing
  → skill.format(data, platform)
  → skill.send(message)        # uses TelegramSender (urllib, not curl)
```

## Goals

1. **CLI routes through `WeatherSkill`** — one orchestration path for all platforms.
2. **All 13 providers accessible from CLI** — provider chain handles routing by location.
3. **One formatter per platform, all operating on `WeatherData`** — consistent, extensible, no dict intermediaries.
4. **Security fixes** — remove bot token from process table, fix parse_mode mismatch.
5. **Efficiency fixes** — remove duplicate API calls, fix deprecated asyncio patterns.

## Non-Goals

- Plugin discovery / reflection-based provider registration (premature)
- YAML/JSON config file support (the `_load_config` TODO stays a TODO)
- New providers or new platforms
- Response caching (separate concern, future enhancement)

## Design

### New Files

| File | Purpose |
|------|---------|
| `weather/formatters/cli_text.py` | `CliTextFormatter(WeatherFormatter)` — plain-text output operating on `WeatherData` |
| `weather/bootstrap.py` | `build_default_skill()` — wires providers, formatters, senders based on available env vars |

### Modified Files

| File | Change |
|------|--------|
| `weather/cli.py` | Rewrite `main()` to use `build_default_skill()` → `WeatherSkill`. Delete ~300 lines of dead code: `fetch_weather()`, `_fetch_weather_direct()`, `format_text()`, `_dict_to_weather_data()`, `_hko_icon_to_condition()`, `_text_to_condition()`, `send_telegram()`, `_psr_to_percent()` |
| `weather/senders/telegram.py` | Replace `subprocess`/`curl` with `urllib.request` in `_send_via_json()` |
| `weather/formatters/telegram.py` | Remove duplicate `CONDITION_EMOJI`; import from `models.py` |
| `weather/formatters/whatsapp.py` | Remove duplicate `CONDITION_EMOJI`; import from `models.py` |
| `weather/senders/base.py` | Fix `SendResult.metadata` mutable default |
| `weather/providers/kr_kma.py` | Switch API URL from `http://` to `https://` (if supported) |
| `pyproject.toml` | Bump `requires-python` to `>=3.10` |
| All providers | Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` |

### `build_default_skill()` Behavior

```python
def build_default_skill() -> WeatherSkill:
    skill = WeatherSkill()

    # Always register free providers
    skill.add_provider(HKOProvider())
    skill.add_provider(SGNEAProvider())
    skill.add_provider(JMAProvider())
    skill.add_provider(BOMProvider())
    skill.add_provider(MetServiceProvider())
    skill.add_provider(NWSProvider())
    skill.add_provider(BMKGProvider())
    skill.add_provider(DWDProvider())

    # Register key-required providers when configured
    if os.environ.get("CWA_API_KEY"):
        skill.add_provider(CWAProvider())
    if os.environ.get("METOFFICE_API_KEY"):
        skill.add_provider(UKMetOfficeProvider())
    if os.environ.get("KMA_SERVICE_KEY"):
        skill.add_provider(KMAProvider())
    if os.environ.get("TMD_API_TOKEN"):
        skill.add_provider(TMDProvider())
    if os.environ.get("OPENWEATHERMAP_API_KEY"):
        skill.add_provider(OpenWeatherMapProvider(
            api_key=os.environ["OPENWEATHERMAP_API_KEY"]
        ))

    # Formatters
    skill.add_formatter("text", CliTextFormatter())
    skill.add_formatter("telegram", TelegramFormatter())
    skill.add_formatter("whatsapp", WhatsAppFormatter())

    # Senders (only when configured)
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        skill.add_sender("telegram", TelegramSender())

    return skill
```

### `CliTextFormatter` Output

Same visual style as current `format_text()` but reading from `WeatherData` properties:

```
🌤️ Weather for Tokyo
🌡️ Temperature: 22°C
   Feels like: 24°C
   Range: 18° - 26°
💧 Humidity: 65%
💨 Wind: NE 12 km/h
🌧️ Rain chance: 30%
☀️ UV Index: 6
🌫️ AQHI: 3 (Low)
📍 Provider: jma
```

### CLI `main()` Rewrite (simplified)

```python
async def main(args):
    skill = build_default_skill()

    provider_name = None if args.provider == "auto" else args.provider

    if args.forecast:
        data = await skill.get_forecast(args.location, args.days, provider_name)
    else:
        data = await skill.get_current(args.location, provider_name)

    if args.format == "json":
        print(json.dumps(asdict(data) if not isinstance(data, list)
              else [asdict(d) for d in data], indent=2, default=str))
        return 0

    message = skill.format(data, platform=args.platform)

    if args.send:
        result = await skill.send(message, channel="telegram",
                                  chat_id=args.chat_id, topic_id=args.topic_id)
        ...
    else:
        print(message)
        return 0
```

## Success Criteria

- [x] `weather --location Tokyo` returns JMA data (not HKO) — verified via provider chain
- [x] `weather --location "New York"` returns NWS data — verified via provider chain
- [ ] `weather --location Singapore --format telegram --send` uses MarkdownV2 consistently — blocked by pre-existing SG NEA provider bug
- [x] `ps aux | grep curl` shows no bot token during sends — TelegramSender now uses urllib
- [x] All existing tests pass — 37/37 pass
- [x] `--provider hko` forces HKO; `--provider auto` uses chain — `--provider` accepts any name, no `choices` restriction

## Phases

| Phase | Scope | Description | Status |
|-------|-------|-------------|--------|
| **1** | Unify CLI | `CliTextFormatter` + `bootstrap.py` + rewrite `cli.py` | Done |
| **2** | Security | Replace curl with urllib in sender, fix parse_mode, remove hardcoded chat ID | In progress (Task 1.3 done early; 2.1, 2.2 remaining) |
| **3** | Efficiency | Fix deprecated asyncio, dedupe emoji maps, fix metadata default, bump Python version | Not started |
| **4** | Cleanup | Delete leftover dead code, update docs, update SKILL.md provider list | Not started |

### Phase 1 Implementation Notes

- Task 1.3 (TelegramSender urllib fix) was pulled into Phase 1 ahead of schedule since the CLI rewrite deleted the duplicate `send_telegram()` in `cli.py`
- `--platform` and `--format` flags were collapsed into a single `--format` flag with choices: `text|telegram|whatsapp|json`
- `bootstrap.py` uses explicit `from .providers.xxx import` instead of `__import__` (the latter failed with relative paths)
- cli.py reduced from 575 to 110 lines

See `docs/tasks-001-prd-001-unified-cli-architecture.md` for detailed task breakdown.
