from __future__ import annotations

"""Testes para as expressões regulares de padrões de negócio.

Testa cada padrão exportado do módulo ``business/patterns.py``
com casos válidos e inválidos.
"""

import re

from spark_eda.domain.services.business.patterns import (
    CEP,
    CNPJ,
    CPF,
    EMAIL,
    IPV4,
    PHONE_BR,
    URL,
    UUID,
)


class TestBusinessPatterns:
    """Testes para as regex de padrões de negócio brasileiros."""

    def test_cpf_matches_formatted(self) -> None:
        assert CPF.match("529.982.247-25") is not None

    def test_cpf_rejects_unformatted(self) -> None:
        assert CPF.match("52998224725") is None

    def test_cpf_rejects_invalid_format(self) -> None:
        assert CPF.match("529.982.247-2") is None

    def test_cpf_rejects_letters(self) -> None:
        assert CPF.match("abc.def.ghi-jk") is None

    def test_cnpj_matches_formatted(self) -> None:
        assert CNPJ.match("11.444.524/0001-84") is not None

    def test_cnpj_rejects_unformatted(self) -> None:
        assert CNPJ.match("11444524000184") is None

    def test_cnpj_rejects_invalid_format(self) -> None:
        assert CNPJ.match("11.444.524/0001-8") is None

    def test_email_matches_simple(self) -> None:
        assert EMAIL.match("user@example.com") is not None

    def test_email_matches_with_plus(self) -> None:
        assert EMAIL.match("user+tag@example.co.uk") is not None

    def test_email_rejects_no_at(self) -> None:
        assert EMAIL.match("not-an-email") is None

    def test_uuid_matches_canonical(self) -> None:
        assert UUID.match("550e8400-e29b-41d4-a716-446655440000") is not None

    def test_uuid_rejects_short(self) -> None:
        assert UUID.match("550e8400-e29b-41d4") is None

    def test_url_matches_https(self) -> None:
        assert URL.match("https://example.com") is not None

    def test_url_matches_http(self) -> None:
        assert URL.match("http://example.com/path") is not None

    def test_url_rejects_no_protocol(self) -> None:
        assert URL.match("not-a-url") is None

    def test_ipv4_matches_valid(self) -> None:
        assert IPV4.match("192.168.1.1") is not None

    def test_ipv4_rejects_out_of_range(self) -> None:
        assert IPV4.match("999.999.999.999") is None

    def test_ipv4_rejects_invalid_format(self) -> None:
        assert IPV4.match("192.168.1") is None

    def test_cep_matches_with_hyphen(self) -> None:
        assert CEP.match("01001-000") is not None

    def test_cep_matches_digits_only(self) -> None:
        assert CEP.match("01001000") is not None

    def test_cep_rejects_letters(self) -> None:
        assert CEP.match("abcde-fgh") is None

    def test_phone_br_matches_full(self) -> None:
        assert PHONE_BR.match("+5511999998888") is not None

    def test_phone_br_matches_without_plus(self) -> None:
        assert PHONE_BR.match("5511999998888") is not None

    def test_phone_br_matches_with_spaces(self) -> None:
        assert PHONE_BR.match("+55 11 9999-8888") is not None

    def test_phone_br_rejects_without_country_code(self) -> None:
        assert PHONE_BR.match("11999998888") is None

    def test_patterns_are_compiled_regex(self) -> None:
        assert isinstance(CPF, re.Pattern)
        assert isinstance(CNPJ, re.Pattern)
        assert isinstance(EMAIL, re.Pattern)
        assert isinstance(UUID, re.Pattern)
        assert isinstance(URL, re.Pattern)
        assert isinstance(IPV4, re.Pattern)
        assert isinstance(CEP, re.Pattern)
        assert isinstance(PHONE_BR, re.Pattern)
