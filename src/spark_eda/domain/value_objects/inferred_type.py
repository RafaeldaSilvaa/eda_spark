"""Tipos de negócio inferidos para colunas."""

from __future__ import annotations

from enum import Enum


class InferredType(Enum):
    """Enumeração dos tipos semânticos inferidos para uma coluna."""

    CPF = "cpf"
    CNPJ = "cnpj"
    EMAIL = "email"
    UUID = "uuid"
    URL = "url"
    IPV4 = "ipv4"
    CEP = "cep"
    PHONE_BR = "phone_br"
    CREDIT_CARD = "credit_card"
    AUTO_INCREMENT = "auto_increment"
    TECHNICAL_KEY = "technical_key"
    NONE = "none"
