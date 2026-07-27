"""DTO da seção de distribuição."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.utils.formatting import format_number


@dataclass(frozen=True)
class HistogramBin:
    """Um único intervalo (bin) de um histograma.

    Attributes:
        lower: Limite inferior do bin.
        upper: Limite superior do bin.
        count: Contagem de valores neste bin.
    """

    lower: float
    upper: float
    count: int


@dataclass(frozen=True)
class FrequencyEntry:
    """Uma entrada de frequência para dados categóricos.

    Attributes:
        label: Rótulo da categoria.
        count: Contagem de ocorrências.
    """

    label: str
    count: int


@dataclass(frozen=True)
class TemporalPoint:
    """Um ponto em uma série temporal agregada.

    Attributes:
        period: Rótulo do período (ex.: ``"2024-01"``).
        count: Contagem de ocorrências no período.
    """

    period: str
    count: int


@dataclass(frozen=True)
class DistributionSection:
    """Distribuições de valores por tipo de coluna.

    Attributes:
        histograms: Mapeamento de nome de coluna para lista de bins do histograma.
        frequencies: Mapeamento de nome de coluna para lista de frequências categóricas.
        temporal_charts: Mapeamento de nome de coluna para lista de pontos temporais.
    """

    histograms: dict[str, list[HistogramBin]]
    frequencies: dict[str, list[FrequencyEntry]]
    temporal_charts: dict[str, list[TemporalPoint]]

    def _repr_html_(self) -> str:
        """Renderiza distribuições como gráficos HTML baseados em div."""
        parts: list[str] = []

        for col_name, bins in self.histograms.items():
            if not bins:
                continue
            max_count: int = max(b.count for b in bins)
            bars: str = "".join(
                f'<div style="display:flex;align-items:center;margin-bottom:2px;font-size:11px;">'
                f'<span style="width:100px;text-align:right;padding-right:8px;'
                f'color:var(--muted,#64748b);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
                f"{format_number(b.lower)}</span>"
                f'<div style="height:16px;width:{(b.count / max_count) * 100 if max_count else 0:.1f}%;'
                f'background:var(--primary,#2563eb);border-radius:2px;min-width:2px;"></div>'
                f'<span style="padding-left:6px;color:var(--text,#1a1a2e);">{b.count}</span>'
                f"</div>"
                for b in bins
            )
            parts.append(
                f'<div style="margin-bottom:16px;">'
                f'<h4 style="margin:0 0 8px;font-size:13px;color:var(--text,#1a1a2e);">{col_name}</h4>'
                f"{bars}"
                f"</div>"
            )

        for col_name, entries in self.frequencies.items():
            if not entries:
                continue
            max_count = max(e.count for e in entries)
            bars = "".join(
                f'<div style="display:flex;align-items:center;margin-bottom:2px;font-size:11px;">'
                f'<span style="width:140px;text-align:right;padding-right:8px;'
                f'color:var(--muted,#64748b);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
                f"{e.label}</span>"
                f'<div style="height:16px;width:{(e.count / max_count) * 100 if max_count else 0:.1f}%;'
                f'background:var(--success,#16a34a);border-radius:2px;min-width:2px;"></div>'
                f'<span style="padding-left:6px;color:var(--text,#1a1a2e);">{format_number(e.count)}</span>'
                f"</div>"
                for e in entries
            )
            parts.append(
                f'<div style="margin-bottom:16px;">'
                f'<h4 style="margin:0 0 8px;font-size:13px;color:var(--text,#1a1a2e);">{col_name}</h4>'
                f"{bars}"
                f"</div>"
            )

        for col_name, points in self.temporal_charts.items():
            if not points:
                continue
            max_count = max(p.count for p in points)
            bars = "".join(
                f'<div style="display:flex;align-items:center;margin-bottom:2px;font-size:11px;">'
                f'<span style="width:100px;text-align:right;padding-right:8px;'
                f'color:var(--muted,#64748b);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
                f"{p.period}</span>"
                f'<div style="height:16px;width:{(p.count / max_count) * 100 if max_count else 0:.1f}%;'
                f'background:var(--warning,#d97706);border-radius:2px;min-width:2px;"></div>'
                f'<span style="padding-left:6px;color:var(--text,#1a1a2e);">{format_number(p.count)}</span>'
                f"</div>"
                for p in points
            )
            parts.append(
                f'<div style="margin-bottom:16px;">'
                f'<h4 style="margin:0 0 8px;font-size:13px;color:var(--text,#1a1a2e);">{col_name}</h4>'
                f"{bars}"
                f"</div>"
            )

        return "".join(parts) or (
            '<div style="padding:12px;color:var(--muted,#64748b);font-size:13px;">No distributions available.</div>'
        )

    def __str__(self) -> str:
        """Renderiza distribuições como gráficos ASCII para terminal."""
        lines: list[str] = ["Distributions", "-" * 40]

        bar_char: str = "#"

        for col_name, bins in self.histograms.items():
            if not bins:
                continue
            lines.append(f"  {col_name} (histogram):")
            max_count = max(b.count for b in bins)
            for b in bins:
                bar_len: int = int((b.count / max_count) * 20) if max_count else 0
                bar: str = bar_char * bar_len
                lines.append(f"    {format_number(b.lower):>10s} |{bar:<20s} {b.count}")

        for col_name, entries in self.frequencies.items():
            if not entries:
                continue
            lines.append(f"  {col_name} (frequencies):")
            max_count = max(e.count for e in entries)
            for e in entries:
                bar_len = int((e.count / max_count) * 20) if max_count else 0
                bar = bar_char * bar_len
                lines.append(f"    {_truncate_text(e.label, 20):>20s} |{bar:<20s} {e.count}")

        for col_name, points in self.temporal_charts.items():
            if not points:
                continue
            lines.append(f"  {col_name} (temporal):")
            max_count = max(p.count for p in points)
            for p in points:
                bar_len = int((p.count / max_count) * 20) if max_count else 0
                bar = bar_char * bar_len
                lines.append(f"    {p.period:>12s} |{bar:<20s} {p.count}")

        return "\n".join(lines)


def _truncate_text(text: str, max_len: int) -> str:
    """Trunca texto para exibição no terminal."""
    return text if len(text) <= max_len else text[: max_len - 3] + "..."
