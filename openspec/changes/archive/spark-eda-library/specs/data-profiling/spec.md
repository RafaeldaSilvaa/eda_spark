# Data Profiling Specification

## Purpose

Compute structural and statistical profiles of PySpark DataFrames. Domain entities (`DataProfile`, `ColumnProfile`) live in the domain layer; the Spark adapter performs distributed computation.

## Requirements

| ID | Requirement | Strength |
|----|-------------|----------|
| DP-1 | DataProfile MUST contain one ColumnProfile per DataFrame column | MUST |
| DP-2 | ColumnProfile MUST report: count, nullCount, distinctCount, min, max, mean, stddev, inferredType | MUST |
| DP-3 | DataProfile SHALL compute numeric stats with Spark's approximation tolerance | SHOULD |
| DP-4 | The Spark provider MUST execute all profile computations in a single DataFrame pass | MUST |
| DP-5 | Profile computation MUST NOT fail on empty DataFrames; returns zeroed stats | MUST |

## Scenarios

### DP-1: Happy path — profile computation

- GIVEN a DataFrame with 5 numeric and 3 string columns, all with valid data
- WHEN `DataProvider.profile(df)` is called
- THEN a DataProfile is returned with exactly 8 ColumnProfile entries
- AND each ColumnProfile contains non-null count, nullCount, distinctCount, min, max

### DP-2: Edge case — DataFrame with nulls

- GIVEN a DataFrame where column "age" has 30% nulls and column "email" has 10% nulls
- WHEN `DataProvider.profile(df)` is called
- THEN `ColumnProfile("age").nullCount` equals 30% of total rows
- AND `ColumnProfile("email").nullCount` equals 10% of total rows

### DP-3: Error case — empty DataFrame

- GIVEN a DataFrame with a defined schema but zero rows
- WHEN `DataProvider.profile(df)` is called
- THEN a DataProfile is returned with count=0 for all columns
- AND no exception is raised

### DP-4: Error case — null input

- GIVEN a null DataFrame reference
- WHEN `DataProvider.profile(null)` is called
- THEN a `ValueError` or domain-specific `EDAException` is raised

## Input / Output Contracts

| Input | Type | Output | Type |
|-------|------|--------|------|
| DataFrame | `pyspark.sql.DataFrame` | DataProfile | Value object with `columns: dict[str, ColumnProfile]` |
| — | — | ColumnProfile | Value object: `name, count, nullCount, distinctCount, min, max, mean, stddev, inferredType` |

## Clean Architecture Layer Mapping

| Layer | Responsibility |
|-------|---------------|
| Domain | `DataProfile`, `ColumnProfile` entities (pure Python, zero Spark) |
| Adapters | `SparkDataProvider.profile()` — transforms DataFrame into DataProfile |
| Framework | Wiring, sessions, config passed to adapter |

## Acceptance Criteria

- [ ] DataProfile round-trips via pickle/dict serialization in pure Python
- [ ] SparkDataProvider.profile() completes under 30s on a 1M-row, 20-column DataFrame
- [ ] Empty DataFrame returns zeroed stats, not error
- [ ] 100% code coverage on domain entities (pure pytest, no Spark)
