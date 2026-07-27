# Architecture Exploration: spark_eda

## 1. Solution Overview

**spark_eda** is a production-grade Python library for distributed Exploratory Data Analysis (EDA), Data Quality assessment, automatic insight generation, and dataset documentation on PySpark DataFrames.

### Design Philosophy

| Principle | Application |
|-----------|-------------|
| **Zero config by default** | `spark_eda.analyze(df)` produces a complete EDA report with no setup |
| **Decoupled concepts** | `EDA` (analysis) and `Quality` (quality score) are independent public APIs |
| **Distributed-first** | Every operation uses Spark native functions — zero `collect()`, `toPandas()`, or row iteration |
| **Deterministic insights** | Natural language insights from heuristic rules, never AI/ML |
| **Transparent scoring** | Data Quality Score (0-100) documents every contributing factor |
| **Type-safe** | Python 3.14+, strict type hints, mypy strict mode |
| **Clean Architecture** | 4 camadas (Domain → Use Cases → Adapters → Framework). Dependency Rule explícita. Spark APENAS nos adapters |
| **Testabilidade em camadas** | Domain: pytest puro, sem fixtures. Use Cases: mock das portas. Adapters: Docker + PySpark local. Framework: testes de integração |
| **Docstrings em português** | Toda API pública documentada em português (Google Style) |
| **Helpers de desenvolvimento** | Templates, scaffolds, HELPERS.md e checklist PySpark integrados ao projeto |

### Entry Points

```python
import spark_eda

# Zero-config EDA — returns a rich result object
report = spark_eda.analyze(df)

# Zero-config Data Quality
score = spark_eda.assess_quality(df)  # returns QualityReport

# Sections are individually accessible
report.overview  # DatasetOverview
report.schema  # SchemaReport
report.quality  # QualityReport (embedded or standalone)
report.stats  # StatisticsReport
report.distributions  # DistributionReport
report.correlations  # CorrelationReport
report.outliers  # OutlierReport
report.insights  # InsightsReport
report.recommendations  # RecommendationsReport

# Each section is self-renderable in Jupyter (HTML) and terminal (text)
display(report.overview)  # Jupyter HTML widget
print(report.overview)  # Terminal text

# Advanced config via dataclass
from spark_eda import EDAConfig

config = EDAConfig(
    max_categories=50,
    correlation_methods=["pearson", "spearman", "cramers_v"],
    outlier_method="iqr",
    enable_insights=True,
)
report = spark_eda.analyze(df, config=config)
```

---

## 2. Module Responsibilities — Clean Architecture

A arquitetura segue rigorosamente as 4 camadas da **Clean Architecture** (Robert C. Martin), com a **Dependency Rule**: dependências de código-fonte apontam **sempre para dentro**. Nada em uma camada interna sabe da existência de uma camada externa.

```
spark_eda/
├── __init__.py                 # Public API: analyze(), assess_quality() (delega ao controller)
├── _version.py                 # Version (semver)
│
╔══════════════════════════════════════════════════════════════════╗
║  CAMADA 1 — DOMAIN (Enterprise Business Rules)                  ║
║  ⚡ Zero dependências externas. Sem PySpark, sem I/O            ║
║  ⚡ 100% testável em isolation (pytest puro, sem fixtures)      ║
╚══════════════════════════════════════════════════════════════════╝
│
├── domain/
│   ├── __init__.py
│   │
│   ├── entities/               # Enterprise business rules + value objects
│   │   ├── __init__.py
│   │   ├── data_profile.py     # DataProfile: profile completo de um dataset
│   │   ├── column_profile.py   # ColumnProfile: profile de uma coluna
│   │   ├── column_metadata.py  # ColumnMetadata: nome, tipo, nulabilidade
│   │   ├── statistic.py        # Statistic (union: NumericStats | CategoricalStats | ...)
│   │   ├── distribution.py     # Distribution (sealed: Histogram | Frequency | Temporal)
│   │   ├── outlier.py          # OutlierInfo: método, contagem, bounds
│   │   ├── correlation.py      # Correlation: par de colunas, método, valor
│   │   ├── quality_score.py    # QualityScore: score 0-100 com dimensões e fatores
│   │   ├── insight.py          # Insight: categoria, severidade, coluna, mensagem
│   │   ├── recommendation.py   # Recommendation: categoria, prioridade, ação
│   │   └── dataset_analysis.py # DatasetAnalysis: entidade raiz (contém tudo)
│   │
│   ├── value_objects/          # Value objects imutáveis
│   │   ├── __init__.py
│   │   ├── data_type.py        # DataType enum (INTEGER, LONG, DOUBLE, STRING, BOOLEAN, ...)
│   │   ├── inferred_type.py    # InferredType enum (CPF, CNPJ, EMAIL, UUID, ...)
│   │   ├── severity.py         # Severity enum (LOW, MEDIUM, HIGH, CRITICAL)
│   │   ├── correlation_method.py # CorrelationMethod enum
│   │   ├── outlier_method.py   # OutlierMethod enum
│   │   ├── insight_category.py # InsightCategory enum
│   │   └── recommendation_category.py # RecommendationCategory enum
│   │
│   └── services/               # Domain services — lógica de negócio pura
│       ├── __init__.py
│       ├── quality_calculator.py    # QualityScoreCalculator: algoritmo do score (0-100)
│       ├── insight_engine.py        # InsightEngine: geração de insights determinísticos
│       ├── recommendation_engine.py # RecommendationEngine: geração de recomendações
│       └── column_classifier.py     # ColumnClassifier: inferência de tipo de negócio
│
╔══════════════════════════════════════════════════════════════════╗
║  CAMADA 2 — USE CASES (Application Business Rules)              ║
║  ⚡ Depende APENAS de domain/ (entidades e serviços)            ║
║  ⚡ Define PORTAS (interfaces) para camadas externas            ║
║  ⚡ NÃO importa nada de adapters/ ou framework/                 ║
╚══════════════════════════════════════════════════════════════════╝
│
├── use_cases/
│   ├── __init__.py
│   │
│   ├── ports/                   # Interfaces que as camadas externas implementam
│   │   ├── __init__.py
│   │   ├── data_provider.py    # DataProvider: como obter dados do mundo externo
│   │   ├── cache_provider.py   # CacheProvider: como armazenar em cache
│   │   └── output_presenter.py # OutputPresenter: como formatar a saída
│   │
│   ├── analyze_dataset.py      # AnalyzeDatasetUseCase: EDA completa
│   ├── assess_quality.py       # AssessQualityUseCase: qualidade isolada
│   ├── generate_insights.py    # GenerateInsightsUseCase: insights (puro, sem Spark)
│   └── generate_recommendations.py # GenerateRecommendationsUseCase: recomendações
│
╔══════════════════════════════════════════════════════════════════╗
║  CAMADA 3 — ADAPTERS (Interface Adapters)                       ║
║  ╚═► Implementa as portas definidas em use_cases/ports/         ║
║  ╚═► Converte dados entre use cases e o mundo externo           ║
║  ╚═► TUDO que toca PySpark está AQUI                             ║
╚══════════════════════════════════════════════════════════════════╝
│
├── adapters/
│   ├── __init__.py
│   │
│   ├── controllers/             # Entrada: recebe dados do framework, chama use cases
│   │   ├── __init__.py
│   │   ├── analyze_controller.py    # analyze(df, config) → EDAReport
│   │   └── quality_controller.py    # assess_quality(df, config) → QualityReport
│   │
│   ├── providers/               # Implementações concretas das portas
│   │   ├── __init__.py
│   │   ├── spark_data_provider.py   # DataProvider: computa DataProfile via Spark
│   │   ├── lru_cache_provider.py    # CacheProvider: cache LRU em memória
│   │   └── column_inferrer.py       # Inferência otimizada com Spark expressions
│   │
│   ├── presenters/              # Saída: entidades → DTOs de apresentação
│   │   ├── __init__.py
│   │   ├── analysis_presenter.py    # DatasetAnalysis → EDAReport
│   │   └── quality_presenter.py     # QualityScore → QualityReport
│   │
│   ├── renderers/               # Renderização (HTML, texto, JSON)
│   │   ├── __init__.py
│   │   ├── html_renderer.py     # Seções → HTML (Jupyter _repr_html_)
│   │   ├── text_renderer.py     # Seções → Terminal (__str__, __repr__)
│   │   └── json_serializer.py   # Seções → JSON
│   │
│   └── dto/                     # Output DTOs (ViewModel) — objeto rico que o usuário vê
│       ├── __init__.py
│       ├── eda_report.py        # EDAReport: container com todas as seções
│       ├── overview_section.py  # Visão geral
│       ├── schema_section.py    # Schema report
│       ├── quality_section.py   # Quality report
│       ├── stats_section.py     # Estatísticas
│       ├── distribution_section.py # Distribuições
│       ├── correlation_section.py  # Correlações
│       ├── outlier_section.py   # Outliers
│       ├── insights_section.py  # Insights
│       └── recommendations_section.py # Recomendações
│
╔══════════════════════════════════════════════════════════════════╗
║  CAMADA 4 — FRAMEWORK (Frameworks & Drivers)                    ║
║  ╚═► Tudo que é externo: PySpark, config, infra                 ║
║  ╚═► Depende de adapters/ e use_cases/                         ║
╚══════════════════════════════════════════════════════════════════╝
│
├── framework/
│   ├── __init__.py
│   ├── spark_session.py        # Gerenciamento de SparkSession
│   ├── config.py               # EDAConfig, QualityConfig (dataclasses de configuração)
│   └── exceptions.py           # Exceções de framework (não de domínio)
│
├── business/                    # Padrões de negócio (framework-agnostic, usado por providers)
│   ├── __init__.py
│   ├── patterns.py             # Regex patterns (CPF, CNPJ, email, UUID, ...)
│   └── validators.py           # Validadores com dígito verificador (CPF, CNPJ, CNES)
│
└── utils/
    ├── __init__.py
    ├── formatting.py           # Formatação de números, tamanhos legíveis
    └── hashing.py              # Hashing de fingerprints

### Arquivos na Raiz do Projeto

```
spark_eda/
├── pyproject.toml              # Build system, deps, tool config (ruff, mypy, pytest)
├── setup.cfg                   # Fallback config (se necessário)
├── README.md                   # Documentação principal (português)
├── HELPERS.md                  # Referência rápida de desenvolvimento
├── CHANGELOG.md                # Histórico de versões (Keep a Changelog)
├── LICENSE                     # MIT License
├── Makefile                    # Comandos de desenvolvimento (test, build, lint)
├── docker-compose.yml          # Serviços: test, benchmark, shell
├── tests/
│   ├── Dockerfile              # Imagem PySpark para testes
│   ├── Dockerfile.py314        # Variante Python 3.14
│   ├── Dockerfile.py315        # Variante Python 3.15 (futuro)
│   ├── Dockerfile.benchmark    # Variante com pytest-benchmark
│   ├── unit/                   # Testes sem Spark (matemática, formatação, hash)
│   ├── integration/            # Testes com PySpark local
│   │   ├── test_analyze.py
│   │   ├── test_quality_score.py
│   │   ├── test_column_inference.py
│   │   ├── test_cache.py
│   │   └── ...
│   ├── contract/               # Testes de contrato de strategies
│   ├── benchmarks/             # Testes de performance
│   └── fixtures/               # Dados de teste compartilhados
├── scripts/
│   ├── scaffold_factor.py      # Gera scaffold de novo fator de qualidade
│   ├── scaffold_strategy.py    # Gera scaffold de nova strategy
│   └── generate_fixtures.py    # Gera dados de teste sintéticos
├── docs/                       # Documentação adicional
│   ├── architecture.md         # Este ADR
│   ├── getting_started.md      # Guia de instalação e primeiro uso
│   ├── notebooks.md            # Guia de uso em Jupyter
│   ├── glue.md                 # Deploy em AWS Glue
│   ├── databricks.md           # Uso em Databricks
│   ├── emr.md                  # Uso em EMR
│   ├── api_reference.md        # Documentação completa da API
│   ├── contributing.md         # Guia de contribuição
│   └── faq.md                  # Perguntas frequentes
├── notebooks/                  # Notebooks de exemplo
│   ├── 01_introducao.ipynb
│   ├── 02_analise_completa.ipynb
│   └── 03_quality_score.ipynb
└── .github/
    └── workflows/
        └── ci.yml              # CI pipeline (lint → typecheck → test → coverage)
```

## 3. Logical Architecture Diagram — Clean Architecture

A seta indica direção da dependência — **sempre aponta para dentro** (Dependency Rule).

```
   FRAMEWORK (4)           ADAPTERS (3)            USE CASES (2)           DOMAIN (1)
 ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
 │                  │  │                  │  │                  │  │                  │
 │  spark_eda.      │  │  Controllers     │  │  Use Cases       │  │  Entities        │
 │  analyze(df)     │──►│                  │──►│                  │──►│                  │
 │  assess_quality  │  │  • AnalyzeCtrl   │  │  • AnalyzeDS     │  │  • DataProfile   │
 │       │          │  │  • QualityCtrl   │  │  • AssessQual    │  │  • ColumnProfile │
 │       ▼          │  │                  │  │  • GenInsights   │  │  • QualityScore  │
 │  framework/      │  │  Providers       │  │  • GenRecs       │  │  • Insight       │
 │  • spark_session │  │  • SparkDataProv │  │                  │  │  • Recommendation│
 │  • config        │  │  • LRUCacheProv  │  │  Ports           │  │  • DatasetAn.    │
 │  • exceptions    │  │  • ColumnInfrr   │  │  • DataProvider  │  │                  │
 │                  │  │                  │  │  • CacheProvider │  │  Domain Services │
 │  PySpark         │  │  Presenters      │  │  • OutputPresent │  │  • QualityCalc   │
 │  DataFrames      │  │  • AnalysisPres  │  │                  │  │  • InsightEngine │
 │                  │  │  • QualityPres   │  │                  │  │  • RecEngine     │
 │                  │  │                  │  │                  │  │  • ColumnClassif │
 │                  │  │  Renderers       │  │                  │  │                  │
 │                  │  │  • HTML, Text,   │  │                  │  │                  │
 │                  │  │    JSON          │  │                  │  │                  │
 │                  │  │                  │  │                  │  │                  │
 │                  │  │  DTOs (ViewModel)│  │                  │  │                  │
 │                  │  │  • EDAReport     │  │                  │  │                  │
 │                  │  │  • Sections      │  │                  │  │                  │
 └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
        │                       │                       │                     │
        │   PySpark depende     │   Adapters DEPENDEM   │   Use Cases DEPENDEM │
        │   de adapters/        │   de use_cases/ports  │   de domain/         │
        │   (injeção)           │   (implementam)       │   (usam entidades)   │
        ▼                       ▼                       ▼                     ▼
  "Framework conhece           "Adapter conhece        "Use case conhece      "Domain conhece
   adapter"                     use case"               domain"                nada externo"
```

### Fluxo completo através das camadas

```
 analyze(df, config)                                    FRAMEWORK
        │
        ▼
 AnalyzeController.execute(df, config)                   ADAPTERS (Controller)
        │
        ├──► Cria AnalyzeRequest (DTO de entrada)
        ├──► Cria SparkDataProvider, LRUCacheProvider
        ├──► Cria AnalyzeDatasetUseCase(request, provider, cache)
        │
        ▼
 AnalyzeDatasetUseCase.execute(request)                  USE CASES
        │
        ├──► 1. Gera fingerprint → chave de cache
        ├──► 2. CacheProvider.get(fingerprint) → hit? retorna
        │
        ├──► 3. DataProvider.compute_profile(columns, config)
        │         │
        │         ▼                                          ADAPTERS (Provider)
        │    SparkDataProvider.compute_profile()              │
        │      ├── agg() single-pass → row de métricas       │  (toca PySpark)
        │      ├── approxQuantile() → percentis               │
        │      ├── rlike() pipeline → inferência              │
        │      └── ► retorna DataProfile (ENTIDADE) ──────────┤
        │                                                      │
        ├──► 4. QualityCalculator.compute(profile)            DOMAIN
        │         └── ► retorna QualityScore (ENTIDADE)
        │
        ├──► 5. InsightEngine.generate(profile, quality)
        │         └── ► retorna list[Insight] (ENTIDADES)
        │
        ├──► 6. RecommendationEngine.generate(insights, quality)
        │         └── ► retorna list[Recommendation] (ENTIDADES)
        │
        ├──► 7. Monta DatasetAnalysis (entidade raiz)
        ├──► 8. CacheProvider.set(fingerprint, analysis)
        │
        └──► 9. Retorna DatasetAnalysis (entidade)
                    │
                    ▼
 AnalysisPresenter.present(analysis)                       ADAPTERS (Presenter)
        │
        ├──► Converte DatasetAnalysis → EDAReport
        │    (cada entidade → sua seção de apresentação)
        ├──► EDAReport contém métodos _repr_html_(), __str__()
        │    que delegam para HTMLRenderer / TextRenderer
        │
        └──► ► Retorna EDAReport (ViewModel) ────────────────► FRAMEWORK
                                                                   │
                                                                   ▼
                                                          Usuário vê o relatório
                                                          (Jupyter ou terminal)
```

### Regras da Dependency Rule

| Regra | Aplicação |
|-------|-----------|
| **Domain não importa nada** | `domain/` não importa `use_cases/`, `adapters/`, `framework/`, PySpark, ou qualquer biblioteca externa |
| **Use Cases importa apenas Domain** | `use_cases/` importa `domain/entities/` e `domain/services/`. Define interfaces em `ports/` — NUNCA importa implementações concretas |
| **Adapters importa Use Cases e Domain** | `adapters/` implementa as portas de `use_cases/ports/`. Importa entidades de `domain/`. Pode importar `framework/` (ex: SparkSession) |
| **Framework importa tudo** | `framework/` importa `adapters/`, `use_cases/`, `domain/`. É o "composite root" que monta toda a aplicação |

### O que muda com Clean Architecture vs versão anterior

| Antes (híbrido) | Agora (Clean Architecture pura) | Benefício |
|---|---|---|
| SparkSession conhecido pela engine central | SparkSession APENAS em `adapters/providers/spark_data_provider.py` | Use cases testáveis sem Spark |
| Entidades anêmicas (só dados) | Entidades ricas com comportamento de negócio (QualityScore.calcular(), Insight.gerar_mensagem()) | Lógica de negócio centralizada e testável |
| Estratégias de análise misturadas com Spark | Domain services puros (sem Spark) + Adapters Spark | Separação clara: o quê vs como |
| Use case = função solta em `api/` | Use case = classe com método `execute()` em `use_cases/` | Ciclo de vida explícito, testável |
| Cache acoplado ao fluxo | CacheProvider como porta → implementação intercambiável | Pode trocar LRU por Redis sem tocar use case |
| Output = dict ou dataclass sem padrão | Output = Presenter que converte entidade → ViewModel (DTO) | Controla exatamente o que o usuário vê

---

## 4. Complete Execution Flow (Clean Architecture)

O fluxo percorre as 4 camadas **em direção ao centro** (entrada) e **de volta à periferia** (saída), jamais violando a Dependency Rule.

### `spark_eda.analyze(df, config=None)` — Travessia das Camadas

```
┌────────────────────────────────────────────────────────────────────────────┐
│ FRAMEWORK LAYER: spark_eda.analyze(df, config)                             │
│                                                                             │
│  STEP 1: Resolve Config                                                     │
│    └─ framework/config.py → EDAConfig(default) se config=None              │
│    └─ Apenas validação de tipos, sem lógica de negócio                     │
│                                                                             │
│  STEP 2: Resolver/Criar SparkSession                                        │
│    └─ framework/spark_session.py → SparkSession                             │
│                                                                             │
│  STEP 3: Delegar para o Controller                                          │
│    └─ AnalyzeController.execute(df, config)                                 │
│    └─ ISO: framework NÃO tem lógica — só monta dependências e chama adapter│
└────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ ADAPTER LAYER (Controller): AnalyzeController.execute(df, config)           │
│                                                                             │
│  STEP 4: Criar dependências e Request                                       │
│    └─ Cria SparkDataProvider(spark_session)  ──── implementa DataProvider   │
│    └─ Cria LRUCacheProvider()                ──── implementa CacheProvider   │
│    └─ Cria AnalysisPresenter()                ──── implementa OutputPresent.│
│    └─ Cria AnalyzeRequest(colunas, config)    ──── DTO de entrada           │
│                                                                             │
│  STEP 5: Delegar para o Use Case                                            │
│    └─ AnalyzeDatasetUseCase.execute(request, provider, cache, presenter)    │
│    └─ ISO: Controller NÃO tem regras — só orquestra injeção e chamada      │
└────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ USE CASE LAYER: AnalyzeDatasetUseCase.execute(request, provider, cache)     │
│                                                                             │
│  STEP 6: Verificar Cache                                                    │
│    └─ provider.compute_fingerprint(request) → hash                          │
│    └─ cache.get(hash) → se hit, retorna DatasetAnalysis (entidade)          │
│                                                                             │
│  STEP 7: Buscar Dados (via PORTA, sem saber implementação)                  │
│    └─ DataProvider.compute_profile(                                         │
│    └─   columns=request.columns,                                            │
│    └─   config=request.config                                               │
│    └─ ) → DataProfile (ENTIDADE)                                            │
│    └─ ISO: Use case não sabe se é Spark, Pandas ou arquivo CSV             │
│                                                                             │
│  STEP 8: Processar Regras de Negócio (DOMAIN, sem Spark)                    │
│    └─ QualityCalculator.compute(profile)        → QualityScore (entidade)   │
│    └─ InsightEngine.generate(profile, quality)  → list[Insight]            │
│    └─ RecommendationEngine.generate(insights)   → list[Recommendation]     │
│                                                                             │
│  STEP 9: Montar Entidade Raiz                                               │
│    └─ DatasetAnalysis(profile, quality, insights, recommendations, now())    │
│                                                                             │
│  STEP 10: Armazenar em Cache                                                │
│    └─ cache.set(hash, analysis)                                             │
│                                                                             │
│  STEP 11: Retornar DatasetAnalysis (ENTIDADE PURA)                          │
└────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ ADAPTER LAYER (Presenter): AnalysisPresenter.present(analysis)              │
│                                                                             │
│  STEP 12: Converter Entidades → ViewModel (DTO de saída)                    │
│    └─ DatasetAnalysis       → EDAReport                                    │
│    └─ DataProfile           → OverviewSection + SchemaSection               │
│    └─ QualityScore          → QualitySection                                │
│    └─ ColumnProfile.stats   → StatsSection                                  │
│    └─ ColumnProfile.dist    → DistributionSection                           │
│    └─ Correlations          → CorrelationSection                            │
│    └─ ColumnProfile.outlier → OutlierSection                                │
│    └─ Insights              → InsightsSection                               │
│    └─ Recommendations       → RecommendationsSection                        │
│                                                                             │
│  STEP 13: Retornar EDAReport (ViewModel com renderização)                   │
│    └─ EDAReport._repr_html_() → HTMLRenderer.render(report)                │
│    └─ EDAReport.__str__()     → TextRenderer.render(report)                 │
└────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ FRAMEWORK LAYER: Recebe EDAReport e retorna ao usuário                      │
│                                                                             │
│  STEP 14: Retornar EDAReport                                                 │
│    └─ Se Jupyter: _repr_html_() é chamado automaticamente                  │
│    └─ Se terminal: __str__() é chamado automaticamente                     │
└────────────────────────────────────────────────────────────────────────────┘
```

### `spark_eda.assess_quality(df, config=None)` — Fluxo Simplificado

```
FRAMEWORK:
  assess_quality(df, config) → QualityController.execute(df, config)

ADAPTER (Controller):
  Cria SparkDataProvider, LRUCacheProvider, QualityPresenter
  Cria AssessQualityUseCase.execute(request, provider, cache)

USE CASE:
  STEP 1: Cache check (fingerprint)
  STEP 2: DataProvider.compute_profile(columns) → DataProfile
  STEP 3: QualityCalculator.compute(profile) → QualityScore  (DOMAIN)
  STEP 4: Cache.set(fingerprint, quality_score)
  STEP 5: Retorna QualityScore (entidade)

ADAPTER (Presenter):
  QualityPresenter.present(quality_score) → QualityReport

FRAMEWORK:
  Retorna QualityReport
```

### Mapa: Quem Toca no Spark?

| Operação | Camada | Arquivo |
|----------|--------|---------|
| Criar SparkSession | FRAMEWORK | `framework/spark_session.py` |
| Computar métricas agregadas | ADAPTER | `adapters/providers/spark_data_provider.py` |
| Inferir tipos de coluna | ADAPTER | `adapters/providers/column_inferrer.py` |
| Computar fingerprint | DOMAIN | `domain/entities/data_profile.py` (hash, sem Spark) |
| Calcular quality score | DOMAIN | `domain/services/quality_calculator.py` |
| Gerar insights | DOMAIN | `domain/services/insight_engine.py` |
| Gerar recomendações | DOMAIN | `domain/services/recommendation_engine.py` |
| Renderizar HTML | ADAPTER | `adapters/renderers/html_renderer.py` |

**Spark SÓ aparece em adapters/providers/**. Domain e Use Cases são 100% livres de Spark — testáveis com pytest puro, sem fixtures complexas.

---

## 5. Design Patterns Used and Rationale

| Pattern | Where | Why | Camada |
|---------|-------|-----|--------|
| **Entity Pattern** | `domain/entities/` | Business objects with behavior (DataProfile, QualityScore, Insight). Identity, lifecycle, invariants | DOMAIN |
| **Value Object Pattern** | `domain/value_objects/` | Immutable, comparison-by-value types (DataType, Severity, CorrelationMethod). Replace stringly-typed code | DOMAIN |
| **Domain Service** | `domain/services/` | Stateless operations across entities (QualityCalculator, InsightEngine). Pure business logic, no I/O | DOMAIN |
| **Use Case / Interactor** | `use_cases/analyze_dataset.py`, `use_cases/assess_quality.py` | Each application operation is a class with `execute()`. Validates, orchestrates, returns entities | USE CASES |
| **Port / Interface** | `use_cases/ports/` | Contracts between layers (DataProvider, CacheProvider, OutputPresenter). Dependency Inversion | USE CASES |
| **Controller** | `adapters/controllers/` | Receives framework input, creates dependencies, calls use case. No business logic | ADAPTER |
| **Presenter** | `adapters/presenters/` | Converts entities → ViewModel (DTO). Desacopla formato de saída do domínio | ADAPTER |
| **Strategy Pattern** | `adapters/providers/spark_data_provider.py` (sub-strategies para cada tipo de coluna e método de correlação/outlier) | Algoritmos de computação Spark intercambiáveis. IQR vs Z-score são estratégias NO ADAPTER, não no domínio. Open/Closed | ADAPTER |
| **Facade Pattern** | `__init__.py` (público) | `analyze()` e `assess_quality()` escondem toda a complexidade das 4 camadas. API de 2 funções | FRAMEWORK |
| **Composite Pattern** | `adapters/dto/*_section.py` | Cada Section é auto-renderizável (HTML + text). EDAReport é composite de sections | ADAPTER |
| **Template Method** | `adapters/renderers/` | Renderizadores definem skeleton; formatos específicos (HTML, texto, JSON) sobrescrevem | ADAPTER |
| **Command Pattern** | `domain/services/insight_engine.py` (regras internas) | Cada regra de insight é auto-contida. Novos insights = novo módulo | DOMAIN |
| **Null Object Pattern** | `adapters/dto/` sections desabilitadas | Section nula que renderiza vazio — evita `None` checks | ADAPTER |
| **Composite Root** | `__init__.py` (público) | Único lugar que monta o grafo de dependências. Conhece todas as implementações concretas | FRAMEWORK |
| **Strategy Registry** | `adapters/providers/spark_data_provider.py` | Mapeia tipo de coluna → estratégia de computação Spark. Sem if/else chains | ADAPTER |
| **Caching Proxy** | `core/cache.py` | Proxies computation results. Returns cached data if the DataFrame fingerprint (schema + plan hash + config) matches. |
| **Value Object / Immutable Data** | All result types | All result objects are frozen dataclasses — thread-safe, hashable, predictable. |
| **Lazy Evaluation Wrapper** | `core/engine.py` | Wraps Spark's native lazy eval. No computation is triggered until `.run()` or first access to a section that requires it. |

### Clean Architecture Patterns Added

Beyond the patterns above, Clean Architecture adiciona:

| Padrão | Onde | Por quê |
|--------|------|---------|
| **Dependency Inversion** | `use_cases/ports/` | Interfaces (portas) definidas no use case, implementadas no adapter. Use case nunca depende de adapter — só da interface |
| **Boundary / Port** | `DataProvider`, `CacheProvider`, `OutputPresenter` | Define contratos entre camadas. Qualquer implementação que respeite o contrato funciona — Spark, Pandas, Redis, Mock |
| **Use Case / Interactor** | `AnalyzeDatasetUseCase`, `AssessQualityUseCase` | Cada operação de negócio da aplicação tem sua própria classe com um único método `execute()`. Dá nome, validação e ciclo de vida explícitos |
| **Entity** | `DataProfile`, `QualityScore`, `Insight` | Objetos de negócio com comportamento. QualityScore sabe calcular seu próprio breakdown. Insight sabe se formatar em linguagem natural|
| **Value Object** | `DataType`, `Severity`, `CorrelationMethod` | Imutáveis, comparáveis por valor. Sem identidade própria. Tipos fortemente tipados substituem strings mágicas |
| **Domain Service** | `QualityCalculator`, `InsightEngine`, `RecommendationEngine` | Operações que não se encaixam naturalmente em uma única entidade. Stateless, puras, testáveis |
| **Presenter** | `AnalysisPresenter`, `QualityPresenter` | Converte entidades (estrutura de dados do domínio) em ViewModels (estrutura de dados da apresentação). Desacopla o formato de saída do domínio |
| **DTO / ViewModel** | `EDAReport`, `OverviewSection`, `StatsSection` | Objetos de apresentação com métodos de renderização. Não contêm lógica de negócio — só formatação |
| **Controller** | `AnalyzeController`, `QualityController` | Recebe entrada do framework, cria dependências, chama use case. Não tem regras de negócio — só orquestração |
| **Composite Root** | `__init__.py` (público) | Monta o grafo de dependências. Único lugar que conhece todas as implementações concretas |

### Fluxo de Dependência (Estrutural)

```python
# DOMAIN — sem dependências externas
# domain/entities/data_profile.py
@dataclass(frozen=True)
class DataProfile:
    id: str
    schema: tuple[ColumnMetadata, ...]
    row_count: int
    column_profiles: dict[str, ColumnProfile]

    def null_ratio(self, column: str) -> float:
        """Regra de negócio: proporção de nulos."""
        col = self.column_profiles.get(column)
        if col is None or self.row_count == 0:
            return 0.0
        return col.metadata.null_count / self.row_count


# domain/services/quality_calculator.py
# PURO — sem import de PySpark, adapters, ou framework
class QualityCalculator:
    """Domain service: calcula quality score a partir de um DataProfile.

    Esta classe NÃO sabe nada sobre Spark, DataFrames, ou I/O.
    Ela só processa entidades do domínio.
    """

    def compute(self, profile: DataProfile) -> QualityScore:
        completude = self._avaliar_completude(profile)
        unicidade = self._avaliar_unicidade(profile)
        consistencia = self._avaliar_consistencia(profile)
        ...
        # → retorna QualityScore (entidade)


# USE CASE — importa apenas domain/ e ports/
# use_cases/analyze_dataset.py
class AnalyzeDatasetUseCase:
    """Application business rule: orquestra a análise exploratória.

    Depende APENAS de:
      - domain/entities/    (entidades)
      - domain/services/    (serviços de domínio)
      - ports/              (interfaces — NUNCA implementações)
    """

    def __init__(
        self,
        data_provider: DataProvider,      # ← interface em ports/
        cache_provider: CacheProvider,    # ← interface em ports/
        quality_calculator: QualityCalculator,  # ← domain service
        insight_engine: InsightEngine,          # ← domain service
    ):
        ...

    def execute(self, request: AnalyzeRequest) -> DatasetAnalysis:
        fingerprint = self.cache_provider.compute_key(...)
        cached = self.cache_provider.get(fingerprint)
        if cached:
            return cached

        profile = self.data_provider.compute_profile(request.columns, ...)
        quality = self.quality_calculator.compute(profile)
        insights = self.insight_engine.generate(profile, quality)
        ...


# ADAPTER — implementa a porta, toca no Spark
# adapters/providers/spark_data_provider.py
class SparkDataProvider(DataProvider):   # ← implements port
    """Adapter concreto: computa DataProfile usando PySpark."""

    def __init__(self, spark: SparkSession):
        self._spark = spark

    def compute_profile(self, columns, config) -> DataProfile:
        # AQUI SIM — Spark aggregations, single-pass, etc.
        row = df.agg(*self._build_exprs(columns)).collect()[0]
        return DataProfile(...)   # → retorna ENTIDADE, não dict
```

---

## 6. Trade-offs and Justifications

### Architecture Decisions Record

| Decision | Chosen | Rejected | Rationale |
|----------|--------|----------|-----------|
| **API Shape** | Freestanding functions (`analyze()`, `assess_quality()`) | Class-based entry point (`EDAReport(df)`) | Functions are discoverable, importable, and compose better for the "zero config" use case |
| **Config** | Frozen dataclass (`EDAConfig`) | Dict, YAML, or Pydantic model | Dataclass is type-safe, IDE-friendly, and needs no external dependency. Pydantic would add weight for marginal benefit in this use case |
| **SparkSession** | Reuse existing or auto-create | Force user to pass it | Respects existing SparkContext; avoids "SparkSession already started" errors |
| **Result Types** | Dataclasses (frozen, typed) | Plain dicts, NamedTuple, custom classes | Dataclasses provide rich repr, comparison, and pattern matching. Frozen for immutability safety |
| **Column Inference** | Pure Spark regex-based | ML models or UDFs | Regex is deterministic, testable, and avoids UDF overhead. Patterns run via `rlike()` in native Spark |
| **Insights** | Deterministic heuristics | AI/NLP generated | Deterministic = reproducible, testable, no API calls, no latency, no cost. AI insights would be non-deterministic and add a brittle dependency |
| **Correlation** | Multiple strategies, configurable | Single method | Different column type pairs require different correlation measures. Strategy Pattern allows selecting the right algorithm |
| **Quality Score** | Weighted sum with full factor documentation | Black-box ML score | Transparency is critical for trust — users must understand why the score is what it is |
| **Outlier Detection** | Multiple strategies (IQR, Z-score, MAD) | Single method | Different data distributions require different detection methods |
| **Caching** | LRU with plan hash | Disk-based, Redis | In-memory LRU is lightweight and auto-evicts. Plan hash captures schema AND logic changes |
| **Visualization** | Stateless chart data + external rendering | Built-in matplotlib/plotly | Separates data from rendering. Users can use any viz library. Chart data is JSON-serializable |
| **Rendering** | Dual protocol: HTML + text | Single format | Jupyter requires HTML/widgets, terminal requires text. Both protocols on every section |
| **Integrity as dimension** | Sub-dimension of Consistency (weighted factor, not top-level) | 6th top-level dimension | Integrity overlaps heavily with Consistency (cross-column rules) and Accuracy (format validation). A separate 6th dimension would increase formula complexity without proportional insight gain. All integrity factors are individually tracked in the factor breakdown |
| **Near-constant detection** | Factor within Uniqueness dimension (<1% variance threshold) | Separate dimension or outlier factor | Near-constant is conceptually a uniqueness concern (low variance). Threshold is configurable. The factor is individually documented in the score breakdown — user sees exactly which columns are near-constant and the contribution to the score |
| **Corrupted data detection** | Heuristic pattern matching via Spark `rlike()` — compiled expression tree | ML classifier, character n-gram analysis, dictionary lookup | Heuristics are deterministic, testable, and run entirely in Spark (no UDFs). Patterns cover: garbled text (non-printable chars), placeholders (known wordlist), truncated fields (length = max), encoding artifacts. ML would be non-deterministic and add brittle dependencies for minimal gain |
| **Test infrastructure** | Docker container with PySpark local mode | Local JVM setup, remote Spark cluster, pytest-spark plugin | Docker guarantees reproducible environment across dev machines and CI. Eliminates "works on my machine". Code is live-mounted for fast iteration. Single command for full suite |
| **AAA test pattern** | Mandatory convention enforced in code review | No pattern, BDD (given/when/then), custom DSL | AAA is language-agnostic, minimal ceremony, and maps directly to arrange/mock/assert in pytest. BDD adds overhead for no benefit in a library project |
| **Docstring language** | Português (Google Style) | Inglês | O público principal da biblioteca é falante de português. Documentação em português reduz barreira de entrada e é mais natural para o contexto de uso. Código-fonte (identificadores, comentários técnicos) permanece em inglês |
| **Developer helpers** | HELPERS.md + scripts de scaffold + templates AAA | Apenas documentação avulsa | Helpers reduzem o atrito para criar novas strategies/fatores. Templates garantem consistência. Scripts de scaffold evitam erros de estrutura |
| **Arquitetura** | Clean Architecture (4 camadas, Dependency Rule) | Hexagonal (Ports & Adapters), Layered, MVC | Clean Architecture é a mais rigorosa das arquiteturas em camadas. A Dependency Rule é explícita e checável. Para uma biblioteca com regras de negócio complexas (quality score, insights, recomendações) e necessidade de testabilidade extrema, a pureza de Clean Architecture se paga |
| **DataProvider como porta** | Interface em `use_cases/ports/`, implementação em `adapters/providers/` | Spark direto no use case, DataLoader separado | Use case testável sem Spark: basta implementar DataProvider com dados mockados. Trocar Spark por Pandas ou outro backend é questão de criar outro adapter |
| **Presenter separado** | AnalysisPresenter converte DatasetAnalysis → EDAReport | EDAReport montado no use case, entidades com métodos de renderização | Presenter desacopla o formato de saída do domínio. Se amanhã precisar de saída em Parquet ou Protobuf, só criar novo presenter — domínio não muda |
| **Domain services vs entity methods** | Lógica complexa em services (QualityCalculator, InsightEngine), validações simples em entity methods | Tudo em entities, tudo em services | Services para operações que envolvem múltiplas entidades (ex: quality score combina DataProfile + métricas). Entity methods para regras atômicas (ex: DataProfile.null_ratio()). Single Responsibility |
| **SparkSession injection** | SparkSession criada no framework, injetada no adapter | SparkSession global, criada dentro do provider | Injeção permite testes com SparkSession controlada (ex: `local[1]`, `shuffle.partitions=1`) sem variáveis de ambiente |
| **Python version** | 3.14+ | 3.12, 3.13 | Python 3.14 traz pattern matching aprimorado, melhor tratamento de erros, e suporte estendido. A biblioteca deve mirar a versão mais recente estável |
| **Variable naming** | Sempre completamente explicativo, mesmo que longo | Abreviações, nomes curtos, acrônimos | Nomes auto-explicativos eliminam a necessidade de comentários para entender o que uma variável contém. O custo de digitar `numero_funcionarios_ativos` é irrelevante comparado ao custo de ler e interpretar |
| **Language split** | Docstrings em português, TODO o resto em inglês | Tudo em português, tudo em inglês | Código é lido globalmente — variáveis, funções e comentários em inglês. Docstrings em português porque o público principal é falante de português |

### What We Deliberately Don't Do

| Out of Scope | Reason |
|-------------|--------|
| **AI/ML-based insights** | Non-deterministic, non-testable, introduces model drift, requires external dependencies |
| **Real-time streaming** | Spark Structured Streaming is a different paradigm. Batch EDA is the scope |
| **Database/data source abstraction** | Let Spark handle data sources. We operate on DataFrames only |
| **Data pipeline integration** | spark_eda is a library, not a platform. Integrations belong in orchestration layers |
| **UI dashboard** | HTML reports are the deliverable. Interactive dashboards belong in downstream tools |

---

## 7. Scalability Strategy

### Distributed-First Execution

| Concern | Strategy |
|---------|----------|
| **Memory** | Zero driver memory for data — all computations stay distributed. Only aggregated statistics (always small: a few KB per column) reach the driver |
| **Compute** | Single-pass aggregations combine multiple metrics into one scan where possible. Uses `agg()` with multiple expressions, not multiple `groupBy()` calls |
| **Shuffle** | Minimized by design. Correlations use approximate methods where exact would require shuffle. Caching avoids recomputation |
| **Catalyst Optimization** | Code is written to expose filter pushdown and column pruning opportunities. No UDFs unless absolutely necessary |
| **AQE** | Adaptive Query Execution is explicitly enabled. Shuffle partitions auto-tuned by Spark runtime |
| **Sampling** | For very large datasets (>100M rows), optional sampling for approximate results. Configurable fraction. Sampling uses `fraction` parameter with `seed` for reproducibility |
| **Approximate Algorithms** | `approx_count_distinct()` instead of `countDistinct()`, approx quantiles instead of exact, approx correlation for large datasets |

### Single-Scan Aggregation Pattern

```python
# Core pattern — ALL numeric stats in ONE scan
from pyspark.sql import functions as F

agg_exprs = [
    F.count(F.col(c)).alias(f"{c}_count"),
    F.sum(F.col(c)).alias(f"{c}_sum"),
    F.mean(F.col(c)).alias(f"{c}_mean"),
    F.stddev(F.col(c)).alias(f"{c}_std"),
    F.min(F.col(c)).alias(f"{c}_min"),
    F.max(F.col(c)).alias(f"{c}_max"),
    F.approx_count_distinct(F.col(c)).alias(f"{c}_nunique"),
    F.skewness(F.col(c)).alias(f"{c}_skew"),
    F.kurtosis(F.col(c)).alias(f"{c}_kurt"),
]

row = df.agg(*agg_exprs).collect()[0]  # single collect() → 1 row
```

### Collect() Discipline

```
RULES:
  ✅ collect() → allowed ONLY on aggregated results (1 row, few hundred columns)
  ✅ collect() → allowed on sampled data (explicit with .sample() or .limit())
  ✅ collect() → allowed on row count checks for small phases
  ❌ collect() → NEVER on full DataFrame
  ❌ toPandas() → NEVER called
  ❌ .rdd.map() → NEVER (bypasses Catalyst)
  ❌ Row iteration → NEVER
```

---

## 8. Cache Strategy

### Design

```python
@dataclass
class AnalysisCache:
    """Intelligent LRU cache for EDA results."""

    max_size: int = 10
    ttl_seconds: int = 3600  # 1 hour default

    # keys: DataFrame fingerprint (hash of schema + logical plan + config)
    # values: cached section results
    _cache: OrderedDict[str, CacheEntry] = field(default_factory=OrderedDict)
```

### Cache Key Generation

```python
def compute_fingerprint(df: DataFrame, config: EDAConfig) -> str:
    """Unique, deterministic hash for cache key."""
    schema_json = df.schema.json()  # column names + types
    plan = df._jdf.queryExecution().logical().toString()  # logical plan
    config_json = json.dumps(asdict(config), sort_keys=True)
    raw = f"{schema_json}::{plan}::{config_json}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

### What Gets Cached

| Granularity | Cache Key | Lifetime | Reason |
|-------------|-----------|----------|--------|
| **Full report** | fingerprint | Configurable TTL | Avoid recomputing entire EDA when nothing changed |
| **Per-section** | fingerprint + section_name | Configurable TTL | Enables incremental execution (run only missing sections) |
| **Phase 1 raw stats** | fingerprint + "phase1" | Configurable TTL | Phase 1 is the most expensive (single DataFrame scan); Phase 2/3 reuse it |

### Cache Invalidation

| Trigger | Action |
|---------|--------|
| DataFrame schema changes | Automatic — different fingerprint |
| DataFrame data changes | Automatic — different logical plan fingerprint |
| Config changes | Automatic — config hash in fingerprint |
| Explicit TTL expiry | Eviction from LRU |
| Memory pressure | LRU eviction |
| Explicit `invalidate_cache()` | Full clear |

---

## 9. Spark-Specific Concerns

### 1. Catalyst Optimization Awareness

Every transformation is written to maximize Catalyst optimization opportunities:

```python
# GOOD: Filter pushdown + column pruning happen naturally
df = spark.read.parquet("data/")
result = (
    df
    .select("col_a", "col_b", "col_c")  # column pruning
    .filter(F.col("col_a").isNotNull())  # filter pushdown
    .agg(...)
)

# BAD: No column pruning, filter applied after aggregation
result = df.agg(...).filter(F.col("col_a").isNotNull())
```

### 2. No UDFs in Hot Paths

| Situation | Solution |
|-----------|----------|
| Column type inference | Spark SQL expressions (`rlike()`, `when()`, `regexp_extract()`) |
| Date parsing | `to_date()`, `to_timestamp()` with format strings |
| String operations | `length()`, `trim()`, `upper()`, `lower()`, `regexp_replace()` |
| Business rule detection | Compound `when()` chains — compiled to a single expression tree |
| Complex validation | `pandas_udf` only as last resort, with documented performance impact |

### 3. Column Inference via Pure Spark Expressions

```python
# Pattern for business column detection — NO UDFs
import pyspark.sql.functions as F


def infer_column_types(df: DataFrame) -> dict[str, list[str]]:
    """Detect business column types using pure Spark expressions."""

    patterns = {
        "cpf": r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
        "cnpj": r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$",
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        "cep": r"^\d{5}-?\d{3}$",
        "phone_br": r"^\(?\d{2}\)?\s?\d{4,5}-?\d{4}$",
        "url": r"^https?://[^\s/$.?#].[^\s]*$",
        "ipv4": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
    }

    # Sample a fraction of data to check patterns efficiently
    sample_df = df.sample(0.01, seed=42) if df.count() > 100_000 else df

    # Build detection expressions — single scan
    match_exprs = []
    for col_name, col_type in df.dtypes:
        if col_type in ("string", "varchar"):
            col_matches = {}
            for pattern_name, regex in patterns.items():
                alias = f"{col_name}__{pattern_name}"
                # Check if >80% of non-null values match
                match_ratio = F.avg(F.when(F.col(col_name).rlike(regex), 1).otherwise(0)).alias(alias)
                col_matches[alias] = match_ratio
            match_exprs.extend(col_matches.values())

    if match_exprs:
        ratios = sample_df.agg(*match_exprs).collect()[0].asDict()
        # Determine column types from match ratios
        ...
```

### 4. Approximate vs Exact Trade-offs

| Operation | Default | When to use exact |
|-----------|---------|-------------------|
| Distinct count | `approx_count_distinct()` (HyperLogLog) | Small datasets, critical accuracy needs |
| Quantiles | `approxQuantile()` (Greenwald-Khanna) | Small datasets, exact percentiles needed |
| Correlation | Approximate on large samples | Small datasets |
| Count | Exact `.count()` | Always — count is cheap with Parquet row group stats |

### 5. Partition Awareness

```python
# Check partition count for optimization hints
num_partitions = df.rdd.getNumPartitions()

# Hint: repartition only when necessary (e.g., before heavy shuffle)
if num_partitions < 2 * spark.sparkContext.defaultParallelism:
    df = df.repartition(spark.sparkContext.defaultParallelism * 2)
```

---

## 10. Test Plan

### 10.1 Testing Principles

Every test follows the **AAA (Arrange-Act-Assert)** pattern:

```python
# ARRANGE: Create test data with known properties
data = [(1, "alice", 100.0), (2, "bob", 200.0), (3, None, None)]
schema = "id INT, name STRING, salary DOUBLE"
df = spark.createDataFrame(data, schema)

# ACT: Call the analysis function (single, unambiguous action)
result = spark_eda.analyze(df)

# ASSERT: Verify specific, measurable outcomes
assert result.overview.row_count == 3
assert result.quality.dimensions["completeness"].score < 1.0
assert result.schema.columns["salary"].nullable is True
```

AAA rules:
- **Arrange**: One logical block — create or load test fixtures
- **Act**: Exactly one action per test — one function call, one method invocation
- **Assert**: Assertions on the return value, never on side effects unless unavoidable
- No mocks in integration tests; mocks only for unit tests of pure-logic components (e.g., score formula math, rendering helpers)

### 10.2 Coverage Target

| Metric | Target | Enforcement |
|--------|--------|-------------|
| Line coverage | **≥ 95%** | pytest-cov with `--cov-fail-under=95` |
| Branch coverage | **≥ 85%** | pytest-cov branch mode |
| Strategy contract coverage | **100%** | Every strategy implements and passes the abstract contract test suite |
| Type annotation coverage | **100% public API** | mypy --strict on `spark_eda/api/`, `spark_eda/core/types.py` |

### 10.3 Testing Layers

| Layer | Tool | Focus | Spark needed? |
|-------|------|-------|---------------|
| **Pure-logic unit tests** | pytest + hypothesis | Score calculation math, formatting, hashing, pattern matching logic | ❌ No |
| **Factor unit tests** | pytest | Each quality factor in isolation — test boundary conditions, edge cases | ❌ No (fixtures as dicts) |
| **Strategy contract tests** | pytest + ABC | Every strategy (stats, correlation, distribution, outlier) passes the same contract suite | ✅ Yes (PySpark local) |
| **Spark integration tests** | pytest + PySpark local | End-to-end: create DataFrame → analyze → verify section contents | ✅ Yes |
| **Quality Score integration tests** | pytest + PySpark local | Full quality pipeline against curated datasets with known quality levels | ✅ Yes |
| **Column inference tests** | pytest + PySpark local | CPF, CNPJ, email, UUID detection against labeled test data | ✅ Yes |
| **Regression / snapshot tests** | pytest + inline snapshots | Deterministic outputs against frozen reference datasets | ✅ Yes |
| **Performance benchmarks** | pytest-benchmark | Execution time per section: 10K, 100K, 1M, 10M rows | ✅ Yes |
| **Docker integration tests** | docker-compose + pytest | Full CI pipeline inside a reproducible container | ✅ Yes (Docker) |
| **Type checking** | mypy --strict | Enforce type safety across the entire API surface | ❌ No |

### 10.4 CI Pipeline

```yaml
# .github/workflows/ci.yml (or equivalent GitLab CI / Jenkins)
stages:
  - lint
  - typecheck
  - unit
  - integration
  - contract
  - coverage
  - benchmark

lint:
  script: ruff check spark_eda/ tests/

typecheck:
  script: mypy --strict spark_eda/

unit:
  script: pytest tests/unit/ --cov=spark_eda --cov-fail-under=95

integration:
  script: docker-compose run --rm test
  # Runs inside the PySpark Docker container (see Section 10.5)

contract:
  script: docker-compose run --rm test pytest tests/contract/

coverage:
  script: |
    docker-compose run --rm test pytest tests/ \
      --cov=spark_eda --cov-branch --cov-report=xml \
      --cov-fail-under=95

benchmark:
  script: docker-compose run --rm test pytest tests/benchmarks/ \
    --benchmark-json output.json

compatibility:
  script: |
    docker-compose run --rm test-py314 pytest tests/unit/
    docker-compose run --rm test-py315 pytest tests/unit/
```

### 10.5 Docker-Based Testing Infrastructure

#### Rationale

PySpark requires a Java Runtime (JRE) and native Hadoop binaries. Running tests directly on developer machines leads to:
- Environment inconsistencies (different Java versions, missing WINUTILS on Windows)
- "Works on my machine" failures
- Complex setup instructions

A Docker container encapsulates **all** dependencies: Python 3.14+, OpenJDK 21, PySpark, and test tooling.

#### Dockerfile

```dockerfile
# tests/Dockerfile
FROM python:3.14-slim-bookworm AS base

# Install Java (required by PySpark)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

WORKDIR /app

# Install project with test deps
COPY pyproject.toml README.md ./
COPY src/spark_eda/ ./src/spark_eda/
RUN pip install --no-cache-dir -e ".[dev,test]"

# Copy tests
COPY tests/ ./tests/

# Default command: run full test suite
CMD ["pytest", "tests/", "--cov=spark_eda", "--cov-fail-under=95", "-v"]
```

#### docker-compose.yml

```yaml
# docker-compose.yml
version: "3.9"

services:
  test:
    build:
      context: .
      dockerfile: tests/Dockerfile
    volumes:
      - ./src:/app/src          # Live code mount (no rebuild for code changes)
      - ./tests:/app/tests      # Live test mount
      - ./pyproject.toml:/app/pyproject.toml
      - ./coverage:/app/coverage # Coverage output
    environment:
      - PYSPARK_PYTHON=python3
      - PYSPARK_DRIVER_PYTHON=python3
      - SPARK_LOCAL_IP=127.0.0.1
      - PYTEST_ADDOPTS=--color=yes
    working_dir: /app
    command: pytest tests/ --cov=spark_eda --cov-report=term --cov-report=xml -v --tb=short

  test-py314:
    extends: test
    build:
      context: .
      dockerfile: tests/Dockerfile.py314

  test-py315:
    extends: test
    build:
      context: .
      dockerfile: tests/Dockerfile.py315

  benchmark:
    extends: test
    build:
      context: .
      dockerfile: tests/Dockerfile.benchmark
    command: pytest tests/benchmarks/ --benchmark-json=/app/benchmark_output.json
    volumes:
      - ./benchmark_output:/app/benchmark_output

  shell:
    extends: test
    command: /bin/bash
    stdin_open: true
    tty: true
```

#### Makefile (local dev convenience)

```makefile
# Makefile
.PHONY: test test-unit test-integration test-all shell

test-all:
    docker-compose run --rm test

test-unit:
    docker-compose run --rm test pytest tests/unit/ -v

test-integration:
    docker-compose run --rm test pytest tests/integration/ -v

test-contract:
    docker-compose run --rm test pytest tests/contract/ -v

test-coverage:
    docker-compose run --rm test pytest tests/ \
        --cov=spark_eda --cov-branch --cov-report=html \
        --cov-fail-under=95

test-benchmark:
    docker-compose run --rm benchmark

shell:
    docker-compose run --rm shell

build:
    docker-compose build

clean:
    docker-compose down -v
    rm -rf coverage/ benchmark_output/ .pytest_cache/ __pycache__/
```

#### Workflow

1. **First run**: `make build` (builds the Docker image with PySpark)
2. **Development**: `make test-all` (runs everything in the container)
3. **During coding**: `docker-compose run --rm test pytest tests/integration/test_quality_score.py -v --tb=short` (fast, no rebuild needed — code is mounted)
4. **CI**: Same `docker-compose run --rm test` command used in CI pipeline

Benefits:
- Zero local Java/PySpark setup
- Same environment in dev and CI
- Code changes are live-mounted — no image rebuild for iterative development
- Multi-version testing (3.14 and 3.15) via separate compose services

### 10.6 Key Test Scenarios

| # | Scenario | What it tests | Layer |
|---|----------|---------------|-------|
| 1 | **Empty DataFrame** (zero rows, valid schema) | Graceful handling of zero rows — no division by zero, no crashes | Integration |
| 2 | **All-null columns** (every value is null) | Null-specific logic: stats return None, correlations skip, quality score = 0 for completeness | Integration |
| 3 | **Single column, single row** | Minimum viable report | Integration |
| 4 | **Column with constant values** (identical values) | Detects constant columns (variance = 0), quality factor penalty | Integration |
| 5 | **Column with single non-null value** | Edge case for statistics: mean = that value, stddev = 0, skewness/kurtosis undefined | Integration |
| 6 | **High-cardinality string column** (100K unique values in 100K rows) | Categorical strategy: should detect cardinality, approximate distinct count accuracy | Integration |
| 7 | **CPF/CNPJ/email/UUID/CEP/URL/IP columns** | Business column inference — pattern matching accuracy, no false positives | Integration |
| 8 | **Date column with regular gaps** (weekends missing) | Temporal analysis: gap detection, temporal completeness score | Integration |
| 9 | **Nullable numeric column** (30% null, 70% distributed) | Mixed null handling in stats, null ratio in quality | Integration |
| 10 | **Duplicate rows** (20% duplicate, 80% unique) | Duplicate detection ratio, uniqueness dimension score | Integration |
| 11 | **Five identical columns** (col_a = col_b = col_c) | Correlation matrix edge case — perfect correlation, no division by zero | Integration |
| 12 | **DataFrame with 500 columns** (mixed types) | Horizontal scalability — verify execution completes within time budget | Benchmark |
| 13 | **Schema evolution** (column added, type changed, column dropped) | Schema resilience: run analyze() after each schema mutation | Integration |
| 14 | **Large dataset — 10M rows, 50 columns** | Distributed performance: Spark AQE tuning, shuffle optimization | Benchmark |
| 15 | **Very large dataset — 100M rows, 20 columns** (if CI resources allow) | Approximate algorithm validation: compare approx vs exact on sample | Benchmark |
| 16 | **Near-constant column** (99.9% same value, 0.1% varying) | Near-constant detection in quality factors | Integration |
| 17 | **Corrupted data** (garbled UTF-8, placeholder values like "test", "asdf") | Corrupted data detection in accuracy dimension | Integration |
| 18 | **Suspicious data** (age=150, salary=-1000, birth > death) | Contradictory value detection, range violations | Integration |
| 19 | **Cross-column inconsistency** (start_date > end_date, city != state) | Cross-column consistency factor validation | Integration |
| 20 | **Referential integrity** (column with orphan IDs) | Orphan detection in integrity dimension | Integration |
| 21 | **Invalid dates** (Feb 30, year=19000, month=13) | Invalid date parsing, temporal dimension penalty | Integration |
| 22 | **Format inconsistency** (mixed date formats in same column) | Format consistency factor penalty | Integration |
| 23 | **All-boolean DataFrame** | Boolean statistics — true/false ratio, mode detection | Integration |
| 24 | **All-string DataFrame** (no numeric, no date) | Graceful degradation — correlations/outliers skipped, relevant sections empty | Integration |
| 25 | **Mixed types in single column** (e.g., string column with 90% parseable as numbers) | Type consistency detection | Integration |
| 26 | **Floating point edge cases** (NaN, Inf, -Inf, extremely small/large values) | Spark numeric stability | Integration |
| 27 | **Unicode/text columns** (accented chars, RTL text, emoji, CJK) | Length stats, corrupted data detection (no false positives) | Integration |
| 28 | **Explicit `invalidate_cache()` then re-analyze** | Cache invalidation — second call recomputes, not stale | Integration |
| 29 | **Two sequential analyze() calls with same DataFrame** | Cache hit — second call returns cached, no additional Spark jobs | Integration |
| 30 | **analyze() followed by assess_quality() on same df** | Cross-function cache reuse — quality reuses phase 1 data | Integration |
| 31 | **Very high-cardinality string as primary key** (UUID, hash) | PK detection — no false positive on business column inference | Integration |
| 32 | **Monotonically increasing ID column** | Auto-increment detection, excluded from correlation by default | Integration |

---

## 11. Future Evolution Roadmap

### Phase 1 — Foundation (0.x → 1.0)
- [ ] **Domain layer**: entities (DataProfile, ColumnProfile, QualityScore, Insight, Recommendation, DatasetAnalysis)
- [ ] **Domain layer**: value objects (DataType, InferredType, Severity, CorrelationMethod, OutlierMethod)
- [ ] **Domain layer**: QualityCalculator service (Completeness, Uniqueness dimensions)
- [ ] **Domain layer**: ColumnClassifier service (inferência de tipo de negócio)
- [ ] **Use cases layer**: AnalyzeDatasetUseCase, AssessQualityUseCase
- [ ] **Use cases layer**: ports (DataProvider, CacheProvider, OutputPresenter)
- [ ] **Adapter layer**: SparkDataProvider (profile computation, single-pass aggregations)
- [ ] **Adapter layer**: LRUCacheProvider, AnalysisPresenter, QualityPresenter
- [ ] **Adapter layer**: DTOs (EDAReport, OverviewSection, SchemaSection, QualitySection)
- [ ] **Adapter layer**: HTML renderer (básico)
- [ ] **Framework layer**: config, spark_session, exceptions, composite root
- [ ] Cross-layer quality factor registry (domain score + adapter spark computation)
- [ ] Per-factor score documentation in QualityReport
- [ ] Domain service tests (pytest puro, sem Spark, >95% coverage)
- [ ] Use case tests (mocks das portas)
- [ ] Provider integration tests (Docker + PySpark local)
- [ ] Docker testing infrastructure (Dockerfile, docker-compose, Makefile)
- [ ] HELPERS.md com referência rápida e armadilhas comuns
- [ ] Scripts de scaffold (`scaffold_factor.py`, `scaffold_strategy.py`)
- [ ] Templates de implementação (domain service, adapter strategy, AAA test) na documentação
- [ ] CI pipeline (lint → typecheck → domain tests → use case tests → integration tests → coverage → benchmark)

### Phase 2 — Analysis Depth (1.x)
- [ ] **Domain**: TemporalStats, TextStats, BooleanStats entities + calculators
- [ ] **Domain**: CorrelationCalculator service (Pearson, Spearman, Cramér's V — puro, sem Spark)
- [ ] **Domain**: OutlierCalculator service (IQR, Z-score, MAD — puro)
- [ ] **Domain**: InsightEngine (nulls, skewness, cardinality, duplicates, constants, zeros)
- [ ] **Domain**: Quality factors — range consistency, type consistency, cross-column consistency, ref_integrity
- [ ] **Domain**: Quality factors — format_consistency, invalid_dates, temporal_gaps, freshness
- [ ] **Domain**: Quality factors — corrupted data, suspicious data, business rules
- [ ] **Adapter**: SparkDataProvider — temporal, text, boolean strategies
- [ ] **Adapter**: SparkDataProvider — correlation strategies (Spark UDFs para Spearman, Cramér's V)
- [ ] **Adapter**: SparkDataProvider — outlier detectors
- [ ] **Adapter**: ColumnInferrer — business column inference (CPF, CNPJ, email, UUID, CEP, phone, URL, IP)
- [ ] **Adapter**: Distribution renderers (histogram, frequency, temporal)
- [ ] **Adapter**: Correlation heatmap visualization
- [ ] **Adapter**: Distribution plots

### Phase 3 — Intelligence (2.x)
- [ ] **Domain**: RecommendationEngine (priority-ordered suggestions based on quality factors)
- [ ] **Domain**: Quality dimensions — Accuracy (outlier ratio, format accuracy, business rules)
- [ ] **Domain**: Quality dimensions — Timeliness (freshness, temporal completeness, date validity)
- [ ] **Domain**: Quality dimensions — Consistency (schema integrity, referential integrity, format consistency)
- [ ] **Domain**: Cross-column consistency rules
- [ ] **Domain**: Dataset comparison entity + use case (diff two DataFrames)
- [ ] **Domain**: Time-series specific analysis
- [ ] **Adapter**: Top Penalizers section in quality report
- [ ] **Adapter**: JSON export
- [ ] **Adapter**: Markdown export
- [ ] **Adapter**: Schema evolution resilience tests
- [ ] **Adapter**: Support for Delta Lake metadata enhancements (via SparkDataProvider)

### Phase 4 — Enterprise (3.x)
- [ ] **Domain/Adapter**: Custom insight rule plugins (via registry pattern)
- [ ] **Domain/Adapter**: Custom quality dimensions (via registry pattern)
- [ ] **Adapter**: Monitoring integration (emit quality score to observability)
- [ ] **Adapter**: Expectations framework (export quality rules as Great Expectations suites)
- [ ] **Adapter**: CI/CD integration (diff quality scores between pipeline runs)
- [ ] **Adapter**: Internationalization (renderers with i18n)
- [ ] **Adapter**: PandasDataProvider (optional, secondary adapter para Pandas DataFrames)

### Out of Scope (For Now)
- Real-time streaming EDA
- ML-based anomaly detection
- Data catalog / data discovery
- Interactive dashboard server
- Database connectors (use Spark for that)

---

## 12. Padrões de Código e Helpers de Implementação

### 12.1 Convenções de Linguagem e Nomeação

#### Regra de Idioma: Apenas Docstrings em Português

| O quê | Idioma | Exemplo |
|-------|--------|---------|
| Docstrings (Google Style) | **Português** | `"""Calcula o score de qualidade..."""` |
| Nomes de classes, funções, variáveis | **Inglês** | `class QualityCalculator`, `def compute_score()` |
| Comentários de código | **Inglês** | `# Normalize by number of columns` |
| README, documentação, CHANGELOG | **Inglês** | Tudo em inglês (open source) |
| Commit messages | **Inglês** | `feat: add quality factor registry` |
| UI/CLI output, logs | **Inglês** | `"Analysis complete. Quality score: 87.3"` |

**Motivação**: Docstrings em português reduzem a barreira de entrada para o público principal (falantes de português). Todo o resto em inglês porque o código é lido globalmente, as ferramentas (PySpark, pytest, mypy) são em inglês, e open source requer inglês.

#### Nomeação: Sempre Completamente Explicativa

Nomes de variáveis, funções, classes e módulos devem ser **auto-explicativos**, mesmo que longos. Preferir clareza a brevidade.

```python
# ❌ RUIM — abreviado, ambíguo
def calc_qs(df, cfg): ...


# ✅ BOM — completamente explicativo
def calculate_quality_score(dataframe: DataFrame, config: QualityConfig) -> QualityScore: ...


# ❌ RUIM — genérico
valores = [1, 2, 3]

# ✅ BOM — revela intenção
salarios_mensais_em_reais = [1000.0, 2000.0, 3000.0]

# ❌ RUIM — acrônimo não documentado
ncc = compute_near_constant_columns(...)

# ✅ BOM — nome completo
numero_colunas_quase_constantes = compute_near_constant_columns(...)

# ❌ RUIM — variável temporária sem significado
tmp = df.groupBy("status").agg(...)

# ✅ BOM — nome descreve o conteúdo
contagem_por_status = df.groupBy("status").agg(F.count("*").alias("total"))

# ❌ RUIM — retorno genérico
return {"s": 0.95, "f": [...]}

# ✅ BOM — dicionário com chaves auto-explicativas
return {
    "quality_score": 0.95,
    "contributing_factors": [...],
    "affected_columns": ["email", "phone"],
}
```

Princípios:
- **Sem abreviações**: `calc` → `calculate`, `cfg` → `config`, `df` → `dataframe`, `idx` → `index`
- **Sem acrônimos não óbvios**: `ncc` → `near_constant_count`, `qs` → `quality_score`
- **Sem nomes de uma letra**: Exceto `i`, `j` em loops simples e `_` para descarte
- **Revelar intenção**: O nome deve dizer o que a variável contém, não como foi obtida
- **Contexto completo**: `salarios` é ambíguo → `salarios_mensais_por_funcionario`
- **Inglês para tudo que não é docstring**: `monthly_salaries_by_employee`

#### Docstrings — Google Style em Português

Toda classe pública, método público e função pública **deve** possuir docstring no formato Google Style, em português.

```python
def analisar_dataframe(df: DataFrame, config: EDAConfig | None = None) -> EDAReport:
    """Executa análise exploratória completa em um DataFrame PySpark.

    Esta função é o ponto de entrada principal da biblioteca. Ela orquestra
    todas as seções de análise (visão geral, schema, qualidade, estatísticas,
    distribuições, correlações, outliers, insights e recomendações) e retorna
    um objeto EDAReport com os resultados.

    Args:
        df: DataFrame PySpark a ser analisado.
            Não deve ser None. O schema deve conter ao menos uma coluna.
        config: Configurações opcionais para personalizar a análise.
            Se None, usa EDAConfig() com valores padrão (zero config).

    Returns:
        EDAReport contendo todas as seções da análise.
        Cada seção é acessível como atributo nomeado.

    Raises:
        ValueError: Se o DataFrame for None ou estiver vazio (zero colunas).
        PySparkAnalysisError: Se ocorrer erro durante a execução Spark.

    Example:
        >>> from pyspark.sql import SparkSession
        >>> spark = SparkSession.builder.getOrCreate()
        >>> df = spark.createDataFrame([(1, 'a'), (2, 'b')], ['id', 'nome'])
        >>> relatorio = analisar_dataframe(df)
        >>> print(relatorio.visao_geral.linha_count)
        2
    """
```

Regras:
- **Idioma**: português (descrições, args, returns, raises, examples)
- **Formato**: Google Style (Args:, Returns:, Raises:, Example:)
- **Toda classe pública**: incluindo dataclasses de resultado
- **Toda strategy concreta**: documentar qual problema resolve, quando usar
- **Todo fator de qualidade**: documentar fórmula, threshold, severidade
- **Todo módulo `__init__.py`**: docstring do módulo explicando o propósito
- **Todo método privado complexo**: docstring opcional, mas recomendada para lógica não-trivial

### 12.2 Templates de Implementação

Cada template explicita EM QUAL CAMADA da Clean Architecture ele vive.

#### Template: Novo Domain Service (CAMADA DOMAIN — sem Spark)

```python
"""Serviço de domínio: [nome do serviço].

Responsabilidade: [descrição]. Opera APENAS sobre entidades do domínio.
Sem dependência de Spark, I/O, ou qualquer framework.
"""

from __future__ import annotations

from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityScore, QualityDimension, QualityFactor
from spark_eda.domain.value_objects.severity import Severity


class MeuNovoDominioService:
    """Serviço de domínio para [propósito].

    Este serviço é PURO — não importa nada de adapters/ ou framework/.
    É testável com pytest sem fixtures, sem Spark, sem Docker.

    Usage:
        >>> service = MeuNovoDominioService()
        >>> resultado = service.executar(data_profile)
    """

    def executar(self, profile: DataProfile) -> list[MeuResultado]:
        """Executa [operação] sobre o perfil de dados.

        Args:
            profile: DataProfile completo do dataset analisado.

        Returns:
            Lista de MeuResultado com os resultados.

        Raises:
            ValueError: Se o profile estiver vazio (zero colunas).
        """
        # ARRANGE: extrair métricas do profile
        ...

        # ACT: aplicar regras de negócio (puramente matemáticas)
        ...

        # ASSERT: garantir invariantes do resultado
        ...

        return [MeuResultado(...)]


@dataclass(frozen=True)
class MeuResultado:
    """Resultado do serviço [nome].

    Attributes:
        nome: Identificador do resultado.
        valor_principal: Métrica principal calculada.
        detalhes: Informações adicionais.
    """

    nome: str
    valor_principal: float
    detalhes: dict[str, Any]
```


#### Template: Nova Strategy de Computação Spark (CAMADA ADAPTER — usa Spark)

```python
"""Strategy de computação Spark para [nome da estratégia].

Responsabilidade: calcular [métrica] usando PySpark e retornar
uma ENTIDADE do domínio (DataProfile, ColumnProfile, etc.).

Esta strategy NUNCA retorna dicts ou tuplas — sempre entidades.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, functions as F

from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.statistic import NumericStats
from spark_eda.domain.value_objects.data_type import DataType


def computar_stats_numericas(
    df: DataFrame,
    coluna: str,
    tipo: DataType,
) -> NumericStats:
    """Calcula estatísticas numéricas para uma coluna usando single-pass agg.

    Args:
        df: DataFrame PySpark com os dados.
        coluna: Nome da coluna numérica.
        tipo: DataType confirmado da coluna.

    Returns:
        NumericStats (entidade do domínio) com média, std, quantis, etc.

    Nota:
        Esta função executa Spark. Deve ser chamada APENAS de dentro de
        um provider (adapters/providers/), nunca de use_cases/ ou domain/.
    """
    # ARRANGE: preparar expressões (Spark native, sem UDFs)
    exprs = [
        F.count(F.col(coluna)).alias(f"{coluna}_count"),
        F.mean(F.col(coluna)).alias(f"{coluna}_mean"),
        F.stddev(F.col(coluna)).alias(f"{coluna}_std"),
        F.min(F.col(coluna)).alias(f"{coluna}_min"),
        F.max(F.col(coluna)).alias(f"{coluna}_max"),
        F.skewness(F.col(coluna)).alias(f"{coluna}_skew"),
        F.kurtosis(F.col(coluna)).alias(f"{coluna}_kurt"),
    ]

    # ACT: executar agg single-pass (1 collect, 1 row)
    row = df.agg(*exprs).collect()[0]

    # ASSERT: validar consistência (domain check, sem Spark)
    if row[f"{coluna}_count"] == 0:
        raise ValueError(f"Coluna {coluna} não possui linhas não-nulas")

    # Retorna ENTIDADE do domínio
    return NumericStats(
        coluna=coluna,
        count=row[f"{coluna}_count"],
        mean=row[f"{coluna}_mean"],
        std=row[f"{coluna}_std"],
        min=row[f"{coluna}_min"],
        max=row[f"{coluna}_max"],
        skewness=row[f"{coluna}_skew"],
        kurtosis=row[f"{coluna}_kurt"],
    )
```


#### Template: Novo Fator de Qualidade (DUAS PARTES)

Um fator de qualidade tem **duas implementações separadas** por camada:

1. **Spark computation** (ADAPTER): computa métricas brutas do DataFrame
2. **Score calculation** (DOMAIN): converte métricas brutas em score normalizado

##### Parte 1 — Adapter: Computação Spark

```python
# adapters/providers/quality_factors/near_constant.py
"""Computação Spark para o fator: colunas quase constantes.

Esta função é CHAMADA pelo SparkDataProvider durante a fase de qualidade.
Retorna métricas BRUTAS, não normalizadas.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, functions as F


@dataclass(frozen=True)
class NearConstantMetrics:
    """Métricas brutas de colunas quase constantes.

    Attributes:
        colunas_afetadas: Lista de colunas com variancia < 1%.
        total_colunas: Total de colunas analisadas.
        proporção_afetadas: Razão entre afetadas e total.
    """

    colunas_afetadas: tuple[str, ...]
    total_colunas: int
    proporção_afetadas: float


def computar_metricas(df: DataFrame, colunas: list[str]) -> NearConstantMetrics:
    """Detecta colunas quase constantes usando Spark aggregations.

    Args:
        df: DataFrame PySpark a ser analisado.
        colunas: Lista de colunas para verificar.

    Returns:
        NearConstantMetrics com as métricas brutas.
    """
    # ARRANGE: para cada coluna, computar distinct count aproximado
    ...

    # ACT: filter distinct_count / total_rows < 0.01
    ...

    # Retorna métricas BRUTAS (não normalizadas)
    return NearConstantMetrics(
        colunas_afetadas=tuple(afetadas),
        total_colunas=len(colunas),
        proporção_afetadas=len(afetadas) / len(colunas),
    )
```

##### Parte 2 — Domain Service: Cálculo do Score

```python
# domain/services/quality_factors/near_constant.py
"""Serviço de domínio: score de colunas quase constantes.

PURO — sem Spark. Recebe métricas brutas, retorna QualityFactor.
"""

from __future__ import annotations

from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.value_objects.severity import Severity


def calcular_score(
    metrics: NearConstantMetrics,  # ← do adapter (DTO simples)
    peso_interno: float = 0.15,
) -> QualityFactor:
    """Calcula o score normalizado para colunas quase constantes.

    Args:
        metrics: Métricas brutas do adapter de computação Spark.
        peso_interno: Peso deste fator dentro da dimensão Uniqueness.

    Returns:
        QualityFactor com score normalizado (0-1) e razão explicativa.
    """
    # ARRANGE: extrair métricas
    proporção = metrics.proporção_afetadas
    qtd = len(metrics.colunas_afetadas)

    # ACT: aplicar regra de negócio (matemática pura)
    # Penalidade linear: cada 10% de colunas afetadas reduz 0.2 do score
    score = max(0.0, 1.0 - (proporção * 2.0))
    score = round(score, 4)

    # Determinar severidade
    if score >= 0.95:
        severidade = Severity.BAIXA
    elif score >= 0.80:
        severidade = Severity.MEDIA
    else:
        severidade = Severity.ALTA

    # ASSERT: validar range
    assert 0.0 <= score <= 1.0, f"Score {score} fora do range [0, 1]"

    # Retorna ENTIDADE DO DOMÍNIO
    return QualityFactor(
        nome="near_constant_columns",
        score=score,
        peso_interno=peso_interno,
        contribuicao=score * peso_interno,
        razao=f"{qtd} colunas quase constantes detectadas (variancia < 1%)",
        severidade=severidade,
        colunas_afetadas=list(metrics.colunas_afetadas),
    )
```

#### Template: Teste AAA — Três Camadas

Cada camada tem seu próprio padrão de teste:

##### Domain Service Test (pytest puro — sem Spark, sem fixtures)

```python
"""Testes para [domain service].

Camada: DOMAIN. Não precisa de Spark, Docker, ou fixtures complexas.
"""

from __future__ import annotations

from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.services.quality_calculator import QualityCalculator
from spark_eda.domain.value_objects.data_type import DataType


class TestQualityCalculator:
    """Suíte de testes para QualityCalculator (domínio puro)."""

    def setup_method(self):
        """Cria dependências de domínio (sem Spark)."""
        self.calculator = QualityCalculator()

    def test_deve_calcular_score_zero_para_dataframe_totalmente_nulo(self):
        """Quality score deve ser 0 quando todas as colunas são 100% nulas."""
        # ARRANGE
        colunas = (
            ColumnMetadata(nome="id", tipo=DataType.INTEGER, nulo_count=100, nao_nulo_count=0),
            ColumnMetadata(nome="nome", tipo=DataType.STRING, nulo_count=100, nao_nulo_count=0),
        )
        profile = DataProfile(
            id="teste",
            colunas=colunas,
            linha_count=100,
            coluna_profiles={},
        )

        # ACT
        score = self.calculator.compute(profile)

        # ASSERT
        assert score.overall == 0.0
        assert score.dimensoes["completude"].score == 0.0

    def test_deve_calcular_score_perfeito_para_dataframe_sem_nulos_nem_duplicatas(self):
        """Quality score deve ser 100 quando dados são perfeitos."""
        # ARRANGE
        ...

        # ACT
        score = self.calculator.compute(profile)

        # ASSERT
        assert score.overall == 100.0
```

##### Use Case Test (mock das portas)

```python
"""Testes para AnalyzeDatasetUseCase.

Camada: USE CASES. Depende de domain (real) + ports (mockadas).
"""

from __future__ import annotations

from unittest.mock import Mock

from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.use_cases.analyze_dataset import AnalyzeDatasetUseCase, AnalyzeRequest


class TestAnalyzeDatasetUseCase:
    """Suíte de testes para o caso de uso de análise."""

    def setup_method(self):
        """Cria use case com portas mockadas."""
        self.data_provider = Mock()
        self.cache_provider = Mock()
        self.quality_calc = Mock()
        self.insight_engine = Mock()
        self.rec_engine = Mock()

        self.use_case = AnalyzeDatasetUseCase(
            data_provider=self.data_provider,
            cache_provider=self.cache_provider,
            quality_calculator=self.quality_calc,
            insight_engine=self.insight_engine,
            recommendation_engine=self.rec_engine,
        )

    def test_deve_retornar_analise_completa(self):
        """Use case deve orquestrar provider e serviços e retornar DatasetAnalysis."""
        # ARRANGE
        request = AnalyzeRequest(colunas=["id", "nome", "salario"])
        profile_mock = Mock(spec=DataProfile)
        self.data_provider.compute_profile.return_value = profile_mock

        # ACT
        resultado = self.use_case.execute(request)

        # ASSERT
        self.data_provider.compute_profile.assert_called_once()
        self.quality_calc.compute.assert_called_once_with(profile_mock)
        assert isinstance(resultado, DatasetAnalysis)

    def test_deve_usar_cache_quando_disponivel(self):
        """Use case não deve chamar provider se cache tiver resultado."""
        # ARRANGE
        request = AnalyzeRequest(colunas=["id"])
        analysis_mock = Mock(spec=DatasetAnalysis)
        self.cache_provider.get.return_value = analysis_mock

        # ACT
        resultado = self.use_case.execute(request)

        # ASSERT
        self.data_provider.compute_profile.assert_not_called()
        assert resultado is analysis_mock
```

##### Provider Test (Docker + PySpark)

```python
"""Testes para SparkDataProvider.

Camada: ADAPTER. Requer PySpark (executar via Docker).
"""

from __future__ import annotations

import pytest
from pyspark.sql import SparkSession

from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.adapters.providers.spark_data_provider import SparkDataProvider
from spark_eda.framework.config import EDAConfig


class TestSparkDataProvider:
    """Suíte de testes para o provider Spark."""

    @classmethod
    def setup_class(cls):
        """Inicializa SparkSession uma vez (Docker)."""
        cls.spark = (
            SparkSession.builder
            .master("local[1]")
            .appName("test")
            .config("spark.sql.shuffle.partitions", "1")
            .getOrCreate()
        )

    def test_deve_computar_profile_corretamente(self):
        """Provider deve retornar DataProfile com métricas corretas."""
        # ARRANGE: criar DataFrame controlado
        dados = [(1, "joão", 1000.0), (2, "maria", 2000.0), (3, None, None)]
        schema = "id INT, nome STRING, salario DOUBLE"
        df = self.spark.createDataFrame(dados, schema)
        provider = SparkDataProvider(self.spark, EDAConfig())

        # ACT: computar profile
        profile = provider.compute_profile(df)

        # ASSERT: verificar entidade de domínio
        assert isinstance(profile, DataProfile)
        assert profile.linha_count == 3
        assert profile.coluna_profiles["id"].stats.media == 2.0
        assert profile.colunas[1].nulo_count == 1  # nome tem 1 nulo
```

### 12.3 Registro de Fatores de Qualidade (Cross-Layer)

Cada fator de qualidade tem **dois registros separados**: um no domínio (score) e um no adapter (Spark computation). O `QualityCalculator` (domain service) usa o registry de domínio para aplicar todos os fatores.

```python
# ───────────────────────────────────────────────────────────────────────────
# DOMAIN LAYER: registry de funções de score (puras, sem Spark)
# domain/services/quality_factors/__init__.py
# ───────────────────────────────────────────────────────────────────────────

from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.value_objects.severity import Severity

# Cada função: recebe métricas brutas (dataclass simples), retorna QualityFactor
RegistryFn = Callable[[Any, float], QualityFactor]

FACTOR_REGISTRY: dict[str, RegistryFn] = {}


def registrar(nome: str):
    """Decorator para registrar um fator de qualidade no domínio."""

    def decorator(fn: RegistryFn) -> RegistryFn:
        FACTOR_REGISTRY[nome] = fn
        return fn

    return decorator


# ───────────────────────────────────────────────────────────────────────────
# ADAPTER LAYER: registry de funções de computação Spark
# adapters/providers/quality_factors/__init__.py
# ───────────────────────────────────────────────────────────────────────────

from pyspark.sql import DataFrame

# Cada função: recebe DataFrame, retorna métricas brutas (dataclass simples)
SparkFactorFn = Callable[[DataFrame, list[str]], Any]

SPARK_FACTOR_REGISTRY: dict[str, SparkFactorFn] = {}


def registrar_spark(nome: str):
    """Decorator para registrar um fator de computação Spark."""

    def decorator(fn: SparkFactorFn) -> SparkFactorFn:
        SPARK_FACTOR_REGISTRY[nome] = fn
        return fn

    return decorator


# ───────────────────────────────────────────────────────────────────────────
# Exemplo de uso: implementação completa de um fator
# ───────────────────────────────────────────────────────────────────────────


# 1. ADAPTER: computação Spark (adapters/providers/quality_factors/near_constant.py)
@registrar_spark("near_constant_columns")
def computar_near_constant(df: DataFrame, colunas: list[str]) -> NearConstantMetrics:
    """..."""


# 2. DOMAIN: score puro (domain/services/quality_factors/near_constant.py)
@registrar("near_constant_columns")
def calcular_score_near_constant(
    metrics: NearConstantMetrics,
    peso_interno: float = 0.15,
) -> QualityFactor:
    """..."""
```

Para adicionar um novo fator:
1. **Adapter**: criar `adapters/providers/quality_factors/meu_fator.py` com função `computar_metricas()` decorada com `@registrar_spark`
2. **Domain**: criar `domain/services/quality_factors/meu_fator.py` com função `calcular_score()` decorada com `@registrar`
3. **QualityCalculator** (domain service): itera `FACTOR_REGISTRY` aplicando cada fator ao `DataProfile`
4. **SparkDataProvider** (adapter): itera `SPARK_FACTOR_REGISTRY` para computar métricas brutas
5. Testes AAA para ambas as camadas

### 12.4 Checklist de Desenvolvimento — Clean Architecture

Antes de considerar um módulo pronto, verificar a **camada correta** e os **critérios** abaixo.

#### Para TODO código (qualquer camada)

- [ ] Docstring Google Style em português?
- [ ] Teste AAA cobre caso normal + edge case + exceção?
- [ ] Tipos são explícitos (sem `Any`, sem `object` genérico)?
- [ ] Resultado/retorno é frozen dataclass ou TypedDict?
- [ ] Sem variáveis/atributos sem tipo (`var = None` sem hint)?
- [ ] Nenhum `# type: ignore` sem justificativa documentada?

#### Para DOMAIN (domain/)

- [ ] **Zero imports de PySpark, adapters/, use_cases/, ou framework/**?
- [ ] **Zero imports de qualquer biblioteca externa** (ex: `pandas`, `numpy`, `requests`)?
- [ ] Testável com pytest puro (sem SparkSession, sem fixtures, sem Docker)?
- [ ] Entidades têm comportamento (métodos de negócio), não são só dados?
- [ ] Value objects substituem strings soltas (ex: `DataType.INTEGER` em vez de `"integer"`)?
- [ ] Domain services são stateless?
- [ ] Nenhum `collect()`, `toPandas()`, ou menção a DataFrame?

#### Para USE CASES (use_cases/)

- [ ] Importa APENAS `domain/` e `use_cases/ports/`?
- [ ] **NUNCA importa `adapters/` ou `framework/`**?
- [ ] **NUNCA importa PySpark**?
- [ ] Dependências injetadas no construtor (não criadas dentro do execute)?
- [ ] Use case retorna ENTIDADE (não dict, não ViewModel)?
- [ ] Testável com mocks das portas?

#### Para ADAPTER (adapters/)

- [ ] Implementa interface definida em `use_cases/ports/`?
- [ ] Retorna ENTIDADES do domínio (não dicts, não tuplas)?
- [ ] Spark usado APENAS aqui? (só `adapters/providers/`)
- [ ] Sem `collect()` em dados brutos? (só em resultados agregados)
- [ ] Sem `toPandas()` ou `.rdd.map()`?
- [ ] Sem iteração linha a linha?
- [ ] Agregações são single-pass (múltiplas expressões em um `agg()`)?
- [ ] `approx_count_distinct` usado para alta cardinalidade?
- [ ] Column pruning possível? (select apenas colunas necessárias)
- [ ] Filter pushdown possível? (filtros antes de agregações)
- [ ] Presenters convertem entidades → DTOs, sem lógica de negócio?

#### Para FRAMEWORK (framework/)

- [ ] Contém apenas configuração, setup, e exceções de infraestrutura?
- [ ] Nenhuma regra de negócio (exceto validação de tipos de input)?
- [ ] Composite Root monta todas as dependências?
- [ ] AQE está habilitado para auto-tuning?

### 12.5 Armadilhas Comuns (Gotchas)

| Problema | Sintoma | Causa | Solução |
|----------|---------|-------|---------|
| **Divisão por zero em skewness/kurtosis** | `NaN` em colunas constantes | stddev = 0 | Verificar stddev > 0 antes de calcular |
| **`approx_count_distinct` subestimando** | Cardinalidade menor que esperada | HiperLogLog com precisão padrão | Ajustar `rsd` para 0.01 em dados críticos |
| **Cache não invalidado** | Relatório não reflete novos dados | Fingerprint não mudou | Incluir timestamp do arquivo Parquet no hash |
| **CrossJoin explosivo** | OOM em correlação | Spark faz produto cartesiano | Usar join explícito com broadcast hint |
| **Null em correlação** | Resultados inconsistentes | Spark ignora nulls em `corr()` | Documentar que nulls são excluídos |
| **Tempo de execução alto em 500+ colunas** | Análise leva minutos | Múltiplos scans do DataFrame | Garantir que Phase 1 é single-pass |
| **Falso positivo em inferência de colunas** | CPF detectado em hash ID | Regex muito genérico | Validar com checksum (dígito verificador) |
| **Diferença entre ambientes Spark** | Teste passa local, falha no cluster | Configurações diferentes de partition | Testar com `spark.sql.shuffle.partitions` baixo no teste |
| **DataFrame fingerprint muda sem dados novos** | Cache sempre miss | Logical plan inclui lineage | Usar só schema + config hash para cache key, não plan |
| **`_jdf.queryExecution()` quebra em Spark 4.x** | Erro de atributo | API interna mudou | Encapsular em wrapper com fallback |

### 12.6 Arquivo de Referência Rápida (Quick Reference)

Manter um arquivo `HELPERS.md` na raiz do projeto com exemplos de uso comum:

```bash
# Executar todos os testes no Docker
make test-all

# Executar testes de um módulo específico
docker-compose run --rm test pytest tests/integration/test_quality_score.py -v

# Verificar cobertura
make test-coverage
# abrir coverage/html/index.html

# Verificar tipos
docker-compose run --rm test mypy spark_eda/ --strict

# Criar novo fator de qualidade (scaffold)
python scripts/scaffold_factor.py nome_do_fator --dimensao completude

# Criar nova strategy
python scripts/scaffold_strategy.py nome_da_strategy --dominio correlation
```

---

## Appendix: Data Quality Score Formula

```
```
Data Quality Score (0-100) = weighted sum of dimension scores

                  DIMENSIONS & WEIGHTS

  Completeness   (weight: 30%)
    ├── factor 1.1: Non-null ratio per column
    │     How: count(nulls) / count(*) per column → weighted by column criticality
    │     Score: 1.0 - (null_ratio × severity)
    │
    ├── factor 1.2: Row-level completeness
    │     How: rows where ALL columns are non-null / total rows
    │     Score: ratio of fully-populated rows
    │
    ├── factor 1.3: Empty / whitespace-only string fields
    │     How: count(trim(col) = '' OR col IS NULL) / count(*)
    │     Score: 1.0 - empty_ratio
    │
    └── factor 1.4: Zero-length fields (non-string)
          How: count(length(col) = 0) / count(*) for string-typed columns
          Score: 1.0 - zero_length_ratio

  Uniqueness     (weight: 20%)
    ├── factor 2.1: Duplicate row ratio
    │     How: (total_rows - distinct_rows) / total_rows
    │     Score: 1.0 - duplicate_ratio  (penalty doubles if ratio > 5%)
    │
    ├── factor 2.2: Primary key uniqueness
    │     How: if a PK column is detected (high cardinality, non-null):
    │           count(distinct(pk)) / count(*)
    │     Score: 1.0 if fully unique; linear penalty for duplicates
    │
    ├── factor 2.3: Near-duplicate row detection
    │     How: hash-based similarity on sampled rows (optional, configurable)
    │     Score: 1.0 - near_duplicate_ratio
    │
    ├── factor 2.4: Constant columns (0% variance)
    │     How: count(distinct(col)) = 1
    │     Score: each constant column reduces 2 points from dimension
    │
    ├── factor 2.5: Near-constant columns (< 1% variance)
    │     How: count(distinct(col)) / count(*) < 0.01
    │     Score: each near-constant column reduces 1 point from dimension
    │
    └── factor 2.6: Very high cardinality indicator
          How: count(distinct(col)) ≈ count(*) for non-PK columns
          Score: flagged as potential technical key — no penalty, just insight

  Consistency    (weight: 20%)
    ├── factor 3.1: Type consistency
    │     How: sample values and check if declared type matches detected type
    │           (e.g., string column that contains only numbers → type mismatch)
    │     Score: 1.0 - mismatched_column_ratio
    │
    ├── factor 3.2: Range consistency
    │     How: min/max values checked against expected bounds
    │           (negative age, future birth_date, salary = 0)
    │     Score: 1.0 - out_of_range_ratio
    │
    ├── factor 3.3: Cross-column consistency
    │     How: logical relationships (end_date >= start_date,
    │           total = sum(parts), country = state parent)
    │     Score: 1.0 - violation_ratio
    │
    ├── factor 3.4: Schema integrity
    │     How: column count vs expected, nullability constraints,
    │           column name conventions, missing required columns
    │     Score: 1.0 - schema_anomaly_ratio
    │
    ├── factor 3.5: Referential integrity
    │     How: if FK relationships are inferable (column name match
    │           with PK in another context), check orphan values
    │     Score: 1.0 - orphan_ratio  (only if FK is detected)
    │
    └── factor 3.6: Format consistency
          How: for string columns with format expectations
                (date strings, phone patterns, document formats),
                check that > 95% of non-null values match the dominant format
          Score: 1.0 - format_violation_ratio

  Timeliness     (weight: 15%)
    ├── factor 4.1: Data freshness
    │     How: time since max(last_updated) vs expected refresh cadence
    │     Score: 1.0 if within SLA; linear decay after SLA threshold
    │
    ├── factor 4.2: Temporal completeness
    │     How: expected time range coverage
    │           (gaps in date sequences, missing months)
    │     Score: 1.0 - gap_ratio
    │
    ├── factor 4.3: Invalid / impossible dates
    │     How: future dates, dates before 1900, February 30,
    │           dates that fail to_timestamp() parsing
    │     Score: 1.0 - invalid_date_ratio
    │
    └── factor 4.4: Temporal gap detection
          How: for time-series data, detect irregular intervals
          Score: 1.0 - irregular_gap_ratio

  Accuracy       (weight: 15%)
    ├── factor 5.1: Outlier ratio per numeric column
    │     How: IQR-based or Z-score-based outlier count
    │     Score: 1.0 - min(outlier_ratio × 5, 1.0)
    │
    ├── factor 5.2: Format accuracy (business format validation)
    │     How: for columns inferred as CPF, CNPJ, email, phone, CEP, UUID:
    │           validate each value against the format regex
    │     Score: 1.0 - format_violation_ratio
    │
    ├── factor 5.3: Suspicious data detection
    │     How: contradictory values (e.g., age = 5 AND salary > 1M),
    │           improbable combinations (gender = pregnancy),
    │           exact duplicates across all columns except PK
    │     Score: 1.0 - suspicious_row_ratio
    │
    ├── factor 5.4: Corrupted data patterns
    │     How: detect garbled text (high ratio of non-printable chars,
    │           repeated garbage characters, encoding artifacts),
    │           truncated fields (string length = max allowed),
    │           placeholder values ("test", "asdf", "xxx", "123")
    │     Score: 1.0 - corrupted_ratio
    │
    └── factor 5.5: Business rule violations
          How: user-defined or auto-inferred business rules
                (e.g., discount < price, birth_date < hire_date)
          Score: 1.0 - violation_ratio

SCORING ALGORITHM:
  dimension_score = weighted_mean(factor_scores)
  quality_score  = Σ(dimension_score × dimension_weight)

  Each factor contributes INDIVIDUALLY to the score.
  The QualityReport.factors dict contains EVERY factor with:
    {
      "dimension": "uniqueness",
      "score": 0.82,
      "weight": 0.20,
      "factors": [
        {
          "name": "near_constant_columns",
          "score": 0.75,
          "weight_within_dimension": 0.15,
          "contribution_to_total": 0.75 × 0.15 × 0.20 = 0.0225,
          "reason": "3 columns detected as near-constant (variance < 1%)",
          "severity": "medium",
          "affected_columns": ["status_flag", "environment", "is_active"]
        },
        ...
      ],
      "score_breakdown": "Each factor explained with actual values"
    }
```

Full example of a QualityReport.factors entry:
```json
{
  "overall_score": 73.4,
  "dimensions": {
    "completeness": {
      "score": 92.1,
      "weight": 0.30,
      "contribution": 27.6,
      "factors": [
        {"name": "non_null_ratio", "score": 0.97, "weight": 0.40, "note": "3 columns have >5% nulls: email (12%), phone (8%), region (6%)"},
        {"name": "row_completeness", "score": 0.88, "weight": 0.30, "note": "12% of rows have at least one null field"},
        {"name": "empty_strings", "score": 0.95, "weight": 0.15, "note": "5% of string fields are empty or whitespace"},
        {"name": "zero_length", "score": 0.99, "weight": 0.15, "note": "0.3% of fields have zero length"}
      ]
    },
    "uniqueness": {
      "score": 65.0,
      "weight": 0.20,
      "contribution": 13.0,
      "factors": [
        {"name": "duplicate_rows", "score": 0.60, "weight": 0.30, "note": "8% duplicate rows detected — ABOVE 5% threshold"},
        {"name": "constant_columns", "score": 0.70, "weight": 0.20, "note": "3 constant columns detected (weight: -2 each)"},
        {"name": "near_constant_columns", "score": 0.85, "weight": 0.15, "note": "3 near-constant columns (<1% variance, -1 each)"},
        {"name": "pk_uniqueness", "score": 1.00, "weight": 0.20, "note": "id column is fully unique"},
        {"name": "cardinality_warning", "score": 1.00, "weight": 0.15, "note": "no unexpected high-cardinality columns"}
      ]
    },
    "consistency": {"score": 78.2, "weight": 0.20, "contribution": 15.6, "factors": [...]},
    "timeliness":  {"score": 70.0, "weight": 0.15, "contribution": 10.5, "factors": [...]},
    "accuracy":    {"score": 63.0, "weight": 0.15, "contribution": 9.5, "factors": [...]}
  }
}
```

The quality score report ALWAYS includes a "Top Penalizers" section listing
the 5 factors that most reduced the score, so the user knows exactly where
to focus improvement efforts.
```

---

*Generated on 2026-07-23 as part of SDD exploration for spark_eda library.*
