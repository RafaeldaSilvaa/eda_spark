from __future__ import annotations

"""Testes de borda para o classificador semântico de colunas.

Cobre branches não testados: AUTO_INCREMENT por nome, amostras com
None, poucas amostras, padrão CREDIT_CARD e CNPJ por amostra.
"""

from spark_eda.domain.services.column_classifier import ColumnClassifier
from spark_eda.domain.value_objects.inferred_type import InferredType


class TestColumnClassifierEdge:
    def test_column_named_id_returns_auto_increment(self) -> None:
        """Nome exatamente 'id' deve retornar AUTO_INCREMENT (linha 65-66)."""
        classifier: ColumnClassifier = ColumnClassifier()
        result: InferredType = classifier.classify(column_name="id")
        assert result == InferredType.AUTO_INCREMENT

    def test_column_named_xid_returns_auto_increment(self) -> None:
        """Nome 'xid' termina com 'id' e len <= 6 → AUTO_INCREMENT."""
        classifier: ColumnClassifier = ColumnClassifier()
        result: InferredType = classifier.classify(column_name="xid")
        assert result == InferredType.AUTO_INCREMENT

    def test_less_than_3_non_null_samples_returns_none(self) -> None:
        """Menos de 3 amostras não nulas → _classify_by_samples retorna None (linha 89-90)."""
        classifier: ColumnClassifier = ColumnClassifier()
        samples: list[str | None] = ["abc", None, "def"]
        result: InferredType = classifier.classify(column_name="unknown", sample_values=samples)
        assert result == InferredType.NONE

    def test_sample_value_with_none_filtered(self) -> None:
        """Valores None nas amostras são filtrados (linha 85-87)."""
        classifier: ColumnClassifier = ColumnClassifier()
        samples: list[str | None] = [None, None, None, None]
        result: InferredType = classifier.classify(column_name="unknown", sample_values=samples)
        assert result == InferredType.NONE

    def test_samples_match_credit_card(self) -> None:
        """Amostras no formato de cartão de crédito retornam CREDIT_CARD (linha 118-120)."""
        classifier: ColumnClassifier = ColumnClassifier()
        samples: list[str | None] = [
            "4111-1111-1111-1111",
            "5500-0000-0000-0004",
            "4111111111111111",
            "5555555555554444",
        ]
        result: InferredType = classifier.classify(column_name="cartao", sample_values=samples)
        assert result == InferredType.CREDIT_CARD

    def test_samples_match_cnpj(self) -> None:
        """Amostras no formato CNPJ retornam CNPJ (linha 96-98)."""
        classifier: ColumnClassifier = ColumnClassifier()
        samples: list[str | None] = [
            "55.605.751/0001-56",
            "22.813.442/0001-50",
            "33.000.167/0001-00",
            "11.444.333/0001-99",
        ]
        result: InferredType = classifier.classify(column_name="cnpj_field", sample_values=samples)
        assert result == InferredType.CNPJ

    def test_samples_match_email(self) -> None:
        """Amostras no formato email retornam EMAIL (linha 99-101)."""
        classifier: ColumnClassifier = ColumnClassifier()
        samples: list[str | None] = [
            "user@example.com",
            "foo@bar.org",
            "test@domain.com.br",
            "admin@site.io",
        ]
        result: InferredType = classifier.classify(column_name="endereco_eletronico", sample_values=samples)
        assert result == InferredType.EMAIL

    def test_samples_match_uuid(self) -> None:
        """Amostras no formato UUID retornam UUID (linha 102-105)."""
        classifier: ColumnClassifier = ColumnClassifier()
        samples: list[str | None] = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "00000000-0000-0000-0000-000000000000",
        ]
        result: InferredType = classifier.classify(column_name="chave", sample_values=samples)
        assert result == InferredType.UUID

    def test_samples_no_majority_returns_none(self) -> None:
        """Amostras onde nenhum padrão atinge >50% de match → None (linha 132-136)."""
        classifier: ColumnClassifier = ColumnClassifier()
        samples: list[str | None] = [
            "abc@def.com",
            "11999999999",
            "12.345.678/0001-90",
            "just a string",
        ]
        result: InferredType = classifier.classify(column_name="campo", sample_values=samples)
        assert result == InferredType.NONE

    def test_samples_none_provided_skips_sampling(self) -> None:
        """Sem amostras, _classify_by_samples não é chamado (linha 165)."""
        classifier: ColumnClassifier = ColumnClassifier()
        result: InferredType = classifier.classify(column_name="descricao")
        assert result == InferredType.NONE

    def test_name_matches_first_takes_priority(self) -> None:
        """Classificação por nome tem prioridade sobre amostras (linha 162-163)."""
        classifier: ColumnClassifier = ColumnClassifier()
        samples: list[str | None] = ["abc", "def", "ghi"]
        result: InferredType = classifier.classify(column_name="email_contato", sample_values=samples)
        assert result == InferredType.EMAIL
