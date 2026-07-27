"""Provider Spark que computa perfis a partir de DataFrames PySpark.

Implementa a interface :class:`DataProvider` usando agregação
PySpark em única passagem para extrair estatísticas descritivas,
distribuições, outliers, correlações e metadados de todas as colunas.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pyspark.sql import DataFrame
from pyspark.sql import functions as F  # noqa: N812
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DecimalType,
    DoubleType,
    FloatType,
    IntegerType,
    LongType,
    StringType,
    StructType,
    TimestampType,
)

from spark_eda.application.ports.data_provider import DataProvider
from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.correlation import Correlation
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.distribution import (
    CategoricalDistribution,
    Distribution,
    NumericDistribution,
    TemporalDistribution,
)
from spark_eda.domain.entities.outlier import OutlierInfo
from spark_eda.domain.entities.statistic import (
    BooleanStats,
    CategoricalStats,
    NumericStats,
    Statistic,
    TemporalStats,
    TextStats,
)
from spark_eda.domain.services.column_classifier import ColumnClassifier
from spark_eda.domain.value_objects.correlation_method import CorrelationMethod
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.inferred_type import InferredType
from spark_eda.domain.value_objects.outlier_method import OutlierMethod

_SPARK_TYPE_TO_DOMAIN: dict[type, DataType] = {
    IntegerType: DataType.INTEGER,
    LongType: DataType.LONG,
    DoubleType: DataType.DOUBLE,
    FloatType: DataType.DOUBLE,
    DecimalType: DataType.DECIMAL,
    StringType: DataType.STRING,
    BooleanType: DataType.BOOLEAN,
    DateType: DataType.DATE,
    TimestampType: DataType.TIMESTAMP,
}

_NUMERIC_TYPES: set[DataType] = {
    DataType.INTEGER,
    DataType.LONG,
    DataType.DOUBLE,
    DataType.DECIMAL,
}

_TEMPORAL_TYPES: set[DataType] = {
    DataType.DATE,
    DataType.TIMESTAMP,
}

_ZSCORE_THRESHOLD: float = 3.0
_MAD_THRESHOLD: float = 3.5
_MIN_QUARTILES: int = 3
_QUARTILE_Q75_IDX: int = 2
_TEXT_LENGTH_THRESHOLD: int = 50


def _infer_data_type(spark_field_type: object) -> DataType:
    """Mapeia o tipo nativo PySpark para o enum :class:`DataType` do domínio.

    Args:
        spark_field_type: Instância do tipo PySpark (ex.: IntegerType, StringType).

    Returns:
        :class:`DataType` correspondente no domínio.
    """
    domain_type: DataType | None = _SPARK_TYPE_TO_DOMAIN.get(
        type(spark_field_type),
    )
    if domain_type is not None:
        return domain_type
    return DataType.OTHER


def _build_numeric_agg_expressions(
    column_name: str,
    expression_list: list[Any],
) -> None:
    """Adiciona expressões de agregação numérica para uma coluna.

    Args:
        column_name: Nome da coluna no DataFrame.
        expression_list: Lista de expressões de agregação sendo construída.
    """
    expression_list.append(F.mean(column_name).alias(f"{column_name}__mean"))
    expression_list.append(F.stddev(column_name).alias(f"{column_name}__std"))
    expression_list.append(F.min(column_name).alias(f"{column_name}__min"))
    expression_list.append(F.max(column_name).alias(f"{column_name}__max"))
    expression_list.append(F.count(column_name).alias(f"{column_name}__count"))
    expression_list.append(
        F.count(F.when(F.isnull(F.col(column_name)), 1)).alias(
            f"{column_name}__null_count"
        ),
    )
    expression_list.append(
        F.approx_count_distinct(column_name).alias(f"{column_name}__approx_distinct"),
    )
    expression_list.append(
        F.skewness(column_name).alias(f"{column_name}__skewness"),
    )
    expression_list.append(
        F.kurtosis(column_name).alias(f"{column_name}__kurtosis"),
    )


def _build_string_agg_expressions(
    column_name: str,
    expression_list: list[Any],
) -> None:
    """Adiciona expressões de agregação para colunas de texto.

    Args:
        column_name: Nome da coluna no DataFrame.
        expression_list: Lista de expressões de agregação sendo construída.
    """
    expression_list.append(F.count(column_name).alias(f"{column_name}__count"))
    expression_list.append(
        F.count(F.when(F.isnull(F.col(column_name)), 1)).alias(
            f"{column_name}__null_count",
        ),
    )
    expression_list.append(
        F.approx_count_distinct(column_name).alias(
            f"{column_name}__approx_distinct",
        ),
    )
    expression_list.append(
        F.min(F.length(F.col(column_name))).alias(f"{column_name}__min_length"),
    )
    expression_list.append(
        F.max(F.length(F.col(column_name))).alias(f"{column_name}__max_length"),
    )
    expression_list.append(
        F.avg(F.length(F.col(column_name))).alias(f"{column_name}__avg_length"),
    )
    expression_list.append(
        F.avg(
            F.when(F.trim(F.col(column_name)) == "", 1.0).otherwise(0.0),
        ).alias(f"{column_name}__empty_ratio"),
    )


def _build_boolean_agg_expressions(
    column_name: str,
    expression_list: list[Any],
) -> None:
    """Adiciona expressões de agregação para colunas booleanas.

    Args:
        column_name: Nome da coluna no DataFrame.
        expression_list: Lista de expressões de agregação sendo construída.
    """
    expression_list.append(F.count(column_name).alias(f"{column_name}__count"))
    expression_list.append(
        F.count(F.when(F.isnull(F.col(column_name)), 1)).alias(
            f"{column_name}__null_count",
        ),
    )
    expression_list.append(
        F.sum(F.when(F.col(column_name), 1).otherwise(0)).alias(
            f"{column_name}__true_count",
        ),
    )
    expression_list.append(
        F.sum(F.when(~F.col(column_name), 1).otherwise(0)).alias(
            f"{column_name}__false_count",
        ),
    )


def _build_temporal_agg_expressions(
    column_name: str,
    expression_list: list[Any],
) -> None:
    """Adiciona expressões de agregação para colunas temporais (date, timestamp).

    Args:
        column_name: Nome da coluna no DataFrame.
        expression_list: Lista de expressões de agregação sendo construída.
    """
    expression_list.append(F.count(column_name).alias(f"{column_name}__count"))
    expression_list.append(
        F.count(F.when(F.isnull(F.col(column_name)), 1)).alias(
            f"{column_name}__null_count",
        ),
    )
    expression_list.append(
        F.min(column_name).alias(f"{column_name}__min_date"),
    )
    expression_list.append(
        F.max(column_name).alias(f"{column_name}__max_date"),
    )
    expression_list.append(
        F.datediff(
            F.max(column_name),
            F.min(column_name),
        ).alias(f"{column_name}__range_days"),
    )


def _build_value_counts(dataframe: DataFrame, column_name: str) -> dict[str, int]:
    """Computa a contagem de valores para uma coluna.

    Args:
        dataframe: DataFrame PySpark.
        column_name: Nome da coluna para computar a contagem de valores.

    Returns:
        Dicionário mapeando cada valor distinto à sua contagem.
    """
    rows: list[Any] = (
        dataframe.groupBy(column_name)
        .agg(F.count(F.lit(1)).alias("count"))
        .orderBy(F.col("count").desc())
        .limit(50)
        .collect()
    )

    value_counts: dict[str, int] = {}
    for row in rows:
        value: Any = row[column_name]
        count_value: Any = row["count"]
        if value is not None:
            value_counts[str(value)] = int(count_value)

    return value_counts


def _extract_numeric_stats(
    aggregation_row: Any,
    column_name: str,
    _total_rows: int,
) -> NumericStats:
    """Extrai estatísticas numéricas da linha de agregação em única passagem.

    Args:
        aggregation_row: Row resultante de df.agg().
        column_name: Nome da coluna.
        total_rows: Número total de linhas no dataset.

    Returns:
        :class:`NumericStats` com média, desvio padrão, quartis e outras métricas.
    """
    return NumericStats(
        mean=float(aggregation_row[f"{column_name}__mean"] or 0.0),
        std=float(aggregation_row[f"{column_name}__std"] or 0.0),
        min=float(aggregation_row[f"{column_name}__min"] or 0.0),
        q25=0.0,
        q50=0.0,
        q75=0.0,
        max=float(aggregation_row[f"{column_name}__max"] or 0.0),
        skewness=float(aggregation_row[f"{column_name}__skewness"] or 0.0),
        kurtosis=float(aggregation_row[f"{column_name}__kurtosis"] or 0.0),
    )


def _extract_categorical_stats(
    aggregation_row: Any,
    column_name: str,
    value_counts: dict[str, int],
    _total_rows: int,
) -> CategoricalStats:
    """Extrai estatísticas categóricas da linha de agregação.

    Args:
        aggregation_row: Row resultante de df.agg().
        column_name: Nome da coluna.
        value_counts: Dicionário de contagem de valores.
        total_rows: Número total de linhas no dataset.

    Returns:
        :class:`CategoricalStats` com cardinalidade, moda e proporção de únicos.
    """
    cardinality: int = len(value_counts)
    non_null_count: int = int(
        aggregation_row[f"{column_name}__count"] or 0,
    )

    mode: str | None = None
    if value_counts:
        mode = max(value_counts, key=value_counts.__getitem__)

    unique_ratio: float = (
        cardinality / non_null_count if non_null_count > 0 else 0.0
    )

    return CategoricalStats(
        value_counts=value_counts,
        mode=mode,
        cardinality=cardinality,
        unique_ratio=round(unique_ratio, 4),
    )


def _extract_temporal_stats(
    aggregation_row: Any,
    column_name: str,
) -> TemporalStats:
    """Extrai estatísticas temporais da linha de agregação.

    Args:
        aggregation_row: Row resultante de df.agg().
        column_name: Nome da coluna.

    Returns:
        :class:`TemporalStats` com datas mín/máx e intervalo.
    """
    min_date_value: Any = aggregation_row[f"{column_name}__min_date"]
    max_date_value: Any = aggregation_row[f"{column_name}__max_date"]

    min_date_str: str = str(min_date_value) if min_date_value is not None else ""
    max_date_str: str = str(max_date_value) if max_date_value is not None else ""

    range_days: int = int(aggregation_row[f"{column_name}__range_days"] or 0)

    return TemporalStats(
        min_date=min_date_str,
        max_date=max_date_str,
        range_days=range_days,
        gap_count=0,
    )


def _extract_text_stats(
    aggregation_row: Any,
    column_name: str,
) -> TextStats:
    """Extrai estatísticas de texto da linha de agregação.

    Args:
        aggregation_row: Row resultante de df.agg().
        column_name: Nome da coluna.

    Returns:
        :class:`TextStats` com comprimento mín/méd/máx e proporção de vazios.
    """
    return TextStats(
        min_length=int(aggregation_row[f"{column_name}__min_length"] or 0),
        max_length=int(aggregation_row[f"{column_name}__max_length"] or 0),
        avg_length=float(aggregation_row[f"{column_name}__avg_length"] or 0.0),
        empty_ratio=float(aggregation_row[f"{column_name}__empty_ratio"] or 0.0),
    )


def _extract_boolean_stats(
    aggregation_row: Any,
    column_name: str,
) -> BooleanStats:
    """Extrai estatísticas booleanas da linha de agregação.

    Args:
        aggregation_row: Row resultante de df.agg().
        column_name: Nome da coluna.

    Returns:
        :class:`BooleanStats` com contagens de true/false.
    """
    true_count: int = int(aggregation_row[f"{column_name}__true_count"] or 0)
    false_count: int = int(aggregation_row[f"{column_name}__false_count"] or 0)
    total: int = true_count + false_count
    true_ratio: float = true_count / total if total > 0 else 0.0

    return BooleanStats(
        true_count=true_count,
        false_count=false_count,
        true_ratio=round(true_ratio, 4),
    )


def _compute_outliers_iqr(
    dataframe: DataFrame,
    column_name: str,
    config: Any,
) -> OutlierInfo | None:
    """Detecta outliers em colunas numéricas usando o método IQR.

    Args:
        dataframe: DataFrame PySpark.
        column_name: Nome da coluna numérica.
        config: Configuração que pode conter o multiplicador IQR.

    Returns:
        :class:`OutlierInfo` com contagem e limites, ou None se não aplicável.
    """
    iqr_multiplier: float = getattr(config, "outlier_iqr_multiplier", 1.5)

    quartiles: list[float] = dataframe.approxQuantile(
        column_name,
        probabilities=[0.25, 0.50, 0.75],
        relativeError=0.01,
    )

    if len(quartiles) < _MIN_QUARTILES:
        return None

    q25: float = quartiles[0]
    q75: float = quartiles[2]

    iqr: float = q75 - q25
    bound_lower: float = q25 - iqr_multiplier * iqr
    bound_upper: float = q75 + iqr_multiplier * iqr

    outlier_count: int = (
        dataframe.filter(
            (F.col(column_name) < bound_lower)
            | (F.col(column_name) > bound_upper),
        ).count()
    )

    total_count: int = dataframe.count()
    outlier_ratio: float = (
        outlier_count / total_count if total_count > 0 else 0.0
    )

    return OutlierInfo(
        method=OutlierMethod.IQR,
        count=outlier_count,
        ratio=round(outlier_ratio, 4),
        bounds_lower=round(bound_lower, 4),
        bounds_upper=round(bound_upper, 4),
    )


def _compute_outliers_zscore(
    dataframe: DataFrame,
    column_name: str,
    config: Any,
) -> OutlierInfo | None:
    """Detecta outliers em colunas numéricas usando o método Z-score.

    Args:
        dataframe: DataFrame PySpark.
        column_name: Nome da coluna numérica.
        config: Configuração que pode conter o limite do z-score.

    Returns:
        :class:`OutlierInfo` com contagem e limites, ou None se não aplicável.
    """
    threshold: float = getattr(config, "outlier_zscore_threshold", _ZSCORE_THRESHOLD)

    stats_row: Any = dataframe.agg(
        F.mean(column_name).alias("mean_val"),
        F.stddev(column_name).alias("std_val"),
    ).collect()[0]

    mean_val: float = float(stats_row["mean_val"] or 0.0)
    std_val: float = float(stats_row["std_val"] or 0.0)

    if std_val == 0.0:
        return None

    bound_lower: float = mean_val - threshold * std_val
    bound_upper: float = mean_val + threshold * std_val

    outlier_count: int = (
        dataframe.filter(
            (F.col(column_name) < bound_lower)
            | (F.col(column_name) > bound_upper),
        ).count()
    )

    total_count: int = dataframe.count()
    outlier_ratio: float = (
        outlier_count / total_count if total_count > 0 else 0.0
    )

    return OutlierInfo(
        method=OutlierMethod.ZSCORE,
        count=outlier_count,
        ratio=round(outlier_ratio, 4),
        bounds_lower=round(bound_lower, 4),
        bounds_upper=round(bound_upper, 4),
    )


def _compute_outliers_mad(
    dataframe: DataFrame,
    column_name: str,
    config: Any,
) -> OutlierInfo | None:
    """Detecta outliers em colunas numéricas usando o método MAD (Desvio Absoluto Mediano).

    Args:
        dataframe: DataFrame PySpark.
        column_name: Nome da coluna numérica.
        config: Configuração que pode conter o limite MAD.

    Returns:
        :class:`OutlierInfo` com contagem e limites, ou None se não aplicável.
    """
    threshold: float = getattr(config, "outlier_mad_threshold", _MAD_THRESHOLD)

    # Approximate median via percentile
    median_list: list[float] = dataframe.approxQuantile(
        column_name,
        probabilities=[0.50],
        relativeError=0.01,
    )

    if not median_list:
        return None

    median_val: float = median_list[0]

    # Compute MAD = median(|xi - median|)
    mad_df: DataFrame = dataframe.select(
        F.abs(F.col(column_name) - median_val).alias("deviation"),
    )
    mad_list: list[float] = mad_df.approxQuantile(
        "deviation",
        probabilities=[0.50],
        relativeError=0.01,
    )

    if not mad_list or mad_list[0] == 0.0:
        return None

    mad_val: float = mad_list[0]

    bound_lower: float = median_val - threshold * mad_val
    bound_upper: float = median_val + threshold * mad_val

    outlier_count: int = (
        dataframe.filter(
            (F.col(column_name) < bound_lower)
            | (F.col(column_name) > bound_upper),
        ).count()
    )

    total_count: int = dataframe.count()
    outlier_ratio: float = (
        outlier_count / total_count if total_count > 0 else 0.0
    )

    return OutlierInfo(
        method=OutlierMethod.MAD,
        count=outlier_count,
        ratio=round(outlier_ratio, 4),
        bounds_lower=round(bound_lower, 4),
        bounds_upper=round(bound_upper, 4),
    )


def _compute_outliers(
    dataframe: DataFrame,
    column_name: str,
    config: Any,
    method: str | None = None,
) -> OutlierInfo | None:
    """Detecta outliers usando o método configurado ou especificado.

    Args:
        dataframe: DataFrame PySpark.
        column_name: Nome da coluna numérica.
        config: Configuração com preferência de método de outlier.
        method: Método de substituição. Se None, lê da config.

    Returns:
        :class:`OutlierInfo` ou None.
    """
    outlier_method = method or getattr(config, "outlier_method", "iqr")

    if outlier_method == "zscore":
        return _compute_outliers_zscore(dataframe, column_name, config)
    elif outlier_method == "mad":
        return _compute_outliers_mad(dataframe, column_name, config)

    # Default to IQR
    return _compute_outliers_iqr(dataframe, column_name, config)


def _compute_distribution(
    dataframe: DataFrame,
    column_name: str,
    domain_type: DataType,
    stats: Statistic,
    total_rows: int,
) -> Distribution | None:
    """Computa a distribuição de valores para uma coluna.

    Para colunas numéricas, computa bins de histograma.
    Para colunas categóricas, retorna distribuição por categoria.
    Para colunas temporais, agrupa por períodos anuais/mensais.

    Args:
        dataframe: DataFrame PySpark.
        column_name: Nome da coluna.
        domain_type: Tipo de dado da coluna no domínio.
        stats: Estatísticas da coluna.
        total_rows: Número total de linhas (já conhecido).

    Returns:
        :class:`Distribution` apropriada ou None se o tipo não for suportado.
    """
    if domain_type in _NUMERIC_TYPES and isinstance(stats, NumericStats):
        min_value: float = stats.min
        max_value: float = stats.max

        if min_value >= max_value or total_rows == 0:
            return None

        bin_count: int = 10
        bin_width: float = (max_value - min_value) / bin_count

        bins: list[tuple[float, float, int]] = []
        for bin_index in range(bin_count):
            bin_lower: float = min_value + bin_index * bin_width
            bin_upper: float = bin_lower + bin_width
            bin_counts: int = dataframe.filter(
                (F.col(column_name) >= bin_lower)
                & (
                    (F.col(column_name) < bin_upper)
                    | ((F.col(column_name) <= bin_upper) & (bin_index == bin_count - 1))
                ),
            ).count()
            bins.append((round(bin_lower, 4), round(bin_upper, 4), bin_counts))

        return NumericDistribution(bins=bins)

    if domain_type == DataType.STRING and isinstance(stats, CategoricalStats):
        categories: list[tuple[str, int]] = sorted(
            stats.value_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        top_categories: list[tuple[str, int]] = categories[:20]
        others_count: int = sum(count for _, count in categories[20:])

        return CategoricalDistribution(
            categories=top_categories,
            others_count=others_count,
        )

    # TemporalDistribution for temporal types
    if domain_type in _TEMPORAL_TYPES:
        return _compute_temporal_distribution(dataframe, column_name)

    return None  # pragma: no cover


def _compute_temporal_distribution(
    dataframe: DataFrame,
    column_name: str,
) -> TemporalDistribution | None:
    """Computa distribuição temporal agrupada por períodos anuais e mensais.

    Args:
        dataframe: DataFrame PySpark.
        column_name: Nome da coluna temporal.

    Returns:
        :class:`TemporalDistribution` com contagens por período, ou None em falha.
    """
    try:
        # Try yearly aggregation first
        periods: list[tuple[str, int]] = []

        # Yearly aggregation
        yearly_rows: list[Any] = (
            dataframe.groupBy(F.year(column_name).alias("year"))
            .agg(F.count(F.lit(1)).alias("count"))
            .orderBy("year")
            .collect()
        )

        if yearly_rows:
            periods = [
                (str(int(row["year"])), int(row["count"]))
                for row in yearly_rows
                if row["year"] is not None
            ]

        # If yearly is too coarse (single year), try monthly
        if len(periods) <= 1:
            monthly_rows: list[Any] = (
                dataframe.groupBy(F.date_format(column_name, "yyyy-MM").alias("month"))
                .agg(F.count(F.lit(1)).alias("count"))
                .orderBy("month")
                .collect()
            )

            if monthly_rows:
                periods = [
                    (str(row["month"]), int(row["count"]))
                    for row in monthly_rows
                    if row["month"] is not None
                ]

        if not periods:
            return None

        return TemporalDistribution(periods=periods)

    except Exception:
        return None


def _compute_both_string_stats(
    aggregation_row: Any,
    column_name: str,
    value_counts: dict[str, int],
    total_rows: int,
) -> tuple[CategoricalStats, TextStats]:
    """Computa estatísticas categóricas e de texto para uma coluna de string.

    Args:
        aggregation_row: Row resultante de df.agg().
        column_name: Nome da coluna.
        value_counts: Dicionário de contagem de valores.
        total_rows: Número total de linhas.

    Returns:
        Tupla de (CategoricalStats, TextStats).
    """
    categorical: CategoricalStats = _extract_categorical_stats(
        aggregation_row, column_name, value_counts, total_rows,
    )
    text: TextStats = _extract_text_stats(aggregation_row, column_name)

    return categorical, text


class SparkDataProvider(DataProvider):
    """Provider de dados que opera diretamente em DataFrames PySpark.

    Realiza agregação em única passagem para extrair perfis completos
    de colunas, minimizando o número de varreduras sobre o dataset.
    Todas as funções retornam entidades de domínio, nunca dicionários.
    """

    def __init__(self, column_classifier: ColumnClassifier | None = None) -> None:
        """Inicializa o provider com um classificador de colunas opcional.

        Args:
            column_classifier: Classificador semântico para inferir
                tipos de negócio das colunas. Se None, cria um padrão.
        """
        self._column_classifier: ColumnClassifier = (
            column_classifier or ColumnClassifier()
        )

    def compute_profile(  # noqa: PLR0912, PLR0915
        self,
        dataframe: DataFrame,
        columns: list[str] | None,
        config: Any,
    ) -> DataProfile:
        """Computa o perfil completo do dataset em agregação de única passagem.

        Constrói uma única lista de expressões de agregação baseada nos
        tipos de coluna, executa ``df.agg(*exprs)`` uma vez e distribui
        os resultados para as entidades de domínio apropriadas.

        Args:
            dataframe: DataFrame PySpark para perfilamento.
            columns: Colunas a incluir, ou None para todas.
            config: Configuração opcional (multiplicador IQR, etc.).

        Returns:
            :class:`DataProfile` com metadados, estatísticas,
            distribuições e informações de outliers.

        Raises:
            ValueError: Se uma coluna solicitada não existir no schema.
            RuntimeError: Se ocorrer um erro durante o processamento.
        """
        spark_schema: StructType = dataframe.schema

        column_names: list[str] = spark_schema.names
        if columns is not None:
            valid_columns: set[str] = set(column_names)
            missing_columns: list[str] = [
                col for col in columns if col not in valid_columns
            ]
            if missing_columns:
                raise ValueError(
                    f"The following columns do not exist in the schema: "
                    f"{missing_columns}",
                )
            column_names = columns

        # Sampling: if the dataset is too large, work on a sample
        total_rows: int = dataframe.count()
        profile_row_count: int = total_rows
        sampling_threshold: int = getattr(config, "sampling_threshold", 1_000_000)
        working_df: DataFrame = dataframe
        if total_rows > sampling_threshold > 0:
            fraction: float = sampling_threshold / total_rows
            working_df = dataframe.sample(withReplacement=False, fraction=fraction, seed=42)
            total_rows = working_df.count()

        classification_sample: DataFrame | None = None
        if any(
            getattr(config, "infer_semantic_types", True)
            and self._should_infer_column(col, spark_schema)
            for col in column_names
        ):
            classification_sample = working_df.select(column_names).limit(1000)

        inferred_types: dict[str, InferredType] = {}
        if classification_sample is not None:
            inferred_types = self._classify_columns(classification_sample, column_names)

        if total_rows == 0:
            columns_meta: list[ColumnMetadata] = []
            column_profiles_result: dict[str, ColumnProfile] = {}
            for column_name in column_names:
                field_type: Any = spark_schema[column_name].dataType
                domain_type: DataType = _infer_data_type(field_type)
                nullable: bool = spark_schema[column_name].nullable
                inferred: InferredType | None = inferred_types.get(column_name)
                columns_meta.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=domain_type,
                        nullable=nullable,
                        inferred_type=inferred,
                        null_count=0,
                        non_null_count=0,
                    ),
                )

            return DataProfile(
                id="empty_dataset",
                columns=tuple(columns_meta),
                row_count=0,
                column_profiles=column_profiles_result,
            )

        expression_list: list[Any] = [F.count(F.lit(1)).alias("__total_rows__")]

        column_domain_types: dict[str, DataType] = {}
        nullable_info: dict[str, bool] = {}

        for column_name in column_names:
            field_type = spark_schema[column_name].dataType
            domain_type = _infer_data_type(field_type)
            column_domain_types[column_name] = domain_type
            nullable_info[column_name] = spark_schema[column_name].nullable

            if domain_type in _NUMERIC_TYPES:
                _build_numeric_agg_expressions(column_name, expression_list)
            elif domain_type == DataType.STRING:
                _build_string_agg_expressions(column_name, expression_list)
            elif domain_type == DataType.BOOLEAN:
                _build_boolean_agg_expressions(column_name, expression_list)
            elif domain_type in _TEMPORAL_TYPES:
                _build_temporal_agg_expressions(column_name, expression_list)

        aggregation_row: Any = working_df.agg(*expression_list).collect()[0]

        columns_processed: list[ColumnMetadata] = []
        column_profiles_processed: dict[str, ColumnProfile] = {}

        for column_name in column_names:
            domain_type = column_domain_types[column_name]
            nullable = nullable_info[column_name]
            inferred = inferred_types.get(column_name)

            null_count: int = 0
            non_null_count: int = 0

            stats: Statistic | None = None
            distribution: Distribution | None = None
            outlier: OutlierInfo | None = None

            if domain_type in _NUMERIC_TYPES:
                non_null_count = int(
                    aggregation_row[f"{column_name}__count"] or 0,
                )
                null_count = total_rows - non_null_count

                quartiles: list[float] = working_df.approxQuantile(
                    column_name,
                    probabilities=[0.25, 0.50, 0.75],
                    relativeError=0.01,
                )

                stats_numeric: NumericStats = _extract_numeric_stats(
                    aggregation_row,
                    column_name,
                    total_rows,
                )
                stats = NumericStats(
                    mean=stats_numeric.mean,
                    std=stats_numeric.std,
                    min=stats_numeric.min,
                    q25=float(quartiles[0]) if len(quartiles) > 0 else stats_numeric.q25,
                    q50=float(quartiles[1]) if len(quartiles) > 1 else stats_numeric.q50,
                    q75=float(quartiles[2]) if len(quartiles) > _QUARTILE_Q75_IDX else stats_numeric.q75,
                    max=stats_numeric.max,
                    skewness=stats_numeric.skewness,
                    kurtosis=stats_numeric.kurtosis,
                )

                # Bug 5 fix: support multiple outlier methods
                outlier = _compute_outliers(working_df, column_name, config)
                distribution = _compute_distribution(
                    working_df,
                    column_name,
                    domain_type,
                    stats,
                    total_rows,
                )

            elif domain_type == DataType.STRING:
                value_counts: dict[str, int] = _build_value_counts(
                    working_df,
                    column_name,
                )
                null_count = int(
                    aggregation_row[f"{column_name}__null_count"] or 0,
                )
                non_null_count = int(
                    aggregation_row[f"{column_name}__count"] or 0,
                )

                # Bug 2 fix: compute both categorical and text stats
                categorical_stats: CategoricalStats
                text_stats: TextStats
                categorical_stats, text_stats = _compute_both_string_stats(
                    aggregation_row,
                    column_name,
                    value_counts,
                    total_rows,
                )

                # Store TextStats when column has long strings
                stats = text_stats if text_stats.avg_length > _TEXT_LENGTH_THRESHOLD else categorical_stats

                distribution = _compute_distribution(
                    working_df,
                    column_name,
                    domain_type,
                    stats if isinstance(stats, CategoricalStats) else categorical_stats,
                    total_rows,
                )

            elif domain_type == DataType.BOOLEAN:
                null_count = int(
                    aggregation_row[f"{column_name}__null_count"] or 0,
                )
                non_null_count = int(
                    aggregation_row[f"{column_name}__count"] or 0,
                )
                stats = _extract_boolean_stats(aggregation_row, column_name)

            elif domain_type in _TEMPORAL_TYPES:
                null_count = int(
                    aggregation_row[f"{column_name}__null_count"] or 0,
                )
                non_null_count = int(
                    aggregation_row[f"{column_name}__count"] or 0,
                )
                stats = _extract_temporal_stats(aggregation_row, column_name)

                # Bug 1 fix: compute temporal distribution
                distribution = _compute_distribution(
                    working_df,
                    column_name,
                    domain_type,
                    stats,
                    total_rows,
                )

            else:
                raw_count: int = working_df.select(column_name).count()
                raw_nulls: int = working_df.filter(
                    F.isnull(F.col(column_name)),
                ).count()
                null_count = raw_nulls
                non_null_count = raw_count - raw_nulls

            column_metadata: ColumnMetadata = ColumnMetadata(
                name=column_name,
                data_type=domain_type,
                nullable=nullable,
                inferred_type=inferred,
                null_count=null_count,
                non_null_count=non_null_count,
            )

            column_profile: ColumnProfile = ColumnProfile(
                metadata=column_metadata,
                stats=stats,
                distribution=distribution,
                outlier=outlier,
            )

            columns_processed.append(column_metadata)
            column_profiles_processed[column_name] = column_profile

        profile_id: str = self._compute_profile_id(dataframe)

        return DataProfile(
            id=profile_id,
            columns=tuple(columns_processed),
            row_count=profile_row_count,
            column_profiles=column_profiles_processed,
        )

    def compute_fingerprint(self, dataframe: DataFrame, config: Any) -> str:
        """Computa uma fingerprint única para o DataFrame.

        Combina o JSON do schema com um hash da configuração para
        produzir uma chave de cache determinística.

        Args:
            dataframe: DataFrame PySpark.
            config: Configuração que pode influenciar a fingerprint.

        Returns:
            String hash SHA-256 representando a fingerprint.
        """
        schema_json: str = dataframe.schema.json()
        config_json: str = json.dumps(
            getattr(config, "__dict__", str(config)),
            sort_keys=True,
            default=str,
        )

        raw_fingerprint: str = f"{schema_json}:{config_json}"
        return hashlib.sha256(raw_fingerprint.encode("utf-8")).hexdigest()

    def compute_correlations(
        self,
        dataframe: DataFrame,
        numeric_columns: list[str],
        method: str = "pearson",
    ) -> list[Correlation]:
        """Computa correlações pareadas para colunas numéricas.

        Args:
            dataframe: DataFrame PySpark.
            numeric_columns: Lista de nomes de colunas numéricas.
            method: Método de correlação. Atualmente apenas "pearson" é suportado.

        Returns:
            Lista de :class:`Correlation` para cada par de colunas.
        """
        if method != "pearson":
            raise ValueError(f"Unsupported correlation method: {method}")

        correlations: list[Correlation] = []
        n: int = len(numeric_columns)

        for i in range(n):
            for j in range(i + 1, n):
                col_a: str = numeric_columns[i]
                col_b: str = numeric_columns[j]

                try:
                    corr_value: float = dataframe.stat.corr(col_a, col_b)
                except Exception:
                    corr_value = 0.0

                correlations.append(
                    Correlation(
                        column_a=col_a,
                        column_b=col_b,
                        method=CorrelationMethod.PEARSON,
                        value=round(corr_value, 4),
                    ),
                )

        return correlations

    def _compute_profile_id(self, dataframe: DataFrame) -> str:
        """Gera um identificador único de perfil baseado no schema.

        Args:
            dataframe: DataFrame PySpark.

        Returns:
            Hash SHA-256 do schema como identificador do perfil.
        """
        return hashlib.sha256(
            dataframe.schema.json().encode("utf-8"),
        ).hexdigest()[:12]

    def _classify_columns(
        self,
        sample_dataframe: DataFrame,
        column_names: list[str],
    ) -> dict[str, InferredType]:
        """Infere tipos semânticos para colunas a partir de uma amostra.

        Para cada coluna, extrai uma lista de valores da amostra
        e delega para o :class:`ColumnClassifier` do domínio.

        Args:
            sample_dataframe: DataFrame com uma amostra limitada de linhas.
            column_names: Lista de nomes de colunas a classificar.

        Returns:
            Dicionário mapeando nome da coluna para :class:`InferredType`.
        """
        inferred_types: dict[str, InferredType] = {}

        for column_name in column_names:
            sample_values: list[str | None] = [
                str(row[column_name]) if row[column_name] is not None else None
                for row in sample_dataframe.select(column_name).collect()
            ]

            inferred_type: InferredType = self._column_classifier.classify(
                column_name=column_name,
                sample_values=sample_values,
            )

            if inferred_type != InferredType.NONE:
                inferred_types[column_name] = inferred_type

        return inferred_types

    def _should_infer_column(
        self,
        column_name: str,
        spark_schema: StructType,
    ) -> bool:
        """Verifica se uma coluna deve passar por inferência semântica.

        Apenas colunas do tipo string ou desconhecido são candidatas.

        Args:
            column_name: Nome da coluna.
            spark_schema: Schema do DataFrame.

        Returns:
            True se a coluna deve ser classificada semanticamente.
        """
        field_type: Any = spark_schema[column_name].dataType
        domain_type: DataType = _infer_data_type(field_type)
        return domain_type in (DataType.STRING, DataType.OTHER)
