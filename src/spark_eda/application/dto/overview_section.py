"""DTO da seção de visão geral do dataset."""
from __future__ import annotations

from dataclasses import dataclass

from spark_eda.utils.formatting import format_bytes, format_number, format_percentage


@dataclass(frozen=True)
class OverviewSection:
    """Visão geral do dataset analisado.

    Attributes:
        row_count: Número total de linhas (registros).
        column_count: Número total de colunas.
        duplicate_count: Número de linhas duplicadas.
        duplicate_ratio: Proporção de linhas duplicadas em relação ao total.
        missing_ratio: Proporção de valores ausentes em relação ao total de células.
        size_estimate: Tamanho estimado do dataset em bytes.
    """

    row_count: int
    column_count: int
    duplicate_count: int
    duplicate_ratio: float
    missing_ratio: float
    size_estimate: int

    def _repr_html_(self) -> str:
        """Renderiza a visão geral como cards HTML com estilos inline."""
        cards: list[tuple[str, str]] = [
            ("Rows", format_number(self.row_count)),
            ("Columns", format_number(self.column_count)),
            ("Duplicates", f"{format_number(self.duplicate_count)} ({format_percentage(self.duplicate_ratio)})"),
            ("Missing", format_percentage(self.missing_ratio)),
            ("Est. Size", format_bytes(self.size_estimate)),
        ]
        items_html: str = "".join(
            f'<div style="flex:1;min-width:140px;padding:16px;background:var(--card-bg,#f8fafc);'
            f'border-radius:8px;border:1px solid var(--border,#e2e8f0);text-align:center;">'
            f'<div style="font-size:12px;color:var(--muted,#64748b);text-transform:uppercase;'
            f'letter-spacing:0.5px;margin-bottom:4px;">{label}</div>'
            f'<div style="font-size:20px;font-weight:600;color:var(--text,#1a1a2e);">{value}</div>'
            f"</div>"
            for label, value in cards
        )
        return (
            f'<div style="display:flex;flex-wrap:wrap;gap:12px;padding:16px 0;">{items_html}</div>'
        )

    def __str__(self) -> str:
        """Renderiza a visão geral como texto formatado para terminal."""
        lines: list[str] = [
            f"  {'Rows':20s} {format_number(self.row_count):>15s}",
            f"  {'Columns':20s} {format_number(self.column_count):>15s}",
            f"  {'Duplicates':20s} {format_number(self.duplicate_count):>10s} ({format_percentage(self.duplicate_ratio)})",
            f"  {'Missing':20s} {format_percentage(self.missing_ratio):>15s}",
            f"  {'Est. Size':20s} {format_bytes(self.size_estimate):>15s}",
        ]
        return "Overview\n" + "-" * 40 + "\n" + "\n".join(lines)
