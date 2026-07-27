"""DTO da seção de correlação."""
from __future__ import annotations

from dataclasses import dataclass

from spark_eda.utils.formatting import format_number

_CORR_NEGLIGIBLE: float = 0.1
_CORR_WEAK: float = 0.3
_CORR_LIGHT: float = 0.5
_CORR_MODERATE: float = 0.6
_CORR_STRONG: float = 0.7


@dataclass(frozen=True)
class CorrelationEntry:
    """Correlação entre um par de colunas.

    Attributes:
        column_a: Nome da primeira coluna.
        column_b: Nome da segunda coluna.
        method: Método de correlação utilizado.
        value: Valor da correlação.
    """

    column_a: str
    column_b: str
    method: str
    value: float


def _correlation_color(value: float) -> str:
    """Retorna uma cor CSS baseada na intensidade e direção da correlação."""
    abs_val: float = abs(value)
    if abs_val < _CORR_WEAK:
        return "#64748b"
    if abs_val < _CORR_MODERATE:
        return "#2563eb" if value > 0 else "#dc2626"
    return "#1d4ed8" if value > 0 else "#b91c1c"


def _correlation_symbol(value: float) -> str:
    """Retorna um símbolo de intensidade para a correlação."""
    abs_val: float = abs(value)
    if abs_val < _CORR_NEGLIGIBLE:
        return " "
    if abs_val < _CORR_WEAK:
        return "."
    if abs_val < _CORR_LIGHT:
        return "o"
    if abs_val < _CORR_STRONG:
        return "O"
    return "@"


@dataclass(frozen=True)
class CorrelationSection:
    """Seção de correlação entre colunas do dataset.

    Attributes:
        correlations: Lista de pares de colunas correlacionadas.
        matrix: Matriz de correlação como um dicionário aninhado.
        method: Método de correlação utilizado para gerar a matriz.
    """

    correlations: list[CorrelationEntry]
    matrix: dict[str, dict[str, float]]
    method: str

    def _repr_html_(self) -> str:
        """Renderiza a seção como uma matriz de correlação em HTML."""
        cols: list[str] = sorted(self.matrix.keys())
        if not cols:
            return '<div style="padding:12px;color:var(--muted,#64748b);font-size:13px;">No correlations.</div>'

        header_cells: str = "".join(
            f'<th style="padding:6px 4px;font-size:11px;text-align:center;'
            f'border-bottom:2px solid var(--border,#e2e8f0);'
            f'color:var(--muted,#64748b);writing-mode:vertical-lr;height:80px;'
            f'font-weight:400;">{c}</th>'
            for c in cols
        )
        header: str = (
            f'<thead><tr>'
            f'<th style="padding:6px 4px;font-size:11px;text-align:left;'
            f'border-bottom:2px solid var(--border,#e2e8f0);color:var(--muted,#64748b);font-weight:400;">'
            f'</th>{header_cells}</tr></thead>'
        )

        rows_html: str = ""
        for c1 in cols:
            cells: str = "".join(
                f'<td style="padding:6px 4px;text-align:center;font-size:12px;'
                f'font-weight:500;color:{_correlation_color(self.matrix.get(c1, {}).get(c2, 0.0))};'
                 f'background:color-mix(in srgb, '
                 f'{_correlation_color(self.matrix.get(c1, {}).get(c2, 0.0))} 10%, transparent);'
                f'border-bottom:1px solid var(--border,#e2e8f0);">'
                f'{format_number(self.matrix.get(c1, {}).get(c2, 0.0), 2)}</td>'
                for c2 in cols
            )
            rows_html += (
                f'<tr><td style="padding:6px 4px;font-size:12px;font-weight:500;'
                f'color:var(--text,#1a1a2e);border-bottom:1px solid var(--border,#e2e8f0);'
                f'white-space:nowrap;">{c1}</td>{cells}</tr>'
            )

        return (
            f'<div style="margin-bottom:12px;font-size:12px;color:var(--muted,#64748b);">'
            f'Method: {self.method}</div>'
            f'<div style="overflow-x:auto;"><table style="border-collapse:collapse;font-size:13px;">'
            f'{header}<tbody>{rows_html}</tbody></table></div>'
        )

    def __str__(self) -> str:
        """Renderiza a matriz de correlação como texto para terminal."""
        cols: list[str] = sorted(self.matrix.keys())
        if not cols:
            return "Correlations\n" + "-" * 20 + "\n  (empty)"

        col_width: int = max(len(c) for c in cols) + 2
        header: str = " " * col_width + "".join(c.rjust(col_width) for c in cols)
        lines: list[str] = [
            "Correlations",
            "-" * 40,
            f"  Method: {self.method}",
            "",
            "  " + header,
        ]
        for c1 in cols:
            row: str = c1.rjust(col_width)
            for c2 in cols:
                val: float = self.matrix.get(c1, {}).get(c2, 0.0)
                row += f"{format_number(val, 2):>{col_width}s}"
            lines.append("  " + row)

        return "\n".join(lines)
