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
                "<thead><tr>"
                '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Mean</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Std</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Min</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">P25</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">P50</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">P75</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Max</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Skew</th>'
                "</tr></thead>"
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
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">'
                f"{format_number(s.skewness)}</td>"
                f"</tr>"
                for s in self.numeric
            )
            html_parts.append(
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">Numeric</h4>'
                f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                f"{header}<tbody>{rows}</tbody></table></div>"
            )

        if self.categorical:
            header = (
                "<thead><tr>"
                '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Cardinality</th>'
                '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Mode</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Uniqueness</th>'
                '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Top</th>'
                "</tr></thead>"
            )
            rows = "".join(
                f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
                f'<td style="padding:6px 10px;font-weight:500;color:var(--text,#1a1a2e);">{s.column_name}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.cardinality}</td>'
                f'<td style="padding:6px 10px;color:var(--text,#1a1a2e);">{s.mode or "\u2014"}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">'
                f"{format_percentage(s.unique_ratio)}</td>"
                f'<td style="padding:6px 10px;color:var(--muted,#64748b);font-size:12px;">'
                f"{' | '.join(f'{v}: {c}' for v, c in s.top_values[:3])}</td>"
                f"</tr>"
                for s in self.categorical
            )
            html_parts.append(
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">Categorical</h4>'
                f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                f"{header}<tbody>{rows}</tbody></table></div>"
            )

        if self.temporal:
            header = (
                "<thead><tr>"
                '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Min</th>'
                '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Max</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Range</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Gaps</th>'
                "</tr></thead>"
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
                f"{header}<tbody>{rows}</tbody></table></div>"
            )

        if self.text:
            header = (
                "<thead><tr>"
                '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Min</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Max</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Avg</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Empty</th>'
                "</tr></thead>"
            )
            rows = "".join(
                f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
                f'<td style="padding:6px 10px;font-weight:500;color:var(--text,#1a1a2e);">{s.column_name}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.min_length}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.max_length}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">'
                f"{format_number(s.avg_length)}</td>"
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">'
                f"{format_percentage(s.empty_ratio)}</td>"
                f"</tr>"
                for s in self.text
            )
            html_parts.append(
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">Text</h4>'
                f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                f"{header}<tbody>{rows}</tbody></table></div>"
            )

        if self.boolean:
            header = (
                "<thead><tr>"
                '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">Column</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">True</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">False</th>'
                '<th style="text-align:right;padding:6px 10px;border-bottom:2px solid var(--border,#e2e8f0);'
                'font-size:11px;text-transform:uppercase;color:var(--muted,#64748b);">% True</th>'
                "</tr></thead>"
            )
            rows = "".join(
                f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
                f'<td style="padding:6px 10px;font-weight:500;color:var(--text,#1a1a2e);">{s.column_name}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.true_count}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">{s.false_count}</td>'
                f'<td style="padding:6px 10px;text-align:right;color:var(--text,#1a1a2e);">'
                f"{format_percentage(s.true_ratio)}</td>"
                f"</tr>"
                for s in self.boolean
            )
            html_parts.append(
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">Boolean</h4>'
                f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                f"{header}<tbody>{rows}</tbody></table></div>"
            )

        return "".join(html_parts) or (
            '<div style="padding:12px;color:var(--muted,#64748b);font-size:13px;">No statistics available.</div>'
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
            for cat in self.categorical:
                lines.append(
                    f"    {cat.column_name}: card={cat.cardinality}, "
                    f"mode={cat.mode or '\u2014'}, uniq={format_percentage(cat.unique_ratio)}"
                )

        if self.temporal:
            lines.append("  Temporal:")
            for tmp in self.temporal:
                lines.append(
                    f"    {tmp.column_name}: [{tmp.min_date} .. {tmp.max_date}], "
                    f"{tmp.range_days} days, {tmp.gap_count} gaps"
                )

        if self.text:
            lines.append("  Text:")
            for txt in self.text:
                lines.append(
                    f"    {txt.column_name}: len=[{txt.min_length} .. {txt.max_length}], "
                    f"avg={format_number(txt.avg_length)}, empty={format_percentage(txt.empty_ratio)}"
                )

        if self.boolean:
            lines.append("  Boolean:")
            for bln in self.boolean:
                lines.append(
                    f"    {bln.column_name}: true={bln.true_count}, false={bln.false_count}, "
                    f"ratio={format_percentage(bln.true_ratio)}"
                )

        return "\n".join(lines) if len(lines) > 1 else "Statistics\n" + "-" * 20 + "\n  (empty)"
