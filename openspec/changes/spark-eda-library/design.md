# Design: spark_eda — Distributed EDA Library

## Technical Approach

Layer-by-layer build from inside-out following Clean Architecture (4 layers: Domain → Use Cases → Adapters → Framework). Each capability maps to one Clean Architecture concern: entities and services live in Domain, orchestration lives in Use Cases, Spark computation lives in Adapters, config/infra lives in Framework. Cross-layer wiring via Dependency Injection in a single Composite Root (`__init__.py`).

**Dependency Rule**: Source code dependencies point INWARD. Domain = zero external deps. Use Cases = only Domain + ports. Adapters = implement ports. Framework = composite root wiring every concrete implementation.

---

## 1. Overall Architecture Design

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER (Data Engineer)                              │
│                                                                          │
│  spark_eda.analyze(df)         spark_eda.assess_quality(df)              │
│       │                                 │                                │
│       ▼                                 ▼                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    spark_eda PUBLIC FACADE                         │  │
│  │  __init__.py: analyze(), assess_quality()                          │  │
│  │  framework/config.py: EDAConfig, QualityConfig                     │  │
│  │  framework/spark_session.py: get_or_create_spark()                 │  │
│  └──────────┬────────────────────────────────────────┬────────────────┘  │
│             │  delegates to                          │                    │
│             ▼                                        ▼                    │
│  ┌──────────────────────┐           ┌──────────────────────────┐         │
│  │ AnalyzeController    │           │ QualityController         │         │
│  │ (adapters/)          │           │ (adapters/)               │         │
│  └──────────┬───────────┘           └──────────┬───────────────┘         │
│             │  injects & calls                  │                         │
│             ▼                                   ▼                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    USE CASES LAYER                                 │  │
│  │                                                                     │  │
│  │  AnalyzeDatasetUseCase  AssessQualityUseCase                       │  │
│  │  ┌────────────────────────────────────────────────────────────┐    │  │
│  │  │  PORTS: DataProvider │ CacheProvider │ OutputPresenter     │    │  │
│  │  └────────────────────────────────────────────────────────────┘    │  │
│  └──────────┬────────────────────────────────────────┬────────────────┘  │
│             │  calls via ports                       │                    │
│             ▼                                        ▼                    │
│  ┌──────────────────┐   ┌────────────┐   ┌───────────────────────┐     │
│  │ SparkDataProvider │   │ LRUCache   │   │ AnalysisPresenter     │     │
│  │ (adapters/)       │   │ (adapters/)│   │ QualityPresenter      │     │
│  │  single-pass agg  │   │ 128-entry  │   │ (adapters/)           │     │
│  └────────┬─────────┘   └────────────┘   └──────────┬────────────┘     │
│           │  returns                                 │                    │
│           ▼                                          ▼                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    DOMAIN LAYER (pure Python)                      │  │
│  │                                                                     │  │
│  │  Entities: DataProfile, ColumnProfile, QualityScore, DatasetAnaly. │  │
│  │  Services: QualityCalculator, ColumnClassifier, InsightEngine      │  │
│  │  VOs:      DataType, Severity, BusinessType, CorrelationMethod...  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐    │
│  │ HTML Renderer    │   │ Text Renderer    │   │ JSON Serializer  │    │
│  │ (adapters/)      │   │ (adapters/)      │   │ (adapters/)      │    │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘    │
│                           Reports: EDAReport, QualityReport             │
│                           DTOs: Section DTOs (Overview, Schema, ...)   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Capability Dependency Graph

```
data-profiling ───► quality-scoring ───► analysis-orchestration ───► report-rendering
      │                                                                    │
      ▼                                                                    │
column-classification ◄────────────────────────────────────────────────────┘
      │                                                                    │
      └──► caching ◄──► spark-infrastructure ◄──► developer-tooling
                  │
                  ▼
          testing-infrastructure
```

**Direction**: arrow means "depends on". Dependency flows DOWN. `data-profiling` must exist before `quality-scoring`, which must exist before `analysis-orchestration`, etc. `spark-infrastructure` and `caching` are horizontal services. `developer-tooling` and `testing-infrastructure` are meta-capabilities with no runtime dependency on other capabilities.

### Module Dependency Injection Wiring (Composite Root)

```
spark_eda/__init__.py  (Composite Root — only place that knows ALL concrete classes)
│
├── analyze(df, config=None):
│   ├── config = config or EDAConfig()
│   ├── spark = get_or_create_spark(config)
│   ├── provider = SparkDataProvider(spark)
│   ├── cache = LRUCacheProvider(capacity=128)
│   ├── classifier = ColumnClassifier(spark, config)
│   ├── quality_calc = QualityCalculator()
│   ├── presenter = AnalysisPresenter(HTMLRenderer(), TextRenderer(), JSONSerializer())
│   ├── controller = AnalyzeController(provider, cache, classifier, quality_calc, presenter)
│   └── result = controller.execute(df, config)
│
├── assess_quality(df, config=None):
│   ├── config = config or QualityConfig()
│   ├── spark = get_or_create_spark(config)
│   ├── provider = SparkDataProvider(spark)
│   ├── cache = LRUCacheProvider(capacity=128)
│   ├── quality_calc = QualityCalculator()
│   ├── presenter = QualityPresenter(HTMLRenderer(), TextRenderer(), JSONSerializer())
│   ├── controller = QualityController(provider, cache, quality_calc, presenter)
│   └── result = controller.execute(df, config)
```

### Startup/Initialization Sequence

```
import spark_eda  →  No SparkSession created (lazy)
                     No config loaded (lazy)
                     Only module-level imports (entities, pure functions)

spark_eda.analyze(df)  →
    1. EDAConfig(config or EDAConfig())   — config validation
    2. get_or_create_spark(config)        — reuse existing or create new
       a. Check if active SparkSession exists
       b. If yes: verify config compatibility
       c. If no:  SparkSession.builder().config(...).getOrCreate()
    3. SparkDataProvider(spark)           — adapter, touches PySpark
    4. LRUCacheProvider(128)              — adapter, pure Python
    5. ColumnClassifier(spark, config)    — adapter, Spark expressions
    6. QualityCalculator()                — domain service, pure Python
    7. AnalysisPresenter(...)             — adapter, pure Python
    8. AnalyzeController.execute(df)      — orchestrates the flow
       a. compute_fingerprint(df) → cache key
       b. check cache → hit? return cached EDAReport
       c. DataProvider.profile(df) → DataProfile
       d. ColumnClassifier.classify(df) → dict[column, BusinessType]
       e. QualityCalculator.compute(profile) → QualityScore
       f. DatasetAnalysis(profile, quality, classification, ...)
       g. cache.set(fingerprint, analysis)
       h. Presenter.present(analysis) → EDAReport
```

### Clean Architecture Layer Enforcement Rules

| Rule | Check | Enforced By |
|------|-------|-------------|
| Domain imports NOTHING external | `grep -r "import pyspark\|from pyspark\|import pandas" spark_eda/domain/` | CI `lint` step |
| Domain has ZERO framework deps | `grep -r "spark_eda.use_cases\|spark_eda.adapters\|spark_eda.framework" spark_eda/domain/` | CI `lint` step |
| Use Cases only import domain + ports | `grep -r "spark_eda.adapters\|spark_eda.framework\|pyspark" spark_eda/use_cases/` | CI `lint` step |
| Use Cases do NOT import PySpark | `grep -r "pyspark" spark_eda/use_cases/` | CI `lint` step |
| Adapters import use_cases/ports + domain | Manual code review | PR review |
| Adapters USE Spark only in providers/ | `grep -r "pyspark" spark_eda/adapters/` (allowed only in `providers/`) | CI `lint` step |
| Framework imports everything | Not enforced (Composite Root purpose) | — |
| Domain tests run with zero Spark deps | `pytest tests/unit/ --ignore=tests/integration/` | `make test-unit` |

---

## 2. Per-Capability Design

---

### 2.1 Data Profiling

**Sequence Diagram**:

```
AnalyzeController              SparkDataProvider                  Domain Entities
     │                               │                                  │
     │  execute(df, config)           │                                  │
     │──────────────────────────────►│                                  │
     │                               │                                  │
     │                    ┌─ agg(exprs).collect()  (single pass)        │
     │                    │  count, mean, stddev, min, max,             │
     │                    │  skewness, kurtosis, approx_count_distinct  │
     │                    │  approxQuantile for percentiles             │
     │                    └─► row → DataProfile(row, schema)            │
     │                               │                                  │
     │  ◄─── DataProfile ────────────│                                  │
     │                                                                  │
     │  ─ ─ computes fingerprint ─ ─                                   │
     │  ─ ─ checks cache ─ ─ ─ ─ ─ ─                                   │
```

**Key Classes**:

| Layer | Class | Responsibility |
|-------|-------|----------------|
| Domain | `DataProfile` | Root entity: row_count, schema, column_profiles dict. Methods: `column(name)`, `null_ratio(col)`, `columns_by_type(type)` |
| Domain | `ColumnProfile` | Per-column: count, null_count, distinct_count, min, max, mean, stddev, stats (union type for NumericStats/CategoricalStats/TemporalStats) |
| Domain | `ColumnMetadata` | name, data_type, nullable, inferred_business_type |
| Domain | `Statistic` | Sealed union: `NumericStats`, `CategoricalStats`, `TemporalStats` |
| Domain | `DataType` | Enum: INTEGER, LONG, DOUBLE, STRING, BOOLEAN, DATE, TIMESTAMP, DECIMAL, UNKNOWN |
| Adapter | `SparkDataProvider.profile(df)` | Computes all profile stats in single-pass agg, returns `DataProfile` |

**Interface Contract**:

```python
# use_cases/ports/data_provider.py
class DataProvider(ABC):
    @abstractmethod
    def compute_profile(self, df: DataFrame, config: EDAConfig) -> DataProfile:
        """Computa DataProfile a partir de um DataFrame PySpark.
        Retorna uma ENTIDADE do domínio, nunca um dict.
        """
        ...

# adapters/providers/spark_data_provider.py
class SparkDataProvider(DataProvider):
    def compute_profile(self, df: DataFrame, config: EDAConfig) -> DataProfile:
        exprs = self._build_agg_expressions(df.schema, config)
        row = df.agg(*exprs).collect()[0]  # single pass, 1 row
        return DataProfile.from_agg_row(row, df.schema)
```

**State Management**: `DataProfile` is a frozen dataclass (immutable). No mutable state other than the DataFrame in the adapter (ephemeral — freed after `collect()`).

**Error Handling**:
| Scenario | Exception | Layer |
|----------|-----------|-------|
| `df` is None | `ValueError("DataFrame must not be None")` | Controller |
| Empty DataFrame (zero rows) | No exception — returns DataProfile with all zeroed stats | Adapter |
| Schema has zero columns | `ProfilingError("Cannot profile: zero columns")` | Adapter |
| Spark query fails | `ProfilingError("Spark computation failed: {msg}")` wrapping original exception | Adapter |

**Design Decisions**:
- **Single-pass aggregation**: All numeric stats computed in ONE `agg()` call → ONE `collect()` → minimal driver memory.
- **Approximate distinct count**: `approx_count_distinct()` via HyperLogLog — avoids shuffle for exact count on high-cardinality columns.
- **Exact count**: `count(*)` is always exact (cheap with Parquet row group stats).
- **Percentiles**: `approxQuantile()` (Greenwald-Khanna) to avoid sorting full dataset.

**Integration Points**: `DataProfile` consumed by `QualityCalculator` and `AnalysisPresenter`. Profile ID used as cache key fingerprint.

---

### 2.2 Quality Scoring

**Sequence Diagram**:

```
AssessQualityUseCase            QualityCalculator              QualityFactor Registry
     │                               │                                  │
     │  execute(request)              │                                  │
     │                               │                                  │
     │  provider.profile(df)          │                                  │
     │  → DataProfile                │                                  │
     │                               │                                  │
     │  compute(profile) ───────────►│                                  │
     │                               │                                  │
     │                    for each factor in FACTOR_REGISTRY:            │
     │                    │  factor_fn(profile, weight) → QualityFactor │
     │                    │◄─────────────────────────────────────────────│
     │                    │                                              │
     │                    aggregate → QualityScore                       │
     │  ◄─── QualityScore ────────────│                                  │
     │                               │                                  │
     │  cache.set(fingerprint)       │                                  │
```

**Key Classes**:

| Layer | Class | Responsibility |
|-------|-------|----------------|
| Domain | `QualityScore` | overall: float (0-100), factors: dict[str, QualityFactor], column_scores: dict[str, float], dimensions: dict[str, QualityDimension] |
| Domain | `QualityFactor` | name, score (0-1), weight_within_dim, contribution_to_total, reason, severity, affected_columns |
| Domain | `QualityDimension` | name, weight, score, factors list |
| Domain | `QualityCalculator` | Domain service: registers factors via decorator registry, iterates all registered factors, aggregates QualityScore |
| Domain | `FACTOR_REGISTRY` | `dict[str, Callable[[DataProfile, float], QualityFactor]]` — decorator-based registry |
| Adapter | `SparkComputeRegistry` | Mirror registry for Spark-side factor computation (factors that need raw DataFrame access) |

**Interface Contract**:

```python
# domain/services/quality_calculator.py
FACTOR_REGISTRY: dict[str, Callable[[DataProfile, float], QualityFactor]] = {}

def registrar_factor(nome: str) -> Callable:
    """Decorator que registra um fator de qualidade no registry global."""

class QualityCalculator:
    def compute(self, profile: DataProfile) -> QualityScore:
        """Aplica TODOS os fatores registrados ao DataProfile.
        Fatores são aplicados independentemente — cada um gera um QualityFactor.
        O score final é a média ponderada dos fatores agregados por dimensão.
        """
        factors: list[QualityFactor] = []
        for nome, fn in FACTOR_REGISTRY.items():
            factor = fn(profile, self._get_weight(nome))
            factors.append(factor)
        return QualityScore.from_factors(factors)

# domain/entities/quality_score.py
@dataclass(frozen=True)
class QualityFactor:
    name: str
    score: float           # 0.0 - 1.0
    weight_within_dimension: float
    contribution_to_total: float
    reason: str
    severity: Severity
    affected_columns: tuple[str, ...]
```

**State Management**: `QualityCalculator` is stateless. All factor scores are computed fresh from `DataProfile` on each `compute()` call.

**Error Handling**:
| Scenario | Exception | Layer |
|----------|-----------|-------|
| Empty profile (zero columns) | `ValueError("Cannot assess quality: empty profile")` | Domain |
| Factor returns score outside [0,1] | `AssertionError` (internal invariant) | Domain |
| Factor name longer than 64 chars | `ValueError("Factor name exceeds 64 characters")` | Domain |
| No factors registered | Returns empty QualityScore (overall=0, zero factors) — no exception | Domain |
| Factor weight sum != 1.0 | Logged as warning, not error (auto-normalized) | Domain |

**Design Decisions**:
- **Factor registry via decorator**: New factors are added by creating a module, decorating with `@registrar_factor`. Open/Closed Principle — no modification to QualityCalculator.
- **Two-part factors**: Domain side computes score from DataProfile (pure math). Adapter side computes raw DataFrame metrics and injects them into DataProfile. This keeps QualityCalculator Spark-free.
- **Determinism guaranteed**: Same DataProfile → same QualityScore. No randomness, no external state.
- **Per-factor documentation**: Every factor has a `reason` field explaining exactly what was computed and why the score is what it is.

**Integration Points**: Receives `DataProfile` from `SparkDataProvider`. Output `QualityScore` consumed by `AnalysisPresenter`, `InsightEngine`, `DatasetAnalysis`.

---

### 2.3 Analysis Orchestration

**Sequence Diagram**:

```
AnalyzeController          AnalyzeDatasetUseCase         DataProvider        Domain Services
     │                           │                           │                    │
     │  execute(df, config)      │                           │                    │
     │─────────────────────────►│                           │                    │
     │                           │                           │                    │
     │              fingerprint = compute_key(df, config)    │                    │
     │              cache.get(fingerprint) ──► cache miss    │                    │
     │                           │                           │                    │
     │              profile() ──────────────────────────────►│                    │
     │              ◄─── DataProfile ────────────────────────│                    │
     │                           │                           │                    │
     │              QualityCalc.compute(profile) ────────────│─────►             │
     │              ◄─── QualityScore ◄──────────────────────│─────────────────  │
     │                           │                           │                    │
     │              classify(df) ───────────────────────────►│                    │
     │              ◄─── dict[column, BusinessType] ─────────│                    │
     │                           │                           │                    │
     │              DatasetAnalysis(profile, quality, ...)   │                    │
     │              cache.set(fingerprint, analysis)         │                    │
     │                           │                           │                    │
     │  ◄─── DatasetAnalysis ────│                           │                    │
     │                           │                           │                    │
     │  AnalysisPresenter        │                           │                    │
     │  .present(analysis) → EDAReport                      │                    │
     │  ◄─── EDAReport ──────────│                           │                    │
     ▼                           ▼                           ▼                    ▼
```

**Key Classes**:

| Layer | Class | Responsibility |
|-------|-------|----------------|
| Use Case | `AnalyzeDatasetUseCase` | Orchestrates full EDA: profile → quality → classify → assemble DatasetAnalysis |
| Use Case | `AssessQualityUseCase` | Lightweight: profile → quality score → return QualityScore |
| Use Case | `AnalyzeRequest` | Request DTO: columns, config, fingerprint |
| Port | `DataProvider` | Abstract profile computation |
| Port | `CacheProvider` | Abstract cache get/set/invalidate/clear |
| Port | `OutputPresenter` | Abstract entity → DTO conversion |
| Adapter | `AnalyzeController` | Translates DataFrame + config → use case call, wires dependencies |
| Adapter | `QualityController` | Same for quality-only flow |
| Adapter | `AnalysisPresenter` | DatasetAnalysis → EDAReport |
| Adapter | `QualityPresenter` | QualityScore → QualityReport |

**Interface Contract**:

```python
# use_cases/ports/data_provider.py
class DataProvider(ABC):
    @abstractmethod
    def compute_profile(self, df: DataFrame, config: EDAConfig) -> DataProfile: ...

# use_cases/ports/cache_provider.py
class CacheProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Any | None: ...
    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...
    @abstractmethod
    def invalidate(self, key: str) -> None: ...
    @abstractmethod
    def clear(self) -> None: ...

# use_cases/ports/output_presenter.py
class OutputPresenter(ABC):
    @abstractmethod
    def present_report(self, analysis: DatasetAnalysis) -> EDAReport: ...
    @abstractmethod
    def present_quality(self, score: QualityScore) -> QualityReport: ...

# use_cases/analyze_dataset.py
class AnalyzeDatasetUseCase:
    def __init__(self, provider: DataProvider, cache: CacheProvider,
                 quality_calc: QualityCalculator, classifier: ColumnClassifier):
        ...

    def execute(self, df: DataFrame, config: EDAConfig) -> DatasetAnalysis:
        ...
```

**State Management**: Use case instances are stateless (all dependencies injected). State only lives in the returned `DatasetAnalysis` entity.

**Error Handling**:
| Scenario | Exception | Layer |
|----------|-----------|-------|
| DataFrame is None | `ValueError("DataFrame must not be None")` | Controller |
| Empty DataFrame (zero columns) | `ValueError("DataFrame has no columns")` | Controller |
| Spark query fails | `EDAException` wrapping Spark exception | Adapter → propagates through use case |
| Cache provider fails | Logged as warning, continues without cache | Use case (catch + log + recompute) |
| Presenter fails | EDAReport with error section, not raw exception | Controller |

**Design Decisions**:
- **Use case is stateless**: All dependencies injected via constructor. `execute()` receives only the request — no mutable state.
- **Cache-first pattern**: Check cache before any computation. Cache miss → compute → cache set.
- **Error containment**: Spark exceptions caught at adapter boundary, wrapped in EDAException hierarchy, propagated to user as error report (not stack trace).
- **Presenter separation**: Use case returns Domain entity (`DatasetAnalysis`). Presenter converts to DTO. This means the use case is testable without any presentation concern.

**Integration Points**: Touches ALL other capabilities: calls DataProvider, CacheProvider, QualityCalculator, ColumnClassifier, OutputPresenter. Central orchestrator.

---

### 2.4 Report Rendering

**Sequence Diagram**:

```
AnalysisPresenter              EDAReport DTO              HTML/Text Renderers
     │                              │                           │
     │  present(analysis)            │                           │
     │  ──────────────────────────►│                           │
     │                              │                           │
     │  DatasetAnalysis → EDAReport│                           │
     │  DataProfile → OverviewSect │                           │
     │  ColumnProfile[] → StatsSect│                           │
     │  QualityScore → QualitySect │                           │
     │  Classifications → ClassSect│                           │
     │                              │                           │
     │  EDAReport._repr_html_() ────│──────────────────────────►│
     │                              │         HTMLRenderer      │
     │  ◄─── HTML string ◄──────────│◄─────────────────────────│
     │                              │                           │
     │  EDAReport.__str__() ────────│──────────────────────────►│
     │                              │         TextRenderer      │
     │  ◄─── Text string ◄──────────│◄─────────────────────────│
```

**Key Classes**:

| Layer | Class | Responsibility |
|-------|-------|----------------|
| Adapter | `EDAReport` | Composite DTO: overview, schema, quality, stats, distributions, correlations, outliers, insights, recommendations, metadata sections. Each section is a frozen dataclass. |
| Adapter | `OverviewSection` | Row count, column count, size estimate, duplication ratio |
| Adapter | `SchemaSection` | Per-column: name, type, nullable, business_type |
| Adapter | `QualitySection` | Overall score + dimension breakdown + top penalizers |
| Adapter | `StatsSection` | Per-column: count, mean, std, min, max, null%, distinct% |
| Adapter | `ReportMetadata` | Timestamp, duration, spark_eda version, config snapshot |
| Adapter | `Section` (ABC) | Protocol: `to_dict()`, `_repr_html_()`, `__str__()` |
| Adapter | `HTMLRenderer` | Renders EDAReport → HTML5 string with inline CSS |
| Adapter | `TextRenderer` | Renders EDAReport → monospace text (120-char width) |
| Adapter | `JSONSerializer` | Serializes EDAReport → JSON dict |
| Adapter | `HtmlSafeString` | Value object that auto-escapes HTML chars |

**Interface Contract**:

```python
# adapters/dto/__init__.py
class Section(ABC):
    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...
    @abstractmethod
    def _repr_html_(self) -> str: ...
    @abstractmethod
    def __str__(self) -> str: ...

# adapters/dto/eda_report.py
@dataclass(frozen=True)
class EDAReport:
    overview: OverviewSection
    schema: SchemaSection
    quality: QualitySection
    stats: StatsSection
    distributions: DistributionSection | None
    correlations: CorrelationSection | None
    outliers: OutlierSection | None
    insights: InsightsSection | None
    recommendations: RecommendationsSection | None
    metadata: ReportMetadata

    def _repr_html_(self) -> str: ...   # Jupyter auto-display
    def __str__(self) -> str: ...       # terminal display
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> EDAReport: ...

# adapters/renderers/html_renderer.py
class HTMLRenderer:
    def render_report(self, report: EDAReport) -> str:
        """Produz HTML5 válido com CSS inline (zero dependências externas)."""
        ...

    def render_section(self, section: Section) -> str:
        """Renderiza seção individual (independência de renderização)."""
        ...
```

**State Management**: All DTOs are frozen dataclasses — immutable, hashable, thread-safe. Renderers are stateless singletons.

**Error Handling**:
| Scenario | Exception | Layer |
|----------|-----------|-------|
| Section is None (not computed) | NullSection pattern — renders empty string | Adapter |
| HTML special chars in column names | Auto-escaped via `HtmlSafeString` | Adapter |
| Empty report (no sections) | Minimal message: "No data available" | Renderer |
| JSON serialization of non-serializable value | `TypeError` caught, replaced with str() | Adapter |

**Design Decisions**:
- **Composite pattern**: `EDAReport` is a composite of `Section` objects. Each section handles its own rendering via protocol methods.
- **Null Object pattern**: `None` sections replaced with `NullSection` that renders empty — avoids `if section is not None` everywhere.
- **Dual-protocol rendering**: Every section implements both `_repr_html_()` (Jupyter) and `__str__()` (terminal). Jupyter auto-displays `_repr_html_`.
- **HTML escape**: Column names and values are ALWAYS escaped — XSS prevention.
- **Zero external CSS/JS**: Inline CSS only — reports are self-contained (email-friendly, notebook-friendly).

**Integration Points**: Receives `DatasetAnalysis` from `AnalysisPresenter`. Consumed by `HTMLRenderer`/`TextRenderer`/`JSONSerializer`. No upstream dependencies on other capabilities — pure adapter-layer concern.

---

### 2.5 Column Classification

**Key Classes**:

| Layer | Class | Responsibility |
|-------|-------|----------------|
| Domain | `BusinessType` | Enum: CPF, CNPJ, EMAIL, PHONE, DATE, ZIP_CODE, IP_V4, UUID, URL, UNKNOWN |
| Adapter | `ColumnClassifier` | Heuristic: 2-phase detection (name match → regex validation) using Spark `rlike()` |
| Adapter | `BusinessPatterns` | Pattern library with regex patterns per business type |

**Interface Contract**:

```python
# domain/value_objects/inferred_type.py
class BusinessType(str, Enum):
    CPF = "cpf"
    CNPJ = "cnpj"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    ZIP_CODE = "zip_code"
    IP_V4 = "ip_v4"
    UUID = "uuid"
    URL = "url"
    UNKNOWN = "unknown"

# adapters/providers/column_inferrer.py
class ColumnClassifier:
    def __init__(self, spark: SparkSession, config: EDAConfig):
        self._spark = spark
        self._patterns = BusinessPatterns(config)

    def classify(self, df: DataFrame) -> dict[str, BusinessType]:
        """Classifica colunas por nome e validação regex via Spark rlike().
        
        1. Name-based match: se nome da coluna contém keyword → tipo candidato
        2. Regex validation: para colunas string ambíguas, verifica via rlike()
           se >80% dos non-null values match o pattern
        3. Majority rule: >80% match → classifica; <80% → UNKNOWN
        """
        ...
```

**Error Handling**:
| Scenario | Exception | Layer |
|----------|-----------|-------|
| Empty DataFrame (zero rows) | Falls back to name-based detection only | Adapter |
| Column with all nulls | Returns UNKNOWN (no data to match against) | Adapter |
| No name match and no data (empty) | Returns UNKNOWN for every column | Adapter |
| Unsupported column type (not string) | Skipped (only string columns are classified) | Adapter |

**Design Decisions**:
- **Spark-native regex**: All pattern matching via `rlike()` (Spark SQL native) — zero UDFs, runs as Catalyst expression.
- **Two-phase detection**: Name match is fastest and requires zero data scanning. Regex validation only for ambiguous name → data scan.
- **80% threshold**: A column must have >80% of non-null values matching the pattern to be classified.
- **Deterministic**: Same DataFrame + config → same classification. No ML, no randomness.

**Integration Points**: Classification results stored in DataProfile (as ColumnMetadata.inferred_business_type). Used by QualityScore (accuracy dimension) and EDAReport (schema section). Classification is a DataProvider concern (same Spark scan).

---

### 2.6 Caching

**Key Classes**:

| Layer | Class | Responsibility |
|-------|-------|----------------|
| Port | `CacheProvider` | Abstract interface (get, set, invalidate, clear) |
| Adapter | `LRUCacheProvider` | Thread-safe in-memory LRU with TTL, capacity=128 |
| Domain | `Fingerprint` | Value object: SHA256(schema_json + config_hash + plan_hash_partial) |

**Interface Contract**:

```python
# use_cases/ports/cache_provider.py
class CacheProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Any | None: ...
    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...
    @abstractmethod
    def invalidate(self, key: str) -> None: ...
    @abstractmethod
    def clear(self) -> None: ...

# adapters/providers/lru_cache_provider.py
class LRUCacheProvider(CacheProvider):
    def __init__(self, capacity: int = 128):
        self._capacity = capacity
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.expires_at and time.monotonic() > entry.expires_at:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)  # LRU update
            return entry.value
    ...
```

**State Management**: `LRUCacheProvider` maintains internal `OrderedDict` with `threading.Lock` for thread safety. State is ephemeral — lost when process exits.

**Error Handling**:
| Scenario | Exception | Layer |
|----------|-----------|-------|
| Non-string key passed to set/get | `TypeError("Cache key must be a string")` | Adapter |
| TTL expires | Treated as cache miss (returns None) | Adapter |
| Cache at capacity | LRU eviction (oldest entry removed) | Adapter |

**Design Decisions**:
- **Thread-safe**: `threading.Lock` around all operations. PySpark workers are separate processes, but user code and the driver may access cache from multiple threads.
- **TTL checked on get**: Expired entries are cleaned lazily on access, not via timer.
- **Fingerprint key**: `SHA256(schema.json() + config hash + truncated logical plan)`. Logical plan gives data sensitivity; schema gives structure sensitivity. Config hash gives parameter sensitivity.
- **Cache miss NOT an error**: Cache is optimization, not correctness. Use cases handle misses gracefully.

**Integration Points**: Used by `AnalyzeDatasetUseCase` and `AssessQualityUseCase` to avoid recomputing expensive profile/quality operations for unchanged DataFrames.

---

### 2.7 Spark Infrastructure

**Key Classes**:

| Layer | Class | Responsibility |
|-------|-------|----------------|
| Framework | `EDAConfig` | Frozen dataclass: app_name, shuffle_partitions, kryo, aqe_enabled, etc. Supports `from_dict()`, `from_yaml()`. Validates config keys. |
| Framework | `QualityConfig` | Similar for quality-only flow |
| Framework | `spark_session.get_or_create_spark(config)` | Returns existing SparkSession or creates new. Reuses if config matches. |
| Framework | `EDAException` | Base exception class for all spark_eda errors |
| Framework | `ProfilingError`, `QualityError`, `ClassificationError`, `ConfigurationError` | Typed exception hierarchy |

**Interface Contract**:

```python
# framework/config.py
@dataclass(frozen=True)
class SparkConfig:
    app_name: str = "spark_eda"
    shuffle_partitions: int | None = None
    kryo_serializer: bool = True
    aqe_enabled: bool = True
    additional_config: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        """Valida que todas as chaves em additional_config são
        prefixos Spark conhecidos (spark.*). Lança ConfigurationError
        se alguma chave for inválida."""
        ...

@dataclass(frozen=True)
class EDAConfig:
    spark: SparkConfig = field(default_factory=SparkConfig)
    max_categories: int = 50
    correlation_methods: tuple[str, ...] = ("pearson",)
    outlier_method: str = "iqr"
    enable_insights: bool = True
    sample_fraction: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> EDAConfig: ...
    @classmethod
    def from_yaml(cls, path: str) -> EDAConfig: ...

# framework/spark_session.py
_active_session: SparkSession | None = None

def get_or_create_spark(config: EDAConfig) -> SparkSession:
    global _active_session
    if _active_session is not None and _is_compatible(_active_session, config):
        return _active_session
    builder = SparkSession.builder.appName(config.spark.app_name)
    ...
    _active_session = builder.getOrCreate()
    return _active_session

# framework/exceptions.py
class EDAException(Exception):
    """Base exception for all spark_eda errors."""
    def __init__(self, message: str, cause: Exception | None = None): ...

class ConfigurationError(EDAException): ...
class ProfilingError(EDAException): ...
class QualityError(EDAException): ...
class ClassificationError(EDAException): ...
```

**State Management**: Global `_active_session` module variable holds the SparkSession singleton. `EDAConfig` is immutable frozen dataclass.

**Error Handling**:
| Scenario | Exception | Layer |
|----------|-----------|-------|
| Invalid Spark config key | `ConfigurationError` with invalid keys listed | Framework |
| SparkSession creation fails | `EDAException` wrapping the underlying Spark exception | Framework |
| Config YAML not found | `FileNotFoundError` (re-raised as `ConfigurationError`) | Framework |

**Design Decisions**:
- **Singleton session reuse**: Avoids "SparkSession already started" errors. Reuses if config is compatible.
- **Frozen config**: Immutable config prevents accidental mutation during analysis.
- **Config validation**: Valid Spark config keys checked at construction time, not at Spark session creation.
- **Exception hierarchy**: All custom exceptions inherit from `EDAException`, so users can `except EDAException` and catch everything.

**Integration Points**: `EDAConfig` consumed by ALL other capabilities. `spark_session` consumed by `SparkDataProvider` and `ColumnClassifier`. Framework is imported by everything.

---

### 2.8 Developer Tooling

**Key Artifacts**:

| File | Purpose |
|------|---------|
| `HELPERS.md` | Quick reference: project structure, setup, test commands, architecture rules, troubleshooting |
| `scripts/scaffold_factor.py` | Generates new quality factor: adapter Spark computation + domain score + AAA tests |
| `scripts/scaffold_strategy.py` | Generates new strategy (stats/correlation/outlier) + contract test |
| `scripts/scaffold_entity.py` | Generates new domain entity + unit test stub |
| `scripts/generate_fixtures.py` | Generates synthetic test data for known quality scenarios |

**Interface Contract**:

```bash
# CLI interface for scaffold tools
python scripts/scaffold_factor.py <factor_name> --dimension <dimension>

python scripts/scaffold_strategy.py <strategy_name> --domain <correlation|outlier|distribution>

python scripts/scaffold_entity.py <entity_name> <target_directory>

python scripts/generate_fixtures.py <dataset_type> --rows <count> --output <path>
```

**Scaffold Templates Location**: `scripts/templates/` (one per scaffold type)

**Design Decisions**:
- **Scaffolds create paired files**: Source + test together. Ensures test coverage is not an afterthought.
- **Cross-platform**: POSIX + Windows (Git Bash/WSL) compatible — no OS-specific assumptions.
- **AAA test template**: Arrange-Act-Assert sections pre-filled with mock imports specific to the target layer.

**Integration Points**: Meta-capability — aids developers, no runtime integration.

---

### 2.9 Testing Infrastructure

**Key Artifacts**:

| File | Purpose |
|------|---------|
| `Dockerfile` | Python 3.14-slim + OpenJDK 21 + PySpark 4.0+ |
| `docker-compose.yml` | Services: test, benchmark, shell, test-py314, test-py315 |
| `Makefile` | Targets: test-all, test-unit, test-integration, lint, typecheck, clean |
| `pyproject.toml` | Build system, deps, ruff/mypy/pytest config |
| `.github/workflows/ci.yml` | Stages: lint → typecheck → unit → integration → coverage → benchmark |
| `tests/fixtures/` | Shared test data (synthetic datasets) |
| `tests/unit/` | Pure Python tests (no Spark) |
| `tests/integration/` | Spark-dependent tests |
| `tests/contract/` | Strategy contract tests (abstract base test classes) |

**Test Layer Strategy**:

| Directory | Tool | Spark? | Docker? | Speed |
|-----------|------|--------|---------|-------|
| `tests/unit/` | pytest | ❌ | ❌ | ms |
| `tests/integration/` | pytest + PySpark | ✅ | ✅ | s |
| `tests/contract/` | pytest + ABC | ✅ | ✅ | s |
| `tests/benchmarks/` | pytest-benchmark | ✅ | ✅ | min |
| `tests/fixtures/` | shared data | ❌ | ❌ | — |

**Error Handling**:
| Scenario | Behavior |
|----------|----------|
| Docker build failure | Non-zero exit, error stream captured |
| Docker not installed | `make test-all` fails with clear message |
| Coverage below 80% | CI pipeline fails, report generated |

**Design Decisions**:
- **Docker-only integration**: PySpark requires JVM + Hadoop native binaries. Docker guarantees reproducible environment. Code is live-mounted for fast iteration (no rebuild for code changes).
- **Unit tests run outside Docker**: Pure pytest, no Spark, no JVM — runs in milliseconds.
- **CI mirrors local**: Same `docker-compose run --rm test` command used in both local dev and CI.
- **Layer caching in Docker**: Dependencies layer cached before code copy → fast rebuilds.
- **Test layer isolation**: Unit tests NEVER require Spark. Integration tests ALWAYS run in Docker.

**Integration Points**: Meta-capability — supports all source code layers equally.

---

## 3. Integration Design

### Data Provider Integration

```
SparkDataProvider
  │
  ├── compute_profile(df, config)
  │     └── ProfileBuilder
  │           ├── NumericStrategy  (for DOUBLE/LONG/INTEGER columns)
  │           ├── CategoricalStrategy  (for STRING/BOOLEAN columns)
  │           ├── TemporalStrategy  (for DATE/TIMESTAMP columns)
  │           └── all strategies return ColumnProfile entities
  │
  ├── classify_columns(df) → dict[str, BusinessType]
  │     └── ColumnClassifier
  │           ├── name_match() → candidate type
  │           └── regex_validate() → Spark rlike() expression tree
  │
  └── compute_fingerprint(df, config) → str
        └── hashlib.sha256(schema + config + plan)
```

### Use Case Coordination

```
AnalyzeDatasetUseCase.execute(df, config):
  1. RequestValidator.validate(df, config)           (domain)
  2. provider.compute_profile(df, config)            (adapter → domain entity)
  3. quality_calculator.compute(profile)             (domain)
  4. insight_engine.generate(profile, quality)       (domain)
  5. recommendation_engine.generate(insights)        (domain)
  6. DatasetAnalysis(profile, quality, insights, recs, metadata)  (domain entity)
  7. cache.set(fingerprint, analysis)                (adapter)
  8. → return DatasetAnalysis
```

### Presenter → DTO → Renderer Flow

```
DatasetAnalysis (domain entity)
     │
     ▼
AnalysisPresenter.present(analysis)
     │
     ├── DataProfile → OverviewSection + SchemaSection + StatsSection
     ├── QualityScore → QualitySection
     ├── dict[column, BusinessType] → ClassificationSection
     ├── list[Insight] → InsightsSection
     └── ReportMetadata (timestamp, duration, version)
     │
     ▼
EDAReport (DTO — frozen dataclass)
     │
     ├── ._repr_html_() → HTMLRenderer.render_report(report) → HTML5 string
     ├── .__str__()     → TextRenderer.render_report(report) → monospace text
     └── .to_dict()     → JSONSerializer.serialize(report) → dict
```

### Cache Integration in Use Case Flow

```
execute(df, config):
  1. fingerprint = Fingerprint.compute(df, config)
  2. cached = cache.get(fingerprint)
  3. if cached:
       return cached.DatasetAnalysis  (skip ALL computation)
  4. # no cache — compute everything
     profile = provider.compute_profile(df, config)
     quality = quality_calc.compute(profile)
     analysis = DatasetAnalysis(profile, quality, ...)
  5. cache.set(fingerprint, analysis, ttl=3600)
  6. return analysis
```

---

## 4. Architecture Decisions Summary

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | **Module layout** | Clean Architecture layers as top-level dirs | Dependency Rule is visually enforced. Import checker in CI. |
| 2 | **Dependency injection** | Constructor injection in use cases + Composite Root | Testable without mocks? No — but ports are mockable. Use cases testable with Mock(). |
| 3 | **API entry points** | Free-standing functions (`analyze()`, `assess_quality()`) wrapped in `__init__.py` | Discoverable, composable. Users import once and call. |
| 4 | **Config immutability** | Frozen dataclass for EDAConfig | Thread-safe, hashable, IDE-friendly. No accidental mutation. |
| 5 | **Cache strategy** | In-memory LRU with fingerprint key | No external infra needed. Fingerprint captures schema + config + plan. |
| 6 | **Quality factor registry** | Decorator-based registry (Open/Closed) | New factors added as modules without editing QualityCalculator. |
| 7 | **Identity column detection** | Heuristic (high cardinality, non-null, name match) | Deterministic, no config needed. Users override if wrong. |
| 8 | **Spark session reuse** | Global singleton with config check | Prevents "session already started" errors. |
| 9 | **Test isolation** | Docker for integration, pure pytest for domain | Domain tests run in ms, no JVM needed. Integration tests are reproducible. |
| 10 | **HTML rendering** | Inline CSS only, zero external dependencies | Reports are self-contained. No CDN, no bundler, no npm. |

---

## 5. File Creation Plan

| File | Action | Description |
|------|--------|-------------|
| `spark_eda/__init__.py` | Create | Public API: `analyze()`, `assess_quality()`. Composite Root wiring. |
| `spark_eda/domain/__init__.py` | Create | Domain exports |
| `spark_eda/domain/entities/data_profile.py` | Create | DataProfile entity |
| `spark_eda/domain/entities/column_profile.py` | Create | ColumnProfile entity |
| `spark_eda/domain/entities/column_metadata.py` | Create | ColumnMetadata entity |
| `spark_eda/domain/entities/quality_score.py` | Create | QualityScore + QualityFactor entities |
| `spark_eda/domain/entities/insight.py` | Create | Insight entity |
| `spark_eda/domain/entities/recommendation.py` | Create | Recommendation entity |
| `spark_eda/domain/entities/dataset_analysis.py` | Create | DatasetAnalysis root entity |
| `spark_eda/domain/entities/statistic.py` | Create | NumericStats/CategoricalStats union |
| `spark_eda/domain/value_objects/` | Create | All VOs: DataType, BusinessType, Severity, etc. |
| `spark_eda/domain/services/quality_calculator.py` | Create | QualityCalculator + FACTOR_REGISTRY |
| `spark_eda/domain/services/column_classifier.py` | Create | ColumnClassifier (pure domain logic) |
| `spark_eda/domain/services/insight_engine.py` | Create | InsightEngine (stub — Phase 2) |
| `spark_eda/domain/services/recommendation_engine.py` | Create | RecommendationEngine (stub — Phase 3) |
| `spark_eda/domain/services/quality_factors/` | Create | Factor implementations (completeness, uniqueness) |
| `spark_eda/use_cases/__init__.py` | Create | Use case exports |
| `spark_eda/use_cases/ports/data_provider.py` | Create | DataProvider port |
| `spark_eda/use_cases/ports/cache_provider.py` | Create | CacheProvider port |
| `spark_eda/use_cases/ports/output_presenter.py` | Create | OutputPresenter port |
| `spark_eda/use_cases/analyze_dataset.py` | Create | AnalyzeDatasetUseCase |
| `spark_eda/use_cases/assess_quality.py` | Create | AssessQualityUseCase |
| `spark_eda/adapters/__init__.py` | Create | Adapter exports |
| `spark_eda/adapters/controllers/analyze_controller.py` | Create | AnalyzeController |
| `spark_eda/adapters/controllers/quality_controller.py` | Create | QualityController |
| `spark_eda/adapters/providers/spark_data_provider.py` | Create | SparkDataProvider |
| `spark_eda/adapters/providers/lru_cache_provider.py` | Create | LRUCacheProvider |
| `spark_eda/adapters/providers/column_inferrer.py` | Create | ColumnClassifier (Spark adapter) |
| `spark_eda/adapters/providers/quality_factors/` | Create | Spark factor computations |
| `spark_eda/adapters/presenters/analysis_presenter.py` | Create | AnalysisPresenter |
| `spark_eda/adapters/presenters/quality_presenter.py` | Create | QualityPresenter |
| `spark_eda/adapters/dto/eda_report.py` | Create | EDAReport DTO |
| `spark_eda/adapters/dto/section_types.py` | Create | All section DTOs |
| `spark_eda/adapters/renderers/html_renderer.py` | Create | HTML5 renderer |
| `spark_eda/adapters/renderers/text_renderer.py` | Create | Terminal renderer |
| `spark_eda/adapters/renderers/json_serializer.py` | Create | JSON serializer |
| `spark_eda/framework/config.py` | Create | EDAConfig, QualityConfig |
| `spark_eda/framework/spark_session.py` | Create | Session management |
| `spark_eda/framework/exceptions.py` | Create | Exception hierarchy |
| `spark_eda/business/patterns.py` | Create | Regex patterns for BR documents |
| `spark_eda/business/validators.py` | Create | CPF/CNPJ digit validators |
| `spark_eda/utils/formatting.py` | Create | Number/size formatting |
| `spark_eda/utils/hashing.py` | Create | Fingerprint computation |
| `pyproject.toml` | Create | Build config, deps, ruff/mypy/pytest |
| `Makefile` | Create | Dev targets |
| `docker-compose.yml` | Create | Test services |
| `tests/Dockerfile` | Create | PySpark test environment |
| `tests/unit/` | Create | Domain + use case tests |
| `tests/integration/` | Create | Provider tests |
| `tests/contract/` | Create | Strategy contract tests |
| `tests/benchmarks/` | Create | Performance tests |
| `tests/fixtures/` | Create | Synthetic test data |
| `scripts/scaffold_factor.py` | Create | Quality factor scaffold |
| `scripts/scaffold_strategy.py` | Create | Strategy scaffold |
| `scripts/scaffold_entity.py` | Create | Entity scaffold |
| `scripts/generate_fixtures.py` | Create | Test data generator |
| `HELPERS.md` | Create | Quick reference |
| `.github/workflows/ci.yml` | Create | CI pipeline |

---

## 6. Testing Strategy

| Layer | What to Test | Approach | Spark? |
|-------|-------------|----------|--------|
| Domain entities | Invariants, null handling, math | Pure pytest, no fixtures | ❌ |
| Domain services | Score calculation, combinatorics | Pure pytest, property-based | ❌ |
| Value objects | Enum values, comparison, hashing | Pure pytest | ❌ |
| Fingerprint/Hashing | Determinism, collision resistance | Pure pytest | ❌ |
| Use cases | Orchestration, cache hit/miss, error propagation | Mock ports, real domain | ❌ |
| Use case ports | Interface contract compliance | pytest with stubs | ❌ |
| Adapter: DataProvider | Profile correctness, empty/null/edge DataFrames | Docker + PySpark local | ✅ |
| Adapter: CacheProvider | LRU ordering, TTL, thread safety | pytest concurrency, pure Python | ❌ |
| Adapter: ColumnClassifier | Type detection accuracy, regex correctness | Docker + PySpark local | ✅ |
| Adapter: Presenters | Entity → DTO mapping completeness | Pure pytest | ❌ |
| Adapter: Renderers | HTML validity, text width, XSS escape | pytest with fixtures | ❌ |
| Integration | Full spark_eda.analyze() on real DataFrames | Docker + PySpark local | ✅ |
| Contract | Every strategy class implements ABC correctly | pytest + abstract base | ✅ |
| Benchmarks | Execution time on 10K, 100K, 1M rows | pytest-benchmark | ✅ |

---

## 7. Migration / Rollout

No migration required — greenfield project. Phase 1 delivers: data profiling, quality scoring (Completeness + Uniqueness), analysis orchestration, column classification, caching, report rendering, and testing infrastructure. Implementation order follows dependency graph: Domain → Use Cases → Adapters → Framework → Tests → CI → Tooling.

**Phase 1 Delivery Order**:
1. `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `Makefile` (infrastructure first)
2. Domain entities + value objects
3. Domain services (QualityCalculator, ColumnClassifier — pure)
4. Use cases + ports
5. Adapters (SparkDataProvider, LRUCacheProvider, ColumnInferrer)
6. Presenters + DTOs
7. Renderers (HTML + text)
8. Framework (config, spark_session, exceptions)
9. Composite root wiring (`__init__.py`)
10. Tests: unit → use case → integration → contract → benchmarks
11. Developer tooling (scaffolds, HELPERS.md)
12. CI pipeline

**Rollback**: `git revert` on the merge commit. No data schema changes, no deployed services.
