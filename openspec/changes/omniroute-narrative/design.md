# Design: OmniRoute AI Co-Analyst for EDA Reports

## Technical Approach

Bundle Node.js via `nodejs-bin` Python package. On first AI call, lazy-install OmniRoute from npm and start as a managed subprocess. HTTP client (`OmniRouteClient`) calls `localhost:20128/v1/chat/completions` with a single prompt containing all 9 sections. Response maps to `AiCommentary` DTO attached to `EDAReport`. Integration points: `OmniRouteManager` (subprocess lifecycle), `OmniRouteClient` (HTTP), `AnalysisPresenter` (orchestration), `EDAConfig` (config), and all 3 renderers (display).

**Zero-config principle**: `pip install spark-eda` → Node.js is bundled. First EDA analysis → lazy npm install + subprocess start. AI commentary works automatically with zero user setup. If anything fails, the report renders identically to today.

## Architecture Decisions

### Decision: Single large prompt vs. 2 separate calls

| Option | Tradeoff |
|--------|----------|
| **Single prompt** + structured JSON response | Fewer round-trips, simpler error handling, but larger context window |
| 2 calls (per-section + executive) | Independent retries, but double latency |

**Choice**: Single prompt requesting JSON with both per-section commentary and executive analysis. Fallback: if JSON parsing fails, degrade gracefully.

### Decision: httpx vs. requests

| Option | Tradeoff |
|--------|----------|
| **httpx** | Already common in ecosystem, async-capable, native timeout support |
| requests | Synchronous only, no timeout in core API |

**Choice**: `httpx` (sync mode). Matches the synchronous presenter pattern.

### Decision: Subprocess lifecycle management

| Option | Tradeoff |
|--------|----------|
| **Lazy start on first AI call** | No resource usage when ai_enabled=False; first call slower |
| Start on import | Wastes resources, delays import, conflicts if user has own OmniRoute |

**Choice**: Lazy start. `OmniRouteManager.start()` called by `AnalysisPresenter` on first AI analysis. `atexit` handles cleanup.

### Decision: OmniRoute install strategy

| Option | Tradeoff |
|--------|----------|
| **Lazy npm install on first AI call** | First analysis slower (npm install), but pip install is fast |
| npm install via post-install hook | Slows pip install, harder to debug failures |

**Choice**: Lazy install. Cache dir under package data or `~/.cache/spark_eda/omniroute/`. Subsequent runs skip install.

### Decision: Commentary field location

| Option | Tradeoff |
|--------|----------|
| **`AiCommentary` DTO in `EDAReport`** | Keeps non-deterministic data isolated, easy to make Optional, no domain model changes |
| Inline in each section DTO | Pollutes deterministic DTOs, harder to detect "AI present" at render level |

**Choice**: Standalone `AiCommentary` dataclass with per-section `Optional[str]` fields + `executive_analysis`, stored as `Optional[AiCommentary]` on `EDAReport`.

## Data Flow

```
pip install spark_eda
  └── nodejs-bin → ~40MB Node.js portátil no site-packages

Análise EDA (primeira vez com ai_enabled=True)
  └── OmniRouteManager.start()
        ├── node-bin → find Node.js
        ├── npm install omniroute → ~/.cache/spark_eda/omniroute/
        └── subprocess omniroute → localhost:20128

Análise EDA (subsequente)
  EDAConfig (ai_enabled=True)
    │
    ▼
  OmniRouteManager.ensure_running()  ← healthcheck, restart if dead
    │
    ▼
  AnalysisPresenter.present()
    ├── Build 9 heuristic sections (existing)
    ├── if ai_enabled:
    │     ├── PromptBuilder.build(report) → str
    │     ├── OmniRouteClient.analyze(prompt) → AiCommentary
    │     │     └── httpx POST localhost:20128/v1/chat/completions
    │     └── report.commentary = AiCommentary(...)
    │
    └── return EDAReport
          │
          ▼
    Renderer (HTML / Text / JSON)
      ├── if commentary: render per-section inline + executive
      └── if no commentary: render as today

atexit → OmniRouteManager.stop() → kill subprocess
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | Modify | Add `nodejs-bin` + `httpx` dependencies |
| `src/spark_eda/adapters/omniroute/__init__.py` | Create | Package init |
| `src/spark_eda/adapters/omniroute/manager.py` | Create | `OmniRouteManager` — node-bin discovery, npm install, subprocess lifecycle, healthcheck, cleanup |
| `src/spark_eda/adapters/omniroute/client.py` | Create | `OmniRouteClient` — httpx POST, timeout, error handling |
| `src/spark_eda/adapters/omniroute/prompt_builder.py` | Create | `PromptBuilder` — serializes sections, builds system + user prompt |
| `src/spark_eda/adapters/omniroute/models.py` | Create | `AiCommentary` dataclass |
| `src/spark_eda/application/dto/eda_report.py` | Modify | Add `commentary: AiCommentary | None = None` |
| `src/spark_eda/application/dto/__init__.py` | Modify | Export `AiCommentary` |
| `src/spark_eda/framework/config.py` | Modify | Add `ai_enabled`, `omniroute_url`, `omniroute_timeout` |
| `src/spark_eda/adapters/presenters/analysis_presenter.py` | Modify | Inject OmniRouteManager.ensure_running + AI call |
| `src/spark_eda/adapters/renderers/html_renderer.py` | Modify | Per-section AI block + executive section |
| `src/spark_eda/adapters/renderers/text_renderer.py` | Modify | Per-section AI block + executive section |
| `src/spark_eda/adapters/renderers/json_serializer.py` | Modify | Include commentary field in JSON |

## Interfaces / Contracts

```python
@dataclass
class AiCommentary:
    overview: str | None = None
    schema: str | None = None
    quality: str | None = None
    stats: str | None = None
    distributions: str | None = None
    correlations: str | None = None
    outliers: str | None = None
    insights: str | None = None
    recommendations: str | None = None
    executive_analysis: str | None = None

class OmniRouteManager:
    def ensure_running(self) -> bool: ...
    # Returns True if OmniRoute is healthy on localhost:20128
    # On first call: find Node.js, npm install, start subprocess
    # On subsequent: healthcheck, restart if dead
    def stop(self) -> None: ...
    # Kill subprocess, cleanup (registered via atexit)

class OmniRouteClient:
    def __init__(self, base_url: str, timeout: int = 30) -> None: ...
    def analyze(self, prompt: str) -> AiCommentary: ...
    # raises OmniRouteError on connection/timeout/parse failures

class PromptBuilder:
    @staticmethod
    def build(sections: EDAReport) -> str: ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `OmniRouteManager` — npm install, start, healthcheck, stop | Mock subprocess/httpx, verify lifecycle |
| Unit | `OmniRouteClient` — success, timeout, HTTP error, parse error | Mock httpx, verify graceful degradation |
| Unit | `PromptBuilder` — sections present/absent, empty data | Unit test output string structure |
| Unit | `AiCommentary` data class | Construction and defaults |
| Unit | Renderers — commentary present vs None | Pre-built `EDAReport` with/without commentary |
| Integration | Presenter — AI call disabled, install fail, start fail, success | Mock manager + client at presenter boundary |
| Integration | Full pipeline — config toggle | `ai_enabled=False` → no manager init, no HTTP call |

## Open Questions (Resolved)

- [x] Cache directory location: `~/.cache/spark_eda/omniroute/`, configurable via `EDAConfig.omniroute_cache_dir`
- [x] OmniRoute startup healthcheck: 6 retries × 5s = 30s total
- [x] Executive analysis token budget: prompt instructs "2-4 sentences per section, exec analysis max 6 sentences"
- [x] nodejs-bin — exact PyPI package: `nodejs-bin`, import: `import nodejs`, attr: `nodejs.path`
- [x] npm version pinned: `omniroute@3.8.48`
- [x] Port conflict detection: `_port_in_use()` checks `localhost:20128/health` before starting subprocess
