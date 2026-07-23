# Quality Scoring Specification

## Purpose

Compute a deterministic 0–100 quality score per column and dataset-wide, with per-factor breakdown. Domain purity: `QualityCalculator` is Spark-free; the adapter calls registered factors and aggregates results.

## Requirements

| ID | Requirement | Strength |
|----|-------------|----------|
| QS-1 | QualityCalculator MUST expose a `register_factor(name, fn)` method | MUST |
| QS-2 | QualityScore MUST contain: `overall: float`, `factors: dict[str, float]`, `column_scores: dict[str, float]` | MUST |
| QS-3 | Factors MUST return 0.0–1.0 floats; the calculator maps to 0–100 | MUST |
| QS-4 | At minimum, Completeness (null ratio) and Uniqueness (duplicate ratio) SHALL be registered | SHALL |
| QS-5 | Score computation MUST be deterministic — same input always produces same score | MUST |
| QS-6 | Calculator MUST reject factor names longer than 64 characters | MUST |
| QS-7 | Overall score SHALL be the mean of all factor scores | SHOULD |

## Scenarios

### QS-1: Happy path — full quality assessment

- GIVEN a DataProfile with nullCount=0 and distinctCount=rowCount for all columns
- WHEN `QualityCalculator.assess(profile)` is called with Completeness and Uniqueness factors
- THEN `QualityScore.overall` equals 100.0
- AND `QualityScore.factors["completeness"]` equals 1.0
- AND `QualityScore.factors["uniqueness"]` equals 1.0

### QS-2: Edge case — mixed quality

- GIVEN a profile where one column has 50% nulls and 20% duplicates
- WHEN `QualityCalculator.assess(profile)` is called
- THEN `QualityScore.column_scores["that_column"]` is below 50.0
- AND the overall score reflects the average across all columns

### QS-3: Error case — empty profile

- GIVEN an empty DataProfile (no columns)
- WHEN `QualityCalculator.assess(profile)` is called
- THEN a `ValueError` or domain exception is raised with message "Cannot assess quality: empty profile"

### QS-4: Error case — unregistered factor called

- GIVEN a QualityCalculator with no factors registered
- WHEN `assess()` is called
- THEN the result SHALL contain factor scores only for registered factors (empty/zero)

## Input / Output Contracts

| Input | Type | Output | Type |
|-------|------|--------|------|
| DataProfile | Domain value object | QualityScore | Value object: `overall, factors, column_scores` |
| Factor fn | `Callable[[ColumnProfile], float]` | — | — |

## Clean Architecture Layer Mapping

| Layer | Responsibility |
|-------|---------------|
| Domain | `QualityCalculator`, `QualityScore`, factor type (`QualityFactor`) |
| Adapters | Factor implementations read DataProfile and compute scores |
| Use Cases | `AssessQualityUseCase` — orchestrates calculator + profile data |

## Acceptance Criteria

- [ ] QualityCalculator is 100% pure Python — no PySpark imports, path, or reference
- [ ] Completeness + Uniqueness produce correct scores on synthetic test data
- [ ] Calculator round-trips via JSON serialization (verify dict/from_dict)
- [ ] Determinism verified: 3 calls with same profile produce identical scores
