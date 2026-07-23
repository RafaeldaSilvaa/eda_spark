"""Funções utilitárias de formatação de valores para apresentação."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def format_number(
    value: int | float,
    decimal_places: int = 2,
) -> str:
    """Formata um número com separadores de milhar e casas decimais fixas.

    Args:
        value: Valor numérico a ser formatado.
        decimal_places: Quantidade de casas decimais (padrão: 2).

    Returns:
        String formatada (ex.: ``"1.234,57"``).
    """
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")

    rounded = float(Decimal(str(value)).quantize(Decimal(10) ** -decimal_places, rounding=ROUND_HALF_UP))
    integer_part, _, frac_part = f"{rounded:.{decimal_places}f}".partition(".")
    integer_part = f"{int(integer_part):,}".replace(",", ".")
    return f"{integer_part},{frac_part}"


def format_percentage(
    value: float,
    decimal_places: int = 1,
) -> str:
    """Formata um valor decimal como percentual.

    Args:
        value: Proporção no intervalo ``[0.0, 1.0]``.
        decimal_places: Quantidade de casas decimais (padrão: 1).

    Returns:
        String percentual (ex.: ``"73,5%"``).
    """
    pct = value * 100.0
    fmt = f"%0.{decimal_places}f"
    return f"{fmt % pct}%".replace(".", "," if decimal_places > 0 else ".")


def format_bytes(bytes_: int) -> str:
    """Formata um valor em bytes para uma representação legível.

    Args:
        bytes_: Quantidade de bytes.

    Returns:
        String com unidade adequada (ex.: ``"2,5 MB"``).
    """
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    size = float(bytes_)
    unit_idx = 0
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024.0
        unit_idx += 1
    if unit_idx == 0:
        return f"{int(size)} {units[unit_idx]}"
    return f"{size:.2f} {units[unit_idx]}".replace(".", ",")


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = "...",
) -> str:
    """Trunca um texto no comprimento máximo, adicionando sufixo se truncado.

    Args:
        text: Texto original.
        max_length: Comprimento máximo em caracteres (padrão: 100).
        suffix: Sufixo adicionado quando o texto é truncado (padrão: ``"..."``).

    Returns:
        Texto truncado com sufixo, ou o texto original se dentro do limite.
    """
    text = text.replace("\n", " ").replace("\r", " ")
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)].rstrip() + suffix
