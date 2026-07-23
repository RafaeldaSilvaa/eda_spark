from __future__ import annotations

"""Testes para o classificador semântico de colunas.

Testa o serviço ColumnClassifier com regras de nome e amostras de
valores, sem dependência de Spark.
"""

from spark_eda.domain.services.column_classifier import ColumnClassifier
from spark_eda.domain.value_objects.inferred_type import InferredType


class TestColumnClassifier:
    """Testes para o classificador semântico de colunas."""

    def test_column_named_cpf_returns_cpf(self) -> None:
        """Uma coluna com nome contendo 'cpf' deve ser classificada como
        InferredType.CPF.
        """
        classifier: ColumnClassifier = ColumnClassifier()
        result: InferredType = classifier.classify(column_name="cpf_cliente")

        assert result == InferredType.CPF

    def test_column_named_email_returns_email(self) -> None:
        """Uma coluna com nome contendo 'email' deve ser classificada como
        InferredType.EMAIL.
        """
        classifier: ColumnClassifier = ColumnClassifier()
        result: InferredType = classifier.classify(column_name="email_contato")

        assert result == InferredType.EMAIL

    def test_column_named_uuid_returns_uuid(self) -> None:
        """Uma coluna com nome contendo 'uuid' deve ser classificada como
        InferredType.UUID.
        """
        classifier: ColumnClassifier = ColumnClassifier()
        result: InferredType = classifier.classify(column_name="uuid_transacao")

        assert result == InferredType.UUID

    def test_unknown_column_name_returns_none(self) -> None:
        """Uma coluna com nome desconhecido deve retornar InferredType.NONE
        quando não há amostras.
        """
        classifier: ColumnClassifier = ColumnClassifier()
        result: InferredType = classifier.classify(column_name="descricao")

        assert result == InferredType.NONE

    def test_with_sample_values_matching_cpf_pattern(self) -> None:
        """Uma coluna cujas amostras correspondem ao padrão de CPF deve ser
        classificada como InferredType.CPF, mesmo que o nome não
        corresponda.
        """
        classifier: ColumnClassifier = ColumnClassifier()
        samples: list[str] = [
            "123.456.789-09",
            "987.654.321-00",
            "111.222.333-44",
            "555.666.777-88",
        ]
        result: InferredType = classifier.classify(column_name="documento", sample_values=samples)

        assert result == InferredType.CPF
