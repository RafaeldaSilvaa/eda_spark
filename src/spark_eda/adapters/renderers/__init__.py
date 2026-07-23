"""Renderizadores de saída para relatórios EDA."""

from spark_eda.adapters.renderers.html_renderer import HTMLRenderer
from spark_eda.adapters.renderers.text_renderer import TextRenderer
from spark_eda.adapters.renderers.json_serializer import JSONSerializer
from spark_eda.utils.formatting import (
    format_bytes,
    format_number,
    format_percentage,
    truncate_text,
)

__all__ = [
    "HTMLRenderer",
    "TextRenderer",
    "JSONSerializer",
    "format_number",
    "format_percentage",
    "format_bytes",
    "truncate_text",
]
