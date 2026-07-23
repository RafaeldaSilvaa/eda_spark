"""Classificador semântico de colunas.

Infere o tipo de negócio de uma coluna a partir de seu nome e,
opcionalmente, de amostras de seus valores.
"""

from __future__ import annotations

import re

from spark_eda.domain.value_objects.inferred_type import InferredType


class ColumnClassifier:
    """Classificador semântico de colunas, sem estado.

    Utiliza um conjunto de regras baseadas em padrões de nomenclatura e,
    quando disponível, amostras de valores para inferir o tipo semântico
    de uma coluna.
    """

    @staticmethod
    def _classify_by_name(column_name: str) -> InferredType | None:
        """Tenta inferir o tipo semântico apenas pelo nome da coluna.

        A comparação é feita contra um nome normalizado (minúsculo,
        sem underscores e hífens) para maximizar o casamento.

        Args:
            column_name: Nome original da coluna.

        Returns:
            :class:`InferredType` se uma regra de nome foi satisfeita,
            ou ``None`` caso contrário.
        """
        normalized_name: str = column_name.lower().replace("_", "").replace("-", "")

        patterns: dict[InferredType, tuple[str, ...]] = {
            InferredType.CPF: ("cpf", "documento", "doc", "documento", "cpfformatado"),
            InferredType.CNPJ: ("cnpj",),
            InferredType.EMAIL: ("email", "eemail", "emailaddress", "mail", "correioeletronico"),
            InferredType.UUID: ("uuid", "guid", "idglobal", "chaveglobal"),
            InferredType.URL: ("url", "link", "site", "website", "web", "homepage", "enderecoweb"),
            InferredType.IPV4: ("ip", "enderecoip", "ipaddress", "ipv4"),
            InferredType.CEP: ("cep", "codigopostal", "zipcode", "postalcode"),
            InferredType.PHONE_BR: (
                "telefone", "phone", "celular", "fone", "tel",
                "telefonecelular", "telemovel", "contato",
            ),
            InferredType.CREDIT_CARD: (
                "cartao", "card", "numerocartao", "ccnumber",
                "creditcard", "bandeiracartao",
            ),
            InferredType.TECHNICAL_KEY: (
                "sk", "surrogatekey", "chavetecnica", "etl",
                "dwid", "dwhid", "hashkey",
            ),
        }

        for inferred_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern in normalized_name:
                    return inferred_type

        if normalized_name == "id" or normalized_name.endswith("id") and len(normalized_name) <= 6:
            return InferredType.AUTO_INCREMENT

        return None

    @staticmethod
    def _classify_by_samples(sample_values: list[str | None]) -> InferredType | None:
        """Tenta inferir o tipo semântico analisando amostras de valores.

        Itera sobre amostras não nulas aplicando expressões regulares
        específicas para cada formato. Retorna o primeiro tipo que
        corresponder à maioria das amostras (> 50 %).

        Args:
            sample_values: Lista de valores amostrados da coluna.

        Returns:
            :class:`InferredType` se um padrão foi detectado na maioria
            das amostras, ou ``None`` caso contrário.
        """
        non_null_values: list[str] = [
            v for v in sample_values if v is not None
        ]

        if len(non_null_values) < 3:
            return None

        regex_patterns: dict[InferredType, re.Pattern[str]] = {
            InferredType.CPF: re.compile(
                r"^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$"
            ),
            InferredType.CNPJ: re.compile(
                r"^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$"
            ),
            InferredType.EMAIL: re.compile(
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            ),
            InferredType.UUID: re.compile(
                r"^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$",
                re.IGNORECASE,
            ),
            InferredType.URL: re.compile(
                r"^https?://[^\s]+$"
            ),
            InferredType.IPV4: re.compile(
                r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
            ),
            InferredType.CEP: re.compile(
                r"^\d{5}-?\d{3}$"
            ),
            InferredType.PHONE_BR: re.compile(
                r"^\+?\d{1,3}\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}$"
            ),
            InferredType.CREDIT_CARD: re.compile(
                r"^\d{4}-?\d{4}-?\d{4}-?\d{4}$"
            ),
        }

        best_type: InferredType | None = None
        best_match_rate: float = 0.0

        for inferred_type, pattern in regex_patterns.items():
            matches: int = sum(
                1 for v in non_null_values if pattern.match(v.strip())
            )
            match_rate: float = matches / len(non_null_values)

            if match_rate > best_match_rate and match_rate > 0.5:
                best_match_rate = match_rate
                best_type = inferred_type

        return best_type

    def classify(
        self,
        column_name: str,
        sample_values: list[str | None] | None = None,
    ) -> InferredType:
        """Infere o tipo semântico de uma coluna.

        A classificação acontece em dois estágios:
        1. **Por nome**: aplica regras de nomenclatura sobre o nome da coluna.
        2. **Por amostras** (se fornecidas): aplica expressões regulares
           sobre valores amostrados.

        Se nenhuma regra for satisfeita, retorna :attr:`InferredType.NONE`.

        Args:
            column_name: Nome da coluna a ser classificada.
            sample_values: Lista opcional de valores amostrados da coluna,
                utilizada para validação baseada em regex.

        Returns:
            :class:`InferredType` mais provável para a coluna, ou
            :attr:`InferredType.NONE` se a classificação não for possível.
        """
        type_by_name: InferredType | None = self._classify_by_name(column_name)
        if type_by_name is not None:
            return type_by_name

        if sample_values is not None:
            type_by_samples: InferredType | None = self._classify_by_samples(sample_values)
            if type_by_samples is not None:
                return type_by_samples

        return InferredType.NONE
