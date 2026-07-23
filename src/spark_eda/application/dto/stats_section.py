"""DTO da seção de estatísticas descritivas agrupadas por tipo de coluna."""
from __future__ import annotations

from dataclasses import dataclass

from spark_eda.utils.formatting import format_number, format_percentage


@dataclass(frozen=True)
class NumericStatsDTO:
    """Estatísticas descritivas para uma coluna numérica.

    Attributes:
        column_name: Nome da coluna.
        mean: Média aritmética.
        std: Desvio padrão.
        min: Valor mínimo.
        q25: Primeiro quartil (percentil 25).
        q50: Mediana (percentil 50).
        q75: Terceiro quartil (percentil 75).
        max: Valor máximo.
        skewness: Assimetria da distribuição.
        kurtosis: Curtose da distribuição.
    """

    column_name: str
    mean: float
    std: float
    min: float
    q25: float
    q50: float
    q75: float
    max: float
    skewness: float
    kurtosis: float


@dataclass(frozen=True)
class CategoricalStatsDTO:
    """Estatísticas descritivas para uma coluna categórica.

    Attributes:
        column_name: Nome da coluna.
        cardinality: Número de valores distintos.
        mode: Valor mais frequente, ou None.
        unique_ratio: Proporção de valores únicos em relação ao total.
        top_values: Lista dos valores mais frequentes com suas contagens.
    """

    column_name: str
    cardinality: int
    mode: str | None
    unique_ratio: float
    top_values: list[tuple[str, int]]


@dataclass(frozen=True)
class TemporalStatsDTO:
    """Estatísticas descritivas para uma coluna temporal.

    Attributes:
        column_name: Nome da coluna.
        min_date: Data mais antiga (formato ISO).
        max_date: Data mais recente (formato ISO).
        range_days: Amplitude em dias.
        gap_count: Número de lacunas temporais.
    """

    column_name: str
    min_date: str
    max_date: str
    range_days: int
    gap_count: int


@dataclass(frozen=True)
class TextStatsDTO:
    """Estatísticas descritivas para uma coluna de texto.

    Attributes:
        column_name: Nome da coluna.
        min_length: Comprimento mínimo observado.
        max_length: Comprimento máximo observado.
        avg_length: Comprimento médio.
        empty_ratio: Proporção de valores vazios.
    """

    column_name: str
    min_length: int
    max_length: int
    avg_length: float
    empty_ratio: float


@dataclass(frozen=True)
class BooleanStatsDTO:
    """Estatísticas descritivas para uma coluna booleana.

    Attributes:
        column_name: Nome da coluna.
        true_count: Número de valores verdadeiros.
        false_count: Número de valores falsos.
        true_ratio: Proporção de valores verdadeiros.
    """

    column_name: str
    true_count: int
    false_count: int
    true_ratio: float


@dataclass(frozen=True)
class StatsSection:
    """Seção de estatísticas descritivas agrupadas por tipo de coluna.

    Attributes:
        numeric: Lista de estatísticas de colunas numéricas.
        categorical: Lista de estatísticas de colunas categóricas.
        temporal: Lista de estatísticas de colunas temporais.
        text: Lista de estatísticas de colunas de texto.
        boolean: Lista de estatísticas de colunas booleanas.
    """

    numeric: list[NumericStatsDTO]
    categorical: list[CategoricalStatsDTO]
    temporal: list[TemporalStatsDTO]
    text: list[TextStatsDTO]
    boolean: list[BooleanStatsDTO]

    def _repr_html_(self) -> str:
        """Renderiza estatísticas como tabelas HTML separadas por tipo."""
        html_parts: list[str] = []

        if self.numeric:
            header: str = (
                f'<thead><tr>'
                f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Mean</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Std</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Min</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">P25</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">P50</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">P75</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Max</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Skew</th>'
                f'</tr></thead>'
            )
            rows: str = "".join(
                f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
                f'<td style="padding:6px 10px;font-weight:500;color:var(--text,#1a1a2e);">{s.column_name}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.mean)}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.std)}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.min)}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.q25)}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.q50)}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.q75)}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.max)}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.skewness)}</td>'
                f"</tr>"
                for s in self.numeric
            )
            html_parts.append(
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">Numeric</h4>'
                f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                f'{header}<tbody>{rows}</tbody></table></div>'
            )

        if self.categorical:
            header = (
                f'<thead><tr>'
                f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Cardinality</th>'
                f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Mode</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Uniqueness</th>'
                f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Top</th>'
                f'</tr></thead>'
            )
            rows = "".join(
                f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
                f'<td style="padding:6px 10px;font-weight:500;color:var(--text,#1a1a2e);">{s.column_name}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.cardinality}</td>'
                f'<td style="padding:6px 10px;color:var(--text,#1a1a2e);">{s.mode or "\u2014"}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_percentage(s.unique_ratio)}</td>'
                f'<td style="padding:6px 10px;color:var(--muted,#64748b);font-size:12px;">'
                f'{" | ".join(f"{v}: {c}" for v, c in s.top_values[:3])}</td>'
                f"</tr>"
                for s in self.categorical
            )
            html_parts.append(
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">Categorical</h4>'
                f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                f'{header}<tbody>{rows}</tbody></table></div>'
            )

        if self.temporal:
            header = (
                f'<thead><tr>'
                f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Min</th>'
                f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Max</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Range</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Gaps</th>'
                f'</tr></thead>'
            )
            rows = "".join(
                f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
                f'<td style="padding:6px 10px;font-weight:500;color:var(--text,#1a1a2e);">{s.column_name}</td>'
                f'<td style="padding:6px 10px;color:var(--text,#1a1a2e);">{s.min_date}</td>'
                f'<td style="padding:6px 10px;color:var(--text,#1a1a2e);">{s.max_date}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.range_days} days</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.gap_count}</td>'
                f"</tr>"
                for s in self.temporal
            )
            html_parts.append(
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">Temporal</h4>'
                f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                f'{header}<tbody>{rows}</tbody></table></div>'
            )

        if self.text:
            header = (
                f'<thead><tr>'
                f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Min</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Max</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Avg</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Empty</th>'
                f'</tr></thead>'
            )
            rows = "".join(
                f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
                f'<td style="padding:6px 10px;font-weight:500;color:var(--text,#1a1a2e);">{s.column_name}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.min_length}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.max_length}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_number(s.avg_length)}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_percentage(s.empty_ratio)}</td>'
                f"</tr>"
                for s in self.text
            )
            html_parts.append(
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">Text</h4>'
                f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                f'{header}<tbody>{rows}</tbody></table></div>'
            )

        if self.boolean:
            header = (
                f'<thead><tr>'
                f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">True</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">False</th>'
                f'<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                f'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">% True</th>'
                f'</tr></thead>'
            )
            rows = "".join(
                f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
                f'<td style="padding:6px 10px;font-weight:500;color:var(--text,#1a1a2e);">{s.column_name}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.true_count}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.false_count}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{format_percentage(s.true_ratio)}</td>'
                f"</tr>"
                for s in self.boolean
            )
            html_parts.append(
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">Boolean</h4>'
                f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                f'{header}<tbody>{rows}</tbody></table></div>'
            )

        return "".join(html_parts) or (
            '<div style="padding:12px;color:var(--muted,#64748b);font-size:13px;">'
            "No statistics available.</div>"
        )

    def __str__(self) -> str:
        """Renderiza estatísticas como texto formatado para terminal."""
        lines: list[str] = ["Statistics", "-" * 40]

        if self.numeric:
            lines.append("  Numeric:")
            for s in self.numeric:
                lines.append(
                    f"    {s.column_name}: mean={format_number(s.mean)}, "
                    f"std={format_number(s.std)}, "
                    f"[{format_number(s.min)} .. {format_number(s.max)}]"
                )

        if self.categorical:
            lines.append("  Categorical:")
            for s in self.categorical:
                lines.append(
                    f"    {s.column_name}: card={s.cardinality}, "
                    f"mode={s.mode or '\u2014'}, uniq={format_percentage(s.unique_ratio)}"
                )

        if self.temporal:
            lines.append("  Temporal:")
            for s in self.temporal:
                lines.append(
                    f"    {s.column_name}: [{s.min_date} .. {s.max_date}], "
                    f"{s.range_days} days, {s.gap_count} gaps"
                )

        if self.text:
            lines.append("  Text:")
            for s in self.text:
                lines.append(
                    f"    {s.column_name}: len=[{s.min_length} .. {s.max_length}], "
                    f"avg={format_number(s.avg_length)}, empty={format_percentage(s.empty_ratio)}"
                )

        if self.boolean:
            lines.append("  Boolean:")
            for s in self.boolean:
                lines.append(
                    f"    {s.column_name}: true={s.true_count}, false={s.false_count}, "
                    f"ratio={format_percentage(s.true_ratio)}"
                )

        return "\n".join(lines) if len(lines) > 1 else "Statistics\n" + "-" * 20 + "\n  (empty)"
