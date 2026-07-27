# Proposal: OmniRoute AI Co-Analyst for EDA Reports

## Intent

EDA reports today are data-rich but machine-driven: stats, correlations, and heuristic insights tell *what* is in the data but not *what it means* or *what to do about it*. An AI co-analyst — powered by OmniRoute — understands the dataset context, identifies non-obvious problems and patterns, extracts business ideas, and adds human-readable commentary at every step of the report, regardless of data scope or schema. The heuristic engine stays as the deterministic baseline; the AI layer layers on top as an intelligent interpreter.

## Scope

### In Scope
- **AI commentary in every report section**: overview, schema, stats, distributions, correlations, outliers, insights, quality, recommendations — each gets AI-generated commentary that interprets the numbers
- **Comprehensive executive analysis**: a dedicated AI section that ties everything together, identifies cross-cutting patterns, surfaces non-obvious relationships, suggests hypotheses, and flags business implications
- **HTTP client module** (`adapters/omniroute/`): `OmniRouteClient` that sends structured context (serialized EDAReport sections as JSON) to OmniRoute and receives AI commentary back
- **Prompt template engine**: builds a structured prompt from all report sections, optimized for the model to produce coherent multi-section commentary
- **OmniRoute subprocess management** (`adapters/omniroute/manager.py`): `OmniRouteManager` that installs OmniRoute from npm (via bundled Node.js from `node-bin`), starts it as a subprocess on first AI call, and cleans up via `atexit`
- **Zero-config embedded runtime**: after `pip install`, AI commentary works automatically — `node-bin` provides Node.js portátil, lazy `npm install omniroute` + subprocess start on first use. No user setup required.
- **Integration in `AnalysisPresenter`**: after building all 9 DTO sections, lazy-starts OmniRoute, sends single prompt for per-section commentary + executive analysis
- **Updates to all 3 renderers** (`HTMLRenderer`, `TextRenderer`, `JSONSerializer`): each section shows AI commentary if available, plus the executive analysis section
- **`EDAConfig` flags**: `ai_enabled: bool = True`, `omniroute_url: str = "http://localhost:20128/v1"`
- **Graceful degradation**: if OmniRoute fails to install, start, or respond, log warning, skip AI, report renders without commentary (no crash)
- **AiCommentary DTO**: structured container mapping section names to commentary text, stored in EDAReport

### Out of Scope
- Replacing existing `InsightEngine` or `RecommendationEngine`
- Streaming responses (simple request/response)
- MCP server integration
- Domain layer changes (only Application/Adapters)
- Training or fine-tuning models

## Capabilities

### New Capabilities
- `ai-commentary`: Per-section AI commentary generation — overview, schema, stats, distributions, correlations, outliers, insights, quality, recommendations — plus executive analysis that cross-cuts all sections.

### Modified Capabilities
- None — no existing specs to modify.

## Approach

1. Add `node-bin` to `pyproject.toml` — provides portable Node.js binary (~40MB) during `pip install`
2. Create `src/spark_eda/adapters/omniroute/` with:
   - `manager.py`: `OmniRouteManager` — on first AI call, finds Node.js from node-bin, lazy `npm install omniroute` in package cache dir, starts subprocess on `localhost:20128`, healthcheck loop, `atexit` cleanup
   - `client.py`: `OmniRouteClient` — httpx-based, POST to `/v1/chat/completions`, handles timeouts, connection errors
   - `prompt_builder.py`: `PromptBuilder` — serializes relevant context from each section, builds structured prompt requesting per-section commentary + executive analysis
   - `models.py`: `AiCommentary` dataclass with per-section fields + executive_analysis
3. Add `AiCommentary | None` field to `EDAReport`
4. Extend `AnalysisPresenter.present()`: after building all 9 sections, if `ai_enabled`, lazy-start OmniRoute via manager, build prompt, call client, attach commentary
5. Each renderer renders per-section commentary inline and the executive analysis as a dedicated section
6. `JSONSerializer` includes commentary in the JSON output

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `pyproject.toml` | Modified | Add `nodejs-bin` + `httpx` dependencies |
| `src/spark_eda/adapters/omniroute/` | New | manager.py, client.py, prompt_builder.py, models.py |
| `src/spark_eda/application/dto/eda_report.py` | Modified | Add AiCommentary field |
| `src/spark_eda/application/dto/` | New file | ai_commentary.py DTO |
| `src/spark_eda/adapters/presenters/analysis_presenter.py` | Modified | OmniRouteManager + client after section build |
| `src/spark_eda/adapters/renderers/html_renderer.py` | Modified | Render per-section + executive commentary |
| `src/spark_eda/adapters/renderers/text_renderer.py` | Modified | Render per-section + executive commentary |
| `src/spark_eda/adapters/renderers/json_serializer.py` | Modified | Include commentary in JSON |
| `src/spark_eda/framework/config.py` | Modified | Add ai_enabled, omniroute_url |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| node-bin platform incompatibility (Alpine, exotic ARM) | Low | Graceful degradation — if Node.js fails, skip AI silently |
| First-use latency (npm install omniroute) | Medium | Lazy install on first AI call; user sees commentary on 2nd+ run |
| OmniRoute subprocess crashes | Low | Healthcheck before each call; restart or graceful degradation |
| Disk space (~150MB extra) | Low | Documented in README; optional `ai_enabled=False` to skip entirely |
| npm registry unreachable | Low | Graceful degradation — log warning, render without commentary |
| Hallucination / poor commentary | Medium | Prompt engineering; prefix "AI suggestion"; deterministic baseline intact |
| Token costs at scale | Low | OmniRoute auto combo picks cheapest; 90+ free tiers absorb most usage |

## Rollback Plan

- Set `EDAConfig.ai_enabled = False` globally — report reverts to current behavior, no Node.js/OmniRoute initialization
- Revert `EDAReport` and `AnalysisPresenter` changes
- Delete `adapters/omniroute/` module
- Remove `nodejs-bin` from `pyproject.toml` dependencies

## Dependencies

- `nodejs-bin` Python package — portable Node.js binary bundled during `pip install`
- `httpx` Python package — HTTP client for API calls
- `omniroute@3.8.48` npm package — installed lazily on first AI call via bundled Node.js

## Success Criteria

- [ ] Each report section shows AI commentary when OmniRoute is reachable and `ai_enabled=True`
- [ ] Executive analysis section exists and is coherent
- [ ] Report renders identically to current behavior when `ai_enabled=False`
- [ ] Report renders without crash when OmniRoute is unreachable (empty commentary, warning logged)
- [ ] All 3 renderers handle commentary presence/absence correctly
- [ ] 95%+ unit test coverage for new modules (mocked HTTP)
