# Tasks: spark_eda — Distributed EDA Library

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

~5000+ lines, 77 source files + 19 test files. Single PR delivered.

## Phase 1: Infrastructure ✅

- [x] 1.1 `pyproject.toml` — deps, build, ruff/mypy/pytest (M)
- [x] 1.2 `tests/Dockerfile` — Python 3.14 + JDK 21 + PySpark 4.0 (M)
- [x] 1.3 `docker-compose.yml` — test/benchmark/shell services (M)
- [x] 1.4 `Makefile` — test-all, test-unit, test-integration (S)

## Phase 2: Domain Entities + VOs ✅

- [x] 2.1 DataType, InferredType, Severity, CorrelationMethod, OutlierMethod enums (S)
- [x] 2.2 DataProfile, ColumnProfile, ColumnMetadata frozen dataclasses (M)
- [x] 2.3 QualityScore, QualityFactor, QualityDimension entities (M)
- [x] 2.4 DatasetAnalysis, Insight, Recommendation entities (M)
- [x] 2.5 Statistic union: NumericStats, CategoricalStats, TemporalStats, TextStats, BooleanStats (S)
- [x] 2.6 Distribution union: NumericDistribution, CategoricalDistribution, TemporalDistribution (S)

## Phase 3: Domain Services ✅

- [x] 3.1 QualityCalculator + FACTOR_REGISTRY decorator (M)
- [x] 3.2 Completeness + Uniqueness + Consistency + Timeliness + Accuracy factors (M)
- [x] 3.3 Domain ColumnClassifier (pure logic) (S)
- [x] 3.4 InsightEngine + RecommendationEngine (S)

## Phase 4: Use Cases + Ports ✅ (moved to application/)

- [x] 4.1 DataProvider, CacheProvider, OutputPresenter port ABCs (S)
- [x] 4.2 AnalyzeDatasetUseCase — cache-first orchestration (M)
- [x] 4.3 AssessQualityUseCase — profile → quality score (S)

## Phase 5: Adapters ✅

- [x] 5.1 SparkDataProvider — single-pass profile agg + correlations + outlier methods (M)
- [x] 5.2 LRUCacheProvider — thread-safe OrderedDict + TTL (M)
- [x] 5.3 ColumnClassifier — domain service (S)
- [x] 5.4 AnalyzeController, QualityController — thin orchestrators (S)

## Phase 6: Presenters + DTOs ✅

- [x] 6.1 EDAReport composite DTO + all section DTOs (M)
- [x] 6.2 AnalysisPresenter, QualityPresenter (S)
- [x] 6.3 business/patterns.py + business/validators.py (S)

## Phase 7: Renderers ✅

- [x] 7.1 HTMLRenderer — inline CSS (M)
- [x] 7.2 TextRenderer — 120-char monospace layout (S)
- [x] 7.3 JSONSerializer — dict round-trip (S)
- [x] 7.4 utils/formatting.py + utils/hashing.py (S)

## Phase 8: Framework ✅

- [x] 8.1 EDAConfig + QualityConfig frozen dataclasses (M)
- [x] 8.2 spark_session.py — get_or_create_spark() singleton (M)
- [x] 8.3 exceptions.py — EDAException hierarchy (S)

## Phase 9: Composite Root ✅

- [x] 9.1 spark_eda/__init__.py — analyze(), assess_quality() DI (M)
- [x] 9.2 All package __init__.py exports (S)

## Phase 10: Tests ✅

- [x] 10.1 Domain entity unit tests — pure pytest (M)
- [x] 10.2 Domain service tests — QualityCalculator + factors (M)
- [x] 10.3 Use case tests — mock ports (M)
- [x] 10.4 Adapter tests — SparkDataProvider, LRUCacheProvider (M)
- [ ] 10.5 Presenter + renderer tests + EDAReport round-trip (S)
- [ ] 10.6 Integration tests — full analyze()/assess_quality() (L)
- [x] 10.7 Contract + benchmark tests (S)
- [x] 10.8 Shared test fixtures (S)

## Phase 11: Developer Tooling ✅

- [x] 11.1 Scaffold scripts — templates (M)
- [x] 11.2 HELPERS.md — setup, test commands, troubleshooting (S)

## Phase 12: CI Pipeline ✅

- [x] 12.1 .github/workflows/ci.yml — lint, typecheck, unit, integration, coverage (S)
