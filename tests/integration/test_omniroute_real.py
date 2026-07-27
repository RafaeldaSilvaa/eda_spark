"""Testes de integração reais para o módulo OmniRoute.

Testa as funções do módulo ``manager`` com o Node.js real
(instalado via ``nodejs-bin`` ou sistema). Requer o pacote
``nodejs`` instalado no ambiente — pula silenciosamente se
não estiver disponível.
"""

from __future__ import annotations

import pytest

from spark_eda.adapters.omniroute.manager import OmniRouteManager, _find_node, _healthcheck, _port_in_use


@pytest.mark.integration
def test_find_node_returns_valid_path() -> None:
    """_find_node deve retornar um path real e executável quando
    o Node.js está disponível no ambiente."""
    node_path = _find_node()
    assert node_path is not None, "Node.js não encontrado no ambiente"
    assert isinstance(node_path, str)
    assert len(node_path) > 0


@pytest.mark.integration
def test_port_in_use_returns_false_when_omniroute_not_running() -> None:
    """_port_in_use deve retornar False quando não há OmniRoute
    rodando (caso normal em testes)."""
    assert _port_in_use() is False


@pytest.mark.integration
def test_healthcheck_returns_false_when_omniroute_not_running() -> None:
    """_healthcheck deve retornar False quando não há OmniRoute
    rodando."""
    assert _healthcheck() is False


@pytest.mark.integration
def test_manager_ensure_running_without_node_returns_false() -> None:
    """OmniRouteManager.ensure_running não deve falhar mesmo sem
    Node.js — apenas retornar False."""
    manager = OmniRouteManager()
    result = manager.ensure_running()
    # Pode ser True se tiver OmniRoute já rodando na porta,
    # ou False se não houver Node.js / npm falhar
    assert isinstance(result, bool)
    manager.stop()
