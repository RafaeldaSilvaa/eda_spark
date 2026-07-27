"""DTO da seção de insights."""
from __future__ import annotations

from dataclasses import dataclass

from spark_eda.utils.formatting import format_number


def _severity_color(severity: str) -> str:
    """Retorna a cor CSS para o nível de severidade informado."""
    return {
        "critical": "#dc2626",
        "high": "#d97706",
        "medium": "#eab308",
        "low": "#22c55e",
    }.get(severity, "#64748b")


def _severity_icon(severity: str) -> str:
    """Retorna um caractere de ícone para o nível de severidade."""
    return {
        "critical": "\u26a0\ufe0f",
        "high": "\u26a0\ufe0f",
        "medium": "\u2139\ufe0f",
        "low": "\u2139\ufe0f",
    }.get(severity, "\u2139\ufe0f")


def _severity_marker(severity: str) -> str:
    """Retorna um marcador textual para o nível de severidade."""
    return {
        "critical": "!!!",
        "high": "!!",
        "medium": "!",
        "low": "i",
    }.get(severity, "?")


def _column_tag(col: str | None) -> str:
    return f'<span style="font-size:11px;color:var(--muted,#64748b);">| {col}</span>' if col else ""


def _metric_tag(value: float | None) -> str:
    return f" <strong>{format_number(value)}</strong>" if value is not None else ""


@dataclass(frozen=True)
class InsightDTO:
    """Insight gerado durante a análise exploratória.

    Attributes:
        category: Categoria temática do insight.
        severity: Nível de severidade.
        column: Coluna associada, ou None se global.
        message: Descrição textual do insight.
        metric_value: Valor numérico que suporta o insight, ou None.
    """

    category: str
    severity: str
    column: str | None
    message: str
    metric_value: float | None


@dataclass(frozen=True)
class InsightsSection:
    """Seção de insights gerados durante a análise.

    Attributes:
        insights: Lista de insights encontrados.
    """

    insights: list[InsightDTO]

    def _repr_html_(self) -> str:
        """Renderiza insights como cards HTML ordenados por severidade."""
        if not self.insights:
            return '<div style="padding:12px;color:var(--muted,#64748b);font-size:13px;">No insights generated.</div>'

        severity_order: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_insights: list[InsightDTO] = sorted(
            self.insights,
            key=lambda i: (severity_order.get(i.severity, 9), i.message),
        )

        items: str = "".join(
            f'<div style="display:flex;gap:10px;padding:10px 14px;margin-bottom:6px;'
            f'background:var(--card-bg,#f8fafc);border-radius:8px;'
            f'border-left:3px solid {_severity_color(insight.severity)};'
            f'border-top:1px solid var(--border,#e2e8f0);border-right:1px solid var(--border,#e2e8f0);'
            f'border-bottom:1px solid var(--border,#e2e8f0);">'
            f'<span style="font-size:14px;line-height:1.4;flex-shrink:0;">{_severity_icon(insight.severity)}</span>'
            f'<div style="flex:1;">'
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">'
            f'<span style="font-size:11px;font-weight:600;color:{_severity_color(insight.severity)};'
            f'text-transform:uppercase;">{insight.category.replace("_", " ")}</span>'
            f'{_column_tag(insight.column)}'
            f'</div>'
            f'<div style="font-size:13px;color:var(--text,#1a1a2e);line-height:1.4;">{insight.message}'
            f'{_metric_tag(insight.metric_value)}'
            f"</div>"
            f"</div>"
            f"</div>"
            for insight in sorted_insights
        )
        return f'<div>{items}</div>'

    def __str__(self) -> str:
        """Renderiza insights como texto para terminal."""
        if not self.insights:
            return "Insights\n" + "-" * 20 + "\n  No insights generated."

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_insights = sorted(
            self.insights,
            key=lambda i: (severity_order.get(i.severity, 9), i.message),
        )

        lines: list[str] = ["Insights", "-" * 40]
        for insight in sorted_insights:
            marker: str = _severity_marker(insight.severity)
            col: str = f" [{insight.column}]" if insight.column else ""
            val: str = f" ({format_number(insight.metric_value)})" if insight.metric_value is not None else ""
            lines.append(f"  {marker} [{insight.category}] {col} {insight.message}{val}")

        return "\n".join(lines)
