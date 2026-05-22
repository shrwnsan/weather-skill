# Eval-001: PRD-002 Phase 0 + Phase 1 + Phase 2 + Phase 3 + Phase 5 + Phase 6 + Phase 7.4 + Phase 7.5 + Phase 7.6 Review

**Reviewed commits:**
- `67a78b6` — docs(prd-002): finalize PRD with Phase-0 decisions and add tasks file
- `fd1d52c` — feat(prd-002 phase 1): extract shared data layer to weather/data/
- `807e1fb` — feat(prd-002 phase 2): Bun/TypeScript scaffold + core types
- `1eba637` — feat(prd-002 phase 3): port batch-1 providers + OWM to Bun
- `b3c138e` — feat(prd-002 phase 5): port formatters + Telegram sender to Bun
- `02421e1` — feat(prd-002 phase 6): add Bun CLI + cross-compiled binary
- `120c82a` — feat(prd-002 phase 7.5+7.6): add formatter + CLI integration tests
- `528c4c0` — feat(prd-002 phase 7.4): add Bun provider tests for all 5 providers

**Date:** 2026-05-13 (updated 2026-05-23)
**Status:** Open

---

## Commit 67a78b6 (Docs)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| D-1 | Medium | Effort estimate contradiction — scope table says v0.1 ETA "~15h" but detailed estimate mid-points ~25h. Commit message says "re-baseline to ~25h" but scope table wasn't updated. | Open |
| D-2 | Medium | Directory naming inconsistency within the PRD — repo structure tree (L88) says `condition-maps/` (hyphen) but `importlib.resources` code example (L212) references `weather.data.condition_maps` (underscore). | Open |
| D-3 | Medium | Repository structure (L125-138) lists all 13 Bun providers without marking the 8 batch-2 providers as deferred. Contradicts scope section. | Open |
| D-4 | Low | Missing Phase 4 note in dependency graph — jumps from Phase 3 to Phase 5 with no comment. | Open |
| D-5 | Low | Task 1.9 assumes a single `kma-conditions.json` but the actual provider has two maps (PTY + sky). Task spec didn't anticipate the split. | Open |

## Commit fd1d52c (Phase 1 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| I-1 | Medium | `scripts/extract_data.py` and `scripts/refactor_providers.py` reference `condition-maps/` (hyphen) but the actual directory is `condition_maps/` (underscore). Scripts are explicitly kept for PRD-002b re-extraction and will fail if re-run. | Open |
| I-2 | Medium | Float trailing zeros lost in city coordinate JSON — e.g. `(-74.0060, -112.0740)` becomes `[-74.006, -112.074]`. No runtime impact but canonical data loses precision signaling. Affects `us-nws.json` and `metoffice.json`. | Open |
| I-3 | Low | CI wheel smoke test threshold is `>= 18` but 21 JSON files exist. Up to 3 files could disappear without CI catching it. Should be `>= 21`. File: `.github/workflows/python-ci.yml:44`. | Open |
| I-4 | Low | `weather/data/cities/metoffice.json` was extracted but `uk_metoffice.py` still hardcodes `UK_CITIES`. Dead data file in Python — either load it or remove it. **Bun side resolved**: Phase 2 imports it as `METOFFICE_CITIES` in `src/data-loader.ts`. | Partial |
| I-5 | Low | `weather/data/weather-conditions.json` exists but no Python code loads it at runtime. **Bun side resolved**: Phase 2 imports it to build `VALID_CONDITION_VALUES` for `toCondition()` in `src/data-loader.ts`. | Partial |
| I-6 | Low | `cli.py:137` uses duck-typing (`hasattr(o, "value") and hasattr(type(o), "__members__")`) instead of `isinstance(o, enum.Enum)` for enum serialization. Works but fragile. | Open |
| I-7 | Low | `models.py:36` — `from .data.loader import load_json` appears mid-file (after enum def). Works (avoids circular dependency) but deserves a comment explaining why. | Open |

## Commit 807e1fb (Phase 2 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P2-1 | High | `makeWeatherData` in `src/models.ts` does not set `condition_raw: ""` default. Python's dataclass always has `condition_raw` (defaults to `""`). Missing default means Bun providers that don't explicitly set it will omit the key from JSON output, breaking cross-runtime parity tests. | Fixed |
| P2-2 | High | `condition_raw` is optional (`string?`) in `src/types.ts:74` but required with default `""` in Python's `weather/models.py:70`. `JSON.stringify` omits `undefined` values, so the serialized JSON diverges from Python's `dataclasses.asdict()` which always includes `condition_raw: ""`. | Fixed |
| P2-3 | Medium | `tsconfig.json` uses `"types": ["bun"]` (resolves to `@types/bun`) but task 2.1 spec says `"types": ["bun-types"]`. The newer `"bun"` convention is correct for Bun 1.1.30+ — update the task spec to match. | Open |
| P2-4 | Medium | `Math.round` in `src/models.ts` (tempRangeStr, windStr) uses "round half up" while Python's `:.0f` uses banker's rounding (round half to even). E.g. `Math.round(0.5)` = 1 vs Python `f"{0.5:.0f}"` = "0". Negligible for weather data but could cause edge-case snapshot test failures. | Open |
| P2-5 | Low | `bunfig.toml` references `./test/setup.ts` which doesn't exist yet (Phase 7). Comment explains the situation but a TODO link to task 7.3 would improve traceability. | Open |

## Commit 1eba637 (Phase 3 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P3-1 | **High** | `parseLocation` in `src/models.ts` does not apply `normalizeLocation` / `LOCATION_ALIASES`. Python's `WeatherSkill.parse_location()` resolves aliases (e.g. "hk" -> "hong kong", "nyc" -> "new york") before passing to providers. The TS version just does `raw.toLowerCase().trim()`, so alias-based queries fail in Bun. Affects every provider. | ✅ Fixed |
| P3-2 | **High** | `hko.ts` declares `supportsAirQuality = true` but never populates the `aqhi` field from the HKO API response. Python has the same declaration gap, so this is parity-preserving — but the flag misleads downstream consumers. | Deferred (parity-preserving — needs cross-runtime fix) |
| P3-3 | Medium | `us_nws.ts:263-266` — forecast date deduplication uses `toISOString().slice(0,10)` which converts to UTC. For US western time zones near midnight, a period like `2026-05-13T23:00:00-04:00` becomes `2026-05-14` in UTC, misassigning the forecast day. Python uses `.date()` which preserves the local date from the ISO offset. | ✅ Fixed |
| P3-4 | Medium | `openweathermap.ts` stores `wind_speed` as m/s (raw OWM value) to match Python parity, but `WeatherData.wind_speed` is documented as `// km/h` in both `types.ts:66` and `models.py:61`. The `windStr()` helper formats with "km/h" units, producing incorrect output for OWM-sourced data. | Deferred (intentional Python parity quirk — coordinate fix in PRD-002b or follow-up Python PR) |
| P3-5 | Medium | `jma.ts:53` — `supportsLocation` only checks `JMA_AREA_CODES` keys. Python includes Japanese locale names ("日本", "東京", etc.) via an explicit set union. If `jma-area-codes.json` lacks Japanese keys, Japanese-language queries will fail in Bun. | ✅ Fixed |
| P3-6 | Low | `hko.ts:157-163` — `observedAt` constructed as UTC (`Date.UTC(...)`) while Python parses `BulletinTime` as a naive datetime (implicitly HKT, UTC+8). Results in 8-hour offset. | Deferred to Phase 7 (cross-runtime TZ normalization) |
| P3-7 | Low | `jma.ts:79` — `getForecast` defaults to `days=3` while Python defaults to `days=7`. JMA API supports 7-day forecasts. | ✅ Fixed |
| P3-8 | Low | `sg_nea.ts:239-245` — `forecast_date` parsed via `new Date(dateStr)` (UTC midnight) vs Python's `datetime.strptime(date_str, "%Y-%m-%d").date()` (naive date). Minor timezone ambiguity. | Deferred to Phase 7 (cross-runtime date-vs-datetime normalization) |
| P3-9 | Low | `skill.ts:176-191` — `formatSimple` fallback omits humidity, wind, and emoji compared to Python's `_format_simple`. Simplified but less informative when no formatter is registered. | ✅ Fixed |

**Verified correct in Phase 3:**
- All providers set `condition_raw` to a string (defaults to `""` when unavailable) — P2-1/P2-2 fix confirmed in practice
- All providers use conditional-spread pattern for optional fields (`...(v != null ? { f: v } : {})`)
- All providers re-throw `LocationNotSupportedError` and wrap other errors with `ProviderError`
- HKO icon mapping, PSR rain probability, HTML stripping match Python
- JMA dual-endpoint parallel fetch via `Promise.all`, 3-level timeSeries traversal
- SG NEA partial-failure-tolerant parallel fetch via `fetchJsonSafe`, PSI extraction
- NWS User-Agent header (`WeatherSkill/1.0 (support@weather-skill.io)`) — avoids 403
- NWS `degToDirection` correctly handles negative degrees with `(index + 16) % 16`
- NWS F->C, m/s->km/h, Pa->hPa, m->km conversions all match Python
- OWM `q=` query, `units=metric`, forecast aggregation via `mostCommon`, AQI 1-5 scale
- Bootstrap registers HKO/SGNEA/JMA/NWS unconditionally, OWM conditionally on API key
- Priority sorting handled by `WeatherSkill` constructor

## Commit b3c138e (Phase 5 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P5-1 | Medium | `formatLongDate` in `src/utils.ts:75` uses `Date.getDay()` / `Date.getMonth()` / `Date.getDate()` which return **local-timezone** values. If a `Date` object was constructed from UTC (e.g. `new Date("2026-05-16T00:00:00Z")`), `formatLongDate` will render it in the local timezone (e.g. "Friday, May 16" in UTC-4 but "Saturday, May 16" in UTC+8). Python's `strftime` on a `date` object has no timezone at all — it just formats the date fields. For parity, callers must ensure `Date` objects are either naive-local or that the UTC→local conversion is intentional. No runtime bug today because all callers pass `forecast_date` / `observed_at` which are constructed from local-timezone sources in providers, but this is a latent foot-gun. | Deferred to Phase 7 (rolls up with the cross-runtime TZ normalization tracked in P3-6 / P3-8) |
| P5-2 | Medium | `truncateDescription` in `src/utils.ts:281` checks `firstSentenceEnd > 0` but Python's `desc.find('. ')` returns the index of the period. If the description starts with ". " (index 0), Python includes it (0 < 120 → true, slice to 1) while TS skips it (0 is not > 0). Edge-case only — unlikely in real weather descriptions. | Not a bug — Python uses `> 0` too (`weather/formatters/telegram.py:104`, `whatsapp.py:83`). Both runtimes skip index 0. Verified by grep. |
| P5-3 | Medium | `TelegramFormatter.formatCurrent` (`src/formatters/telegram.ts:115-125`) checks `if (wind || data.wind_speed != null)` but `wind` is assigned from `data.wind_description ?? null`. If `data.wind_description` is an empty string `""`, JS truthiness makes `wind` falsy, falling through to the `wind_speed` branch — which is correct parity with Python's `data.wind_str and data.wind_str != "N/A"` (empty string is falsy in Python too). However, the TS code also does `data.wind_speed as number` on line 122 without a runtime guard — if `wind_speed` is `undefined` and `wind_description` is `""`, we'd hit `Math.round(undefined)` → `NaN`. This can't happen in practice because the outer `if` ensures at least one of `wind` or `wind_speed` is truthy/non-null, but the `as number` cast bypasses type-safety silently. | Acknowledged — outer guard makes `NaN` unreachable. Telegram branch simplified to match the WhatsApp pattern in the P5-8 fix; the cast remains intentional with the guard documented. |
| P5-4 | Low | `roundTemp` in `src/utils.ts:247` is exported but unused by any current consumer — formatters use `Math.round` directly via `formatTempC` / `formatTempBare`. Dead export. | ✅ Fixed — removed dead export. |
| P5-5 | Low | `SendResult` in `src/types.ts` added `metadata?: Record<string, unknown>` but Python's `SendResult` dataclass also has `__bool__` returning `self.success`. TS `SendResult` has no equivalent — callers must check `.success` explicitly. Not a parity bug (TS convention), but worth noting for anyone comparing structs. | WontFix — JS has no equivalent of `__bool__`; `.success` is the idiomatic check. Already documented in the interface JSDoc. |
| P5-6 | Low | `TelegramSender` in `src/senders/telegram.ts` does not implement `send_with_retry` (Python's `WeatherSender.send_with_retry` in `base.py`). Not required for v0.1 parity (Python's `TelegramSender` doesn't override it either — it inherits the default), but the base-class retry helper is absent on the TS side entirely. | WontFix — Python's `send_with_retry` has zero callers in the codebase (verified via grep). Adding it on the TS side is YAGNI. Reopen if a real consumer appears. |
| P5-7 | Low | `CliTextFormatter.formatForecast` (`src/formatters/cli_text.ts:89-91`) uses `day.description || day.condition_raw || day.condition` for the condition text. Python uses `day.description or day.condition_raw or str(day.condition.value)`. The TS version falls through to `day.condition` which is the enum **value** (e.g. `"partly_cloudy"`) while Python gets `"Partly Cloudy"` via `.value.title()`. This means the CLI text forecast falls through to a snake_case string when both `description` and `condition_raw` are absent, while Python would show a title-cased version. Minor cosmetic divergence. | Not a bug — Python is `str(day.condition.value)`, not `.value.title()`. `WeatherCondition.PARTLY_CLOUDY.value` is `"partly_cloudy"` and `str(...)` keeps it as-is. TS `day.condition` is the same snake_case enum value. Output is byte-identical. |
| P5-8 | Low | `WhatsAppFormatter.formatCurrent` (`src/formatters/whatsapp.ts:80-86`) checks `if (data.wind_description || data.wind_speed != null)` but Python's whatsapp.py checks `if data.wind_str and data.wind_str != "N/A"`. The TS version doesn't filter out "N/A" wind strings — it only checks `wind_description` (which maps to `wind_str` in Python). If `wind_description` is `"N/A"` somehow, TS would render `"💨 Wind: N/A"` while Python would skip the line. Actual risk is near-zero because `wind_description` comes from provider-processed data, not `windStr()`. | ✅ Fixed — added defensive `w !== "N/A"` filter to both WhatsApp and Telegram formatters for symmetric parity. |

**Verified correct in Phase 5:**
- `MDV2_ESCAPE_CHARS` character set matches Python's `r'_*[]()~`>#+-=|{}.!'` exactly — verified char-by-char
- `escapeMdv2()` iterates character-by-character with `Set.has()` lookup — byte-identical behavior to Python's `for char in text: if char in MDV2_ESCAPE_CHARS`
- All three formatters' `platform` strings ("text", "telegram", "whatsapp") match Python
- `BaseFormatter` abstract class mirrors `WeatherFormatter` ABC: `format()` dispatches on `Array.isArray(data)`, `truncate()` uses same logic
- `TelegramFormatter.formatCurrent` matches Python's escaping placement: location, date, description/condition, wind, AQ quality, UV desc, sunrise/sunset, summary — all escaped
- `TelegramFormatter.formatCurrent` AQ fallback `🌬️ Air Quality: Data unavailable` matches Python when both `aqhi` and `aqi` are null — WhatsApp correctly omits this fallback (parity-preserving asymmetry)
- `WhatsAppFormatter` uses `*bold*` and `_italic_` syntax with no escaping — matches Python
- `generateSummary` condition map (`CONDITION_SKY`) matches Python's `condition_desc` dict entry-for-entry
- `generateSummary` activity suggestion chain (wet → sunny+hot → humid) matches Python's if/elif order
- `aqhiQuality`, `aqiQuality`, `uvDescription` thresholds all match Python helpers exactly
- `conditionTitle` splits on `_` and title-cases each word — matches `condition.value.title()`
- `truncateDescription` first-sentence / 117+3 truncation logic matches Python's inline pattern
- `truncateMessage` mirrors `WeatherFormatter.truncate()` in `base.py`
- Date formatting: `formatLongDate`, `formatShortDate`, `formatIsoDate` use lookup tables to avoid `Intl.DateTimeFormat` — correct approach
- `TelegramSender` uses `fetch` + `AbortSignal.timeout(30s)` — no subprocess/shell-out, matching Python's urllib migration
- `TelegramSender` constructor token resolution: `init.bot_token ?? process.env.TELEGRAM_BOT_TOKEN` — matches Python's `bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")`
- `TelegramSender.send` payload construction uses conditional spread (`...(topicId != null ? { message_thread_id: topicId } : {})`) — matches Python's conditional `if topic_id: payload["message_thread_id"] = topic_id`
- `TelegramSender.send` success path returns `metadata: { chat_id: chatId }` — matches Python's `metadata={"chat_id": target_chat}`
- `TelegramSender.send` error paths: no chat_id, HTTP error, generic exception — all match Python's error returns
- `SendResult.metadata` field matches Python's `SendResult.metadata` dataclass field
- `FormatterError` and `SenderError` classes match Python's counterparts
- `buildFormatters()` registers all three formatters unconditionally — matches Python's `_build_formatters()`
- `buildSenders()` registers Telegram only when `TELEGRAM_BOT_TOKEN` is set — matches Python's `_build_senders()`
- `src/index.ts` re-exports all new public symbols
- `bun run typecheck` → 0 errors
- `pytest` → 69/69 pass (zero regressions)

## Commit 02421e1 (Phase 6 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P6-1 | Medium | `parseInt` in `parseArgs` silently truncates floats (e.g. `--days=3.5` → `3`). Python's `argparse` with `type=int` rejects `"3.5"` with an error. Minor behavioral divergence — negligible for real CLI usage but fails strict parity if tested. | Fixed in `src/cli.ts` — added `parseStrictInt` helper that pre-validates with `/^-?\d+$/` before calling `parseInt`. Now `--days 3.5` errors with `argument --days: invalid int value: '3.5'`, matching Python's argparse message style. Applied to `--days` and `--topic-id`. |
| P6-2 | Low | `--days=0` and `--days=-1` are accepted without validation. Python accepts them too (`argparse` doesn't range-check `type=int` by default). Parity-preserving, but negative days is semantically wrong for both runtimes. | WontFix (parity-preserving) — would diverge from Python. If we want a range check it has to land on both runtimes simultaneously, otherwise the parity test fails. |
| P6-3 | Low | `run()` catch block references `args.verbose` (L263) but `args` is only assigned inside the try block after the `_help` early return. If `parseArgs` succeeds but a later line throws, `args` is in scope. However, if `parseArgs` itself threw, `args` would be undefined on L263 — but the outer catch on L196-200 returns before reaching L263, so this is unreachable. No bug. | Acknowledged — reviewer self-resolved. The early `parseArgs` catch returns before the inner try, so `args` is always assigned when the inner catch runs. No code change. |
| P6-4 | Low | `build` script output renamed from `weather` to `weather-linux-x64`. This avoids colliding with the `weather/` Python package directory, which is the right call. However, the task spec (6.2) still references `--outfile weather` and `./weather --location`. Doc/spec should be updated to match. | Fixed in `docs/tasks-002-prd-002-bun-runtime-support.md` — Task 6.2 now references `--outfile weather-linux-x64` and `./weather-linux-x64` consistently, with a parenthetical noting the directory-collision rationale. |

**Verified correct in Phase 6:**
- `parseArgs` handles all 9 flags: `-l/--location`, `-f/--forecast`, `-d/--days`, `--format {text,telegram,whatsapp,json}`, `--send`, `--chat-id`, `--topic-id`, `--provider`, `-v/--verbose`, `-h/--help`
- Both `--flag value` and `--flag=value` forms supported
- Exit codes match Python: 0 (success), 1 (error), 2 (`--send` + `--format json`)
- `--provider <unknown>` lists available providers sorted alphabetically and exits 1 — matches Python's `NoProviderError` behavior
- `--format` validates against the same 4 choices as Python's `argparse choices=["text","telegram","whatsapp","json"]`
- `sortKeys` recursively sorts object keys for deterministic JSON — matches Python's `json.dumps(..., sort_keys=True)`
- `toJson` replacer handles `Date` via `toISOString()` — matches Python's `hasattr(o, "isoformat")` → `.isoformat()`
- TS enums serialize as their string values (e.g. `WeatherCondition.Sunny` → `"sunny"`) — verified via `bun -e` test. Matches Python's enum `.value` serialization.
- `import.meta.main` guard prevents side effects on import — correct for a dual-purpose module (importable + executable)
- `run()` returns exit code (doesn't call `process.exit` directly) — testable from unit tests
- `package.json` build script uses `--target=bun-linux-x64` for NanoClaw compatibility; output renamed to `weather-linux-x64`
- Binary size: 90 MB Linux x64, 61 MB Darwin arm64 — both well under 150 MB ceiling

## Commit 528c4c0 (Phase 7.4 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P7.4-1 | Medium | SG NEA `getCurrent` error-path test regex `/NEA API error/` is overly broad — it matches any `ProviderError` from that provider, not specifically the `{text, code}` object-shape crash. A stronger assertion would verify both the wrapper message and the inner error cause (e.g. `TypeError` from `.toLowerCase()` on a non-string). File: `test/providers/sg_nea.test.ts:37`. | Open |
| P7.4-2 | Medium | NWS `getCurrent` test asserts `typeof result.wind_speed === "number"` but does not pin the actual value, despite having deterministic fixture data (`windSpeed.value = 5.4`). The NWS provider treats this as m/s and multiplies by 3.6, but the fixture's `unitCode` is `wmoUnit:km_h-1` (km/h). The comment says "documented separately" but there is no inline TODO or issue reference tracking this latent unit-mismatch bug. File: `test/providers/us_nws.test.ts:46-49`. | Open — relates to P3-4 wind-unit mismatch batch |
| P7.4-3 | Medium | `test/setup.ts` `freezeTime()` overrides `Date.UTC` but the `FrozenDate.UTC` implementation forwards `undefined` for omitted args when called with fewer than 7 parameters, causing `Date.UTC(y, mo, d, hh, mm)` to return `NaN`. HKO test works around by not calling `freezeTime()` at all and using fixture-derived constants instead. This bug will bite any future test that uses `freezeTime` + a provider that calls `Date.UTC` with partial args. File: `test/setup.ts:125-135`. | Open |
| P7.4-4 | Medium | SG NEA live API schema change — `general.forecast` and `forecasts[].forecast` now return `{text, code}` objects instead of bare strings. The provider's `textToCondition()` calls `.toLowerCase()` on the value, which throws on an object. This is a **provider bug** (not just a test issue), affecting both `getCurrent` and `getForecast` against real data. Mirrors a latent Python-side bug in `weather/providers/sg_nea.py`. The test correctly captures the failure mode with `rejects.toThrow(/NEA API error/)`. Files: `src/providers/sg_nea.ts:90`, `test/providers/sg_nea.test.ts:37`. | Deferred — provider fix batched for follow-up |
| P7.4-5 | Medium | JMA weekly forecast day-0 has missing `temp_high`/`temp_low`/`precipitation_chance` — the canned `forecast-130000.json` has empty strings for `tempsMin[0]`/`tempsMax[0]`/`pops[0]` (today is covered by the short-term block). The provider parses these as `NaN` → `undefined`. The test is correctly skipped with a `test.skip` documenting the scout finding. The provider should fall back to the short-term block for day 0. File: `test/providers/jma.test.ts:75-85`. | Deferred — provider fix batched for follow-up |
| P7.4-6 | Low | HKO and NWS `condition` assertions use `not.toBe(WeatherCondition.Unknown)` instead of asserting the specific mapped condition. For fixture-replay tests, asserting the exact `WeatherCondition` value would confirm the icon/weather-code mapping is correct, not just that a mapping exists. Files: `test/providers/hko.test.ts:42,61`, `test/providers/us_nws.test.ts:41`. | Open |
| P7.4-7 | Low | OpenWeatherMap test file has zero fixture-replay coverage — only tests constructor and `supportsLocation`. The 2 skipped tests are blocked on fixture capture (`needs_capture: true` in manifest). Consider whether this file should have been deferred entirely until fixtures are captured, since it adds no integration coverage. File: `test/providers/openweathermap.test.ts`. | Acknowledged — file is scaffolding for when fixtures land |
| P7.4-8 | Low | NWS `getForecast` test uses `toBeCloseTo((68 - 32) * 5 / 9, 5)` for `temp_low` but `(68 - 32) * 5 / 9 = 20.0` is an exact integer in IEEE 754. `toBe(20)` would be clearer and equally correct. Style nit only. File: `test/providers/us_nws.test.ts:65`. | WontFix — style preference, assertion is correct |
| P7.4-9 | Low | No provider test file verifies the `LocationNotSupportedError` throw path for `getCurrent()`/`getForecast()` with an unsupported location. The `supportsLocation` tests check `false` is returned, but the throw guard in each provider's `getCurrent` (e.g. HKO L59-63) is untested. Low priority since the guard is a simple `if (!supports) throw`. | Open |

**Verified correct in Phase 7.4:**
- All 12 active tests pass against fixture data; 5 skipped tests have valid, well-documented reasons
- HKO: alias matching (`"Hong Kong"`, `"hk"`, `"Paris"`), `getCurrent` field assertions (temperature 25.2, humidity 89, `observed_at` 2026-05-18T08:20Z from `BulletinTime`), 3-day `getForecast` shape + first-day high/low/date
- JMA: Japanese locale alias (`"東京"`), `getCurrent` short-term parsing (tempLow=18, tempHigh=29, temperature=23.5 derived average, precip=0, overview description present), weekly `getForecast` 5-day cap with day 1 verified (tempLow=17, tempHigh=28, pops=10)
- SG NEA: alias matching (`"Singapore"`, `"sg"`, `"Bangkok"`), `getCurrent` error-path assertion (`rejects.toThrow(/NEA API error/)`) correctly captures the `{text, code}` object-shape crash
- NWS: alias matching (`"New York"`, `"Chicago"`, `"Hong Kong"`), `getCurrent` observation chain (temperature 26.7, humidity 46, `condition_raw "Clear"` → `WeatherCondition.Sunny`, `observed_at` 2026-05-17T23:51Z), 5-day `getForecast` first-period parsing (`PartlyCloudy`, F→C conversion, wind direction SW)
- OWM: instantiation + `supportsLocation` returns `true` for London/Hong Kong/Tokyo
- All tests use `mockFetch` preload from Phase 7.3 — no live network calls
- `bun test` → 50 pass / 5 skip / 0 fail (169 expects across 10 files)
- `bun run typecheck` → 0 errors
- `pytest` → 69/69 pass (no Python regressions)
- CHANGELOG.md entry is thorough and accurate
- tasks-002 marks Task 7.4 ✅

## Commit 120c82a (Phase 7.5 + 7.6 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P7.5-1 | Low | `escapeMdv2` test `"never double-escapes"` name is misleading — the test body documents that double-escaping **does** happen (`twice !== once`) and the comment explains why. The test name says the opposite of what it proves. Should be renamed to `"double-escape documents non-idempotency"` or similar. | Fixed — test renamed to `double-escape documents non-idempotency (P7.5-1)` in `test/formatters/telegram.test.ts`; comment updated to state `escapeMdv2` is intentionally non-idempotent. |
| P7.5-2 | Low | `test/formatters/fixtures.ts` — `fullyPopulatedCurrent` does not include `sunrise`/`sunset` fields, so the Telegram and WhatsApp snapshot tests never exercise the astro line (`🌅 Sunrise: ... | 🌇 Sunset: ...`). A second fixture with astro data would close the gap. | Fixed — added `sunrise: "06:30"` / `sunset: "19:45"` to `fullyPopulatedCurrent`; Telegram and WhatsApp full-current snapshots now assert the astro line. |
| P7.5-3 | Low | `test/formatters/fixtures.ts` — no fixture exercises the `aqi` (non-AQHI) air quality branch. Both formatters have `else if (data.aqi != null)` paths that render "AQI" instead of "AQHI" — these are untested. | Fixed — added `aqiOnlyCurrent` fixture (Beijing, `aqi: 180`); Telegram and WhatsApp now have dedicated AQI-branch tests asserting `AQI 180` rendering. |
| P7.6-1 | Low | `test/cli.test.ts:29-49` — `captureIO()` monkey-patches `process.stdout.write` / `process.stderr.write`. If a test throws before `io.restore()` runs, the real streams remain patched. The `afterEach` calls `io.restore()`, so in practice Bun's test runner always calls `afterEach`, but using a `try/finally` in the capture wrapper would be more defensive. | Acknowledged — Bun's test runner guarantees `afterEach` execution. No code change needed. |
| P7.6-2 | Medium | `test/cli.test.ts` — all 10 CLI tests target the Hong Kong location (default + explicit). No test exercises location aliases (`"hk"`, `"nyc"`) or non-default providers. The alias fix from P3-1 is untested at the CLI level. While `parseLocation` alias resolution is tested at the model level, a CLI integration test for `"hk" → "Hong Kong"` would guard against future regressions in the `buildDefaultSkill` → `getCurrent` pipeline. | Fixed — added two tests in `test/cli.test.ts`: alias `--location hk` resolves to `Hong Kong` via HKO, and explicit `--provider hko` selects HKO directly. |
| P7.6-3 | Low | `test/cli.test.ts:80-97` — the JSON sorted-key test asserts `Object.keys(parsed)` is sorted but doesn't verify key order matches Python's `json.dumps(..., sort_keys=True)` for any specific key sequence. A stronger assertion would check the first N keys match an expected order. The current test catches unsorted output but not key-spelling regressions (e.g. `wind_speed` vs `windspeed`). | Fixed — test now pins the exact 14-key sequence the HKO fixture emits in alphabetical order; catches both unsorted output and key-spelling regressions. |

**Verified correct in Phase 7.5 + 7.6:**
- `MDV2_ESCAPE_CHARS` exported from `src/formatters/telegram.ts` matches Python's `r'_*[]()~`>#+-=|{}.!'` exactly — 18 chars verified
- `escapeMdv2` iterates character-by-character with `Set.has()` lookup — byte-identical behavior to Python's `for char in text: if char in MDV2_ESCAPE_CHARS`
- Telegram formatter snapshot output verified line-by-line against `src/formatters/telegram.ts` source: escaping on location, date, description, wind, AQ quality, UV desc, summary — all match source logic
- WhatsApp snapshot verified: no `\` characters in output (correct — WhatsApp formatter never calls `escapeMdv2`)
- CLI text snapshot: `"no N/A placeholders"` test correctly mirrors Python's `cli_text.py` policy (skip rows with missing data)
- CLI text forecast uses `formatIsoDate` (UTC) → `"2026-01-02"` format, matching the snapshot
- Telegram/WhatsApp forecast uses `formatShortDate` → `"Fri Jan 2"` format, matching snapshots
- CLI integration: `captureIO` + `freezeTime` + fetch mock combo works cleanly — 34/34 tests pass
- `--send --format json` → exit 2 with proper error message
- `--provider nonexistent` → exit 1 with sorted provider list `"hko, jma, nws, sg_nea"`
- `--days 3.5` → exit 1 with strict-int error (P6-1 fix coverage)
- `--help` → exit 0 with full usage text on stdout
- `--format xml` → exit 1 with choices error
- `--bogus` → exit 1 with unrecognized argument error
- `CHANGELOG.md` entry is thorough and accurate
- `tasks-002` marks Task 7.5 ✅ and Task 7.6 ✅

---

## Quick Wins

These are low-effort fixes that improve correctness:

1. Update both scripts to use `condition_maps` (underscore) — blocks PRD-002b re-extraction (I-1)
2. Bump CI threshold from `>= 18` to `>= 21` (I-3)
3. Either wire `metoffice.json` into `uk_metoffice.py` or remove the file (I-4 Python side)
4. Update PRD scope table ETA from "~15h" to "~25h" (D-1)
5. Add `condition_raw: ""` to `makeWeatherData` defaults in `src/models.ts` (P2-1) ✅
6. Update task 2.1 spec to reflect `"types": ["bun"]` instead of `"bun-types"` (P2-3)
7. **Fix `parseLocation` to apply `normalizeLocation`** — one-line fix in `src/models.ts`, unblocks all alias-based queries in Bun (P3-1) ✅
8. Fix JMA `getForecast` default from `days=3` to `days=7` (P3-7) ✅
9. Remove unused `roundTemp` export from `src/utils.ts` (P5-4) ✅
10. Add defensive `w !== "N/A"` filter to the wind block in both Bun formatters for symmetric parity with Python's whatsapp.py / telegram.py (P5-8) ✅
11. Add `parseStrictInt` helper in `src/cli.ts` so `--days 3.5` errors instead of silently truncating to `3` (P6-1) ✅
12. Update task 6.2 spec to reference `weather-linux-x64` outfile (P6-4) ✅
13. Rename misleading `escapeMdv2` test from `never double-escapes` to `double-escape documents non-idempotency` (P7.5-1) ✅
14. Add `sunrise`/`sunset` to the full-current fixture so Telegram/WhatsApp astro line is covered (P7.5-2) ✅
15. Add an `aqiOnlyCurrent` fixture so the non-AQHI `aqi` branch is covered in both formatters (P7.5-3) ✅
16. Add CLI integration coverage for the `hk` alias and explicit `--provider hko` selection (P7.6-2) ✅
17. Pin the exact JSON key sequence (HKO 14-key set) in the sorted-key CLI test to catch key-spelling regressions (P7.6-3) ✅
18. Fix `freezeTime()` `Date.UTC` partial-args bug in `test/setup.ts` — forward only provided args, not `undefined` (P7.4-3)
19. Fix SG NEA provider to unwrap `{text, code}` object shape from data.gov.sg v2 API (P7.4-4)
20. Fix JMA provider to fall back to short-term block for weekly day-0 temps/pops when weekly values are empty strings (P7.4-5)
21. Assert specific `WeatherCondition` values instead of `not.toBe(Unknown)` in HKO and NWS fixture-replay tests (P7.4-6)
