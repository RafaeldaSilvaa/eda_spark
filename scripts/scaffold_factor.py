"""Scaffold para criação de novos fatores de qualidade.

Uso:
    python scripts/scaffold_factor.py <nome_dimensao>

Cria:
    - src/spark_eda/domain/services/quality_factors/<nome>.py
    - tests/contract/test_<nome>_contract.py
    - Registra no FACTOR_REGISTRY via decorador @registrar
"""

import os
import sys
from pathlib import Path


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

_SRC_DIR: Path = _PROJECT_ROOT / "src" / "spark_eda" / "domain" / "services" / "quality_factors"
_TEST_DIR: Path = _PROJECT_ROOT / "tests"

_FACTOR_TEMPLATE: str = '''"""Fatores de qualidade da dimensão **{dimensao_title}**.

Descreva aqui o que esta dimensão avalia e como os fatores
contribuem para o score geral de qualidade.
"""

from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.services.quality_factors import registrar
from spark_eda.domain.value_objects.severity import Severity


def _severidade(score: float) -> Severity:
    """Mapeia um score no intervalo [0, 1] para um nível de severidade."""
    if score < 0.3:
        return Severity.CRITICAL
    if score < 0.6:
        return Severity.HIGH
    if score < 0.8:
        return Severity.MEDIUM
    return Severity.LOW


def _fator_exemplo_um(profile: DataProfile) -> QualityFactor:
    """Primeiro fator da dimensão {dimensao_title}.

    Substitua esta lógica pelo cálculo real do fator.
    """
    colunas_afetadas: list[str] = []
    for coluna_metadata in profile.colunas:
        profile_coluna: ColumnProfile = profile.coluna_profiles[coluna_metadata.nome]
        _ = profile_coluna
        # TODO: implementar lógica de avaliação

    return QualityFactor(
        nome="Nome do fator",
        score=1.0,
        peso_interno=0.5,
        contribuicao=0.5,
        razao="Descrição do motivo do score.",
        severidade=Severity.LOW,
        colunas_afetadas=colunas_afetadas,
    )


def _fator_exemplo_dois(profile: DataProfile) -> QualityFactor:
    """Segundo fator da dimensão {dimensao_title}."""
    colunas_afetadas: list[str] = []
    for coluna_metadata in profile.colunas:
        profile_coluna: ColumnProfile = profile.coluna_profiles[coluna_metadata.nome]
        _ = profile_coluna
        # TODO: implementar lógica de avaliação

    return QualityFactor(
        nome="Nome do segundo fator",
        score=1.0,
        peso_interno=0.5,
        contribuicao=0.5,
        razao="Descrição do motivo do score.",
        severidade=Severity.LOW,
        colunas_afetadas=colunas_afetadas,
    )


@registrar("{dimensao}")
def calcular_score(profile: DataProfile) -> list[QualityFactor]:
    """Calcula todos os fatores da dimensão **{dimensao_title}**.

    Args:
        profile: Perfil completo do *dataset*.

    Returns:
        Lista de fatores de qualidade da dimensão {dimensao_title}.
    """
    return [
        _fator_exemplo_um(profile),
        _fator_exemplo_dois(profile),
    ]
'''

_TEST_TEMPLATE: str = '''"""Testes de contrato para fatores de qualidade da dimensão **{dimensao_title}**.

Testa a criação de fatores usando os dados de perfil e verifica
que os scores estão no intervalo esperado.
"""

import pytest

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.services.quality_factors.{dimensao} import calcular_score
from spark_eda.domain.value_objects.data_type import DataType
from tests.fixtures.sample_data import create_column_metadata, create_data_profile


class Test{dimensao_capitalized}Contract:
    """Testes de contrato para os fatores de {dimensao_title}."""

    def test_calcular_score_retorna_lista_de_fatores(self) -> None:
        """Verifica que calcular_score retorna uma lista de QualityFactor."""
        # Arrange
        coluna: ColumnMetadata = create_column_metadata(
            name="coluna_teste",
            type_=DataType.STRING,
            nullable=True,
            nulls=5,
            non_nulls=95,
        )
        profile = create_data_profile(
            id_="teste_{dimensao}",
            columns=[coluna],
            rows=100,
        )

        # Act
        fatores = calcular_score(profile)

        # Assert
        assert len(fatores) > 0
        for fator in fatores:
            assert 0.0 <= fator.score <= 1.0
            assert fator.peso_interno > 0.0
            assert isinstance(fator.colunas_afetadas, list)
'''


def _validar_nome_dimensao(nome: str) -> str:
    """Valida e normaliza o nome da dimensão.

    Args:
        nome: Nome bruto da dimensão fornecido pelo usuário.

    Returns:
        Nome normalizado (minúsculo, sem espaços).

    Raises:
        ValueError: Se o nome for vazio ou inválido.
    """
    nome_normalizado: str = nome.strip().lower().replace(" ", "_")
    if not nome_normalizado:
        raise ValueError("O nome da dimensão não pode ser vazio.")
    if not nome_normalizado.isidentifier():
        raise ValueError(
            f"'{nome}' não é um identificador Python válido. "
            f"Use apenas letras, números e underscores.",
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


def _registrar_no_init(caminho_init: Path, nome_modulo: str) -> None:
    """Adiciona a importação do novo módulo no ``__init__.py`` do pacote.

    Args:
        caminho_init: Caminho do arquivo ``__init__.py``.
        nome_modulo: Nome do módulo a ser importado.
    """
    if not caminho_init.exists():
        return

    linha_import: str = f"    {nome_modulo},\n"
    conteudo_atual: str = caminho_init.read_text(encoding="utf-8")

    if nome_modulo in conteudo_atual:
        print(f"  Import já existe em {caminho_init}")
        return

    marcador: str = "# isort:skip"
    linha_alvo: str = f"from spark_eda.domain.services.quality_factors import (  # noqa: E402  {marcador}"

    if linha_alvo not in conteudo_atual:
        print(f"  Aviso: não foi possível encontrar o bloco de imports em {caminho_init}")
        return

    novo_conteudo: str = conteudo_atual.replace(
        f"{marcador}\n)",
        f"{marcador}\n{linha_import})",
    )
    caminho_init.write_text(novo_conteudo, encoding="utf-8")
    print(f"  Registrado em: {caminho_init}")


def _main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python scripts/scaffold_factor.py <nome_dimensao>")
        print("")
        print("Exemplos:")
        print("  python scripts/scaffold_factor.py volumetria")
        print("  python scripts/scaffold_factor.py integridade_referencial")
        sys.exit(1)

    nome_dimensao: str = _validar_nome_dimensao(sys.argv[1])
    nome_dimensao_title: str = nome_dimensao.replace("_", " ").title()
    nome_modulo: str = nome_dimensao

    caminho_fator: Path = _SRC_DIR / f"{nome_modulo}.py"
    caminho_teste: Path = _TEST_DIR / "contract" / f"test_{nome_modulo}_contract.py"
    caminho_init: Path = _SRC_DIR / "__init__.py"

    print(f"Criando fator de qualidade para dimensão: {nome_dimensao_title}")
    print("")

    try:
        _criar_arquivo(
            caminho_fator,
            _FACTOR_TEMPLATE.format(
                dimensao=nome_dimensao,
                dimensao_title=nome_dimensao_title,
            ),
        )
        _criar_arquivo(
            caminho_teste,
            _TEST_TEMPLATE.format(
                dimensao=nome_dimensao,
                dimensao_title=nome_dimensao_title,
                dimensao_capitalized=nome_dimensao.title().replace("_", ""),
            ),
        )
        _registrar_no_init(caminho_init, nome_modulo)

        print("")
        print("Próximos passos:")
        print(f"  1. Implemente a lógica de cálculo em {caminho_fator}")
        print(f"  2. Ajuste os testes em {caminho_teste}")
        print("  3. Adicione o peso da dimensão em quality_calculator.py (DIMENSION_WEIGHTS)")
        print("")
        print("Feito!")

    except FileExistsError as erro:
        print(f"Erro: {erro}")
        sys.exit(1)


if __name__ == "__main__":
    _main()
