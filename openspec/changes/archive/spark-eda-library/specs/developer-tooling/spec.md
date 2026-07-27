# Developer Tooling Specification

## Purpose

Provide onboarding, scaffolding, and testing-pattern resources to ensure consistent developer experience across the project.

## Requirements

| ID | Requirement | Strength |
|----|-------------|----------|
| DT-1 | HELPERS.md MUST document: project structure, setup, test commands, architecture rules | MUST |
| DT-2 | Scaffold scripts MUST generate new domain entity and use-case files from templates | MUST |
| DT-3 | AAA (Arrange-Act-Assert) test templates MUST exist for: domain, use cases, adapters, framework | MUST |
| DT-4 | Scaffold scripts SHALL create corresponding test files alongside source files | SHOULD |
| DT-5 | All tooling MUST run on POSIX (Linux/macOS) and Windows (Git Bash / WSL) | MUST |
| DT-6 | HELPERS.md MUST include a troubleshooting section for common Spark/Docker issues | MUST |

## Scenarios

### DT-1: Happy path — scaffold new domain entity

- GIVEN a developer runs `scaffold entity QualityScore` from the project root
- THEN files are created: `spark_eda/domain/entities/quality_score.py`, `tests/unit/domain/test_quality_score.py`
- AND both files follow the established templates with placeholder docstrings and test stubs

### DT-2: Happy path — AAA template applied

- GIVEN a developer requests a use-case test template
- WHEN `scaffold test use_case AnalyzeDataset` is run
- THEN a test file is created with AAA sections: `# Arrange`, `# Act`, `# Assert`
- AND mock imports for DataProvider, CacheProvider, and OutputPresenter are pre-filled

### DT-3: Error case — scaffold with missing template

- GIVEN a developer runs `scaffold entity UnknownType`
- WHEN no template exists for "UnknownType"
- THEN a clear error message lists available entity types

## Input / Output Contracts

| Tool | Input | Output |
|------|-------|--------|
| `scaffold` CLI | `{type} {name}` | Created source + test files |
| HELPERS.md | — | Documentation file at project root |

## Clean Architecture Layer Mapping

| Layer | Responsibility |
|-------|---------------|
| Framework | `scaffold` scripts, HELPERS.md, test templates |
| — | Tooling is meta — aids developers, not runtime |

## Acceptance Criteria

- [ ] `scaffold entity` and `scaffold use_case` produce valid, importable Python files
- [ ] HELPERS.md `make test` command works on a fresh clone
- [ ] Scaffold runs on both Ubuntu 22.04 and Windows Server 2022 (CI matrix)
- [ ] All generated test files pass `pytest --collect-only` without modification
