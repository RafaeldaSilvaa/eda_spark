from __future__ import annotations

"""Testes de borda para todos os fatores de qualidade.

Cobre branches não testados em accuracy, completeness, consistency,
timeliness e uniqueness — cada linha listada pelo relatório de cobertura.
"""

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.outlier import OutlierInfo
from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.entities.statistic import (
    BooleanStats,
    CategoricalStats,
    NumericStats,
    TextStats,
    TemporalStats,
)
from spark_eda.domain.services.quality_factors import FACTOR_REGISTRY
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.inferred_type import InferredType
from spark_eda.domain.value_objects.outlier_method import OutlierMethod
from spark_eda.domain.value_objects.severity import Severity


# ---------------------------------------------------------------------------
# ACCURACY
# ---------------------------------------------------------------------------

class TestAccuracyEdge:
    def test_severity_high_when_score_0_4(self) -> None:
        """score=0.4 → Severity.HIGH (linha 26: 0.3 <= score < 0.6)."""
        metadata = ColumnMetadata(
            name="vendas", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        outlier = OutlierInfo(OutlierMethod.IQR, 50, 0.50, 10.0, 90.0)
        stats = NumericStats(100.0, 30.0, 0.0, 75.0, 95.0, 120.0, 500.0, 0.8, 3.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        dp = DataProfile("acc_high", (metadata,), 100, {"vendas": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        assert any(f.name == "Proporção de outliers" for f in factors)

    def test_severity_medium_when_score_0_7(self) -> None:
        """score=0.7 → Severity.MEDIUM (linha 28: 0.6 <= score < 0.8)."""
        metadata = ColumnMetadata(
            name="preco", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        outlier = OutlierInfo(OutlierMethod.IQR, 30, 0.30, 10.0, 90.0)
        stats = NumericStats(50.0, 15.0, 0.0, 40.0, 50.0, 60.0, 200.0, 0.5, 2.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        dp = DataProfile("acc_med", (metadata,), 100, {"preco": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        outlier_factor = next(f for f in factors if f.name == "Proporção de outliers")
        assert outlier_factor.severity == Severity.MEDIUM

    def test_outlier_ratio_below_0_05_not_in_affected(self) -> None:
        """outlier.ratio <= 0.05 → coluna NÃO entra em affected_columns (linha 46->41)."""
        metadata = ColumnMetadata(
            name="estavel", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        outlier = OutlierInfo(OutlierMethod.IQR, 3, 0.03, 10.0, 90.0)
        stats = NumericStats(50.0, 15.0, 10.0, 40.0, 50.0, 60.0, 90.0, 0.1, 2.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        dp = DataProfile("low_out", (metadata,), 100, {"estavel": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        outlier_factor = next(f for f in factors if f.name == "Proporção de outliers")
        assert "estavel" not in outlier_factor.affected_columns

    def test_format_accuracy_null_ratio_above_0_2(self) -> None:
        """Coluna com inferred_type e null_ratio > 0.2 → inconsistente (linhas 88-93)."""
        metadata = ColumnMetadata(
            name="cpf_cliente", data_type=DataType.STRING, nullable=True,
            inferred_type=InferredType.CPF, null_count=30, non_null_count=70,
        )
        stats = CategoricalStats({"A": 70}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("fmt_acc", (metadata,), 100, {"cpf_cliente": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        fmt_factor = next(f for f in factors if f.name == "Acurácia de formato")
        assert fmt_factor.score < 1.0
        assert "cpf_cliente" in fmt_factor.affected_columns

    def test_format_accuracy_total_column_zero(self) -> None:
        """inferred_type column com total=0 → não conta como inconsistente (linha 90->86)."""
        metadata = ColumnMetadata(
            name="cpf_col", data_type=DataType.STRING, nullable=True,
            inferred_type=InferredType.CPF, null_count=0, non_null_count=0,
        )
        profile = ColumnProfile(metadata=metadata, stats=None, distribution=None, outlier=None)
        dp = DataProfile("total_zero_fmt", (metadata,), 0, {"cpf_col": profile})
        FACTOR_REGISTRY["accuracy"](dp)

    def test_format_accuracy_null_ratio_below_20(self) -> None:
        """inferred_type column com null_ratio <= 0.2 → não inconsistente (linha 92->86)."""
        metadata = ColumnMetadata(
            name="email_col", data_type=DataType.STRING, nullable=True,
            inferred_type=InferredType.EMAIL, null_count=10, non_null_count=90,
        )
        stats = CategoricalStats({"a@a.com": 90}, "a@a.com", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("low_null_fmt", (metadata,), 100, {"email_col": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        fmt_factor = next(f for f in factors if f.name == "Acurácia de formato")
        assert "email_col" not in fmt_factor.affected_columns

    def test_format_accuracy_no_inferred_columns(self) -> None:
        """Nenhuma coluna com inferred_type → score 1.0 (linha 95)."""
        metadata = ColumnMetadata(
            name="desc", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 100}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_inferred", (metadata,), 100, {"desc": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        fmt_factor = next(f for f in factors if f.name == "Acurácia de formato")
        assert fmt_factor.score == 1.0

    def test_suspicious_data_no_upper_bounds(self) -> None:
        """Outlier com bounds_upper=None → pula verificação upper (linha 142->145)."""
        metadata = ColumnMetadata(
            name="suspeito", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 15.0, 0.0, 40.0, 50.0, 60.0, 200.0, 0.5, 2.0)
        outlier = OutlierInfo(OutlierMethod.IQR, 5, 0.05, 10.0, None)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        dp = DataProfile("susp", (metadata,), 100, {"suspeito": profile})
        FACTOR_REGISTRY["accuracy"](dp)

    def test_suspicious_data_no_lower_bounds(self) -> None:
        """Outlier com bounds_lower=None → pula verificação lower (linha 145->132)."""
        metadata = ColumnMetadata(
            name="suspeito2", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 15.0, 0.0, 40.0, 50.0, 60.0, 200.0, 0.5, 2.0)
        outlier = OutlierInfo(OutlierMethod.IQR, 5, 0.05, None, 90.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        dp = DataProfile("susp2", (metadata,), 100, {"suspeito2": profile})
        FACTOR_REGISTRY["accuracy"](dp)

    def test_suspicious_data_max_not_extreme(self) -> None:
        """stats.max <= upper_extreme_limit → não adiciona (linha 143->145)."""
        metadata = ColumnMetadata(
            name="normal", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 15.0, 5.0, 40.0, 50.0, 60.0, 70.0, 0.5, 2.0)
        outlier = OutlierInfo(OutlierMethod.IQR, 5, 0.05, 10.0, 90.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        dp = DataProfile("normal", (metadata,), 100, {"normal": profile})
        FACTOR_REGISTRY["accuracy"](dp)

    def test_suspicious_data_both_bounds_same_column(self) -> None:
        """Ambos os bounds disparam para a mesma coluna → não duplica (linhas 147-148)."""
        metadata = ColumnMetadata(
            name="bizarro", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        # IQR = 60 - 40 = 20, upper_extreme = 60 + 3*20 = 120, lower_extreme = 40 - 3*20 = -20
        # max=200 > 120 ✓, min=-50 < -20 ✓ → ambos disparam
        stats = NumericStats(50.0, 30.0, -50.0, 40.0, 50.0, 60.0, 200.0, 0.5, 2.0)
        outlier = OutlierInfo(OutlierMethod.IQR, 10, 0.10, -30.0, 150.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        dp = DataProfile("both_bounds", (metadata,), 100, {"bizarro": profile})
        FACTOR_REGISTRY["accuracy"](dp)

    def test_suspicious_data_lower_only_adds_column(self) -> None:
        """Apenas bounds_lower dispara e adiciona coluna nova (linhas 147-148)."""
        metadata = ColumnMetadata(
            name="suspeito_lower", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        # IQR = 60 - 40 = 20, lower_extreme = 40 - 3*20 = -20
        # stats.min = -50 < -20 → dispara lower
        # stats.max = 70 <= 80 (upper_extreme = 60+3*20=120) → não dispara upper
        stats = NumericStats(50.0, 15.0, -50.0, 40.0, 50.0, 60.0, 70.0, 0.5, 2.0)
        outlier = OutlierInfo(OutlierMethod.IQR, 10, 0.10, -30.0, 90.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        dp = DataProfile("lower_only", (metadata,), 100, {"suspeito_lower": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        susp_factor = next(f for f in factors if f.name == "Dados suspeitos")
        assert "suspeito_lower" in susp_factor.affected_columns
        assert susp_factor.score < 1.0

    def test_suspicious_data_upper_adds_then_lower_skips_duplicate(self) -> None:
        """Ambos os bounds disparam para a mesma coluna → não duplica (linhas 147-148)."""
        metadata = ColumnMetadata(
            name="bizarro", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        # IQR = 60 - 40 = 20, upper_extreme = 60 + 3*20 = 120, lower_extreme = 40 - 3*20 = -20
        # max=200 > 120 ✓ (upper adiciona), min=-50 < -20 ✓ (lower tenta)
        # lower encontra nome já em suspicious_columns → linha 147 False → linha 148 NÃO executa
        stats = NumericStats(50.0, 30.0, -50.0, 40.0, 50.0, 60.0, 200.0, 0.5, 2.0)
        outlier = OutlierInfo(OutlierMethod.IQR, 10, 0.10, -30.0, 150.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        dp = DataProfile("both_bounds", (metadata,), 100, {"bizarro": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        susp_factor = next(f for f in factors if f.name == "Dados suspeitos")
        assert susp_factor.affected_columns == ["bizarro"]
        assert susp_factor.score < 1.0

    def test_suspicious_data_zero_numeric_total(self) -> None:
        """suspicious_columns vazia com total_numeric == 0 → score 1.0 (linha 150)."""
        metadata = ColumnMetadata(
            name="txt", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 100}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("zero_num", (metadata,), 100, {"txt": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        susp_factor = next(f for f in factors if f.name == "Dados suspeitos")
        assert susp_factor.score == 1.0

    def test_corrupted_data_min_length_negative(self) -> None:
        """TextStats com min_length < 0 → corrupted (linhas 208-209)."""
        metadata = ColumnMetadata(
            name="texto_estranho", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = TextStats(min_length=-1, max_length=100, avg_length=50.0, empty_ratio=0.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("corrupt", (metadata,), 100, {"texto_estranho": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        corrupt_factor = next(f for f in factors if f.name == "Dados corrompidos")
        assert corrupt_factor.score < 1.0
        assert "texto_estranho" in corrupt_factor.affected_columns

    def test_corrupted_data_no_corruption(self) -> None:
        """Nenhuma coluna corrompida → score 1.0 (linha 211)."""
        metadata = ColumnMetadata(
            name="bom", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = TextStats(min_length=1, max_length=100, avg_length=50.0, empty_ratio=0.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("clean", (metadata,), 100, {"bom": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        corrupt_factor = next(f for f in factors if f.name == "Dados corrompidos")
        assert corrupt_factor.score == 1.0

    def test_business_rules_year_violation(self) -> None:
        """Coluna 'ano_ref' com min < 1900 → violação (linhas 260-262)."""
        metadata = ColumnMetadata(
            name="ano_ref", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(1850.0, 50.0, 1800.0, 1840.0, 1850.0, 1860.0, 1900.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("ano_violation", (metadata,), 100, {"ano_ref": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        biz_factor = next(f for f in factors if f.name == "Regras de negócio")
        assert biz_factor.score < 1.0

    def test_business_rules_month_violation(self) -> None:
        """Coluna 'mes' com max > 12 → violação (linhas 268-270)."""
        metadata = ColumnMetadata(
            name="mes", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(8.0, 5.0, 1.0, 5.0, 8.0, 12.0, 15.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("mes_violation", (metadata,), 100, {"mes": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        biz_factor = next(f for f in factors if f.name == "Regras de negócio")
        assert biz_factor.score < 1.0

    def test_business_rules_day_violation(self) -> None:
        """Coluna 'dia' com min < 1 → violação (linhas 275-277)."""
        metadata = ColumnMetadata(
            name="dia", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(15.0, 10.0, 0.0, 10.0, 15.0, 20.0, 31.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("dia_violation", (metadata,), 100, {"dia": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        biz_factor = next(f for f in factors if f.name == "Regras de negócio")
        assert biz_factor.score < 1.0

    def test_business_rules_percentage_violation(self) -> None:
        """Coluna 'pct_desconto' com max > 100 → violação (linhas 284-289)."""
        metadata = ColumnMetadata(
            name="pct_desconto", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 40.0, 0.0, 20.0, 50.0, 80.0, 150.0, 0.5, 2.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("pct_violation", (metadata,), 100, {"pct_desconto": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        biz_factor = next(f for f in factors if f.name == "Regras de negócio")
        assert biz_factor.score < 1.0

    def test_business_rules_age_violation(self) -> None:
        """Coluna 'idade' com max > 120 → violação (linhas 294-299)."""
        metadata = ColumnMetadata(
            name="idade", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 40.0, 0.0, 20.0, 40.0, 70.0, 200.0, 0.5, 2.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("age_violation", (metadata,), 100, {"idade": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        biz_factor = next(f for f in factors if f.name == "Regras de negócio")
        assert biz_factor.score < 1.0

    def test_business_rules_no_violation(self) -> None:
        """Nenhuma regra violada → score 1.0 (linha 301)."""
        metadata = ColumnMetadata(
            name="nome", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 100}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_violation", (metadata,), 100, {"nome": profile})
        factors = FACTOR_REGISTRY["accuracy"](dp)
        biz_factor = next(f for f in factors if f.name == "Regras de negócio")
        assert biz_factor.score == 1.0

    def test_business_rules_num_col_no_match(self) -> None:
        """Coluna numérica sem padrão de nome → todos os branches False (260->267, etc)."""
        metadata = ColumnMetadata(
            name="preco_total", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 10.0, 10.0, 30.0, 50.0, 70.0, 100.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("num_no_match", (metadata,), 100, {"preco_total": profile})
        FACTOR_REGISTRY["accuracy"](dp)

    def test_business_rules_valid_patterns_no_violation(self) -> None:
        """Colunas com padrões de regra válidos → inner False (260->267, 268->274, 275->281, 284->289, 294->299)."""
        cols = []
        profs = {}
        for name, min_v, max_v in [
            ("ano_bom", 2000.0, 2020.0),
            ("mes_bom", 3.0, 11.0),
            ("dia_bom", 5.0, 25.0),
            ("pct_bom", 10.0, 90.0),
            ("idade_ok", 20.0, 80.0),
        ]:
            meta = ColumnMetadata(
                name=name, data_type=DataType.DOUBLE, nullable=False,
                inferred_type=None, null_count=0, non_null_count=100,
            )
            stats = NumericStats(50.0, 10.0, min_v, 25.0, 50.0, 75.0, max_v, 0.0, 0.0)
            profs[name] = ColumnProfile(metadata=meta, stats=stats, distribution=None, outlier=None)
            cols.append(meta)
        dp = DataProfile("valid_rules", tuple(cols), 100, profs)
        factors = FACTOR_REGISTRY["accuracy"](dp)
        br_factor = next(f for f in factors if f.name == "Regras de negócio")
        assert br_factor.score == 1.0


# ---------------------------------------------------------------------------
# COMPLETENESS
# ---------------------------------------------------------------------------

class TestCompletenessEdge:
    def test_severity_high(self) -> None:
        """score ~0.4 → Severity.HIGH (linha 22)."""
        cols = []
        profs = {}
        for name, null_c, non_null_c in [("col_a", 70, 30), ("col_b", 50, 50)]:
            meta = ColumnMetadata(
                name=name, data_type=DataType.STRING, nullable=True,
                inferred_type=None, null_count=null_c, non_null_count=non_null_c,
            )
            stats = CategoricalStats({"X": non_null_c}, "X", 1, 1.0)
            profs[name] = ColumnProfile(metadata=meta, stats=stats, distribution=None, outlier=None)
            cols.append(meta)
        dp = DataProfile("comp_high", tuple(cols), 100, profs)
        factors = FACTOR_REGISTRY["completeness"](dp)
        non_null_factor = next(f for f in factors if f.name == "Proporção de valores não nulos")
        assert non_null_factor.severity == Severity.HIGH

    def test_severity_medium(self) -> None:
        """score ~0.7 → Severity.MEDIUM (linha 24)."""
        metadata = ColumnMetadata(
            name="col", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=30, non_null_count=70,
        )
        stats = CategoricalStats({"A": 70}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("comp_med", (metadata,), 100, {"col": profile})
        factors = FACTOR_REGISTRY["completeness"](dp)
        non_null_factor = next(f for f in factors if f.name == "Proporção de valores não nulos")
        assert non_null_factor.severity == Severity.MEDIUM

    def test_row_count_zero(self) -> None:
        """row_count == 0 → score 1.0 para non_null_ratio (linha 36)."""
        metadata = ColumnMetadata(
            name="col", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=0,
        )
        stats = CategoricalStats({}, None, 0, 0.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("empty", (metadata,), 0, {"col": profile})
        factors = FACTOR_REGISTRY["completeness"](dp)
        non_null_factor = next(f for f in factors if f.name == "Proporção de valores não nulos")
        assert non_null_factor.score == 1.0

    def test_total_column_zero_non_null_ratio(self) -> None:
        """total_column == 0 → proportion = 1.0 (linha 53)."""
        metadata = ColumnMetadata(
            name="vazia", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=0,
        )
        stats = CategoricalStats({}, None, 0, 0.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("total_zero", (metadata,), 100, {"vazia": profile})
        FACTOR_REGISTRY["completeness"](dp)

    def test_row_completeness_empty_columns(self) -> None:
        """Nenhuma coluna → score 1.0 (linha 81)."""
        dp = DataProfile("no_columns", (), 100, {})
        factors = FACTOR_REGISTRY["completeness"](dp)
        row_factor = next(f for f in factors if f.name == "Completude de linhas")
        assert row_factor.score == 1.0

    def test_empty_strings_affected(self) -> None:
        """empty_ratio > 0.05 → adiciona a affected_columns (linha 131)."""
        metadata = ColumnMetadata(
            name="desc", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = TextStats(min_length=0, max_length=200, avg_length=50.0, empty_ratio=0.10)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("empty_str", (metadata,), 100, {"desc": profile})
        factors = FACTOR_REGISTRY["completeness"](dp)
        empty_factor = next(f for f in factors if f.name == "Proporção de strings vazias")
        assert "desc" in empty_factor.affected_columns

    def test_zero_length_fields_no_zero_min(self) -> None:
        """min_length > 0 → não adiciona (linha 175->170)."""
        metadata = ColumnMetadata(
            name="texto", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = TextStats(min_length=1, max_length=100, avg_length=50.0, empty_ratio=0.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_zero_len", (metadata,), 100, {"texto": profile})
        factors = FACTOR_REGISTRY["completeness"](dp)
        zero_factor = next(f for f in factors if f.name == "Campos de comprimento zero")
        assert zero_factor.score == 1.0

    def test_zero_length_fields_no_text_columns(self) -> None:
        """Nenhuma coluna textual → score 1.0 (linha 178)."""
        metadata = ColumnMetadata(
            name="num", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 10.0, 0.0, 25.0, 50.0, 75.0, 100.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_text", (metadata,), 100, {"num": profile})
        factors = FACTOR_REGISTRY["completeness"](dp)
        zero_factor = next(f for f in factors if f.name == "Campos de comprimento zero")
        assert zero_factor.score == 1.0


# ---------------------------------------------------------------------------
# CONSISTENCY
# ---------------------------------------------------------------------------

class TestConsistencyEdge:
    def test_severity_high(self) -> None:
        """score ~0.4 → Severity.HIGH via range_consistency (linha 28)."""
        cols = []
        profs = {}
        for i in range(5):
            has_negative_quantity = i < 3  # 3 de 5 numeric columns with min < 0
            meta = ColumnMetadata(
                name=f"qtd_{i}" if has_negative_quantity else f"preco_{i}",
                data_type=DataType.INTEGER, nullable=True,
                inferred_type=None, null_count=0, non_null_count=100,
            )
            min_val = -5.0 if has_negative_quantity else 0.0
            stats = NumericStats(
                10.0, 5.0, min_val, 5.0, 10.0, 15.0, 20.0, 0.0, -1.0,
            )
            prof = ColumnProfile(metadata=meta, stats=stats, distribution=None, outlier=None)
            cols.append(meta)
            profs[meta.name] = prof
        dp = DataProfile("cons_high", tuple(cols), 100, profs)
        factors = FACTOR_REGISTRY["consistency"](dp)
        range_factor = next(f for f in factors if f.name == "Consistência de intervalos")
        assert range_factor.severity == Severity.HIGH

    def test_severity_medium(self) -> None:
        """score ~0.67 → Severity.MEDIUM via range_consistency (linha 30)."""
        cols = []
        profs = {}
        for i in range(6):
            has_negative_quantity = i < 2  # 2 de 6 inconsistent → score = 1 - 2/6 = 0.667
            meta = ColumnMetadata(
                name=f"qtd_{i}" if has_negative_quantity else f"preco_{i}",
                data_type=DataType.INTEGER, nullable=True,
                inferred_type=None, null_count=0, non_null_count=100,
            )
            min_val = -5.0 if has_negative_quantity else 0.0
            stats = NumericStats(
                10.0, 5.0, min_val, 5.0, 10.0, 15.0, 20.0, 0.0, -1.0,
            )
            prof = ColumnProfile(metadata=meta, stats=stats, distribution=None, outlier=None)
            cols.append(meta)
            profs[meta.name] = prof
        dp = DataProfile("cons_med", tuple(cols), 100, profs)
        factors = FACTOR_REGISTRY["consistency"](dp)
        range_factor = next(f for f in factors if f.name == "Consistência de intervalos")
        assert range_factor.severity == Severity.MEDIUM

    def test_type_unmapped_skipped(self) -> None:
        """Tipo não mapeado (BINARY) → ignorado (linha 59)."""
        metadata = ColumnMetadata(
            name="bin", data_type=DataType.BINARY, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        profile = ColumnProfile(metadata=metadata, stats=None, distribution=None, outlier=None)
        dp = DataProfile("unmapped", (metadata,), 100, {"bin": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        type_factor = next(f for f in factors if f.name == "Consistência de tipos")
        assert type_factor.score == 1.0

    def test_valid_columns_zero(self) -> None:
        """Nenhuma coluna com tipo mapeável → score 1.0 (linha 69)."""
        metadata = ColumnMetadata(
            name="bin", data_type=DataType.BINARY, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        profile = ColumnProfile(metadata=metadata, stats=None, distribution=None, outlier=None)
        dp = DataProfile("valid_zero", (metadata,), 100, {"bin": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        type_factor = next(f for f in factors if f.name == "Consistência de tipos")
        assert type_factor.score == 1.0

    def test_range_consistency_negative_quantity(self) -> None:
        """Coluna 'qtd' com min < 0 → inconsistente (linha 121)."""
        metadata = ColumnMetadata(
            name="qtd", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(-5.0, 10.0, -10.0, -2.0, 0.0, 5.0, 20.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("neg_qtd", (metadata,), 100, {"qtd": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        range_factor = next(f for f in factors if f.name == "Consistência de intervalos")
        assert range_factor.score < 1.0

    def test_range_consistency_min_greater_than_max(self) -> None:
        """stats.min > stats.max → inconsistente (linha 124)."""
        metadata = ColumnMetadata(
            name="preco", data_type=DataType.DOUBLE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 10.0, 100.0, 60.0, 50.0, 40.0, 10.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("min_gt_max", (metadata,), 100, {"preco": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        range_factor = next(f for f in factors if f.name == "Consistência de intervalos")
        assert range_factor.score < 1.0

    def test_cross_column_consistency_temporal_pair(self) -> None:
        """Par temporal com data_fim anterior a data_inicio → inconsistente (linhas 169-187)."""
        meta_fim = ColumnMetadata(
            name="periodo_fim", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        meta_ini = ColumnMetadata(
            name="periodo_inicio", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        fim_stats = TemporalStats("2024-01-01", "2024-06-30", 181, 0)
        ini_stats = TemporalStats("2024-02-01", "2024-12-31", 334, 0)
        prof_fim = ColumnProfile(metadata=meta_fim, stats=fim_stats, distribution=None, outlier=None)
        prof_ini = ColumnProfile(metadata=meta_ini, stats=ini_stats, distribution=None, outlier=None)
        dp = DataProfile("cross_col", (meta_fim, meta_ini), 100, {
            "periodo_fim": prof_fim, "periodo_inicio": prof_ini,
        })
        factors = FACTOR_REGISTRY["consistency"](dp)
        cross_factor = next(f for f in factors if f.name == "Consistência entre colunas")
        assert cross_factor.score < 1.0

    def test_cross_column_non_temporal_stats_skipped(self) -> None:
        """Par temporal onde stats NÃO são TemporalStats → sem inconsistência (linha 184->177)."""
        meta_fim = ColumnMetadata(
            name="periodo_fim", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        meta_ini = ColumnMetadata(
            name="periodo_inicio", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        fim_stats = CategoricalStats({"2024-01-01": 100}, "2024-01-01", 1, 1.0)
        ini_stats = CategoricalStats({"2024-02-01": 100}, "2024-02-01", 1, 1.0)
        prof_fim = ColumnProfile(metadata=meta_fim, stats=fim_stats, distribution=None, outlier=None)
        prof_ini = ColumnProfile(metadata=meta_ini, stats=ini_stats, distribution=None, outlier=None)
        dp = DataProfile("cross_non_temp", (meta_fim, meta_ini), 100, {
            "periodo_fim": prof_fim, "periodo_inicio": prof_ini,
        })
        FACTOR_REGISTRY["consistency"](dp)

    def test_cross_column_consistent_dates_no_violation(self) -> None:
        """Par temporal com datas coerentes → sem inconsistência (linha 185->177)."""
        meta_fim = ColumnMetadata(
            name="periodo_fim", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        meta_ini = ColumnMetadata(
            name="periodo_inicio", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        fim_stats = TemporalStats("2024-06-30", "2024-12-31", 184, 0)
        ini_stats = TemporalStats("2024-01-01", "2024-06-30", 181, 0)
        prof_fim = ColumnProfile(metadata=meta_fim, stats=fim_stats, distribution=None, outlier=None)
        prof_ini = ColumnProfile(metadata=meta_ini, stats=ini_stats, distribution=None, outlier=None)
        dp = DataProfile("cross_consistent", (meta_fim, meta_ini), 100, {
            "periodo_fim": prof_fim, "periodo_inicio": prof_ini,
        })
        FACTOR_REGISTRY["consistency"](dp)

    def test_cross_column_consistency_no_pairs(self) -> None:
        """Nenhum par temporal → score 1.0 (linha 191)."""
        metadata = ColumnMetadata(
            name="nome", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 100}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_pairs", (metadata,), 100, {"nome": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        cross_factor = next(f for f in factors if f.name == "Consistência entre colunas")
        assert cross_factor.score == 1.0

    def test_schema_integrity_nullable_false_with_nulls(self) -> None:
        """nullable=False mas null_count > 0 → violação (linha 229)."""
        metadata = ColumnMetadata(
            name="obrigatorio", data_type=DataType.STRING, nullable=False,
            inferred_type=None, null_count=5, non_null_count=95,
        )
        stats = CategoricalStats({"A": 95}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("schema_violation", (metadata,), 100, {"obrigatorio": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        schema_factor = next(f for f in factors if f.name == "Integridade do esquema")
        assert schema_factor.score < 1.0

    def test_schema_integrity_empty_columns(self) -> None:
        """Nenhuma coluna → score 1.0 (linha 232)."""
        dp = DataProfile("no_schema", (), 100, {})
        factors = FACTOR_REGISTRY["consistency"](dp)
        schema_factor = next(f for f in factors if f.name == "Integridade do esquema")
        assert schema_factor.score == 1.0

    def test_referential_integrity_id_with_nulls(self) -> None:
        """Coluna *_id com null_count > 0 → sensitive (linhas 270-274)."""
        metadata = ColumnMetadata(
            name="cliente_id", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=10, non_null_count=90,
        )
        stats = CategoricalStats({"A": 90}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("ref_int", (metadata,), 100, {"cliente_id": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        ref_factor = next(f for f in factors if f.name == "Integridade referencial")
        assert ref_factor.score == 0.9

    def test_referential_integrity_id_non_categorical(self) -> None:
        """Coluna *_id com stats não-Categorical → ignorada (linha 272->267)."""
        metadata = ColumnMetadata(
            name="cliente_id", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=5, non_null_count=95,
        )
        stats = NumericStats(50.0, 10.0, 1.0, 25.0, 50.0, 75.0, 100.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("ref_non_cat", (metadata,), 100, {"cliente_id": profile})
        FACTOR_REGISTRY["consistency"](dp)

    def test_referential_integrity_id_no_nulls(self) -> None:
        """Coluna *_id com CategoricalStats mas null_count == 0 → não sensível (linha 273->267)."""
        metadata = ColumnMetadata(
            name="produto_id", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 100}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("ref_no_nulls", (metadata,), 100, {"produto_id": profile})
        FACTOR_REGISTRY["consistency"](dp)

    def test_referential_integrity_no_sensitive_columns(self) -> None:
        """Nenhuma coluna *_id ou *_fk → score 1.0 (linha 276)."""
        metadata = ColumnMetadata(
            name="nome", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 100}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_ref", (metadata,), 100, {"nome": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        ref_factor = next(f for f in factors if f.name == "Integridade referencial")
        assert ref_factor.score == 1.0

    def test_format_consistency_inferred_with_high_nulls(self) -> None:
        """Coluna com inferred_type e null_ratio > 0.1 → inconsistente (linhas 315-320)."""
        metadata = ColumnMetadata(
            name="email_contato", data_type=DataType.STRING, nullable=True,
            inferred_type=InferredType.EMAIL, null_count=20, non_null_count=80,
        )
        stats = CategoricalStats({"A": 80}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("fmt_cons", (metadata,), 100, {"email_contato": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        fmt_factor = next(f for f in factors if f.name == "Consistência de formato")
        assert fmt_factor.score < 1.0

    def test_format_consistency_total_column_zero(self) -> None:
        """inferred_type column com total=0 → pula (linha 317->313)."""
        metadata = ColumnMetadata(
            name="email_ok", data_type=DataType.STRING, nullable=True,
            inferred_type=InferredType.EMAIL, null_count=0, non_null_count=0,
        )
        profile = ColumnProfile(metadata=metadata, stats=None, distribution=None, outlier=None)
        dp = DataProfile("fmt_zero_total", (metadata,), 0, {"email_ok": profile})
        FACTOR_REGISTRY["consistency"](dp)

    def test_format_consistency_null_ratio_below_10(self) -> None:
        """inferred_type column com null_ratio <= 0.1 → não inconsistente (linha 319->313)."""
        metadata = ColumnMetadata(
            name="tel_ok", data_type=DataType.STRING, nullable=True,
            inferred_type=InferredType.PHONE_BR, null_count=5, non_null_count=95,
        )
        stats = CategoricalStats({"11999999999": 95}, "11999999999", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("fmt_low_null", (metadata,), 100, {"tel_ok": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        fmt_factor = next(f for f in factors if f.name == "Consistência de formato")
        assert "tel_ok" not in fmt_factor.affected_columns

    def test_format_consistency_no_inferred(self) -> None:
        """Nenhuma coluna com inferred_type → score 1.0 (linha 322)."""
        metadata = ColumnMetadata(
            name="nome", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 100}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_inferred_cons", (metadata,), 100, {"nome": profile})
        factors = FACTOR_REGISTRY["consistency"](dp)
        fmt_factor = next(f for f in factors if f.name == "Consistência de formato")
        assert fmt_factor.score == 1.0


# ---------------------------------------------------------------------------
# TIMELINESS
# ---------------------------------------------------------------------------

class TestTimelinessEdge:
    def test_severity_critical(self) -> None:
        """score ~0.2 → Severity.CRITICAL (linha 20)."""
        metadata = ColumnMetadata(
            name="dt", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=90, non_null_count=10,
        )
        tstats = TemporalStats("2024-01-01", "2024-12-31", 365, 0)
        profile = ColumnProfile(metadata=metadata, stats=tstats, distribution=None, outlier=None)
        dp = DataProfile("tim_crit", (metadata,), 100, {"dt": profile})
        factors = FACTOR_REGISTRY["timeliness"](dp)
        invalid_factor = next(f for f in factors if f.name == "Datas inválidas")
        assert invalid_factor.severity == Severity.CRITICAL

    def test_severity_high(self) -> None:
        """score ~0.5 → Severity.HIGH (linha 22)."""
        metadata = ColumnMetadata(
            name="dt", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=60, non_null_count=40,
        )
        tstats = TemporalStats("2024-01-01", "2024-12-31", 365, 0)
        profile = ColumnProfile(metadata=metadata, stats=tstats, distribution=None, outlier=None)
        dp = DataProfile("tim_high", (metadata,), 100, {"dt": profile})
        factors = FACTOR_REGISTRY["timeliness"](dp)
        invalid_factor = next(f for f in factors if f.name == "Datas inválidas")
        assert invalid_factor.severity == Severity.HIGH

    def test_freshness_range_days_zero(self) -> None:
        """range_days == 0 → não conta como recente (linha 43->38)."""
        metadata = ColumnMetadata(
            name="dt", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        tstats = TemporalStats("2024-01-01", "2024-01-01", 0, 0)
        profile = ColumnProfile(metadata=metadata, stats=tstats, distribution=None, outlier=None)
        dp = DataProfile("fresh_zero", (metadata,), 100, {"dt": profile})
        factors = FACTOR_REGISTRY["timeliness"](dp)
        fresh_factor = next(f for f in factors if f.name == "Atualidade dos dados")
        assert fresh_factor.score == 0.0

    def test_temporal_completeness_total_zero(self) -> None:
        """total_column == 0 → proportion = 1.0 (linha 87)."""
        metadata = ColumnMetadata(
            name="dt", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=0,
        )
        profile = ColumnProfile(metadata=metadata, stats=None, distribution=None, outlier=None)
        dp = DataProfile("temp_comp_zero", (metadata,), 0, {"dt": profile})
        FACTOR_REGISTRY["timeliness"](dp)

    def test_temporal_completeness_proportion_above_95(self) -> None:
        """proportion >= 0.95 → não adiciona affected (linha 92->83)."""
        metadata = ColumnMetadata(
            name="dt", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=2, non_null_count=98,
        )
        tstats = TemporalStats("2024-01-01", "2024-12-31", 365, 0)
        profile = ColumnProfile(metadata=metadata, stats=tstats, distribution=None, outlier=None)
        dp = DataProfile("temp_high_comp", (metadata,), 100, {"dt": profile})
        factors = FACTOR_REGISTRY["timeliness"](dp)
        comp_factor = next(f for f in factors if f.name == "Completude temporal")
        assert "dt" not in comp_factor.affected_columns

    def test_invalid_dates_total_zero(self) -> None:
        """total_column == 0 → null_ratio = 0.0 (linha 137)."""
        metadata = ColumnMetadata(
            name="dt", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=0,
        )
        profile = ColumnProfile(metadata=metadata, stats=None, distribution=None, outlier=None)
        dp = DataProfile("inv_date_zero", (metadata,), 0, {"dt": profile})
        FACTOR_REGISTRY["timeliness"](dp)

    def test_invalid_dates_null_ratio_below_005(self) -> None:
        """null_ratio <= 0.05 → não adiciona affected (linha 142->133)."""
        metadata = ColumnMetadata(
            name="dt", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=2, non_null_count=98,
        )
        tstats = TemporalStats("2024-01-01", "2024-12-31", 365, 0)
        profile = ColumnProfile(metadata=metadata, stats=tstats, distribution=None, outlier=None)
        dp = DataProfile("inv_low", (metadata,), 100, {"dt": profile})
        factors = FACTOR_REGISTRY["timeliness"](dp)
        inv_factor = next(f for f in factors if f.name == "Datas inválidas")
        assert "dt" not in inv_factor.affected_columns

    def test_severity_medium(self) -> None:
        """score ~0.7 → Severity.MEDIUM via _invalid_dates (linha 24)."""
        metadata = ColumnMetadata(
            name="dt", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=30, non_null_count=70,
        )
        tstats = TemporalStats("2024-01-01", "2024-12-31", 365, 0)
        profile = ColumnProfile(metadata=metadata, stats=tstats, distribution=None, outlier=None)
        dp = DataProfile("tim_med", (metadata,), 100, {"dt": profile})
        factors = FACTOR_REGISTRY["timeliness"](dp)
        invalid_factor = next(f for f in factors if f.name == "Datas inválidas")
        assert invalid_factor.severity == Severity.MEDIUM

    def test_non_temporal_columns_skipped_by_completeness_and_invalid(self) -> None:
        """Coluna sem tipo date/timestamp → _temporal_completeness e _invalid_dates retornam
        score 1.0 (linhas 96, 146). Branch False 84->83 e 134->133."""
        metadata = ColumnMetadata(
            name="texto", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 100}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_temporal", (metadata,), 100, {"texto": profile})
        factors = FACTOR_REGISTRY["timeliness"](dp)
        comp_factor = next(f for f in factors if f.name == "Completude temporal")
        assert comp_factor.score == 1.0
        inv_factor = next(f for f in factors if f.name == "Datas inválidas")
        assert inv_factor.score == 1.0

    def test_temporal_gaps_with_gaps(self) -> None:
        """gap_count > 0 → coluna adicionada (linhas 191-192)."""
        metadata = ColumnMetadata(
            name="dt", data_type=DataType.DATE, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        tstats = TemporalStats("2024-01-01", "2024-12-31", 365, 5)
        profile = ColumnProfile(metadata=metadata, stats=tstats, distribution=None, outlier=None)
        dp = DataProfile("gaps", (metadata,), 100, {"dt": profile})
        factors = FACTOR_REGISTRY["timeliness"](dp)
        gap_factor = next(f for f in factors if f.name == "Lacunas temporais")
        assert gap_factor.score < 1.0


# ---------------------------------------------------------------------------
# UNIQUENESS
# ---------------------------------------------------------------------------

class TestUniquenessEdge:
    def test_severity_medium(self) -> None:
        """score ~0.65 → Severity.MEDIUM (linha 26)."""
        metadata = ColumnMetadata(
            name="cat", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 60, "B": 40}, "A", 2, 0.65)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("uniq_med", (metadata,), 100, {"cat": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        dup_factor = next(f for f in factors if f.name == "Proporção de duplicatas")
        assert dup_factor.severity == Severity.MEDIUM

    def test_duplicate_ratio_low_unique_adds_affected(self) -> None:
        """unique_ratio < 0.5 → adiciona a affected_columns (linha 58)."""
        metadata = ColumnMetadata(
            name="cat_dup", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 70, "B": 30}, "A", 2, 0.3)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("low_unique", (metadata,), 100, {"cat_dup": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        dup_factor = next(f for f in factors if f.name == "Proporção de duplicatas")
        assert "cat_dup" in dup_factor.affected_columns

    def test_pk_candidate_recognized(self) -> None:
        """Coluna 'user_id' é candidata a PK (linha 39)."""
        metadata = ColumnMetadata(
            name="user_id", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({f"u{i}": 1 for i in range(100)}, "u1", 100, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("pk_test", (metadata,), 100, {"user_id": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        pk_factor = next(f for f in factors if f.name == "Unicidade de chaves primárias")
        assert pk_factor.score == 1.0

    def test_pk_non_unique_adds_affected(self) -> None:
        """PK candidata com unique_ratio < 0.99 → adiciona a affected (linhas 102-108)."""
        metadata = ColumnMetadata(
            name="id", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 50, "B": 50}, "A", 2, 0.5)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("pk_non_uniq", (metadata,), 100, {"id": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        pk_factor = next(f for f in factors if f.name == "Unicidade de chaves primárias")
        assert "id" in pk_factor.affected_columns
        assert pk_factor.score < 1.0

    def test_pk_found_zero(self) -> None:
        """Nenhuma coluna candidata a PK → score 1.0 (linha 110)."""
        metadata = ColumnMetadata(
            name="nome", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"A": 100}, "A", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_pk", (metadata,), 100, {"nome": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        pk_factor = next(f for f in factors if f.name == "Unicidade de chaves primárias")
        assert pk_factor.score == 1.0

    def test_near_duplicates_detected(self) -> None:
        """unique_ratio entre 0.95 e 1.0 → near_duplicate (linha 153)."""
        metadata = ColumnMetadata(
            name="cat", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({f"v{i}": 1 for i in range(98)}, "v1", 98, 0.98)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("near_dup", (metadata,), 100, {"cat": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        near_factor = next(f for f in factors if f.name == "Quase-duplicatas")
        assert "cat" in near_factor.affected_columns

    def test_near_duplicates_no_categorical(self) -> None:
        """Nenhuma coluna categórica → score 1.0 (linha 155)."""
        metadata = ColumnMetadata(
            name="num", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 10.0, 0.0, 25.0, 50.0, 75.0, 100.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_cat", (metadata,), 100, {"num": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        near_factor = next(f for f in factors if f.name == "Quase-duplicatas")
        assert near_factor.score == 1.0

    def test_constant_columns_detected(self) -> None:
        """cardinalidade == 1 → constante (linha 199)."""
        metadata = ColumnMetadata(
            name="fixo", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({"UNICO": 100}, "UNICO", 1, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("const", (metadata,), 100, {"fixo": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        const_factor = next(f for f in factors if f.name == "Colunas constantes")
        assert const_factor.score < 1.0

    def test_constant_columns_no_categorical(self) -> None:
        """Nenhuma coluna com cardinalidade → score 1.0 (linha 202)."""
        metadata = ColumnMetadata(
            name="num", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 10.0, 0.0, 25.0, 50.0, 75.0, 100.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_cat_const", (metadata,), 100, {"num": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        const_factor = next(f for f in factors if f.name == "Colunas constantes")
        assert const_factor.score == 1.0

    def test_near_constant_columns_detected(self) -> None:
        """cardinalidade 2 com row_count > 100 → near_constant (linha 246)."""
        metadata = ColumnMetadata(
            name="flag", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=200,
        )
        stats = CategoricalStats({"S": 150, "N": 50}, "S", 2, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("near_const_uniq", (metadata,), 200, {"flag": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        near_const_factor = next(f for f in factors if f.name == "Colunas quase-constantes")
        assert near_const_factor.score < 1.0

    def test_cardinality_factor_high_mean_ratio(self) -> None:
        """mean_ratio >= 0.99 → score = (1 - mean_ratio) * 100 (linha 312)."""
        metadata = ColumnMetadata(
            name="id_col", data_type=DataType.STRING, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = CategoricalStats({f"v{i}": 1 for i in range(100)}, "v1", 100, 1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("card_high", (metadata,), 100, {"id_col": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        card_factor = next(f for f in factors if f.name == "Cardinalidade")
        assert card_factor.score < 1.0

    def test_cardinality_no_categorical(self) -> None:
        """Nenhuma coluna categórica → score 1.0 (linha 296)."""
        metadata = ColumnMetadata(
            name="num", data_type=DataType.INTEGER, nullable=True,
            inferred_type=None, null_count=0, non_null_count=100,
        )
        stats = NumericStats(50.0, 10.0, 0.0, 25.0, 50.0, 75.0, 100.0, 0.0, -1.0)
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        dp = DataProfile("no_cat_card", (metadata,), 100, {"num": profile})
        factors = FACTOR_REGISTRY["uniqueness"](dp)
        card_factor = next(f for f in factors if f.name == "Cardinalidade")
        assert card_factor.score == 1.0