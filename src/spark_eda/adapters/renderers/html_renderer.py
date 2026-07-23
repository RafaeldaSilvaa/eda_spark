"""Renderizador HTML para relatórios spark_eda."""

from __future__ import annotations

from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.quality_section import QualityFactorReport, QualityReport
from spark_eda.utils.formatting import format_number, format_percentage


def _severity_color(severity: str) -> str:
    """Retorna a cor CSS para o nível de severidade."""
    return {
        "critical": "#dc2626",
        "high": "#d97706",
        "medium": "#eab308",
        "low": "#22c55e",
    }.get(severity, "#64748b")

_INLINE_CSS: str = """
:root {
    --bg: #ffffff;
    --text: #1a1a2e;
    --muted: #64748b;
    --border: #e2e8f0;
    --primary: #2563eb;
    --success: #16a34a;
    --warning: #d97706;
    --danger: #dc2626;
    --card-bg: #f8fafc;
    --section-bg: #ffffff;
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg: #0f172a;
        --text: #e2e8f0;
        --muted: #94a3b8;
        --border: #334155;
        --primary: #60a5fa;
        --success: #4ade80;
        --warning: #fbbf24;
        --danger: #f87171;
        --card-bg: #1e293b;
        --section-bg: #1e293b;
    }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    padding: 24px;
}
h1 { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
h2 {
    font-size: 18px; font-weight: 600; margin: 24px 0 12px;
    padding-bottom: 8px; border-bottom: 2px solid var(--border);
}
h3 { font-size: 15px; font-weight: 600; margin: 16px 0 8px; }
.section {
    background: var(--section-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
}
.section-title {
    font-size: 16px; font-weight: 600; margin-bottom: 12px;
    color: var(--primary);
}
.footer {
    text-align: center; font-size: 11px; color: var(--muted);
    margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);
}
"""


class HTMLRenderer:
    """Renderizador de relatórios em HTML com estilos inline.

    Gera documentos HTML completos e autocontidos sem
    dependências externas de CSS ou JavaScript.
    """

    @staticmethod
    def render_report(eda_report: EDAReport) -> str:
        """Renderiza o relatório completo como uma página HTML.

        Args:
            eda_report: Relatório de análise exploratória.

        Returns:
            String HTML completa com estilos inline.
        """
        sections: list[str] = [
            HTMLRenderer._wrap_section("Overview", eda_report.overview._repr_html_()),
            HTMLRenderer._wrap_section("Schema", eda_report.schema._repr_html_()),
            HTMLRenderer._wrap_section("Quality", HTMLRenderer.render_quality_report(eda_report.quality)),
            HTMLRenderer._wrap_section("Statistics", eda_report.stats._repr_html_()),
            HTMLRenderer._wrap_section(
                "Distributions", eda_report.distributions._repr_html_()
            ),
            HTMLRenderer._wrap_section(
                "Correlations", eda_report.correlations._repr_html_()
            ),
            HTMLRenderer._wrap_section("Outliers", eda_report.outliers._repr_html_()),
            HTMLRenderer._wrap_section("Insights", eda_report.insights._repr_html_()),
            HTMLRenderer._wrap_section(
                "Recommendations", eda_report.recommendations._repr_html_()
            ),
        ]
        sections_html: str = "".join(sections)
        return HTMLRenderer._document(sections_html)

    @staticmethod
    def render_quality(quality_report: QualityReport) -> str:
        """Renderiza o relatório de qualidade como uma página HTML.

        Args:
            quality_report: Relatório de qualidade dos dados.

        Returns:
            String HTML completa.
        """
        content: str = HTMLRenderer._wrap_section(
            "Data Quality", HTMLRenderer.render_quality_report(quality_report)
        )
        return HTMLRenderer._document(content)

    @staticmethod
    def render_quality_report(quality: QualityReport) -> str:
        """Renderiza o relatório de qualidade como um fragmento HTML com gauge visual.

        Args:
            quality: Relatório de qualidade dos dados.

        Returns:
            String com fragmento HTML.
        """
        gauge_value: float = max(0.0, min(100.0, quality.overall))
        gauge_deg: float = (gauge_value / 100.0) * 180.0
        gauge_color: str = (
            "#dc2626" if gauge_value < 40
            else "#d97706" if gauge_value < 70
            else "#16a34a"
        )
        gauge_svg: str = (
            f'<svg width="160" height="90" viewBox="0 0 160 90" style="display:block;margin:0 auto;">'
            f'<path d="M 15 85 A 65 65 0 0 1 145 85" fill="none" stroke="#e2e8f0" stroke-width="12" stroke-linecap="round"/>'
            f'<path d="M 15 85 A 65 65 0 0 1 145 85" fill="none" stroke="{gauge_color}" '
            f'stroke-width="12" stroke-dasharray="{gauge_deg / 180.0 * 204.0} 204" stroke-linecap="round"/>'
            f'<text x="80" y="55" text-anchor="middle" font-size="28" font-weight="700" '
            f'fill="var(--text,#1a1a2e)">{format_number(gauge_value, 1)}</text>'
            f'<text x="80" y="75" text-anchor="middle" font-size="10" fill="var(--muted,#64748b)">'
            f'QUALITY</text>'
            f'</svg>'
        )

        dims_html: str = "".join(
            f'<div style="margin-bottom:12px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;'
            f'font-size:13px;color:var(--text,#1a1a2e);">'
            f'<span style="font-weight:500;">{dim.name.title()}</span>'
            f'<span>{format_number(dim.score, 1)}</span>'
            f"</div>"
            f'<div style="height:6px;background:var(--border,#e2e8f0);border-radius:3px;overflow:hidden;">'
            f'<div style="height:100%;width:{dim.score}%;background:{gauge_color if dim.score < 70 else "#16a34a"};'
            f'border-radius:3px;transition:width 0.3s;"></div>'
            f"</div>"
            f"</div>"
            for dim in quality.dimensions
        )

        penalizers_html: str = ""
        if quality.top_penalizers:
            items: str = "".join(
                f'<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;'
                f'background:var(--card-bg,#f8fafc);border-radius:6px;'
                f'border:1px solid var(--border,#e2e8f0);margin-bottom:6px;">'
                f'<span style="width:8px;height:8px;border-radius:50%;'
                f'background:{_severity_color(f.severity)};flex-shrink:0;"></span>'
                f'<span style="font-size:13px;color:var(--text,#1a1a2e);flex:1;">{f.reason}</span>'
                f'<span style="font-size:12px;font-weight:600;color:{_severity_color(f.severity)};">'
                f'{format_percentage(1.0 - f.score)}</span>'
                f"</div>"
                for f in quality.top_penalizers
            )
            penalizers_html = (
                f'<h4 style="margin:16px 0 8px;font-size:14px;color:var(--text,#1a1a2e);">'
                f'Top Penalizers</h4>{items}'
            )

        return (
            f'<div style="padding:8px 0;">'
            f'{gauge_svg}'
            f'<div style="margin-top:16px;">{dims_html}</div>'
            f'{penalizers_html}'
            f"</div>"
        )

    @staticmethod
    def render_section(section: object) -> str:
        """Renderiza uma seção individual do relatório como HTML.

        Args:
            section: Qualquer DTO de seção com método ``_repr_html_``.

        Returns:
            Fragmento HTML da seção.
        """
        if hasattr(section, "_repr_html_"):
            return section._repr_html_()
        return f"<div>{section!r}</div>"

    @staticmethod
    def _wrap_section(title: str, content_html: str) -> str:
        """Encapsula um fragmento HTML em um bloco de seção.

        Args:
            title: Título da seção.
            content_html: HTML do conteúdo da seção.

        Returns:
            HTML completo da seção.
        """
        return (
            f'<div class="section">'
            f'<div class="section-title">{title}</div>'
            f"{content_html}</div>"
        )

    @staticmethod
    def _document(body_html: str) -> str:
        """Constrói o documento HTML completo com head e body.

        Args:
            body_html: Conteúdo HTML do body.

        Returns:
            Documento HTML completo.
        """
        return (
            "<!DOCTYPE html>"
            '<html lang="en">'
            "<head>"
            '<meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            f"<style>{_INLINE_CSS}</style>"
            "<title>spark_eda Report</title>"
            "</head>"
            "<body>"
            "<h1>Exploratory Data Analysis Report</h1>"
            f'<p style="color:var(--muted);margin-bottom:20px;">'
            f'Generated by <strong>spark_eda</strong></p>'
            f"{body_html}"
            f'<div class="footer">spark_eda &mdash; Exploratory Data Analysis with PySpark</div>'
            "</body></html>"
        )
