# Changelog

All notable changes to spark_eda are documented here.

## [Unreleased]

### Added
- AI Co-Analyst integration via OmniRoute (optional, zero-config, graceful degradation)
  - OmniRouteManager: Node.js discovery, npm install, subprocess lifecycle, healthcheck, port conflict detection, atexit cleanup
  - OmniRouteClient: HTTP client with timeout, JSON parsing, error recovery
  - PromptBuilder: single-prompt design with staff-level persona, token budget
  - HTML/Text/JSON renderers: per-section AI commentary + Executive Analysis
  - `EDAConfig.ai_enabled`, `omniroute_url`, `omniroute_timeout`, `omniroute_cache_dir`
  - 16+ module-level unit tests covering all edge cases (port conflict, ImportError, npm failures, healthcheck timeouts, kill fallback)
  - 58 AI-related tests total (manager, client, prompt_builder, renderers, presenter)
- `docs/architecture.md` — Layer diagram, design decisions, data flow
- `docs/contributing.md` — Development setup, PR process, AI commentary guidelines
- `CHANGELOG.md` — This file

### Changed
- `pyproject.toml`: added `nodejs-bin` and `httpx` dependencies
- `pyproject.toml`: configured `asyncio_default_fixture_loop_scope`, relaxed `filterwarnings` for deprecation warnings
- `README.md`: rewritten with AI Commentary section, architecture overview, installation, Contributing link
- Coverage target: 95% minimum enforced

### Fixed
- `node-bin` → `nodejs-bin` (package didn't exist)
- API endpoint path corrected for OmniRoute v3.8.48
- Port conflict detection before subprocess start
- mypy warnings (10): return types, Optional handling, type ignores
- ruff errors (4): unused imports, line length

## [0.1.0] - 2026-07

### Added
- Initial EDA pipeline: `spark_eda.analyze(dataframe)`
- Data Quality Score: `spark_eda.assess_quality(dataframe)`
- 9-section report: Overview, Schema, Quality, Stats, Distributions, Correlations, Outliers, Insights, Recommendations
- HTML, Text, and JSON renderers
- Use cases: AnalyzeDatasetUseCase, AssessQualityUseCase
- Domain logic: quality scoring, insight engine, recommendation engine, column classifier
- 433 unit/contract tests
- CI workflow (`ruff format`, `ruff check`, `mypy`, `pytest`, coverage)
