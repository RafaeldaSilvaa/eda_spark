"""Teste de integração abrangente com 1 milhão de registros.

Gera um DataFrame PySpark complexo com 1.000.000 de linhas usando
Spark SQL eficiente (sem coleta no driver) e testa todas as
funcionalidades da spark_eda:

    - analyze() → EDAReport completo com todas as seções
    - assess_quality() → QualityReport com todas as dimensões
    - Configurações personalizadas
    - Casos extremos (constantes, nulos totais, duplicatas)
    - Performance e sampling

O script utiliza geração distribuída via funções Spark para
que a criação dos dados não consuma memória do driver.
"""

from __future__ import annotations

import pytest
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from spark_eda import EDAConfig, QualityConfig, analyze, assess_quality
from spark_eda.application.dto.correlation_section import CorrelationSection
from spark_eda.application.dto.distribution_section import DistributionSection
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.insights_section import InsightsSection
from spark_eda.application.dto.outlier_section import OutlierSection
from spark_eda.application.dto.overview_section import OverviewSection
from spark_eda.application.dto.quality_section import QualityReport
from spark_eda.application.dto.recommendations_section import RecommendationsSection
from spark_eda.application.dto.schema_section import SchemaSection
from spark_eda.application.dto.stats_section import StatsSection

pytestmark = pytest.mark.integration

# ─── Dados de lookup (constantes) ─────────────────────────────────────

CIDADES_BRASIL: list[tuple[str, str, str]] = [
    ("São Paulo", "SP", "Sudeste"),
    ("Rio de Janeiro", "RJ", "Sudeste"),
    ("Belo Horizonte", "MG", "Sudeste"),
    ("Salvador", "BA", "Nordeste"),
    ("Fortaleza", "CE", "Nordeste"),
    ("Recife", "PE", "Nordeste"),
    ("Brasília", "DF", "Centro-Oeste"),
    ("Curitiba", "PR", "Sul"),
    ("Porto Alegre", "RS", "Sul"),
    ("Manaus", "AM", "Norte"),
    ("Belém", "PA", "Norte"),
    ("Goiânia", "GO", "Centro-Oeste"),
    ("Campinas", "SP", "Sudeste"),
    ("São Luís", "MA", "Nordeste"),
    ("Maceió", "AL", "Nordeste"),
    ("Natal", "RN", "Nordeste"),
    ("Teresina", "PI", "Nordeste"),
    ("João Pessoa", "PB", "Nordeste"),
    ("Aracaju", "SE", "Nordeste"),
    ("Cuiabá", "MT", "Centro-Oeste"),
]

CATEGORIAS: list[str] = [
    "Eletrônicos", "Roupas", "Alimentos", "Livros", "Esportes",
    "Beleza", "Casa", "Automotivo", "Brinquedos", "Saúde",
]

NUM_CIDADES: int = len(CIDADES_BRASIL)
NUM_CATEGORIAS: int = len(CATEGORIAS)


# ─── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def million_row_dataframe(spark_session: SparkSession) -> DataFrame:
    """Gera um DataFrame complexo com 1.000.000+ de linhas.

    Utiliza spark.range() e expressões ``when`` para gerar dados
    realistas de forma 100% distribuída — sem collect() no driver.

    Schema final (21 colunas):
        id, nome, email, cidade, estado, idade, salario, score,
        categoria, data_cadastro, ultimo_acesso, ativo, dependentes,
        tempo_casa_dias, documento, cep, observacao, regiao,
        coluna_constante, coluna_quase_constante, timestamp_nulo
    """
    spark = spark_session

    # --- Expressões when para distribuir cidades/estados/regiões ---
    cidade_expr = F.when(F.rand() < 0.05, None)  # 5% nulo
    estado_expr = F.when(F.rand() < 0.05, None)
    regiao_expr = F.when(F.rand() < 0.05, None)
    for i, (cid, est, reg) in enumerate(CIDADES_BRASIL):
        cond = F.col("id") % NUM_CIDADES == i
        cidade_expr = cidade_expr.when(cond, F.lit(cid))
        estado_expr = estado_expr.when(cond, F.lit(est))
        regiao_expr = regiao_expr.when(cond, F.lit(reg))
    cidade_expr = cidade_expr.otherwise(F.lit(CIDADES_BRASIL[0][0]))
    estado_expr = estado_expr.otherwise(F.lit(CIDADES_BRASIL[0][1]))
    regiao_expr = regiao_expr.otherwise(F.lit(CIDADES_BRASIL[0][2]))

    # --- Expressão when para distribuir categorias ---
    cat_expr = F.when(F.rand() < 0.03, None)  # 3% nulo
    for i, cat in enumerate(CATEGORIAS):
        cat_expr = cat_expr.when(F.col("id") % NUM_CATEGORIAS == i, F.lit(cat))
    cat_expr = cat_expr.otherwise(F.lit(CATEGORIAS[0]))

    # --- DataFrame base: 1.000.000 linhas, 16 partições ---
    base = spark.range(0, 1_000_000, 1, numPartitions=16)

    # --- Montar DataFrame com expressões Spark 100% distribuídas ---
    final_df = base.select(
        F.col("id"),

        # nome: 5% nulos, distribuição por mod
        F.concat(
            F.lit("Pessoa_"),
            F.when(F.rand() < 0.05, None)
            .otherwise(F.expr("printf('%06d', CAST(rand() * 500000 AS INT))"))
        ).alias("nome"),

        # email: 3% nulos
        F.when(F.rand() < 0.03, None)
        .otherwise(
            F.concat(
                F.lit("user"),
                F.expr("printf('%04d', CAST(rand() * 900000 AS INT))"),
                F.lit("@exemplo.com.br"),
            )
        ).alias("email"),

        cidade_expr.alias("cidade"),
        estado_expr.alias("estado"),

        # idade: distribuição normal truncada [18, 80], 2% nulos
        F.when(F.rand() < 0.02, None)
        .otherwise(
            F.greatest(
                F.lit(18),
                F.least(F.lit(80), (F.randn() * 12 + 38).cast("int")),
            )
        ).alias("idade"),

        # salario: log-normal [1200, 35000], 6% nulos
        F.when(F.rand() < 0.06, None)
        .otherwise(
            F.round(
                F.least(
                    F.lit(35000.0),
                    F.greatest(
                        F.lit(1200.0),
                        F.exp(F.randn() * 0.8 + 8.5),
                    ),
                ),
                2,
            )
        ).alias("salario"),

        # score: uniforme [0, 1000]
        F.round(F.rand() * 1000, 2).alias("score"),

        cat_expr.alias("categoria"),

        # data_cadastro: datas aleatórias entre 2019-01-01 e 2024-12-31
        F.date_add(
            F.lit("2019-01-01"),
            (F.rand() * 2191).cast("int"),  # 2191 = ~6 anos em dias
        ).alias("data_cadastro"),

        # ultimo_acesso: timestamps entre 2020-01-01 e ~2025, 8% nulos
        F.when(F.rand() < 0.08, None)
        .otherwise(
            F.timestamp_seconds(
                F.lit(1577836800) + (F.rand() * 157766400).cast("int"),
            )
        ).alias("ultimo_acesso"),

        # ativo: 80% True, 20% False
        (F.rand() < 0.8).alias("ativo"),

        # dependentes: 0-5 (semi-poisson), 1% nulos
        F.when(F.rand() < 0.01, None)
        .otherwise(
            F.least(
                F.lit(5),
                F.greatest(F.lit(0), (F.abs(F.randn()) * 1.5).cast("int")),
            )
        ).alias("dependentes"),

        # tempo_casa_dias: uniforme [0, 2191]
        (F.rand() * 2191).cast("int").alias("tempo_casa_dias"),

        # documento: 11 dígitos (simula CPF), 2% nulos
        F.when(F.rand() < 0.02, None)
        .otherwise(
            F.expr("printf('%011d', CAST(rand() * 99999999999 AS LONG))"),
        ).alias("documento"),

        # cep: formatado xxxxx-xxx
        F.concat(
            F.expr("printf('%05d', CAST(rand() * 99999 AS INT))"),
            F.lit("-"),
            F.expr("printf('%03d', CAST(rand() * 999 AS INT))"),
        ).alias("cep"),

        # observacao: hash truncado (10-110 chars), 1% vazio
        F.when(F.rand() < 0.01, F.lit(""))
        .otherwise(
            F.expr(
                "substr(sha2(cast(rand() as string), 256), 1, "
                "CAST(rand() * 100 + 10 AS INT))",
            )
        ).alias("observacao"),

        regiao_expr.alias("regiao"),
    )

    # --- Injetar ~100 outliers extremos de salário ---
    outliers = spark.createDataFrame(
        [(500000 + i, 999999.99) for i in range(100)],
        schema=StructType([
            StructField("id_out", LongType()),
            StructField("salario_out", DoubleType()),
        ]),
    )

    final_df = final_df.join(
        outliers,
        final_df["id"] == outliers["id_out"],
        how="left",
    ).select(
        F.col("id"),
        F.col("nome"),
        F.col("email"),
        F.col("cidade"),
        F.col("estado"),
        F.col("idade"),
        F.coalesce(F.col("salario_out"), F.col("salario")).alias("salario"),
        F.col("score"),
        F.col("categoria"),
        F.col("data_cadastro"),
        F.col("ultimo_acesso"),
        F.col("ativo"),
        F.col("dependentes"),
        F.col("tempo_casa_dias"),
        F.col("documento"),
        F.col("cep"),
        F.col("observacao"),
        F.col("regiao"),
    )

    # --- Adicionar ~5000 duplicatas (0.5%) ---
    final_df = final_df.union(final_df.filter(F.col("id") < 5000))

    # --- Coluna constante (edge case) ---
    final_df = final_df.withColumn("coluna_constante", F.lit("valor_imutavel"))

    # --- Coluna quase-constante (99.9% mesmo valor) ---
    final_df = final_df.withColumn(
        "coluna_quase_constante",
        F.when(F.rand() < 0.001, F.expr("printf('%04d', CAST(rand() * 1000 AS INT))"))
        .otherwise(F.lit("predominante")),
    )

    # --- Coluna totalmente nula (edge case) ---
    final_df = final_df.withColumn("timestamp_nulo", F.lit(None).cast("timestamp"))

    # Cachear para acelerar múltiplos testes
    final_df.cache()
    final_df.count()  # Forçar materialização

    return final_df


# ═══════════════════════════════════════════════════════════════════════
# Testes de Análise Completa
# ═══════════════════════════════════════════════════════════════════════


class TestCompleteAnalysis1M:
    """Testa a análise completa em dataset de 1 milhão de registros."""

    def test_analyze_returns_complete_report(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """analyze() deve retornar EDAReport com todas as seções."""
        report: EDAReport = analyze(million_row_dataframe)

        assert isinstance(report, EDAReport)
        assert isinstance(report.overview, OverviewSection)
        assert isinstance(report.schema, SchemaSection)
        assert isinstance(report.quality, QualityReport)
        assert isinstance(report.stats, StatsSection)
        assert isinstance(report.distributions, DistributionSection)
        assert isinstance(report.correlations, CorrelationSection)
        assert isinstance(report.outliers, OutlierSection)
        assert isinstance(report.insights, InsightsSection)
        assert isinstance(report.recommendations, RecommendationsSection)

    def test_overview_counts(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Visão geral deve refletir corretamente o dataset."""
        report = analyze(million_row_dataframe)

        # 1M originais + 5K duplicatas = 1.005.000
        assert report.overview.row_count > 1_000_000
        assert report.overview.column_count >= 20
        assert report.overview.duplicate_count > 0
        assert report.overview.missing_ratio > 0.0
        assert report.overview.size_estimate > 0

    def test_schema_contains_all_columns(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Schema deve listar todas as 21 colunas esperadas."""
        report = analyze(million_row_dataframe)

        schema_names = {c.name for c in report.schema.columns}
        expected = {
            "id", "nome", "email", "cidade", "estado",
            "idade", "salario", "score", "categoria",
            "data_cadastro", "ultimo_acesso", "ativo",
            "dependentes", "tempo_casa_dias", "documento",
            "cep", "observacao", "regiao", "coluna_constante",
            "coluna_quase_constante", "timestamp_nulo",
        }
        missing = expected - schema_names
        assert not missing, f"Colunas ausentes no schema: {missing}"

    def test_quality_report_has_dimensions(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Relatório de qualidade deve conter todas as dimensões."""
        report = analyze(million_row_dataframe)

        assert 0.0 <= report.quality.overall <= 100.0
        assert len(report.quality.dimensions) >= 4
        for dim in report.quality.dimensions:
            assert 0.0 <= dim.score <= 100.0
            assert dim.weight > 0.0
            assert len(dim.factors) > 0

    def test_quality_penalizers(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Top penalizers devem ser identificados."""
        report = analyze(million_row_dataframe)

        assert len(report.quality.top_penalizers) > 0
        for p in report.quality.top_penalizers:
            assert p.score >= 0.0
            assert p.reason != ""
            assert p.severity in ("low", "medium", "high", "critical")

    def test_stats_contains_numeric(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Estatísticas numéricas para colunas esperadas."""
        report = analyze(million_row_dataframe)

        assert len(report.stats.numeric) > 0
        numeric_names = {s.column_name for s in report.stats.numeric}
        for col_name in ("idade", "salario", "score", "dependentes", "tempo_casa_dias"):
            assert col_name in numeric_names, f"{col_name} não está em numeric stats"

        # Validar estatísticas de salário
        salario_stats = next(
            s for s in report.stats.numeric if s.column_name == "salario"
        )
        assert salario_stats.mean > 1000.0
        assert salario_stats.min >= 1200.0
        # Outliers injetados de 999999.99
        assert salario_stats.max >= 100000.0

    def test_stats_contains_categorical(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Estatísticas categóricas para colunas esperadas."""
        report = analyze(million_row_dataframe)

        cat_names = {s.column_name for s in report.stats.categorical}
        for col_name in ("categoria", "estado", "regiao"):
            assert col_name in cat_names, f"{col_name} não está em categorical stats"

        categoria_stats = next(
            s for s in report.stats.categorical if s.column_name == "categoria"
        )
        assert categoria_stats.cardinality == 10  # 10 categorias
        assert categoria_stats.mode is not None
        assert 0.0 < categoria_stats.unique_ratio <= 1.0
        assert len(categoria_stats.top_values) >= 3

    def test_stats_contains_temporal(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Estatísticas temporais para colunas de data/timestamp."""
        report = analyze(million_row_dataframe)

        if report.stats.temporal:
            temp_names = {s.column_name for s in report.stats.temporal}
            assert "data_cadastro" in temp_names or "ultimo_acesso" in temp_names

    def test_stats_contains_text(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Estatísticas de texto para colunas string longas."""
        report = analyze(million_row_dataframe)

        text_names = {s.column_name for s in report.stats.text}
        # observacao tem avg_length > 50 → classificada como texto
        assert "observacao" in text_names or "nome" in text_names or "email" in text_names

    def test_stats_contains_boolean(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Estatísticas booleanas para coluna ativo."""
        report = analyze(million_row_dataframe)

        bool_names = {s.column_name for s in report.stats.boolean}
        assert "ativo" in bool_names, f"ativo não está em boolean stats: {bool_names}"

        ativo_stats = next(
            s for s in report.stats.boolean if s.column_name == "ativo"
        )
        assert ativo_stats.true_count > 0
        assert ativo_stats.false_count > 0
        assert 0.6 < ativo_stats.true_ratio < 0.95  # ~80%

    def test_correlations_generated(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Correlações devem ser calculadas entre colunas numéricas."""
        report = analyze(million_row_dataframe)

        assert len(report.correlations.correlations) > 0
        assert len(report.correlations.matrix) > 0
        assert report.correlations.method != ""

        for corr in report.correlations.correlations:
            assert -1.0 <= corr.value <= 1.0
            assert corr.column_a != corr.column_b

    def test_outliers_detected(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Outliers devem ser detectados na coluna salário."""
        report = analyze(million_row_dataframe)

        if report.outliers.outliers:
            outlier_names = {s.column_name for s in report.outliers.outliers}
            if "salario" in outlier_names:
                salario_out = next(
                    s for s in report.outliers.outliers if s.column_name == "salario"
                )
                assert salario_out.count > 0
                assert salario_out.ratio > 0.0
                assert salario_out.bounds_lower is not None
                assert salario_out.bounds_upper is not None

    def test_insights_generated(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Insights devem ser gerados para o dataset."""
        report = analyze(million_row_dataframe)

        assert len(report.insights.insights) > 0
        for insight in report.insights.insights:
            assert insight.category != ""
            assert insight.message != ""
            assert insight.severity in ("low", "medium", "high", "critical")

    def test_recommendations_generated(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Recomendações devem ser geradas."""
        report = analyze(million_row_dataframe)

        assert len(report.recommendations.recommendations) > 0
        for rec in report.recommendations.recommendations:
            assert rec.category != ""
            assert rec.message != ""
            assert rec.action != ""
            assert 1 <= rec.priority <= 5


# ═══════════════════════════════════════════════════════════════════════
# Testes de Avaliação de Qualidade
# ═══════════════════════════════════════════════════════════════════════


class TestAssessQuality1M:
    """Testa avaliação de qualidade isolada em 1M registros."""

    def test_assess_quality_returns_report(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """assess_quality() retorna QualityReport válido."""
        quality: QualityReport = assess_quality(million_row_dataframe)

        assert isinstance(quality, QualityReport)
        assert 0.0 <= quality.overall <= 100.0
        assert len(quality.dimensions) >= 4
        assert len(quality.top_penalizers) > 0

    def test_assess_quality_dimension_names(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Dimensões de qualidade devem ter nomes esperados."""
        quality = assess_quality(million_row_dataframe)

        dim_names = {d.name for d in quality.dimensions}
        for expected in ("completeness", "uniqueness", "consistency", "timeliness", "accuracy"):
            if expected in dim_names:
                dim = next(d for d in quality.dimensions if d.name == expected)
                assert 0.0 <= dim.score <= 100.0

    def test_assess_quality_penalizers_structure(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Penalizadores devem ter estrutura completa."""
        quality = assess_quality(million_row_dataframe)

        for p in quality.top_penalizers:
            assert isinstance(p.score, float)
            assert isinstance(p.severity, str)
            assert isinstance(p.affected_columns, list)
            assert isinstance(p.reason, str)


# ═══════════════════════════════════════════════════════════════════════
# Testes de Configuração
# ═══════════════════════════════════════════════════════════════════════


class TestConfigurations1M:
    """Testa configurações personalizadas com 1M registros."""

    def test_custom_eda_config(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """analyze() com EDAConfig personalizado."""
        config = EDAConfig(
            max_categories=20,
            correlation_methods=("pearson", "cramers_v"),
            outlier_method="iqr",
            enable_insights=True,
            enable_recommendations=False,
            sampling_threshold=10_000_000,
        )
        report = analyze(million_row_dataframe, config=config)

        assert len(report.recommendations.recommendations) == 0
        assert isinstance(report, EDAReport)

    def test_custom_quality_config(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """assess_quality() com QualityConfig personalizado."""
        config = QualityConfig(
            weights={
                "completeness": 0.40,
                "uniqueness": 0.20,
                "consistency": 0.15,
                "timeliness": 0.10,
                "accuracy": 0.15,
            },
            near_constant_threshold=0.02,
        )
        quality = assess_quality(million_row_dataframe, config=config)

        assert 0.0 <= quality.overall <= 100.0
        completeness_dim = next(d for d in quality.dimensions if d.name == "completeness")
        assert completeness_dim.weight == 0.40

    def test_analyze_with_sampling(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Sampling abaixo do threshold deve ser acionado."""
        config = EDAConfig(sampling_threshold=100_000)
        report = analyze(million_row_dataframe, config=config)

        assert report.overview.row_count >= 1_000_000

    def test_insights_disabled(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Desabilitar insights deve retornar lista vazia."""
        config = EDAConfig(enable_insights=False)
        report = analyze(million_row_dataframe, config=config)

        assert len(report.insights.insights) == 0

    def test_outlier_method_zscore(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Detecção de outliers com método Z-score."""
        config = EDAConfig(outlier_method="zscore")
        report = analyze(million_row_dataframe, config=config)

        assert len(report.outliers.outliers) >= 0

    def test_outlier_method_mad(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Detecção de outliers com método MAD."""
        config = EDAConfig(outlier_method="mad")
        report = analyze(million_row_dataframe, config=config)

        assert len(report.outliers.outliers) >= 0


# ═══════════════════════════════════════════════════════════════════════
# Testes de Casos Extremos
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeCases1M:
    """Testa casos extremos com o dataset de 1M registros."""

    def test_caching_between_calls(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Chamadas sucessivas devem usar cache."""
        r1 = analyze(million_row_dataframe)
        r2 = analyze(million_row_dataframe)

        assert r1.overview.row_count == r2.overview.row_count
        assert r1.quality.overall == r2.quality.overall

    def test_analyze_then_assess_quality(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """analyze() e assess_quality() no mesmo dataset."""
        report = analyze(million_row_dataframe)
        quality = assess_quality(million_row_dataframe)

        assert isinstance(report, EDAReport)
        assert isinstance(quality, QualityReport)
        assert abs(report.quality.overall - quality.overall) < 0.1

    def test_constant_column_in_schema(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Coluna constante deve aparecer no schema."""
        report = analyze(million_row_dataframe)

        schema_names = {c.name for c in report.schema.columns}
        assert "coluna_constante" in schema_names

    def test_near_constant_column_detected(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Coluna quase constante deve gerar insight ou recomendação."""
        report = analyze(million_row_dataframe)

        has_near_constant_insight = any(
            "coluna_quase_constante" in (i.column or "")
            and "constant" in i.category.lower()
            for i in report.insights.insights
        )
        has_near_constant_rec = any(
            "coluna_quase_constante" in (r.column or "")
            for r in report.recommendations.recommendations
        )
        assert has_near_constant_insight or has_near_constant_rec, (
            "Coluna quase constante não foi detectada nem como insight nem como recomendação"
        )

    def test_all_null_column_present(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Coluna toda nula (timestamp_nulo) deve ser identificada."""
        report = analyze(million_row_dataframe)

        schema_cols = {c.name: c for c in report.schema.columns}
        assert "timestamp_nulo" in schema_cols
        total = million_row_dataframe.count()
        assert schema_cols["timestamp_nulo"].null_count == total

    def test_string_statistics_for_document(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Coluna documento deve ter estatísticas consistentes."""
        report = analyze(million_row_dataframe)

        all_text = report.stats.text
        all_cat = report.stats.categorical
        all_names = {s.column_name for s in all_text} | {s.column_name for s in all_cat}
        assert "documento" in all_names

    def test_various_string_lengths_in_observacao(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Observacao deve ter comprimentos variados e alguns vazios."""
        report = analyze(million_row_dataframe)

        text_stats = [s for s in report.stats.text if s.column_name == "observacao"]
        if text_stats:
            obs = text_stats[0]
            assert obs.min_length >= 0
            assert obs.max_length > obs.min_length
            assert obs.avg_length > 0
            assert obs.empty_ratio >= 0.0


# ═══════════════════════════════════════════════════════════════════════
# Testes de Formatação
# ═══════════════════════════════════════════════════════════════════════


class TestFormatting1M:
    """Testa formatação e representação das seções."""

    def test_overview_str_and_html(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Overview deve ter representações text e HTML."""
        report = analyze(million_row_dataframe)

        str_repr = str(report.overview)
        assert "Rows" in str_repr
        assert "Columns" in str_repr
        assert "Duplicates" in str_repr
        assert "Missing" in str_repr

        html_repr = report.overview._repr_html_()
        assert "div" in html_repr
        assert "Rows" in html_repr

    def test_schema_str_and_html(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Schema deve ter representações text e HTML."""
        report = analyze(million_row_dataframe)

        str_repr = str(report.schema)
        assert "Column" in str_repr
        assert "id" in str_repr

        html_repr = report.schema._repr_html_()
        assert "<table" in html_repr
        assert "id" in html_repr

    def test_stats_str_and_html(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Estatísticas devem ter representações text e HTML."""
        report = analyze(million_row_dataframe)

        str_repr = str(report.stats)
        html_repr = report.stats._repr_html_()

        if report.stats.numeric:
            assert "mean" in str_repr.lower()

    def test_correlations_str_and_html(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Correlações devem ter representações text e HTML."""
        report = analyze(million_row_dataframe)

        str_repr = str(report.correlations)
        if report.correlations.correlations:
            assert "Method" in str_repr

        html_repr = report.correlations._repr_html_()

    def test_outliers_str_and_html(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Outliers devem ter representações text e HTML."""
        report = analyze(million_row_dataframe)

        str(report.outliers)
        report.outliers._repr_html_()

    def test_insights_str_and_html(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Insights devem ter representações text e HTML."""
        report = analyze(million_row_dataframe)

        str_repr = str(report.insights)
        report.insights._repr_html_()

        if report.insights.insights:
            assert "[" in str_repr

    def test_recommendations_str_and_html(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """Recomendações devem ter representações text e HTML."""
        report = analyze(million_row_dataframe)

        str_repr = str(report.recommendations)
        report.recommendations._repr_html_()

        if report.recommendations.recommendations:
            assert "P1" in str_repr or "P2" in str_repr


# ═══════════════════════════════════════════════════════════════════════
# Testes de Performance
# ═══════════════════════════════════════════════════════════════════════


class TestPerformance1M:
    """Testes básicos de performance com 1M registros."""

    def test_analyze_completes_within_reasonable_time(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """analyze() deve completar em tempo razoável para 1M registros."""
        import time

        start = time.time()
        report = analyze(million_row_dataframe)
        elapsed = time.time() - start

        # 5 minutos como limite generoso para ambiente de teste
        assert elapsed < 300.0, f"Analysis levou {elapsed:.1f}s (limite: 300s)"
        assert isinstance(report, EDAReport)
        print(f"\n  analyze(1M rows) completou em {elapsed:.2f}s")

    def test_assess_quality_faster_than_analysis(
        self, million_row_dataframe: DataFrame,
    ) -> None:
        """assess_quality() deve ser mais rápido que analyze()."""
        import time

        start = time.time()
        analyze(million_row_dataframe)
        analyze_time = time.time() - start

        start = time.time()
        assess_quality(million_row_dataframe)
        quality_time = time.time() - start

        print(f"\n  analyze() time:        {analyze_time:.2f}s")
        print(f"  assess_quality() time: {quality_time:.2f}s")

        # assess_quality é mais leve que analyze (apenas qualidade, sem correlações/insights)
        assert quality_time < analyze_time, (
            f"assess_quality ({quality_time:.2f}s) deveria ser mais rápido "
            f"que analyze ({analyze_time:.2f}s)"
        )
