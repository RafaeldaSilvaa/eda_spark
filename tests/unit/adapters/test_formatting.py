from __future__ import annotations

"""Testes para as funções utilitárias de formatação.

Testa format_number, format_percentage, format_bytes e truncate_text
com valores típicos e casos de borda.
"""

from spark_eda.utils.formatting import format_bytes, format_number, format_percentage, truncate_text


class TestFormatNumber:
    """Testes para formatação de números."""

    def test_format_number_integer(self) -> None:
        """Um inteiro deve ser formatado com separador de milhar."""
        # Act
        result: str = format_number(1234)

        # Assert
        assert result == "1.234"

    def test_format_number_float_with_decimals(self) -> None:
        """Um float com 2 casas decimais deve ser formatado corretamente."""
        # Act
        result: str = format_number(1234.5678, 2)

        # Assert
        assert result == "1.234,57"

    def test_format_number_zero(self) -> None:
        """Zero deve ser formatado como '0,00'."""
        # Act
        result: str = format_number(0.0)

        # Assert
        assert result == "0,00"

    def test_format_number_large_without_decimals(self) -> None:
        """Números grandes sem casas decimais devem usar separadores."""
        # Act
        result: str = format_number(1000000, 0)

        # Assert
        assert result == "1.000.000"


class TestFormatPercentage:
    """Testes para formatação de percentuais."""

    def test_format_percentage_default(self) -> None:
        """73,5% com 1 casa decimal."""
        # Act
        result: str = format_percentage(0.735, 1)

        # Assert
        assert result == "73,5%"

    def test_format_percentage_whole(self) -> None:
        """100% sem casas decimais."""
        # Act
        result: str = format_percentage(1.0, 0)

        # Assert
        assert result == "100%"

    def test_format_percentage_zero(self) -> None:
        """0,0% com 1 casa decimal."""
        # Act
        result: str = format_percentage(0.0)

        # Assert
        assert result == "0,0%"


class TestFormatBytes:
    """Testes para formatação de bytes."""

    def test_format_bytes_kb(self) -> None:
        """1024 bytes deve ser formatado como 1,00 KB."""
        # Act
        result: str = format_bytes(1024)

        # Assert
        assert result == "1,00 KB"

    def test_format_bytes_mb(self) -> None:
        """1048576 bytes deve ser formatado como 1,00 MB."""
        # Act
        result: str = format_bytes(1048576)

        # Assert
        assert result == "1,00 MB"

    def test_format_bytes_below_kb(self) -> None:
        """500 bytes deve permanecer em B."""
        # Act
        result: str = format_bytes(500)

        # Assert
        assert result == "500 B"

    def test_format_bytes_gb(self) -> None:
        """1073741824 bytes deve ser formatado como 1,00 GB."""
        # Act
        result: str = format_bytes(1073741824)

        # Assert
        assert result == "1,00 GB"


class TestTruncateText:
    """Testes para truncamento de texto."""

    def test_truncate_long_text(self) -> None:
        """Texto maior que max_length deve ser truncado com sufixo."""
        # Act
        result: str = truncate_text("hello world", 5)

        # Assert
        assert result == "he..."

    def test_truncate_short_text(self) -> None:
        """Texto menor que max_length deve permanecer intacto."""
        # Act
        result: str = truncate_text("short", 100)

        # Assert
        assert result == "short"

    def test_truncate_replaces_newlines(self) -> None:
        """Quebras de linha devem ser substituídas por espaços."""
        # Act
        result: str = truncate_text("hello\nworld")

        # Assert
        assert result == "hello world"
