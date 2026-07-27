"""DTO da seção de esquema e metadados das colunas."""
from __future__ import annotations

from dataclasses import dataclass

from spark_eda.utils.formatting import format_number


@dataclass(frozen=True)
class SchemaColumn:
    """Representação de coluna no relatório de esquema.

    Attributes:
        name: Nome da coluna.
        type: Tipo de dado primitivo (ex.: ``"integer"``, ``"string"``).
        nullable: Se a coluna aceita valores nulos.
        inferred_type: Tipo semântico inferido, ou None.
        null_count: Número de valores nulos.
    """

    name: str
    type: str
    nullable: bool
    inferred_type: str | None
    null_count: int


@dataclass(frozen=True)
class SchemaSection:
    """Esquema do dataset com metadados de todas as colunas.

    Attributes:
        columns: Lista de colunas com seus metadados.
    """

    columns: list[SchemaColumn]

    def _repr_html_(self) -> str:
        """Renderiza o esquema como uma tabela HTML com estilos inline."""
        header: str = (
            '<thead><tr>'
            '<th style="text-align:left;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            'color:var(--muted,#64748b);font-size:12px;text-transform:uppercase;">Column</th>'
            '<th style="text-align:left;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            'color:var(--muted,#64748b);font-size:12px;text-transform:uppercase;">Type</th>'
            '<th style="text-align:center;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            'color:var(--muted,#64748b);font-size:12px;text-transform:uppercase;">Nullable</th>'
            '<th style="text-align:left;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            'color:var(--muted,#64748b);font-size:12px;text-transform:uppercase;">Inferred</th>'
            '<th style="text-align:right;padding:8px 12px;border-bottom:2px solid var(--border,#e2e8f0);'
            'color:var(--muted,#64748b);font-size:12px;text-transform:uppercase;">Nulls</th>'
            '</tr></thead>'
        )
        rows: str = "".join(
            f'<tr style="border-bottom:1px solid var(--border,#e2e8f0);">'
            f'<td style="padding:8px 12px;font-weight:500;color:var(--text,#1a1a2e);">{col.name}</td>'
            f'<td style="padding:8px 12px;color:var(--primary,#2563eb);">{col.type}</td>'
            f'<td style="padding:8px 12px;text-align:center;color:var(--text,#1a1a2e);">'
            f'{"Yes" if col.nullable else "No"}</td>'
            f'<td style="padding:8px 12px;color:var(--text,#1a1a2e);">{col.inferred_type or "\u2014"}</td>'
            f'<td style="padding:8px 12px;text-align:right;color:var(--text,#1a1a2e);">'
            f'{format_number(col.null_count)}</td>'
            f"</tr>"
            for col in self.columns
        )
        return (
            f'<div style="overflow-x:auto;">'
            f'<table style="width:100%;border-collapse:collapse;font-size:14px;">{header}<tbody>{rows}</tbody></table>'
            f"</div>"
        )

    def __str__(self) -> str:
        """Renderiza o esquema como uma tabela com caracteres de caixa."""
        if not self.columns:
            return "Schema\n" + "-" * 20 + "\n  (no columns)"

        col_widths: dict[str, int] = {
            "name": max(len(c.name) for c in self.columns),
            "type": max(len(c.type) for c in self.columns),
            "nullable": 8,
            "inferred": max(len(c.inferred_type or "") for c in self.columns),
            "null": 6,
        }
        col_widths["name"] = max(col_widths["name"], 6)
        col_widths["type"] = max(col_widths["type"], 4)
        col_widths["inferred"] = max(col_widths["inferred"], 8)

        sep: str = "+" + "+".join("-" * (w + 2) for w in col_widths.values()) + "+"
        header: str = (
            f"| {'Column'.ljust(col_widths['name'])} "
            f"| {'Type'.ljust(col_widths['type'])} "
            f"| {'Nullable'.ljust(col_widths['nullable'])} "
            f"| {'Inferred'.ljust(col_widths['inferred'])} "
            f"| {'Nulls'.rjust(col_widths['null'])} |"
        )
        lines: list[str] = [sep, header, sep]
        for col in self.columns:
            lines.append(
                f"| {col.name.ljust(col_widths['name'])} "
                f"| {col.type.ljust(col_widths['type'])} "
                f"| {('Yes' if col.nullable else 'No').ljust(col_widths['nullable'])} "
                f"| {(col.inferred_type or '\u2014').ljust(col_widths['inferred'])} "
                f"| {str(col.null_count).rjust(col_widths['null'])} |"
            )
        lines.append(sep)
        return "Schema\n" + "-" * 20 + "\n" + "\n".join(lines)
