# Contributing to spark_eda

## Development Setup

```bash
# Clone and install
git clone https://github.com/usuario/spark-eda.git
cd spark-eda
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Project Structure

```
src/spark_eda/
├── adapters/          # I/O, renderers (HTML, text, JSON), OmniRoute AI
├── application/       # DTOs, reports, use-case orchestration
├── domain/            # Core business logic, quality scoring, insights
├── framework/         # Spark session management, config
├── utils/             # Hashing, formatting
tests/
├── unit/              # Fast, isolated unit tests
├── contract/          # DTO shape and serialization contracts
└── integration/       # Spark-required integration tests
```

## Running Tests

```bash
# Unit + contract (fast, no Spark needed)
pytest tests/unit tests/contract

# All tests (requires Spark)
pytest

# Coverage
pytest --cov=spark_eda
```

## Code Quality

```bash
ruff format .
ruff check --fix
mypy src/spark_eda
```

## Pull Request Process

1. Open an issue describing the problem or feature.
2. Fork the repo and create a branch from `main`.
3. Write tests covering the change (both positive and edge cases).
4. Ensure all CI checks pass (ruff, mypy, pytest, coverage ≥ 95%).
5. Submit PR with a clear description linking to the issue.

## AI Commentary (OmniRoute)

Changes to the AI commentary system (`src/spark_eda/adapters/omniroute/`) must:
- Maintain backward compatibility (AI-disabled fallback).
- Keep the single-prompt design (one LLM call per report).
- Preserve graceful degradation: any failure returns `AiCommentary` with `None` fields.
- Maintain ≥ 95% coverage on the omniroute module.
