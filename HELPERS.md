# spark_eda — Helpers

Quick reference for common commands, patterns, and conventions.

---

## Common Commands

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m contract
pytest -m benchmark

# Run a single test file
pytest tests/integration/test_spark_data_provider.py

# Run with coverage
pytest --cov=spark_eda

# Lint
ruff check src/ tests/ scripts/

# Type check
mypy src/spark_eda tests scripts

# Format
ruff format src/ tests/ scripts/
```

---

## Creating a New Quality Factor

Quality factors live under `src/spark_eda/domain/services/quality_factors/`. Each dimension is a module with a `calcular_score` function decorated with `@registrar`.

### Step-by-step

1. **Scaffold the dimension:**
   ```bash
   python scripts/scaffold_factor.py <nome_dimensao>
   ```
   This creates:
   - `src/spark_eda/domain/services/quality_factors/<nome>.py`
   - `tests/contract/test_<nome>_contract.py`
   - Registers the module in the `__init__.py` import chain

2. **Implement factor functions** in `<nome>.py`:
   ```python
   def _meu_fator(profile: DataProfile) -> QualityFactor:
       colunas_afetadas: list[str] = []
       # ... compute logic ...
       return QualityFactor(
           nome="Nome legível do fator",
           score=0.95,
           peso_interno=0.5,
           contribuicao=0.475,
           razao="Explicação do score.",
           severidade=Severity.LOW,
           colunas_afetadas=colunas_afetadas,
       )
   ```

3. **Wire factors into `calcular_score`:**
   ```python
   @registrar("minha_dimensao")
   def calcular_score(profile: DataProfile) -> list[QualityFactor]:
       return [_meu_fator(profile)]
   ```

4. **Add dimension weight** in `src/spark_eda/domain/services/quality_calculator.py`:
   ```python
   DIMENSION_WEIGHTS: dict[str, float] = {
       ...
       "minha_dimensao": 0.15,
   }
   ```

5. **Update contract tests** and write integration tests.

### Example (existing)

| Dimension   | Module         | Factors                                                   |
|-------------|----------------|-----------------------------------------------------------|
| completude  | completeness   | non-null ratio, row completeness, empty strings, zero-length |
| unicidade   | uniqueness     | duplicate rows, cardinality ratio                         |

---

## Creating a New Computation Strategy

Strategies are pure computation functions in `src/spark_eda/adapters/`.

### Step-by-step

1. **Scaffold the strategy:**
   ```bash
   python scripts/scaffold_strategy.py <nome_estrategia>
   ```
   This creates:
   - `src/spark_eda/adapters/<nome>.py`
   - `tests/contract/test_<nome>_contract.py`

2. **Implement the logic** in `<nome>.py`:
   ```python
   def compute_<nome>(
       *,
       config: dict[str, Any] | None = None,
   ) -> Any:
       # real implementation here
       pass
   ```

---

## How to Write AAA Tests

Every test **must** follow the **Arrange-Act-Assert** pattern with explicit section comments.

```python
def test_something(self) -> None:
    """Docstring explicando o que está sendo testado."""
    # Arrange
    entrada: type = valor
    expected: type = valor_esperado

    # Act
    resultado: type = funcao_sob_teste(entrada)

    # Assert
    assert resultado == expected
```

Rules:
- One logical assertion per test (or multiple assertions about the same result)
- Use `# Arrange`, `# Act`, `# Assert` comments (not `# Given`/`# When`/`# Then`)
- Variable names are fully explanatory (`entrada`, `resultado`, `esperado`)
- Docstrings in Portuguese for test methods
- Use `...` (Ellipsis) in the Arrange section when no setup is needed

---

## PySpark Gotchas

| Pitfall | Explanation | How to Avoid |
|---------|-------------|--------------|
| `df.show()` truncates | `show()` truncates long strings and columns | Use `df.toPandas().to_dict()` for inspection |
| `collect()` loads all data | Pulls all data to driver, risk of OOM | Always `limit()` or `sample()` before `collect()` |
| Lazy evaluation | Transformations don't execute until an action runs | Call `count()`, `show()`, `collect()` to force evaluation |
| `F.col()` vs `F.lit()` | `F.col()` references a column name, `F.lit()` is a literal | `df.filter(F.col("age") > F.lit(18))` |
| Schema inference | `createDataFrame()` infers types — can surprise | Always define `StructType` explicitly in tests |
| `approxQuantile` speed | Approximate quantiles are fast but non-deterministic | Use `relativeError=0.0` for exact (slower) or `0.01` for tests |
| `F.count()` ignores nulls | `F.count("col")` only counts non-null values | Use `F.count(F.lit(1))` for total row count |
| Shuffle partitions | Default 200 partitions kills test performance | Set `spark.sql.shuffle.partitions = "1"` in tests |
| `local[1]` vs `local[*]` | `local[1]` uses one thread (deterministic), `local[*]` uses all | Use `local[1]` for tests, `local[*]` for exploration |
| `rlike()` is case-sensitive | Regex patterns in `rlike()` are case-sensitive by default | Use `(?i)` prefix or compile with `re.IGNORECASE` |

---

## Clean Architecture Layer Rules

```
┌────────────────────────────────────────────────┐
│                  Use Cases                      │
│  (ports: DataProvider, CacheProvider, Presenter)│
├────────────────────────────────────────────────┤
│                   Domain                        │
│  (entities, value objects, services, factors)   │
├────────────────────────────────────────────────┤
│                 Adapters                        │
│  (providers, controllers, presenters, renderers)│
├────────────────────────────────────────────────┤
│              Framework / Spark                  │
│  (SparkSession, config, exceptions)            │
└────────────────────────────────────────────────┘
```

| Layer | Dependencies | Can import from |
|-------|--------------|-----------------|
| **Domain** | None (pure Python) | Only stdlib, value objects |
| **Use Cases** | Domain | Domain, Ports |
| **Adapters** | Use Cases, Domain | Use Cases, Domain, Framework |
| **Framework** | PySpark | PySpark only |

**Hard rules:**
- Domain NEVER imports from Adapters or Framework
- Use Cases NEVER access PySpark directly (use `DataProvider` port)
- Adapters depend inward (toward Use Cases and Domain)
- Framework code is only consumed by Adapters, never by Domain

**File naming:**
- Domain: snake_case feature name (`column_metadata.py`, `data_profile.py`)
- Adapters: role-based (`spark_data_provider.py`, `json_serializer.py`)
- Tests: mirror source structure (`tests/integration/`, `tests/contract/`, `tests/unit/`)
