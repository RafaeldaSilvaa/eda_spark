"""DTO da seção de outliers."""
from __future__ import annotations

from dataclasses import dataclass

from spark_eda.utils.formatting import format_number, format_percentage


def _outlier_severity(ratio: float) -> str:
    """Classifica a severidade do outlier com base na proporção."""
    if ratio >= 0.10:
        return "critical"
    if ratio >= 0.05:
        return "high"
    if ratio >= 0.01:
        return "medium"
    return "low"


def _severity_color(severity: str) -> str:
    """Retorna a cor CSS para o nível de severidade."""
    return {
        "critical": "#dc2626",
        "high": "#d97706",
        "medium": "#eab308",
        "low": "#22c55e",
    }.get(severity, "#64748b")


def _severity_emoji(severity: str) -> str:
    """Retorna um marcador textual para o nível de severidade."""
    return {
        "critical": "!!",
        "high": "! ",
        "medium": "- ",
        "low": "  ",
    }.get(severity, "? ")


@dataclass(frozen=True)
class OutlierSummary:
    """Resumo de outliers para uma coluna.

    Attributes:
        column_name: Nome da coluna.
        method: Método de detecção utilizado.
        count: Número de valores identificados como outliers.
        ratio: Proporção de outliers em relação ao total.
        bounds_lower: Limite inferior para outlier, ou None.
        bounds_upper: Limite superior para outlier, ou None.
    """

    column_name: str
    method: str
    count: int
    ratio: float
    bounds_lower: float | None
    bounds_upper: float | None


@dataclass(frozen=True)
class OutlierSection:
    """Seção de detecção de outliers por coluna.

    Attributes:
        outliers: Lista de resumos de outliers por coluna.
    """

    outliers: list[OutlierSummary]

    def _repr_html_(self) -> str:
        """Renderiza a seção de outliers como uma tabela HTML."""
        if not self.outliers:
            return '<div style="padding:12px;color:var(--muted,#64748b);font-size:13px;">No outliers detected.</div>'

        header: str = (
            f'<thead><tr>'
            f'<th style="text-align:left;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
            f'<th style="text-align:left;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Method</th>'
            f'<th style="text-align:right;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Outliers</th>'
            f'<th style="text-align:right;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Ratio</th>'
            f'<th style="text-align:center;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Severity</th>'
            f'<th style="text-align:left;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Bounds</th>'
            f'</tr></thead>'
        )
        rows: str = "".join(
            f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
            f'<td style="padding:8px 12px;font-weight:500;color:var(--text,#1a1a2e);">{s.column_name}</td>'
            f'<td style="padding:8px 12px;color:var(--primary,#2563eb);">{s.method}</td>'
            f'<td style="padding:8px 12px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.count)}</td>'
            f'<td style="padding:8px 12px;text-align:right;color:var(--text,#1a1a2e);">{format_percentage(s.ratio)}</td>'
            f'<td style="padding:8px 12px;text-align:center;">'
            f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;'
            f'color:white;background:{_severity_color(_outlier_severity(s.ratio))};">'
            f'{_outlier_severity(s.ratio).title()}</span></td>'
            f'<td style="padding:8px 12px;font-size:12px;color:var(--muted,#64748b);">'
            f'[{format_number(s.bounds_lower) if s.bounds_lower is not None else "\u2014"} .. '
            f'{format_number(s.bounds_upper) if s.bounds_upper is not None else "\u2014"}]</td>'
            f"</tr>"
            for s in self.outliers
        )
        return (
            f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
            f'{header}<tbody>{rows}</tbody></table></div>'
        )

    def __str__(self) -> str:
        """Renderiza a seção de outliers como texto para terminal."""
        if not self.outliers:
            return "Outliers\n" + "-" * 20 + "\n  No outliers detected."

        lines: list[str] = ["Outliers", "-" * 40]
        for s in self.outliers:
            sev: str = _severity_emoji(_outlier_severity(s.ratio))
            bounds: str = (
                f"[{format_number(s.bounds_lower)} .. {format_number(s.bounds_upper)}]"
                if s.bounds_lower is not None or s.bounds_upper is not None
                else "\u2014"
            )
            lines.append(
                f"  {sev} {s.column_name}: {format_number(s.count)} ({format_percentage(s.ratio)}) "
                f"method={s.method} bounds={bounds}"
            )

        return "\n".join(lines)
