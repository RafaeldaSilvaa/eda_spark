from __future__ import annotations

"""Testes para os validadores de documentos brasileiros.

Testa CPFValidator e CNPJValidator com casos conhecidos,
bordas e cenários de invalidação.
"""

from spark_eda.domain.services.business.validators import CNPJValidator, CPFValidator


class TestCPFValidator:
    """Testes para o validador de CPF."""

    def test_valid_cpf_formatted_returns_true(self) -> None:
        assert CPFValidator.validate("529.982.247-25") is True

    def test_valid_cpf_digits_only_returns_true(self) -> None:
        assert CPFValidator.validate("52998224725") is True

    def test_invalid_cpf_wrong_checksum_returns_false(self) -> None:
        assert CPFValidator.validate("529.982.247-24") is False

    def test_invalid_cpf_all_same_digits_returns_false(self) -> None:
        assert CPFValidator.validate("111.111.111-11") is False

    def test_invalid_cpf_wrong_length_returns_false(self) -> None:
        assert CPFValidator.validate("123.456.789-0") is False

    def test_invalid_cpf_with_letters_returns_false(self) -> None:
        assert CPFValidator.validate("abc.def.ghi-jk") is False

    def test_empty_string_returns_false(self) -> None:
        assert CPFValidator.validate("") is False

    def test_short_digits_returns_false(self) -> None:
        assert CPFValidator.validate("1234567890") is False

    def test_alternative_valid_cpf(self) -> None:
        assert CPFValidator.validate("935.411.347-80") is True


class TestCNPJValidator:
    """Testes para o validador de CNPJ."""

    def test_valid_cnpj_formatted_returns_true(self) -> None:
        assert CNPJValidator.validate("00.000.000/0001-91") is True

    def test_valid_cnpj_digits_only_returns_true(self) -> None:
        assert CNPJValidator.validate("00000000000191") is True

    def test_invalid_cnpj_wrong_checksum_returns_false(self) -> None:
        assert CNPJValidator.validate("00.000.000/0001-92") is False

    def test_invalid_cnpj_all_same_digits_returns_false(self) -> None:
        assert CNPJValidator.validate("11.111.111/1111-11") is False

    def test_invalid_cnpj_wrong_length_returns_false(self) -> None:
        assert CNPJValidator.validate("00.000.000/0001-9") is False

    def test_invalid_cnpj_with_letters_returns_false(self) -> None:
        assert CNPJValidator.validate("aa.aaa.aaa/aaaa-aa") is False

    def test_empty_string_returns_false(self) -> None:
        assert CNPJValidator.validate("") is False

    def test_alternative_valid_cnpj(self) -> None:
        assert CNPJValidator.validate("51.017.257/5422-40") is True
