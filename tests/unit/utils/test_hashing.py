from __future__ import annotations

"""Testes para a função de hashing compute_fingerprint.

Verifica a geração de SHA-256 a partir de schema e configuração
em formato JSON.
"""

import hashlib

from spark_eda.utils.hashing import compute_fingerprint


class TestComputeFingerprint:
    """Testes para a função compute_fingerprint."""

    def test_returns_hex_string(self) -> None:
        """compute_fingerprint deve retornar uma string hexadecimal
        de 64 caracteres (SHA-256).
        """
        # Arrange
        schema_json: str = '{"colunas": ["id", "nome"]}'
        config_json: str = '{"max_categories": 30}'

        # Act
        result: str = compute_fingerprint(schema_json, config_json)

        # Assert
        assert isinstance(result, str)
        assert len(result) == 64
        int(result, 16)  # deve ser hex válido

    def test_deterministic_output(self) -> None:
        """compute_fingerprint deve produzir o mesmo resultado para
        as mesmas entradas.
        """
        # Arrange
        schema_json: str = '{"cols": ["a"]}'
        config_json: str = '{"opt": true}'

        # Act
        result1: str = compute_fingerprint(schema_json, config_json)
        result2: str = compute_fingerprint(schema_json, config_json)

        # Assert
        assert result1 == result2

    def test_different_inputs_produce_different_hashes(self) -> None:
        """Entradas diferentes devem produzir hashes diferentes."""
        # Arrange & Act
        hash_a: str = compute_fingerprint('{"x": 1}', "{}")
        hash_b: str = compute_fingerprint('{"x": 2}', "{}")

        # Assert
        assert hash_a != hash_b

    def test_includes_both_schema_and_config(self) -> None:
        """O hash deve depender tanto do schema quanto da config."""
        # Arrange & Act
        hash_schema: str = compute_fingerprint('{"a": 1}', "{}")
        hash_config: str = compute_fingerprint('{"a": 1}', '{"b": 2}')

        # Assert
        assert hash_schema != hash_config

    def test_matches_manual_sha256(self) -> None:
        """O resultado deve corresponder a um SHA-256 calculado
        manualmente.
        """
        # Arrange
        schema_json: str = '{"col": "x"}'
        config_json: str = '{"opt": 1}'
        expected: str = hashlib.sha256(
            f"{schema_json}:::{config_json}".encode("utf-8"),
        ).hexdigest()

        # Act
        result: str = compute_fingerprint(schema_json, config_json)

        # Assert
        assert result == expected
