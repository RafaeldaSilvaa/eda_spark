"""Renderizador de texto para relatórios spark_eda com suporte a terminal."""

from __future__ import annotations

import sys

from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.quality_section import QualityFactorReport, QualityReport
from spark_eda.utils.formatting import format_number, format_percentage


def _severity_emoji(severity: str) -> str:
    """Retorna um marcador de texto para o nível de severidade."""
    return {
        "critical": "!!",
        "high": "!",
        "medium": "-",
        "low": " ",
    }.get(severity, "?")

_ANSI_RESET: str = "\033[0m"
_ANSI_BOLD: str = "\033[1m"
_ANSI_DIM: str = "\033[2m"
_ANSI_RED: str = "\033[91m"
_ANSI_GREEN: str = "\033[92m"
_ANSI_YELLOW: str = "\033[93m"
_ANSI_BLUE: str = "\033[94m"
_ANSI_CYAN: str = "\033[96m"
_ANSI_GRAY: str = "\033[90m"

_HAS_COLOR: bool = sys.stdout.isatty()


def _maybe(code: str) -> str:
    """Retorna o código ANSI apenas se o terminal suportar cores."""
    return code if _HAS_COLOR else ""


def _bold(text: str) -> str:
    return f"{_maybe(_ANSI_BOLD)}{text}{_maybe(_ANSI_RESET)}"


def _dim(text: str) -> str:
    return f"{_maybe(_ANSI_DIM)}{text}{_maybe(_ANSI_RESET)}"


def _red(text: str) -> str:
    return f"{_maybe(_ANSI_RED)}{text}{_maybe(_ANSI_RESET)}"


def _green(text: str) -> str:
    return f"{_maybe(_ANSI_GREEN)}{text}{_maybe(_ANSI_RESET)}"


def _yellow(text: str) -> str:
    return f"{_maybe(_ANSI_YELLOW)}{text}{_maybe(_ANSI_RESET)}"


def _blue(text: str) -> str:
    return f"{_maybe(_ANSI_BLUE)}{text}{_maybe(_ANSI_RESET)}"


def _cyan(text: str) -> str:
    return f"{_maybe(_ANSI_CYAN)}{text}{_maybe(_ANSI_RESET)}"


def _gray(text: str) -> str:
    return f"{_maybe(_ANSI_GRAY)}{text}{_maybe(_ANSI_RESET)}"


_H1: str = f"{_maybe(_ANSI_BOLD)}{_maybe(_ANSI_CYAN)}"
_H2: str = f"{_maybe(_ANSI_BOLD)}{_maybe(_ANSI_BLUE)}"


class TextRenderer:
    """Renderizador de relatórios em texto formatado para terminal.

    Usa caracteres Unicode de caixa para tabelas e códigos ANSI
    para colorização quando o terminal suporta.
    """

    @staticmethod
    def render_report(eda_report: EDAReport) -> str:
        """Renderiza o relatório completo como texto formatado.

        Args:
            eda_report: Relatório de análise exploratória.

        Returns:
            String formatada para terminal.
        """
        lines: list[str] = [
            f"{_H1}{'=' * 60}{_maybe(_ANSI_RESET)}",
            f"{_H1}  spark_eda \u2014 Exploratory Data Analysis Report{_maybe(_ANSI_RESET)}",
            f"{_H1}{'=' * 60}{_maybe(_ANSI_RESET)}",
            "",
            f"{_H2}1. Overview{_maybe(_ANSI_RESET)}",
            f"{_gray('\u2500' * 40)}{_maybe(_ANSI_RESET)}",
            eda_report.overview.__str__(),
            "",
            f"{_H2}2. Schema{_maybe(_ANSI_RESET)}",
            f"{_gray('\u2500' * 40)}{_maybe(_ANSI_RESET)}",
            eda_report.schema.__str__(),
            "",
            f"{_H2}3. Quality{_maybe(_ANSI_RESET)}",
            f"{_gray('\u2500' * 40)}{_maybe(_ANSI_RESET)}",
            TextRenderer.render_quality_report(eda_report.quality),
            "",
            f"{_H2}4. Statistics{_maybe(_ANSI_RESET)}",
            f"{_gray('\u2500' * 40)}{_maybe(_ANSI_RESET)}",
            eda_report.stats.__str__(),
            "",
            f"{_H2}5. Distributions{_maybe(_ANSI_RESET)}",
            f"{_gray('\u2500' * 40)}{_maybe(_ANSI_RESET)}",
            eda_report.distributions.__str__(),
            "",
            f"{_H2}6. Correlations{_maybe(_ANSI_RESET)}",
            f"{_gray('\u2500' * 40)}{_maybe(_ANSI_RESET)}",
            eda_report.correlations.__str__(),
            "",
            f"{_H2}7. Outliers{_maybe(_ANSI_RESET)}",
            f"{_gray('\u2500' * 40)}{_maybe(_ANSI_RESET)}",
            eda_report.outliers.__str__(),
            "",
            f"{_H2}8. Insights{_maybe(_ANSI_RESET)}",
            f"{_gray('\u2500' * 40)}{_maybe(_ANSI_RESET)}",
            eda_report.insights.__str__(),
            "",
            f"{_H2}9. Recommendations{_maybe(_ANSI_RESET)}",
            f"{_gray('\u2500' * 40)}{_maybe(_ANSI_RESET)}",
            eda_report.recommendations.__str__(),
        ]
        return "\n".join(lines)

    @staticmethod
    def render_quality(quality_report: QualityReport) -> str:
        """Renderiza o relatório de qualidade como texto formatado.

        Args:
            quality_report: Relatório de qualidade dos dados.

        Returns:
            String formatada para terminal.
        """
        lines: list[str] = [
            f"{_H1}{'=' * 40}{_maybe(_ANSI_RESET)}",
            f"{_H1}  Data Quality{_maybe(_ANSI_RESET)}",
            f"{_H1}{'=' * 40}{_maybe(_ANSI_RESET)}",
            "",
            TextRenderer.render_quality_report(quality_report),
        ]
        return "\n".join(lines)

    @staticmethod
    def render_quality_report(quality: QualityReport) -> str:
        """Renderiza o relatório de qualidade como texto formatado.

        Args:
            quality: Relatório de qualidade dos dados.

        Returns:
            String formatada para terminal.
        """
        gauge_char: str = "#"
        gauge_fill: int = int(quality.overall / 100.0 * 20)
        gauge_bar: str = gauge_char * gauge_fill + "." * (20 - gauge_fill)

        lines: list[str] = [
            "Quality",
            "-" * 40,
            f"  Overall: {format_number(quality.overall, 1)}",
            f"  [{gauge_bar}] {format_number(quality.overall, 1)}/100",
            "",
            "  Dimensions:",
        ]
        for dim in quality.dimensions:
            bar: str = gauge_char * int(dim.score / 100.0 * 15) + "." * (15 - int(dim.score / 100.0 * 15))
            lines.append(f"    {dim.name.title():15s} [{bar}] {format_number(dim.score, 1)}")

        if quality.top_penalizers:
            lines.extend(["", "  Top Penalizers:"])
            for f in quality.top_penalizers[:5]:
                sev: str = _severity_emoji(f.severity)
                lines.append(f"    {sev} {f.reason} (-{format_percentage(1.0 - f.score)})")

        return "\n".join(lines)

    @staticmethod
    def render_section(section: object) -> str:
        """Renderiza uma seção individual como texto formatado.

        Args:
            section: Qualquer DTO de seção com método ``__str__``.

        Returns:
            Texto formatado da seção.
        """
        if hasattr(section, "__str__"):
            return str(section)
        return repr(section)
