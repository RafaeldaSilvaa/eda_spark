# Analysis Orchestration Specification

## Purpose

Drive the EDA workflow through use cases that coordinate domain entities, adapters, and presenters following Clean Architecture dependency rules.

## Requirements

| ID | Requirement | Strength |
|----|-------------|----------|
| AO-1 | `AnalyzeDatasetUseCase` MUST accept a DataFrame and return an EDAReport through an OutputPresenter | MUST |
| AO-2 | `AssessQualityUseCase` MUST accept a DataFrame and return a QualityReport through an OutputPresenter | MUST |
| AO-3 | Use cases MUST NOT depend on Spark — they depend on `DataProvider`, `CacheProvider`, `OutputPresenter` ports | MUST |
| AO-4 | Controllers SHALL translate framework-specific inputs (DataFrame, config) into use-case parameters | SHOULD |
| AO-5 | Presenters SHALL format domain results into output DTOs (EDAReport, QualityReport) | SHOULD |
| AO-6 | A top-level `spark_eda.analyze(df)` function SHALL wire together the full use-case chain | SHOULD |
| AO-7 | Orchestration MUST handle all domain exceptions and translate them to user-facing messages | MUST |

## Scenarios

### AO-1: Happy path — full analysis

- GIVEN a valid DataFrame loaded via `SparkSession`
- WHEN `spark_eda.analyze(df)` is called
- THEN an EDAReport is returned containing profiling, quality, and column classification sections

### AO-2: Error case — empty DataFrame

- GIVEN an empty DataFrame (zero rows)
- WHEN `spark_eda.analyze(df)` is called
- THEN the use case completes successfully with zeroed profile stats
- AND a note section indicates "Empty dataset — statistics are zeroed"

### AO-3: Error case — Spark failure

- GIVEN a DataFrame referencing a corrupted Parquet source
- WHEN `spark_eda.analyze(df)` is called
- THEN the orchestrator catches the Spark exception
- AND returns an error report containing the exception message and type

## Input / Output Contracts

| Input | Type | Output | Type |
|-------|------|--------|------|
| DataFrame | `pyspark.sql.DataFrame` | EDAReport | Domain DTO (see report-rendering) |
| DataFrame | `pyspark.sql.DataFrame` | QualityReport | Domain DTO with overall + factor scores |

## Port Interfaces

| Port | Methods |
|------|---------|
| DataProvider | `profile(df) → DataProfile`, `classify_columns(df) → dict[str, BusinessType]` |
| CacheProvider | `get(key) → Optional[Any]`, `set(key, value, ttl) → None` |
| OutputPresenter | `present_report(report)` / `present_quality(report)` — formats for output |

## Clean Architecture Layer Mapping

| Layer | Responsibility |
|-------|---------------|
| Use Cases | `AnalyzeDatasetUseCase`, `AssessQualityUseCase` — define ports, orchestrate flow |
| Adapters | Controllers (translate input), Presenters (format output) |
| Framework | Composite root that wires ports to concrete implementations |
| Domain | Never depends on this layer |

## Acceptance Criteria

- [ ] Use case imports contain zero Spark references
- [ ] `spark_eda.analyze(df)` completes on a 10k-row DataFrame in under 10s
- [ ] Error from any port propagates correctly through the use case
- [ ] Use cases are unit-testable with mock ports (no Spark in test)
