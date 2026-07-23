# Proposal: spark_eda — Distributed EDA Library

## Intent

Production-grade Python library for distributed exploratory data analysis, data quality assessment, and deterministic insight generation on PySpark DataFrames. Zero-config API, transparent quality scoring (0-100 with per-factor breakdown), and Clean Architecture for maximal testability.

## Scope

### In Scope
- Domain: entities, value objects, QualityCalculator (Completeness, Uniqueness), ColumnClassifier
- Use Cases: AnalyzeDatasetUseCase, AssessQualityUseCase + ports (DataProvider, CacheProvider, OutputPresenter)
- Adapters: SparkDataProvider, LRUCacheProvider, presenters, DTOs, basic HTML renderer
- Framework: config, spark_session, exceptions, composite root
- Cross-layer quality factor registry + per-factor score docs
- Docker testing infra, Makefile, scaffold scripts, HELPERS.md, CI pipeline

### Out of Scope
- AI/ML-based insights, streaming EDA, database connectors
- UI dashboards, interactive visualization (reports only)
- Correlation, outlier, temporal strategies — Phase 2
- Recommendation engine, full accuracy/timeliness dimensions — Phase 3

## Capabilities

> Contract between proposal and specs phases. Each new capability becomes a spec file.

### New Capabilities
- `data-profiling`: Core domain entities (DataProfile, ColumnProfile) + Spark provider for profile computation
- `quality-scoring`: QualityCalculator + QualityScore + factor registry + adapter computation
- `analysis-orchestration`: Use cases, controllers, presenters
- `report-rendering`: EDAReport DTO, section DTOs, HTML/text renderers
- `column-classification`: Business type inference (CPF, CNPJ, email, etc.) via Spark regex
- `caching`: LRU cache provider + CacheProvider port
- `spark-infrastructure`: SparkSession management, EDAConfig, exceptions
- `developer-tooling`: HELPERS.md, scaffold scripts, AAA test templates
- `testing-infrastructure`: Docker, docker-compose, Makefile, CI pipeline

### Modified Capabilities
None — greenfield project.

## Approach

Layer-by-layer build from inside out: (1) **Domain** — pure entities, VOs, services (zero Spark, pure pytest); (2) **Use Cases** — interactors depending only on domain + ports; (3) **Adapters** — Spark provider, presenters, DTOs, renderers; (4) **Framework** — composite root wiring everything. Docker-first testing from day one.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `spark_eda/domain/` | New | Entities, value objects, services |
| `spark_eda/use_cases/` | New | Interactors + port interfaces |
| `spark_eda/adapters/` | New | Controllers, providers, presenters, DTOs |
| `spark_eda/framework/` | New | Config, spark_session, exceptions |
| `tests/` | New | Unit, integration, contract, benchmarks |
| `pyproject.toml` | New | Build config, deps, tool settings |
| `Docker/` + `Makefile` | New | Testing infrastructure |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| PySpark 4.0 API changes | Med | Pin version, test against RC in CI matrix |
| Clean Architecture purity overhead on Spark code | Low | Strict adapter boundary; domain is always Spark-free |
| Docker build time in CI | Low | Layer caching, pre-built base image |

## Rollback Plan

Greenfield project — standard `git revert` on the merge commit. No data migration, no schema changes, no deployed services.

## Dependencies

- PySpark 4.0+, Python 3.14+, OpenJDK 21
- Docker Engine + docker-compose for reproducible tests

## Success Criteria

- [ ] Domain layer: 100% Spark-free, >95% coverage in pure pytest, no fixtures
- [ ] `spark_eda.analyze(df)` produces complete EDAReport from any DataFrame
- [ ] `spark_eda.assess_quality(df)` produces QualityReport with per-factor breakdown
- [ ] `make test-all` passes inside Docker
- [ ] CI pipeline green: lint → typecheck → unit → integration → coverage
