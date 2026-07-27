# Column Classification Specification

## Purpose

Infer business-level column types (CPF, CNPJ, email, phone, date, ZIP code, IP, UUID) from column names and sample data using Spark SQL regex patterns.

## Requirements

| ID | Requirement | Strength |
|----|-------------|----------|
| CC-1 | Classifier MUST detect business types by column name pattern matching (e.g., "cpf" in name → CPF) | MUST |
| CC-2 | Classifier MUST validate via Spark SQL regex on sample data when name is ambiguous | MUST |
| CC-3 | Supported types SHALL include: CPF, CNPJ, EMAIL, PHONE, DATE, ZIP_CODE, IP_V4, UUID, UNKNOWN | SHALL |
| CC-4 | Classifier MUST return `BusinessType.UNKNOWN` when no pattern matches | MUST |
| CC-5 | BusinessType SHALL be a pure domain enum — no Spark dependency | SHALL |
| CC-6 | Classification SHOULD complete within a single DataFrame scan | SHOULD |

## Scenarios

### CC-1: Happy path — name-based detection

- GIVEN a DataFrame with columns named "cpf_cliente", "email_contato", "data_nascimento"
- WHEN `ColumnClassifier.classify(df)` is called
- THEN column "cpf_cliente" is classified as CPF, "email_contato" as EMAIL, "data_nascimento" as DATE

### CC-2: Happy path — regex validation

- GIVEN a column named "identificador" containing 100% CPF-format values (###.###.###-##)
- WHEN `ColumnClassifier.classify(df)` is called
- THEN column "identificador" is classified as CPF

### CC-3: Edge case — mixed values

- GIVEN a column named "codigo" containing 60% CNPJ format and 40% CPF format
- WHEN `ColumnClassifier.classify(df)` is called
- THEN the column is classified as UNKNOWN (ambiguous; majority rule applies only at >80% threshold)

### CC-4: Error case — empty DataFrame

- GIVEN a DataFrame with zero rows but defined schema
- WHEN `ColumnClassifier.classify(df)` is called
- THEN classification falls back to name-based pattern matching only
- AND columns with no name match return UNKNOWN

## Input / Output Contracts

| Input | Type | Output | Type |
|-------|------|--------|------|
| DataFrame | `pyspark.sql.DataFrame` | Classifications | `dict[str, BusinessType]` — column name → business type |

## Clean Architecture Layer Mapping

| Layer | Responsibility |
|-------|---------------|
| Domain | `BusinessType` enum (pure Python) |
| Adapters | `ColumnClassifier` — name matcher + Spark SQL regex validator |
| Framework | Passes SparkSession to adapter |

## Acceptance Criteria

- [ ] BusinessType enum is importable with zero dependencies
- [ ] CPF and CNPJ regex patterns match valid formats and reject invalid formats
- [ ] Classification of 20 columns completes in under 5s on a 100k-row DataFrame
- [ ] Name-based detection works without DataFrame data (schema-only mode)
