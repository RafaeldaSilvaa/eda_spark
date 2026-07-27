from __future__ import annotations

"""Testes para o cliente HTTP do OmniRoute.

Testa OmniRouteClient: chamadas bem-sucedidas, timeouts,
erros HTTP, erros de parse e servidor indisponível.
"""

import json
from unittest import mock

import httpx

from spark_eda.adapters.omniroute.client import OmniRouteClient
from spark_eda.adapters.omniroute.models import AiCommentary


def _make_valid_response_data() -> dict[str, object]:
    """Retorna dados de resposta JSON válidos do OmniRoute."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "overview": "Dataset overview insight",
                            "schema": "Schema commentary",
                            "quality": "Data quality note",
                            "stats": "Stats commentary",
                            "distributions": "Distributions insight",
                            "correlations": "Correlation note",
                            "outliers": "Outlier analysis",
                            "insights": "Key insight",
                            "recommendations": "Key recommendation",
                            "executive_analysis": "Cross-cutting executive analysis",
                        }
                    ),
                },
            },
        ],
    }


class TestOmniRouteClient:
    """Testes unitários para OmniRouteClient."""

    def test_analyze_with_valid_response_returns_ai_commentary(self) -> None:
        """analyze deve retornar AiCommentary populado quando a
        resposta é válida."""
        response_data = _make_valid_response_data()

        with mock.patch("spark_eda.adapters.omniroute.client.httpx.post") as mock_post:
            mock_response = mock.MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_post.return_value = mock_response

            client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=30)
            result = client.analyze("test prompt")

            assert result.overview == "Dataset overview insight"
            assert result.schema == "Schema commentary"
            assert result.quality == "Data quality note"
            assert result.stats == "Stats commentary"
            assert result.distributions == "Distributions insight"
            assert result.correlations == "Correlation note"
            assert result.outliers == "Outlier analysis"
            assert result.insights == "Key insight"
            assert result.recommendations == "Key recommendation"
            assert result.executive_analysis == "Cross-cutting executive analysis"

    def test_analyze_with_valid_response_correct_endpoint(self) -> None:
        """analyze deve chamar o endpoint /chat/completions."""
        with mock.patch("spark_eda.adapters.omniroute.client.httpx.post") as mock_post:
            mock_response = mock.MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = _make_valid_response_data()
            mock_post.return_value = mock_response

            client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=30)
            client.analyze("test prompt")

            mock_post.assert_called_once()
            call_url = mock_post.call_args[0][0]
            assert call_url == "http://localhost:20128/v1/chat/completions"

    def test_analyze_with_timeout_returns_empty_ai_commentary(self) -> None:
        """analyze deve retornar AiCommentary vazio em caso de
        timeout, e logar warning."""
        with (
            mock.patch("spark_eda.adapters.omniroute.client.httpx.post", side_effect=httpx.TimeoutException("timeout")),
            mock.patch("spark_eda.adapters.omniroute.client._LOGGER") as mock_logger,
        ):
            client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=5)
            result = client.analyze("test prompt")

            assert isinstance(result, AiCommentary)
            assert result.overview is None
            assert result.executive_analysis is None
            mock_logger.warning.assert_called_once()

    def test_analyze_with_http_4xx_returns_empty_ai_commentary(self) -> None:
        """analyze deve retornar AiCommentary vazio em caso de
        HTTP 4xx, e logar warning."""
        mock_response = mock.MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=mock.MagicMock(), response=mock_response
        )

        with (
            mock.patch("spark_eda.adapters.omniroute.client.httpx.post", return_value=mock_response),
            mock.patch("spark_eda.adapters.omniroute.client._LOGGER") as mock_logger,
        ):
            client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=30)
            result = client.analyze("test prompt")

            assert isinstance(result, AiCommentary)
            assert result.overview is None
            mock_logger.warning.assert_called_once()

    def test_analyze_with_http_5xx_returns_empty_ai_commentary(self) -> None:
        """analyze deve retornar AiCommentary vazio em caso de
        HTTP 5xx, e logar warning."""
        mock_response = mock.MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=mock.MagicMock(), response=mock_response
        )

        with (
            mock.patch("spark_eda.adapters.omniroute.client.httpx.post", return_value=mock_response),
            mock.patch("spark_eda.adapters.omniroute.client._LOGGER") as mock_logger,
        ):
            client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=30)
            result = client.analyze("test prompt")

            assert isinstance(result, AiCommentary)
            assert result.overview is None
            mock_logger.warning.assert_called_once()

    def test_analyze_with_json_parse_error_returns_empty_ai_commentary(self) -> None:
        """analyze deve retornar AiCommentary vazio quando a
        resposta não é JSON válido, e logar warning."""
        with mock.patch("spark_eda.adapters.omniroute.client.httpx.post") as mock_post:
            mock_response = mock.MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_post.return_value = mock_response

            with mock.patch("spark_eda.adapters.omniroute.client._LOGGER") as mock_logger:
                client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=30)
                result = client.analyze("test prompt")

                assert isinstance(result, AiCommentary)
                assert result.overview is None
                mock_logger.warning.assert_called_once()

    def test_analyze_when_server_unreachable_returns_empty_ai_commentary(self) -> None:
        """analyze deve retornar AiCommentary vazio quando o
        servidor está inalcançável (connection refused), e logar warning."""
        with (
            mock.patch(
                "spark_eda.adapters.omniroute.client.httpx.post",
                side_effect=httpx.ConnectError("Connection refused"),
            ),
            mock.patch("spark_eda.adapters.omniroute.client._LOGGER") as mock_logger,
        ):
            client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=30)
            result = client.analyze("test prompt")

            assert isinstance(result, AiCommentary)
            assert result.overview is None
            mock_logger.warning.assert_called_once()

    def test_analyze_with_custom_timeout_is_used(self) -> None:
        """analyze deve usar o timeout configurado na chamada HTTP."""
        with mock.patch("spark_eda.adapters.omniroute.client.httpx.post") as mock_post:
            mock_response = mock.MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = _make_valid_response_data()
            mock_post.return_value = mock_response

            client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=15)
            client.analyze("test prompt")

            assert mock_post.call_args[1]["timeout"] == 15

    def test_analyze_default_timeout_is_30(self) -> None:
        """analyze deve usar timeout padrão de 30 segundos."""
        with mock.patch("spark_eda.adapters.omniroute.client.httpx.post") as mock_post:
            mock_response = mock.MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = _make_valid_response_data()
            mock_post.return_value = mock_response

            client = OmniRouteClient(base_url="http://localhost:20128/v1")
            client.analyze("test prompt")

            assert mock_post.call_args[1]["timeout"] == 30

    def test_analyze_sends_system_prompt_with_staff_persona(self) -> None:
        """analyze deve incluir o system prompt com persona de
        staff-level data engineer/analyst."""
        with mock.patch("spark_eda.adapters.omniroute.client.httpx.post") as mock_post:
            mock_response = mock.MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = _make_valid_response_data()
            mock_post.return_value = mock_response

            client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=30)
            client.analyze("test prompt")

            payload = mock_post.call_args[1]["json"]
            system_content = payload["messages"][0]["content"]
            assert "staff-level" in system_content
            assert "15+ years" in system_content

    def test_analyze_with_empty_choices_returns_empty(self) -> None:
        """analyze deve retornar AiCommentary vazio quando choices
        está vazio."""
        response_data: dict[str, object] = {"choices": []}

        with mock.patch("spark_eda.adapters.omniroute.client.httpx.post") as mock_post:
            mock_response = mock.MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_post.return_value = mock_response

            client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=30)
            result = client.analyze("test prompt")

            assert isinstance(result, AiCommentary)
            assert result.overview is None

    def test_analyze_with_inner_json_parse_error_returns_empty(self) -> None:
        """analyze deve retornar AiCommentary vazio quando o
        conteúdo do message não é JSON válido."""
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": "not valid json",
                    },
                },
            ],
        }

        with mock.patch("spark_eda.adapters.omniroute.client.httpx.post") as mock_post:
            mock_response = mock.MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_post.return_value = mock_response

            with mock.patch("spark_eda.adapters.omniroute.client._LOGGER") as mock_logger:
                client = OmniRouteClient(base_url="http://localhost:20128/v1", timeout=30)
                result = client.analyze("test prompt")

                assert isinstance(result, AiCommentary)
                assert result.overview is None
                mock_logger.warning.assert_called_once()
