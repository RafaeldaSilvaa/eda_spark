# Spark Infrastructure Specification

## Purpose

Manage SparkSession lifecycle, application configuration, and typed exceptions. This is the framework layer — closest to PySpark, furthest from domain.

## Requirements

| ID | Requirement | Strength |
|----|-------------|----------|
| SI-1 | `EDAConfig` MUST provide Spark configuration presets (app name, shuffle partitions, Kryo serializer) | MUST |
| SI-2 | `spark_session` module MUST expose `get_or_create_spark(config) → SparkSession` | MUST |
| SI-3 | The session factory MUST reuse existing sessions when config matches | MUST |
| SI-4 | Custom exceptions SHALL inherit from `EDAException` base class | SHALL |
| SI-5 | Exception hierarchy MUST include: `ProfilingError`, `QualityError`, `ClassificationError`, `ConfigurationError` | MUST |
| SI-6 | `EDAConfig` MUST support YAML and dict-based initialization | MUST |
| SI-7 | Configuration validation MUST reject invalid Spark config keys | MUST |

## Scenarios

### SI-1: Happy path — session creation

- GIVEN a valid EDAConfig with app_name="spark_eda" and spark.executor.memory="2g"
- WHEN `get_or_create_spark(config)` is called
- THEN a SparkSession is returned with the configured app name and executor memory

### SI-2: Happy path — session reuse

- GIVEN a previously created SparkSession
- WHEN `get_or_create_spark(config)` is called again with identical config
- THEN the same SparkSession instance is returned (no new JVM process)

### SI-3: Error case — invalid config key

- GIVEN an EDAConfig with an invalid key `spark.nonexistent.setting`
- WHEN the config is validated
- THEN a `ConfigurationError` is raised with a message listing the invalid keys

### SI-4: Error case — Spark session failure

- GIVEN misconfigured Spark (e.g., missing `SPARK_HOME`)
- WHEN session creation is attempted
- THEN an `EDAException` wrapping the underlying Spark exception is raised

## Input / Output Contracts

| Input | Type | Output | Type |
|-------|------|--------|------|
| Config dict/YAML | `dict` / `str(path)` | EDAConfig | Value object with validated spark settings |
| EDAConfig | Value object | SparkSession | `pyspark.sql.SparkSession` |

## Clean Architecture Layer Mapping

| Layer | Responsibility |
|-------|---------------|
| Framework | `EDAConfig`, `spark_session` module, `EDAException` hierarchy |
| Framework | Composite root wiring |

## Acceptance Criteria

- [ ] `EDAConfig.from_dict()` and `EDAConfig.from_yaml()` both produce identical configs
- [ ] `get_or_create_spark` with different config creates a new session (doesn't reuse stale)
- [ ] All custom exceptions are catchable via `except EDAException`
- [ ] Configuration validation covers all standard Spark config namespaces
