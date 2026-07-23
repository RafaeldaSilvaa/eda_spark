"""Interface de porta para provedores de dados Spark."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from spark_eda.domain.entities.data_profile import DataProfile


class DataProvider(ABC):
    """Interface para provedores de dados que operam sobre DataFrames.

    Define operações de profile e fingerprint sem expor dependências
    do PySpark para a camada de aplicação.
    """

    @abstractmethod
    def compute_profile(
        self,
        dataframe: Any,
        columns: list[str] | None,
        config: Any,
    ) -> DataProfile:
        """Calcula o perfil completo do dataset.

        Args:
            dataframe: Referência abstrata a um PySpark DataFrame.
            columns: Colunas a incluir no perfil, ou None para todas.
            config: Configuração opcional de profiling.

        Returns:
            DataProfile com o perfil completo do dataset.

        Raises:
            ValueError: Se o dataframe for inválido ou as colunas não existirem.
            RuntimeError: Se ocorrer um erro durante o processamento.
        """

    @abstractmethod
    def compute_fingerprint(
        self,
        dataframe: Any,
        config: Any,
    ) -> str:
        """Calcula um fingerprint único para o DataFrame.

        Usado como chave de cache para identificar o dataset de forma
        determinística (ex.: hash do schema + contagem de linhas + amostra).

        Args:
            dataframe: Referência abstrata a um PySpark DataFrame.
            config: Configuração opcional para o cálculo do fingerprint.

        Returns:
            String hash representando o fingerprint do dataset.

        Raises:
            RuntimeError: Se ocorrer um erro durante o cálculo.
        """
