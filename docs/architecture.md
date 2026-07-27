# spark_eda Architecture

## Overview

Clean Architecture with 4 layers, single responsibility per module, and dependency inversion via DTOs.

```
┌─────────────────────────────────────────────┐
│                 Adapters                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │Renderers │ │OmniRoute │ │Controllers   │ │
│  │(HTML/TXT │ │(AI Co-   │ │(CLI/API)     │ │
│  │ /JSON)   │ │ Analyst)  │ │              │ │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘ │
├───────┼─────────────┼──────────────┼─────────┤
│       ▼             ▼              ▼         │
│            Application (Use Cases)           │
│  ┌─────────────────────────────────────────┐ │
│  │ AnalyzeDataset  │ AssessQuality        │ │
│  │ UseCase          │ UseCase              │ │
│  └────────┬───────────┬───────────────────┘ │
├───────────┼───────────┼─────────────────────┤
│           ▼           ▼                     │
│              Domain (Business Logic)        │
│  ┌─────────────────────────────────────────┐ │
│  │ Quality │ Insights │ Recommendations   │ │
│  │ Scoring │ Engine   │ Engine            │ │
│  └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│          Framework (Spark, Config)          │
│  ┌─────────────────────────────────────────┐ │
│  │ SparkSession  │ EDAConfig              │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

## Layer Responsibilities

### Domain (`src/spark_eda/domain/`)

Pure Python, zero dependencies on Spark or I/O.

| Module | Responsibility |
|--------|---------------|
| `quality_score.py` | Weighted score calculation, penalizer ranking |
| `quality_factors.py` | Quality dimension definitions and factor computation |
| `insight_engine.py` | Pattern detection (nulls, constants, skew, Zeros, uniqueness) |
| `recommendation_engine.py` | Actionable recommendation generation |
| `column_classifier.py` | Column type inference (numeric, categorical, temporal, text, boolean) |
| `value_objects.py` | Domain value objects (Score, Severity, etc.) |
| `business_validators.py`, `business_patterns.py` | Cross-field validation rules |

### Application (`src/spark_eda/application/`)

Orchestration layer. Use cases call domain services and assemble DTOs.

| Module | Responsibility |
|--------|---------------|
| `use_cases/analyze_dataset.py` | Full EDA pipeline orchestrator |
| `use_cases/assess_quality.py` | Quality-only pipeline orchestrator |
| `dto/` | 15+ frozen dataclasses for data transfer (no logic) |
| `services/` | Coordination between adapters and domain |

### Adapters (`src/spark_eda/adapters/`)

I/O boundaries. All external communication passes through here.

| Module | Responsibility |
|--------|---------------|
| `renderers/` | HTML, Text, JSON output formatters |
| `omniroute/` | AI Co-Analyst integration (Node.js subprocess, HTTP client, prompt builder) |
| `controllers.py` | CLI argument parsing and dispatch |

### Framework (`src/spark_eda/framework/`)

Infrastructure details — Spark session, configuration.

## Key Design Decisions

### Why OmniRoute and not direct API calls?

OmniRoute wraps 290+ LLM providers behind a single API, adds retry/fallback, and runs as a local Node.js sidecar. The Python side never manages provider keys, rate limits, or provider-specific formats.

### Single-prompt design

All 9 sections + executive analysis use ONE LLM call. The prompt serializes the full report, and the JSON instruction tells the model to comment on each section. This keeps latency predictable (1 network round-trip) and simplifies error handling.

### Graceful degradation

Every failure path returns an `AiCommentary` with `None` fields. The HTML/Text renderers check for `None` before rendering AI blocks. An AI failure never breaks the EDA report.

### Zero-config AI

`EDAConfig.ai_enabled = True` by default. The OmniRouteManager auto-discovers Node.js via `nodejs-bin`, runs `npm install omniroute` lazily, starts the sidecar, and healthchecks before use. If anything fails, AI is silently disabled.

## Data Flow

```
User Code
  │
  ▼
spark_eda.analyze(dataframe)
  │
  ▼
AnalyzeDatasetUseCase
  │
  ├─► ColumnClassifier (domain)
  ├─► QualityCalculator (domain)
  ├─► InsightEngine (domain)
  ├─► RecommendationEngine (domain)
  │
  ▼
EDAReport (DTO)
  │
  ├─► TextRenderer ──► stdout
  ├─► HTMLRenderer ──► file.html
  ├─► JSONSerializer ──► file.json
  │
  └─► AnalysisPresenter
       │
       ├─► OmniRouteManager.ensure_running()
       ├─► OmniRouteClient.analyze(prompt)
       │
       ▼
       AiCommentary → injected into EDAReport via dataclasses.replace
```
