"""DTO da seção de recomendações."""
from __future__ import annotations

from dataclasses import dataclass

_PRIORITY_CRITICAL: int = 1
_PRIORITY_HIGH: int = 2
_PRIORITY_MEDIUM: int = 3
_PRIORITY_LOW: int = 4


def _priority_color(priority: int) -> str:
    """Retorna a cor CSS para o nível de prioridade."""
    if priority <= _PRIORITY_CRITICAL:
        return "#dc2626"
    if priority <= _PRIORITY_HIGH:
        return "#d97706"
    if priority <= _PRIORITY_MEDIUM:
        return "#eab308"
    if priority <= _PRIORITY_LOW:
        return "#22c55e"
    return "#64748b"


def _priority_label(priority: int) -> str:
    """Retorna o rótulo textual para o nível de prioridade."""
    if priority <= _PRIORITY_CRITICAL:
        return "Critical"
    if priority <= _PRIORITY_HIGH:
        return "High"
    if priority <= _PRIORITY_MEDIUM:
        return "Medium"
    if priority <= _PRIORITY_LOW:
        return "Low"
    return "Informational"


def _priority_marker(priority: int) -> str:
    """Retorna o marcador para exibição no terminal."""
    if priority <= _PRIORITY_CRITICAL:
        return "!!!"
    if priority <= _PRIORITY_HIGH:
        return "!!"
    if priority <= _PRIORITY_MEDIUM:
        return "! "
    return "  "


def _column_tag(col: str | None) -> str:
    return f'<span style="font-size:11px;color:var(--muted,#64748b);">| {col}</span>' if col else ""


@dataclass(frozen=True)
class RecommendationDTO:
    """Recomendação de ação gerada a partir da análise.

    Attributes:
        category: Categoria temática da recomendação.
        priority: Prioridade de 1 (mais urgente) a 5 (menos urgente).
        column: Coluna associada, ou None se global.
        message: Descrição do problema identificado.
        action: Ação recomendada para resolver o problema.
    """

    category: str
    priority: int
    column: str | None
    message: str
    action: str


@dataclass(frozen=True)
class RecommendationsSection:
    """Seção de recomendações de ação priorizadas.

    Attributes:
        recommendations: Lista de recomendações ordenadas por prioridade.
    """

    recommendations: list[RecommendationDTO]

    def _repr_html_(self) -> str:
        """Renderiza recomendações como cards HTML ordenados por prioridade."""
        if not self.recommendations:
            return '<div style="padding:12px;color:var(--muted,#64748b);font-size:13px;">No recommendations.</div>'

        sorted_recs: list[RecommendationDTO] = sorted(self.recommendations, key=lambda r: r.priority)
        items: str = "".join(
            f'<div style="display:flex;gap:12px;padding:12px 14px;margin-bottom:8px;'
            f'background:var(--card-bg,#f8fafc);border-radius:8px;'
            f'border:1px solid var(--border,#e2e8f0);">'
            f'<div style="flex-shrink:0;">'
            f'<span style="display:inline-block;padding:3px 10px;border-radius:10px;font-size:11px;font-weight:700;'
            f'color:white;background:{_priority_color(rec.priority)};">'
            f'P{rec.priority}</span>'
            f"</div>"
            f'<div style="flex:1;">'
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;flex-wrap:wrap;">'
            f'<span style="font-size:11px;font-weight:600;color:var(--muted,#64748b);'
            f'text-transform:uppercase;">{rec.category.replace("_", " ")}</span>'
            f'{_column_tag(rec.column)}'
            f'</div>'
            f'<div style="font-size:13px;color:var(--text,#1a1a2e);font-weight:500;margin-bottom:4px;">'
            f'{rec.message}</div>'
            f'<div style="font-size:12px;color:var(--muted,#64748b);line-height:1.4;">'
            f'\u2192 {rec.action}</div>'
            f"</div>"
            f"</div>"
            for rec in sorted_recs
        )
        return f'<div>{items}</div>'

    def __str__(self) -> str:
        """Renderiza recomendações como texto para terminal."""
        if not self.recommendations:
            return "Recommendations\n" + "-" * 20 + "\n  No recommendations."

        sorted_recs = sorted(self.recommendations, key=lambda r: r.priority)
        lines: list[str] = ["Recommendations", "-" * 40]
        for rec in sorted_recs:
            marker: str = _priority_marker(rec.priority)
            col: str = f" [{rec.column}]" if rec.column else ""
            lines.append(f"  {marker} P{rec.priority} [{rec.category}]{col}")
            lines.append(f"      {rec.message}")
            lines.append(f"      \u2192 {rec.action}")
            lines.append("")

        return "\n".join(lines)
