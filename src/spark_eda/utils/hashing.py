"""Funções de hashing para geração de *fingerprints* de análise."""

from __future__ import annotations

import hashlib


def compute_fingerprint(
    schema_json: str,
    config_json: str,
) -> str:
    """Gera uma *fingerprint* SHA-256 a partir do schema e configuração.

    A *fingerprint* é utilizada como chave de cache e para detectar
    mudanças na estrutura ou configuração entre execuções.

    Args:
        schema_json: Representação JSON do schema do *dataset*.
        config_json: Representação JSON da configuração da análise.

    Returns:
        *Hash* SHA-256 em formato hexadecimal (64 caracteres).
    """
    content = f"{schema_json}:::{config_json}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
