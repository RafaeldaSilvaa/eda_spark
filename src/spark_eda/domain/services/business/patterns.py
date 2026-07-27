"""Expressões regulares compiladas para padrões de negócio brasileiros comuns."""

from __future__ import annotations

import re

CPF: re.Pattern[str] = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
"""Cadastro de Pessoa Física (CPF) no formato ``XXX.XXX.XXX-XX``."""

CNPJ: re.Pattern[str] = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
"""Cadastro Nacional da Pessoa Jurídica (CNPJ) no formato ``XX.XXX.XXX/XXXX-XX``."""

EMAIL: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
"""Endereço de email conforme RFC 5322 simplificado."""

UUID: re.Pattern[str] = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
"""UUID na forma canônica ``XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX``."""

URL: re.Pattern[str] = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")
"""URL com protocolo HTTP ou HTTPS."""

IPV4: re.Pattern[str] = re.compile(r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$")
"""Endereço IPv4."""

CEP: re.Pattern[str] = re.compile(r"^\d{5}-?\d{3}$")
"""Código de Endereçamento Postal (CEP) com ou sem hífen (``XXXXX-XXX``)."""

PHONE_BR: re.Pattern[str] = re.compile(r"^\+?55\s?\d{2}\s?\d{4,5}-?\d{4}$")
"""Número de telefone brasileiro com código de país ``+55``."""
