# Tasks: OmniRoute AI Co-Analyst (Embedded Runtime)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 350-500 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Medium

## Phase 1: Foundation

- [x] 1.1 Add `nodejs-bin` + `httpx` dependencies to `pyproject.toml`
- [x] 1.2 Create `adapters/omniroute/__init__.py` — package exports
- [x] 1.3 Create `adapters/omniroute/models.py` — `AiCommentary` dataclass with per-section `Optional[str]` + `executive_analysis`
- [x] 1.4 Add `ai_enabled`, `omniroute_url`, `omniroute_timeout` to `EDAConfig` (default: `True`, `http://localhost:20128/v1`, `30`)
- [x] 1.5 Add `commentary: AiCommentary | None = None` to `EDAReport`
- [x] 1.6 Export `AiCommentary` from `application/dto/__init__.py`

## Phase 2: Manager & Client

- [x] 2.1 Create `adapters/omniroute/manager.py` — `OmniRouteManager` with `ensure_running()`: find Node.js from node-bin, lazy `npm install omniroute` in cache dir, start subprocess, healthcheck loop
- [x] 2.2 Create `adapters/omniroute/manager.py` — `stop()` for graceful shutdown + `atexit` registration
- [x] 2.3 Create `adapters/omniroute/client.py` — `OmniRouteClient` with httpx POST to `/v1/chat/completions`, timeout handling, JSON response parsing, error wrapping

## Phase 3: Prompt & Presenter

- [x] 3.1 Create `adapters/omniroute/prompt_builder.py` — `PromptBuilder.build(report)`: serializes all 9 sections into structured prompt with staff-level data analyst persona
- [x] 3.2 Modify `AnalysisPresenter.present()` — after building sections, if `ai_enabled`, call `OmniRouteManager.ensure_running()`, build prompt, call `OmniRouteClient.analyze()`, attach `AiCommentary` to report

## Phase 4: Renderers

- [x] 4.1 Modify `HTMLRenderer.render_report()` — per-section AI commentary block + executive analysis section with "AI-generated suggestion" label
- [x] 4.2 Modify `TextRenderer.render_report()` — per-section AI commentary block + executive analysis section with "AI-generated suggestion" label
- [x] 4.3 Modify `JSONSerializer.serialize_report()` — include `commentary` field in JSON output

## Phase 5: Tests

- [x] 5.1 Unit tests for `OmniRouteManager` — install, start, healthcheck, stop, atexit, failure modes
- [x] 5.2 Unit tests for `OmniRouteClient` — success, timeout, HTTP error, parse error (mocked httpx)
- [x] 5.3 Unit tests for `PromptBuilder` — all sections present, empty data, single column, all nulls
- [x] 5.4 Unit tests for renderers — commentary present vs None, AI disclosure label
- [x] 5.5 Integration: `AnalysisPresenter` — ai_enabled=False, install fail, start fail, full success (mocked manager + client)
- [x] 5.6 Verify ruff check + mypy + pytest pass (433 existing + new tests)
