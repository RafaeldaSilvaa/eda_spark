# spark_eda

**Distributed Exploratory Data Analysis and Data Quality Assessment for PySpark — one line of code, zero configuration.**

[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue)](https://www.python.org/downloads/)
[![PySpark](https://img.shields.io/badge/PySpark-4.0+-orange)](https://spark.apache.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/usuario/spark-eda/ci.yml?branch=main)](https://github.com/usuario/spark-eda/actions)
[![PyPI](https://img.shields.io/pypi/v/spark-eda)](https://pypi.org/project/spark-eda/)
[![Python Versions](https://img.shields.io/pypi/pyversions/spark-eda)](https://pypi.org/project/spark-eda/)

```python
import spark_eda

# Complete EDA report — one line
report = spark_eda.analyze(dataframe)

# Data Quality Score — one line
quality = spark_eda.assess_quality(dataframe)

# Both render automatically in Jupyter (HTML) and terminal (text)
print(report.quality.score)  # → 87.3
display(report)               # → Beautiful HTML report in Jupyter
```

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
  - [Complete EDA](#complete-eda)
  - [Data Quality Assessment](#data-quality-assessment)
  - [Accessing Individual Sections](#accessing-individual-sections)
  - [Configuration](#configuration)
- [Architecture](#architecture)
- [Output](#output)
- [Environments](#environments)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

`spark_eda` is a production-grade Python library for **distributed** Exploratory Data Analysis (EDA), Data Quality assessment, and automatic insight generation on PySpark DataFrames.

Unlike traditional EDA tools that collect data to the driver (and crash on large datasets), `spark_eda` performs **all computations in a distributed manner** using Spark's native functions. No `collect()`, no `toPandas()`, no row-by-row iteration.

It follows a **zero-configuration-by-default** philosophy: import, call, and get a complete report. Advanced configuration is optional and type-safe.

### Design Principles

- **Distributed-first**: Every operation uses Spark native aggregation — zero driver memory for data
- **Zero config**: `spark_eda.analyze(df)` produces a complete report with no setup
- **Deterministic**: All insights and recommendations come from heuristic rules, never AI/ML
- **Transparent**: The Data Quality Score (0–100) documents every contributing factor
- **Type-safe**: Full type hints, mypy strict mode, frozen dataclasses
- **Clean Architecture**: 4-layer architecture (Domain → Use Cases → Adapters → Framework) with strict dependency inversion

---

## Features

### Exploratory Data Analysis

| Section | Description |
|---------|-------------|
| **Overview** | Row count, column count, size estimate, duplicate ratio, missing ratio |
| **Schema** | Column names, types, nullability, inferred business types |
| **Statistics** | Numeric (mean, std, quantiles, skewness, kurtosis), categorical (value counts, mode, cardinality), temporal (date range, gaps, frequency), text (length stats, pattern detection), boolean (true/false ratio) |
| **Distributions** | Numeric histograms, categorical frequency charts, temporal distributions |
| **Correlations** | Pearson, Spearman, Cramér's V, Correlation Ratio — auto-selected by column type |
| **Outliers** | IQR, Z-score, MAD strategies — configurable |
| **Insights** | Skewness, nulls, cardinality, duplicates, constants, near-constants, high correlation, zeros — in natural language |
| **Recommendations** | Type fixes, null treatment, outlier handling, schema improvements — priority-sorted |

### Data Quality

| Feature | Description |
|---------|-------------|
| **Overall Score** | 0–100 weighted score with per-factor breakdown |
| **Completeness** | Null ratios, row-level completeness, empty strings, zero-length fields |
| **Uniqueness** | Duplicate rows, primary key uniqueness, near-duplicates, constant and near-constant columns |
| **Consistency** | Type consistency, range consistency, cross-column logic, schema integrity, referential integrity, format consistency |
| **Timeliness** | Data freshness, temporal completeness, invalid dates, temporal gaps |
| **Accuracy** | Outlier ratio, format validation (CPF, CNPJ, email, UUID, phone), suspicious data, corrupted data, business rules |
| **Top Penalizers** | The 5 factors that most reduced the score — with explanation and affected columns |

### Column Inference

`spark_eda` automatically detects business column types using pure Spark expression trees (no UDFs):

- Brazilian documents: CPF, CNPJ, CEP, phone, RG
- Global patterns: email, UUID, URL, IPv4, credit card
- Technical: auto-increment, primary key candidates, timestamps

---

## Installation

### Via pip

```bash
pip install spark-eda
```

### From source

```bash
git clone https://github.com/usuario/spark-eda.git
cd spark-eda
pip install -e ".[dev,test]"
```

### Requirements

- Python 3.14+
- PySpark 4.0+
- Java 21 (JRE) — required by PySpark

---

## Quick Start

### Analyze a DataFrame

```python
from pyspark.sql import SparkSession
import spark_eda

spark = SparkSession.builder.appName("eda").getOrCreate()
df = spark.read.parquet("s3://data/transactions/")

report = spark_eda.analyze(df)

# Auto-renders in Jupyter
display(report)

# Or explore programmatically
print(f"Rows: {report.overview.row_count}")
print(f"Columns: {report.overview.column_count}")
print(f"Quality Score: {report.quality.score}")
print(f"Insights: {len(report.insights.items)}")

for insight in report.insights.items:
    print(f"  [{insight.severity}] {insight.message}")

for recommendation in report.recommendations.items:
    print(f"  Priority {recommendation.priority}: {recommendation.message}")
```

### Assess Data Quality Only

```python
quality = spark_eda.assess_quality(df)

print(f"Overall: {quality.score}")
print(f"Completeness: {quality.dimensions['completeness'].score}")
print(f"Uniqueness: {quality.dimensions['uniqueness'].score}")

# See what hurt the score most
for penalizer in quality.top_penalizers:
    print(f"  -{penalizer.score * penalizer.weight:.1f} pts: {penalizer.reason}")
```

---

## Usage Examples

### Complete EDA

```python
import spark_eda
from spark_eda import EDAConfig

# Zero config
report = spark_eda.analyze(df)

# Or with custom config
config = EDAConfig(
    max_categories=100,
    correlation_methods=["pearson", "cramers_v"],
    outlier_method="iqr",
    enable_insights=True,
    enable_recommendations=True,
)
report = spark_eda.analyze(df, config=config)
```

### Accessing Individual Sections

```python
# Each section is an independent typed object
overview = report.overview
schema = report.schema
stats = report.stats
distributions = report.distributions
correlations = report.correlations
outliers = report.outliers
quality = report.quality
insights = report.insights
recommendations = report.recommendations

# Each section renders itself
print(overview)       # → Terminal-formatted text
display(schema)       # → HTML table in Jupyter
```

### Configuration Reference

```python
from spark_eda import EDAConfig, QualityConfig

# EDA configuration
eda_config = EDAConfig(
    max_categories=50,             # Max categories for frequency analysis
    correlation_methods=None,      # Auto-select or ["pearson", "spearman", ...]
    outlier_method="iqr",          # "iqr" | "zscore" | "mad"
    enable_insights=True,
    enable_recommendations=True,
    sampling_threshold=10_000_000, # Use sampling above this row count
)

# Quality-only configuration
quality_config = QualityConfig(
    completeness_weight=0.30,
    uniqueness_weight=0.20,
    consistency_weight=0.20,
    timeliness_weight=0.15,
    accuracy_weight=0.15,
    near_constant_threshold=0.01,  # Columns with <1% variance
)
```

---

## Architecture

`spark_eda` follows **Clean Architecture** with 4 strictly separated layers:

```
spark_eda/
├── domain/          # Entities, Value Objects, Domain Services — pure business logic
├── use_cases/       # Application-specific business rules — orchestrate entities
├── adapters/        # Spark computation, presenters, renderers — framework glue
└── framework/       # SparkSession, config, exceptions — outermost infrastructure
```

**Key architectural decisions:**

| Decision | Rationale |
|----------|-----------|
| **Spark only in adapters** | Domain and Use Cases are 100% testable without Spark — pure pytest |
| **Strategies as adapter pattern** | Stat, correlation, outlier strategies live in the adapter layer because they depend on Spark |
| **Ports for dependency inversion** | DataProvider, CacheProvider, OutputPresenter interfaces in use_cases/ports/ |
| **Presenters separate from entities** | Entities return themselves; Presenters convert them to ViewModels for output |

[Full architecture document →](docs/architecture.md)

---

## Output

### Jupyter Notebook

When used in a Jupyter notebook, `spark_eda` renders a complete HTML report automatically:

- Overview card with key metrics
- Schema table with inferred types
- Quality score gauge with dimension breakdown
- Statistics tables per column type
- Distribution charts (histograms, bar charts)
- Correlation heatmap
- Outlier summary
- Insight cards with severity indicators
- Recommendation list with priority ordering

### Terminal

In terminals, the output is a well-formatted text report with:

- Tables with aligned columns
- Color-coded severity indicators (when terminal supports ANSI)
- Compact format suitable for CI/CD logs

### Programmatic Access

Every section is accessible as a typed object with typed attributes:

```python
report.overview.row_count          # int
report.schema.columns["age"]       # ColumnMetadata
report.stats.numeric["age"]        # NumericStats
report.quality.score               # float (0–100)
report.quality.dimensions          # dict[str, QualityDimension]
report.quality.factors             # dict[str, list[QualityFactor]]
report.insights.items              # list[Insight]
report.recommendations.items       # list[Recommendation]
```

---

## Environments

`spark_eda` runs anywhere PySpark runs:

- **Jupyter Notebooks / JupyterLab** — auto-rendering HTML reports
- **Databricks** — optimized for Databricks Spark runtime
- **AWS Glue** — compatible with Glue PySpark jobs
- **Amazon EMR** — tested on EMR 7.x
- **Apache Spark standalone** — any SparkSession, any cluster
- **Local development** — `SparkSession.builder.master("local[*]")`

[Environment-specific guides →](docs/)

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/contributing.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/your-org/spark-eda.git
cd spark-eda
make build      # Build Docker image
make test-all   # Run full test suite in Docker
```

### Quick Commands

```bash
make test-all          # Full test suite (Docker)
make test-unit         # Domain tests only (fast, no Spark)
make test-integration  # Integration tests (Docker + PySpark)
make test-coverage     # Coverage report (target: >95%)
make lint              # ruff check
make typecheck         # mypy --strict
```

### Coding Standards

- **Docstrings**: Google Style, in Portuguese
- **Code**: English (all identifiers, comments, commits)
- **Naming**: Always fully descriptive — no abbreviations, no single-letter names (except loop counters)
- **Architecture**: Must follow Clean Architecture — no Spark imports in domain or use cases

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Roadmap

| Phase | Focus |
|-------|-------|
| **0.x → 1.0** | Core EDA, Quality Score (Completeness + Uniqueness), basic column inference, HTML reports, domain services |
| **1.x** | All correlation/outlier strategies, business column inference, temporal/text/boolean stats, insight engine, distribution plots |
| **2.x** | Recommendations engine, all quality dimensions, cross-column consistency, dataset comparison, JSON/Markdown export |
| **3.x** | Plugin system, expectations export, monitoring integration, i18n, Pandas adapter |

[Full roadmap →](docs/roadmap.md)
