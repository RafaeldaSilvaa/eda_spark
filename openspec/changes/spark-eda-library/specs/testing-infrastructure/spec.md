# Testing Infrastructure Specification

## Purpose

Provide reproducible, containerized test execution for the entire project. Covers Docker-based test environments, Makefile targets, and CI pipeline definition.

## Requirements

| ID | Requirement | Strength |
|----|-------------|----------|
| TI-1 | Dockerfile MUST use a Python 3.14+ base image with OpenJDK 21 and PySpark 4.0+ | MUST |
| TI-2 | docker-compose MUST define services: `tests` (runs suite) and optionally `spark` (standalone) | MUST |
| TI-3 | Makefile MUST expose: `test-all`, `test-unit`, `test-integration`, `lint`, `typecheck`, `clean` | MUST |
| TI-4 | CI pipeline MUST run: lint → typecheck → unit tests → integration tests → coverage | MUST |
| TI-5 | Unit tests MUST run without Docker (pure pytest, no SparkSession needed) | MUST |
| TI-6 | Integration tests SHALL run inside Docker with a live SparkSession | SHALL |
| TI-7 | Coverage threshold SHALL be >= 80% for CI to pass | SHOULD |
| TI-8 | CI SHALL configure Spark's log level to ERROR to reduce output noise | SHOULD |

## Scenarios

### TI-1: Happy path — `make test-all`

- GIVEN a developer on a machine with Docker and make
- WHEN `make test-all` is executed from the project root
- THEN Docker builds the image, runs unit tests first, then integration tests
- AND exit code 0 indicates all tests pass

### TI-2: Happy path — CI pipeline green

- GIVEN a PR is opened against main
- WHEN CI triggers on push
- THEN lint, typecheck, unit, and integration stages run sequentially
- AND coverage report is generated
- AND the pipeline passes if all stages succeed and coverage >= 80%

### TI-3: Error case — Docker build failure

- GIVEN a broken dependency in `pyproject.toml`
- WHEN `make test-all` executes the Docker build step
- THEN Docker build fails with a non-zero exit code
- AND the error message includes the dependency resolution failure

## Input / Output Contracts

| Artifact | Purpose |
|----------|---------|
| `Dockerfile` | Reproducible test environment definition |
| `docker-compose.yml` | Service orchestration for multi-container testing |
| `Makefile` | Developer-facing command targets |
| `.github/workflows/ci.yml` | CI pipeline definition |
| `pyproject.toml` | Build system + dependency management |

## Clean Architecture Layer Mapping

| Layer | Responsibility |
|-------|---------------|
| Framework | Dockerfile, docker-compose, Makefile, CI config |
| — | Infrastructure — supports all layers equally |

## Acceptance Criteria

- [ ] `docker build` completes in under 5 minutes on first build (layer caching subsequent)
- [ ] `make test-unit` runs without Docker and without SparkSession
- [ ] `make test-all` inside Docker completes in under 10 minutes
- [ ] Coverage report is generated and posted as CI artifact
- [ ] CI pipeline renders checks on GitHub PR page (status checks)
