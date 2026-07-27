"""Cliente HTTP para a API OpenAI-compatible do OmniRoute."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from spark_eda.adapters.omniroute.models import AiCommentary

_LOGGER = logging.getLogger(__name__)


class OmniRouteClient:
    """Cliente HTTP síncrono para a API OpenAI-compatible do OmniRoute.

    Envia prompts para ``{base_url}/chat/completions`` e mapeia a
    resposta JSON estruturada para :class:`AiCommentary`.
    """

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        """Inicializa o cliente.

        Args:
            base_url: URL base da API (ex.: ``http://localhost:20128/v1``).
            timeout: Timeout em segundos para requisições HTTP.
        """
        self._base_url: str = base_url.rstrip("/")
        self._timeout: int = timeout

    def analyze(self, prompt: str) -> AiCommentary:
        """Envia um prompt para o OmniRoute e retorna o commentary estruturado.

        Em caso de erro (timeout, HTTP error, parsing), loga um warning
        e retorna um :class:`AiCommentary` vazio — degradação graciosa.

        Args:
            prompt: Prompt completo para análise.

        Returns:
            :class:`AiCommentary` com os comentários gerados, ou vazio
            em caso de falha.
        """
        url: str = f"{self._base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": "omniroute",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a staff-level data engineer/analyst with 15+ years of experience. "
                        "Analyze the EDA report data below and provide critical insights, "
                        "non-obvious patterns, and business implications. "
                        "Respond with a JSON object containing per-section commentary and "
                        "an executive_analysis field."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }

        try:
            response: httpx.Response = httpx.post(
                url,
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        except httpx.TimeoutException:
            _LOGGER.warning("Timeout ao chamar OmniRoute (%ds)", self._timeout)
            return AiCommentary()
        except httpx.HTTPStatusError as exc:
            _LOGGER.warning("HTTP %d do OmniRoute", exc.response.status_code)
            return AiCommentary()
        except httpx.RequestError as exc:
            _LOGGER.warning("Erro de conexão com OmniRoute: %s", exc)
            return AiCommentary()
        except json.JSONDecodeError as exc:
            _LOGGER.warning("Resposta JSON inválida do OmniRoute: %s", exc)
            return AiCommentary()

        return self._parse_response(data)

    def _parse_response(self, data: dict[str, Any]) -> AiCommentary:
        """Parseia a resposta da API para um :class:`AiCommentary`.

        Args:
            data: Dicionário com a resposta da API.

        Returns:
            :class:`AiCommentary` populado, ou vazio se o parsing falhar.
        """
        try:
            choices: list[Any] = data.get("choices", [])
            if not choices:
                return AiCommentary()

            message: dict[str, Any] = choices[0].get("message", {})
            content: str = message.get("content", "")

            commentary_data: dict[str, Any] = json.loads(content)
            return AiCommentary(
                overview=commentary_data.get("overview"),
                schema=commentary_data.get("schema"),
                quality=commentary_data.get("quality"),
                stats=commentary_data.get("stats"),
                distributions=commentary_data.get("distributions"),
                correlations=commentary_data.get("correlations"),
                outliers=commentary_data.get("outliers"),
                insights=commentary_data.get("insights"),
                recommendations=commentary_data.get("recommendations"),
                executive_analysis=commentary_data.get("executive_analysis"),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            _LOGGER.warning("Erro ao processar resposta do OmniRoute: %s", exc)
            return AiCommentary()
