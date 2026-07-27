"""Validadores para documentos brasileiros (CPF e CNPJ)."""

from __future__ import annotations

import re

_CPF_LENGTH = 11
_CNPJ_LENGTH = 14
_DIGIT_THRESHOLD = 2


class CPFValidator:
    """Validador de CPF utilizando o algoritmo oficial de dígitos verificadores."""

    _STRIP_PATTERN: re.Pattern[str] = re.compile(r"[^\d]")

    @staticmethod
    def validate(cpf: str) -> bool:
        """Valida um CPF utilizando o algoritmo oficial de dígitos verificadores.

        Args:
            cpf: CPF no formato ``XXX.XXX.XXX-XX`` ou dígitos puros.

        Returns:
            ``True`` se o CPF for válido, ``False`` caso contrário.
        """
        digits: str = CPFValidator._STRIP_PATTERN.sub("", cpf)

        if len(digits) != _CPF_LENGTH or not digits.isdigit():
            return False

        if all(d == digits[0] for d in digits):
            return False

        def _compute_digit(base: str, weight_start: int) -> int:
            total: int = sum(int(d) * (weight_start - i) for i, d in enumerate(base))
            remainder: int = total % 11
            return 0 if remainder < _DIGIT_THRESHOLD else 11 - remainder

        first_digit: int = _compute_digit(digits[:9], 10)
        if int(digits[9]) != first_digit:
            return False

        second_digit: int = _compute_digit(digits[:10], 11)
        return int(digits[10]) == second_digit


class CNPJValidator:
    """Validador de CNPJ utilizando o algoritmo oficial de dígitos verificadores."""

    _STRIP_PATTERN: re.Pattern[str] = re.compile(r"[^\d]")

    # Weights for the first and second check digits
    _FIRST_WEIGHTS: tuple[int, ...] = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    _SECOND_WEIGHTS: tuple[int, ...] = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)

    @staticmethod
    def validate(cnpj: str) -> bool:
        """Valida um CNPJ utilizando o algoritmo oficial de dígitos verificadores.

        Args:
            cnpj: CNPJ no formato ``XX.XXX.XXX/XXXX-XX`` ou dígitos puros.

        Returns:
            ``True`` se o CNPJ for válido, ``False`` caso contrário.
        """
        digits: str = CNPJValidator._STRIP_PATTERN.sub("", cnpj)

        if len(digits) != _CNPJ_LENGTH or not digits.isdigit():
            return False

        if all(d == digits[0] for d in digits):
            return False

        def _compute_digit(base: str, weights: tuple[int, ...]) -> int:
            total: int = sum(int(d) * w for d, w in zip(base, weights, strict=False))
            remainder: int = total % 11
            return 0 if remainder < _DIGIT_THRESHOLD else 11 - remainder

        first_digit: int = _compute_digit(digits[:12], CNPJValidator._FIRST_WEIGHTS)
        if int(digits[12]) != first_digit:
            return False

        second_digit: int = _compute_digit(digits[:13], CNPJValidator._SECOND_WEIGHTS)
        return int(digits[13]) == second_digit
