"""Gerenciamento de SparkSession com configuração otimizada."""

from __future__ import annotations

from pyspark.sql import SparkSession


def get_or_create_spark_session(
    app_name: str = "spark_eda",
    shuffle_partitions: int | None = None,
    adapter_partition_size: str = "64MB",
) -> SparkSession:
    """Obtém ou cria uma SparkSession com configuração otimizada.

    Reutiliza uma SparkSession existente ou cria uma nova com
    otimizações padrão:

    * **AQE** (Adaptive Query Execution) ativado.
    * Coalescência de partições e skew join ativados.
    * Tamanho de shuffle partition autoajustável.

    Args:
        app_name: Nome da aplicação Spark (padrão: ``"spark_eda"``).
        shuffle_partitions: Número de shuffle partitions.
            Se ``None``, o Spark autoajusta via AQE.
        adapter_partition_size: Tamanho alvo da partição após
            coalesce (padrão: ``"64MB"``).

    Returns:
        SparkSession configurada e pronta para uso.
    """
    builder: SparkSession.Builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.adaptive.skewJoin.enabled", "true")
        .config(
            "spark.sql.adaptive.advisoryPartitionSizeInBytes",
            adapter_partition_size,
        )
    )

    if shuffle_partitions is not None:
        builder = builder.config("spark.sql.shuffle.partitions", shuffle_partitions)

    return builder.getOrCreate()
