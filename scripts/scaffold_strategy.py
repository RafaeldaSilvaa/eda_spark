"""Scaffold para criação de novas estratégias de computação.

Uso:
    python scripts/scaffold_strategy.py <nome_estrategia>

Cria:
    - Adapter com função template para a estratégia
    - Teste de contrato para a estratégia
"""

import sys
from pathlib import Path

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

_ADAPTERS_DIR: Path = _PROJECT_ROOT / "src" / "spark_eda" / "adapters"
_TEST_DIR: Path = _PROJECT_ROOT / "tests"

_ADAPTER_TEMPLATE: str = '''"""Estratégia de computação: {estrategia_title}.

Descreva aqui o propósito e o funcionamento desta estratégia.
"""

from collections.abc import Callable
from typing import Any


{estrategia}_function: Callable[..., Any] = lambda: None
"""Função principal da estratégia. Substitua pela implementação real."""


def compute_{estrategia}(
    *,
    config: dict[str, Any] | None = None,
) -> Any:
    """Executa a estratégia de computação {estrategia_title}.

    Args:
        config: Dicionário opcional com parâmetros de configuração.

    Returns:
        Resultado da computação.
    """
    _ = config or {{}}
    # TODO: implementar a lógica da estratégia
    msg: str = (
        "Estratégia '{estrategia}' ainda não foi implementada."
    )
    raise NotImplementedError(msg)
'''

_CONTRACT_TEST_TEMPLATE: str = '''"""Testes de contrato para a estratégia **{estrategia_title}**.

Verifica os contratos da função ``compute_{estrategia}``.
"""

import pytest

from spark_eda.adapters.{estrategia} import compute_{estrategia}


class Test{estrategia_capitalized}Contract:
    """Testes de contrato para a estratégia {estrategia_title}."""

    def test_compute_{estrategia}_lanca_not_implemented(self) -> None:
        """Verifica que compute_{estrategia} lança NotImplementedError por padrão."""
        # Arrange
        ...

        # Act & Assert
        with pytest.raises(NotImplementedError, match="{estrategia}"):
            compute_{estrategia}()
'''


def _validar_nome_estrategia(nome: str) -> str:
    """Valida e normaliza o nome da estratégia.

    Args:
        nome: Nome bruto fornecido pelo usuário.

    Returns:
        Nome normalizado (minúsculo, snake_case).

    Raises:
        ValueError: Se o nome for vazio ou inválido.
    """
    nome_normalizado: str = nome.strip().lower().replace(" ", "_").replace("-", "_")
    if not nome_normalizado:
        raise ValueError("O nome da estratégia não pode ser vazio.")
    if not nome_normalizado.isidentifier():
        raise ValueError(
            f"'{nome}' não é um identificador Python válido. Use apenas letras, números e underscores.",
        )
    return nome_normalizado


def _criar_arquivo(
    caminho: Path,
    conteudo: str,
) -> None:
    """Cria um arquivo com o conteúdo fornecido.

    Args:
        caminho: Caminho absoluto do arquivo a ser criado.
        conteudo: Conteúdo textual do arquivo.

    Raises:
        FileExistsError: Se o arquivo já existir.
    """
    if caminho.exists():
        raise FileExistsError(f"O arquivo já existe: {caminho}")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
    print(f"  Criado: {caminho}")


def _main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python scripts/scaffold_strategy.py <nome_estrategia>")
        print("")
        print("Exemplos:")
        print("  python scripts/scaffold_strategy.py detector_outliers_iqr")
        print("  python scripts/scaffold_strategy.py amostragem_estratificada")
        sys.exit(1)

    nome_estrategia: str = _validar_nome_estrategia(sys.argv[1])
    nome_title: str = nome_estrategia.replace("_", " ").title()
    nome_capitalized: str = nome_estrategia.title().replace("_", "")

    caminho_adapter: Path = _ADAPTERS_DIR / f"{nome_estrategia}.py"
    caminho_teste: Path = _TEST_DIR / "contract" / f"test_{nome_estrategia}_contract.py"

    print(f"Criando estratégia de computação: {nome_title}")
    print("")

    try:
        _criar_arquivo(
            caminho_adapter,
            _ADAPTER_TEMPLATE.format(
                estrategia=nome_estrategia,
                estrategia_title=nome_title,
            ),
        )
        _criar_arquivo(
            caminho_teste,
            _CONTRACT_TEST_TEMPLATE.format(
                estrategia=nome_estrategia,
                estrategia_title=nome_title,
                estrategia_capitalized=nome_capitalized,
            ),
        )

        print("")
        print("Próximos passos:")
        print(f"  1. Implemente a lógica em {caminho_adapter}")
        print(f"  2. Ajuste os testes em {caminho_teste}")
        print("")
        print("Feito!")

    except FileExistsError as erro:
        print(f"Erro: {erro}")
        sys.exit(1)


if __name__ == "__main__":
    _main()
