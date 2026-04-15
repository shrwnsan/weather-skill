# Contributing

Thanks for your interest in contributing to Weather Skill!

## Getting Started

```bash
git clone https://github.com/nano-ade/weather-skill.git
cd weather-skill
python -m pytest tests/ -v
```

No external dependencies are required — the project uses only Python stdlib (`urllib.request`, `json`, `asyncio`).

## Adding a New Provider

1. Create `weather/providers/<name>.py` subclassing `WeatherProvider`
2. Implement `get_current()`, `get_forecast()`, and `supports_location()`
3. Add city/station lookup tables and condition mapping
4. Register in `weather/providers/__init__.py`
5. Add location aliases to `weather/models.py` if needed
6. Add mocked tests in `tests/`
7. Update docs: `SKILL.md`, `README.md`, `docs/provider-selection.md`

See any existing provider (e.g. `sg_nea.py` for a simple example, `jma.py` for a more complex one) as a template.

## Running Tests

```bash
python -m pytest tests/ -v
```

All tests use mocked API responses — no network access or API keys needed.

## Code Style

- Follow existing patterns and idioms in the codebase
- Use `datetime.now(timezone.utc)` (not `datetime.utcnow()`)
- Use `urllib.request` + `asyncio.run_in_executor` for HTTP (no third-party deps)
- Keep provider files self-contained with their own station/city tables

## Pull Requests

- One feature or fix per PR
- Include tests for new providers or significant logic changes
- Update documentation if adding providers or changing behavior

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
