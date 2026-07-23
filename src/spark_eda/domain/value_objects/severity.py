"""Níveis de severidade para insights e fatores de qualidade."""

from __future__ import annotations

from enum import Enum


class Severity(Enum):
    """Enumeração dos níveis de severidade."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
