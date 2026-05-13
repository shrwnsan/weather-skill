# Eval-001: PRD-002 Phase 0 + Phase 1 Review

**Reviewed commits:**
- `67a78b6` — docs(prd-002): finalize PRD with Phase-0 decisions and add tasks file
- `fd1d52c` — feat(prd-002 phase 1): extract shared data layer to weather/data/

**Date:** 2026-05-13
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

## Commit fd1d52c (Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| I-1 | Medium | `scripts/extract_data.py` and `scripts/refactor_providers.py` reference `condition-maps/` (hyphen) but the actual directory is `condition_maps/` (underscore). Scripts are explicitly kept for PRD-002b re-extraction and will fail if re-run. | Open |
| I-2 | Medium | Float trailing zeros lost in city coordinate JSON — e.g. `(-74.0060, -112.0740)` becomes `[-74.006, -112.074]`. No runtime impact but canonical data loses precision signaling. Affects `us-nws.json` and `metoffice.json`. | Open |
| I-3 | Low | CI wheel smoke test threshold is `>= 18` but 21 JSON files exist. Up to 3 files could disappear without CI catching it. Should be `>= 21`. File: `.github/workflows/python-ci.yml:44`. | Open |
| I-4 | Low | `weather/data/cities/metoffice.json` was extracted but `uk_metoffice.py` still hardcodes `UK_CITIES`. Dead data file — either load it or remove it. | Open |
| I-5 | Low | `weather/data/weather-conditions.json` exists but no Python code loads it at runtime. Presumably for the Bun port but undocumented. | Open |
| I-6 | Low | `cli.py:137` uses duck-typing (`hasattr(o, "value") and hasattr(type(o), "__members__")`) instead of `isinstance(o, enum.Enum)` for enum serialization. Works but fragile. | Open |
| I-7 | Low | `models.py:36` — `from .data.loader import load_json` appears mid-file (after enum def). Works (avoids circular dependency) but deserves a comment explaining why. | Open |

## Quick Wins

These are low-effort fixes that improve correctness:

1. Update both scripts to use `condition_maps` (underscore) — blocks PRD-002b re-extraction
2. Bump CI threshold from `>= 18` to `>= 21`
3. Either wire `metoffice.json` into `uk_metoffice.py` or remove the file
4. Update PRD scope table ETA from "~15h" to "~25h"
