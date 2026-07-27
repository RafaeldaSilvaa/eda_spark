"""Adaptador para o runtime OmniRoute AI."""

from spark_eda.adapters.omniroute.client import OmniRouteClient
from spark_eda.adapters.omniroute.manager import OmniRouteManager
from spark_eda.adapters.omniroute.models import AiCommentary, OmniRouteError
from spark_eda.adapters.omniroute.prompt_builder import PromptBuilder

__all__ = [
    "AiCommentary",
    "OmniRouteClient",
    "OmniRouteError",
    "OmniRouteManager",
    "PromptBuilder",
]
