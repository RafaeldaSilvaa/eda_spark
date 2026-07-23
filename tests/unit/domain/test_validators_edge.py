from __future__ import annotations

"""Testes de borda para validadores de documentos brasileiros.

Cobre as linhas 38 e 78: retorno False no primeiro dígito verificador.
"""

from spark_eda.domain.services.business.validators import CPFValidator, CNPJValidator


class TestCPFValidatorEdge:
    def test_invalid_format_returns_false(self) -> None:
        """CPF com formato inválido → False (linha 26)."""
        assert CPFValidator.validate("abc") is False
        assert CPFValidator.validate("1234567890") is False  # 10 dígitos

    def test_all_same_digits_returns_false(self) -> None:
        """CPF com todos dígitos iguais → False (linha 29)."""
        assert CPFValidator.validate("11111111111") is False

    def test_invalid_first_check_digit_returns_false(self) -> None:
        """CPF cujo primeiro dígito verificador (posição 10) está errado → False (linha 38)."""
        # "529.982.247-35": first 9 = "529982247", first_digit = 2, digits[9] = '3' → mismatch
        assert CPFValidator.validate("529.982.247-35") is False

    def test_second_check_digit_mismatch_returns_false(self) -> None:
        """CPF com primeiro dígito OK mas segundo errado → False (linha 41)."""
        # "529.982.247-24": first_digit=2 → OK; second_digit=5, digits[10]='4' → mismatch
        assert CPFValidator.validate("529.982.247-24") is False


class TestCNPJValidatorEdge:
    def test_invalid_format_returns_false(self) -> None:
        """CNPJ com formato inválido → False (linha 66)."""
        assert CNPJValidator.validate("abc") is False
        assert CNPJValidator.validate("1234567890123") is False  # 13 dígitos

    def test_all_same_digits_returns_false(self) -> None:
        """CNPJ com todos dígitos iguais → False (linha 69)."""
        assert CNPJValidator.validate("11111111111111") is False

    def test_invalid_first_check_digit_returns_false(self) -> None:
        """CNPJ cujo primeiro dígito verificador (posição 13) está errado → False (linha 78)."""
        # "00.000.000/0001-81": first_digit = 9, digits[12] = '8' → mismatch
        assert CNPJValidator.validate("00.000.000/0001-81") is False

    def test_second_check_digit_mismatch_returns_false(self) -> None:
        """CNPJ com primeiro dígito OK mas segundo errado → False (linha 81)."""
        # "00.000.000/0001-92": first_digit=9 → OK; second_digit=1, digits[13]='2' → mismatch
        assert CNPJValidator.validate("00.000.000/0001-92") is False