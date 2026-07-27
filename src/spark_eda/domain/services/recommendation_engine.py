"""Motor de geração de recomendações.

Transforma :class:`~spark_eda.domain.entities.insight.Insight` em
:class:`~spark_eda.domain.entities.recommendation.Recommendation` acionáveis,
ordenados por urgência decrescente.
"""

from __future__ import annotations

from collections.abc import Callable

from spark_eda.domain.entities.insight import Insight
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.entities.recommendation import Recommendation
from spark_eda.domain.value_objects.insight_category import InsightCategory
from spark_eda.domain.value_objects.recommendation_category import RecommendationCategory
from spark_eda.domain.value_objects.severity import Severity


class RecommendationEngine:
    """Motor de geração de recomendações, sem estado.

    Converte :class:`Insight` identificados pelo
    :class:`~spark_eda.domain.services.insight_engine.InsightEngine`
    em recomendações de ação priorizadas com base na severidade e impacto.
    """

    @staticmethod
    def _priority_for_severity(severity: Severity) -> int:
        """Mapeia nível de severidade para uma prioridade numérica.

        Escala de prioridade:
        * :attr:`Severity.CRITICAL` → 1 (mais urgente)
        * :attr:`Severity.HIGH` → 2
        * :attr:`Severity.MEDIUM` → 3
        * :attr:`Severity.LOW` → 4
        * Outros casos → 5 (menos urgente)

        Args:
            severity: Nível de severidade do insight.

        Returns:
            Prioridade numérica entre 1 e 5.
        """
        mapping: dict[Severity, int] = {
            Severity.CRITICAL: 1,
            Severity.HIGH: 2,
            Severity.MEDIUM: 3,
            Severity.LOW: 4,
        }
        return mapping.get(severity, 5)

    @staticmethod
    def _recommend_nulls(
        insight: Insight,
    ) -> list[Recommendation]:
        """Gera recomendações para tratamento de valores nulos.

        Args:
            insight: Insight da categoria :attr:`InsightCategory.NULLS`.

        Returns:
            Lista de uma ou mais recomendações de tratamento de nulos.
        """
        recommendations: list[Recommendation] = []

        priority: int = RecommendationEngine._priority_for_severity(insight.severity)

        recommendations.append(
            Recommendation(
                category=RecommendationCategory.NULL_TREATMENT,
                priority=priority,
                column=insight.column,
                message=(f"Coluna '{insight.column}' com {insight.metric_value:.1%} de valores nulos."),
                action=(
                    f"Avaliar a causa dos nulos em '{insight.column}': "
                    f"se o dado não está disponível, considerar preenchimento "
                    f"com valor default, mediana/moda, ou registro separado. "
                    f"Se o nulo é esperado, documentar a regra de negócio."
                ),
            )
        )

        if insight.severity in (Severity.CRITICAL, Severity.HIGH):
            recommendations.append(
                Recommendation(
                    category=RecommendationCategory.NULL_TREATMENT,
                    priority=priority,
                    column=insight.column,
                    message=(
                        f"Alta taxa de nulos em '{insight.column}' pode "
                        f"inviabilizar análises que dependem desta coluna."
                    ),
                    action=(
                        f"Verificar a origem dos dados de '{insight.column}': "
                        f"o campo é opcional na fonte? Houve falha de captura? "
                        f"Se possível, enriquecer com fonte alternativa."
                    ),
                )
            )

        return recommendations

    @staticmethod
    def _recommend_outliers(
        insight: Insight,
    ) -> list[Recommendation]:
        """Gera recomendações para tratamento de outliers.

        Args:
            insight: Insight da categoria :attr:`InsightCategory.OUTLIERS`.

        Returns:
            Lista de recomendações de tratamento de outliers.
        """
        priority: int = RecommendationEngine._priority_for_severity(insight.severity)

        return [
            Recommendation(
                category=RecommendationCategory.OUTLIER_TREATMENT,
                priority=priority,
                column=insight.column,
                message=(f"Coluna '{insight.column}' com {insight.metric_value:.1%} de outliers identificados."),
                action=(
                    f"Validar os {insight.metric_value:.1%} de outliers "
                    f"em '{insight.column}': são dados legítimos "
                    f"(ex.: transação de alto valor) ou erro de "
                    f"captura? Se erro, corrigir ou remover. "
                    f"Se legítimos, considerar técnicas robustas "
                    f"(mediana em vez de média)."
                ),
            ),
        ]

    @staticmethod
    def _recommend_skewness(
        insight: Insight,
    ) -> list[Recommendation]:
        """Gera recomendações para tratamento de assimetria.

        Args:
            insight: Insight da categoria :attr:`InsightCategory.SKEWNESS`.

        Returns:
            Lista de recomendações de transformação de dados.
        """
        return [
            Recommendation(
                category=RecommendationCategory.TYPE_FIX,
                priority=RecommendationEngine._priority_for_severity(insight.severity),
                column=insight.column,
                message=(
                    f"Coluna '{insight.column}' com distribuição assimétrica (skewness = {insight.metric_value})."
                ),
                action=(
                    f"Para modelos sensíveis a distribuição, aplicar "
                    f"transformação logarítmica ou Box-Cox em "
                    f"'{insight.column}'. Se for análise descritiva, "
                    f"preferir mediana à média como medida de tendência "
                    f"central."
                ),
            ),
        ]

    @staticmethod
    def _recommend_cardinality(
        insight: Insight,
    ) -> list[Recommendation]:
        """Gera recomendações para colunas com alta cardinalidade.

        Args:
            insight: Insight da categoria :attr:`InsightCategory.CARDINALITY`.

        Returns:
            Lista de recomendações de otimização ou investigação.
        """
        return [
            Recommendation(
                category=RecommendationCategory.PERFORMANCE,
                priority=RecommendationEngine._priority_for_severity(insight.severity),
                column=insight.column,
                message=(
                    f"Coluna '{insight.column}' possui alta cardinalidade (unique ratio = {insight.metric_value:.1%})."
                ),
                action=(
                    f"Se '{insight.column}' é chave primária ou candidata, "
                    f"verificar índices e particionamento. Se não é chave, "
                    f"avaliar se é útil para análises agregadas ou se "
                    f"pode ser descartada para reduzir custo de "
                    f"armazenamento."
                ),
            ),
        ]

    @staticmethod
    def _recommend_constants(
        insight: Insight,
    ) -> list[Recommendation]:
        """Gera recomendações para colunas constantes ou quase-constantes.

        Args:
            insight: Insight das categorias :attr:`InsightCategory.CONSTANT`
                ou :attr:`InsightCategory.NEAR_CONSTANT`.

        Returns:
            Lista de recomendações de remoção ou investigação.
        """
        return [
            Recommendation(
                category=RecommendationCategory.SCHEMA,
                priority=RecommendationEngine._priority_for_severity(insight.severity),
                column=insight.column,
                message=(f"Coluna '{insight.column}' é constante ou praticamente constante."),
                action=(
                    f"Colunas constantes não agregam valor analítico. "
                    f"Considere remover '{insight.column}' do *dataset* "
                    f"de análise ou investigar se o valor constante é "
                    f"esperado (ex.: filtro aplicado na extração)."
                ),
            ),
        ]

    @staticmethod
    def _recommend_duplicates(
        insight: Insight,
    ) -> list[Recommendation]:
        """Gera recomendações para tratamento de duplicatas.

        Args:
            insight: Insight da categoria :attr:`InsightCategory.DUPLICATES`.

        Returns:
            Lista de recomendações de deduplicação.
        """
        return [
            Recommendation(
                category=RecommendationCategory.SCHEMA,
                priority=RecommendationEngine._priority_for_severity(insight.severity),
                column=None,
                message=(f"Taxa estimada de duplicatas de {insight.metric_value:.1%}."),
                action=(
                    "Identificar as chaves naturais do dataset e aplicar "
                    "deduplicação baseada em regras de negócio "
                    "(ex.: manter o registro mais recente, ou o de "
                    "maior completude). Documentar o critério utilizado."
                ),
            ),
        ]

    @staticmethod
    def _recommend_business_rule(
        insight: Insight,
    ) -> list[Recommendation]:
        """Gera recomendações para violações de regras de negócio.

        Args:
            insight: Insight da categoria :attr:`InsightCategory.BUSINESS_PATTERN`.

        Returns:
            Lista de recomendações de correção de regras de negócio.
        """
        return [
            Recommendation(
                category=RecommendationCategory.BUSINESS_RULE,
                priority=RecommendationEngine._priority_for_severity(insight.severity),
                column=insight.column,
                message=insight.message,
                action=(
                    f"Revisar os dados da coluna '{insight.column}' "
                    f"à luz das regras de negócio. Corrigir valores "
                    f"inválidos na fonte ou aplicar validação na "
                    f"camada de ingestão para evitar que novos dados "
                    f"violem as regras."
                ),
            ),
        ]

    @staticmethod
    def _recommend_zero_values(
        insight: Insight,
    ) -> list[Recommendation]:
        """Gera recomendações para valores zero atípicos.

        Args:
            insight: Insight da categoria :attr:`InsightCategory.ZERO_VALUES`.

        Returns:
            Lista de recomendações de investigação de valores zero.
        """
        return [
            Recommendation(
                category=RecommendationCategory.BUSINESS_RULE,
                priority=RecommendationEngine._priority_for_severity(insight.severity),
                column=insight.column,
                message=f"Valores zero atípicos identificados em '{insight.column}'.",
                action=(
                    f"Investigar se os valores zero em "
                    f"'{insight.column}' são legítimos (ex.: "
                    f"ausência do evento) ou indicam erro de "
                    f"preenchimento. Se esperados, documentar; "
                    f"se erro, aplicar correção na origem."
                ),
            ),
        ]

    def generate(
        self,
        insights: list[Insight],
        _quality: QualityScore,
    ) -> list[Recommendation]:
        """Gera recomendações de ação a partir dos insights da análise.

        Cada insight é convertido em uma ou mais recomendações acionáveis,
        categorizadas e priorizadas. A prioridade é derivada da severidade
        do insight original.

        Args:
            insights: Lista completa de insights gerados pela análise.
            quality: Pontuação de qualidade consolidada (usada para contexto
                adicional, embora não seja diretamente utilizada na conversão atual).

        Returns:
            Lista de :class:`Recommendation` ordenada por prioridade
            (mais urgentes primeiro).
        """
        recommendations: list[Recommendation] = []

        conversion_map: dict[InsightCategory, Callable[..., list[Recommendation]]] = {
            InsightCategory.NULLS: RecommendationEngine._recommend_nulls,
            InsightCategory.OUTLIERS: RecommendationEngine._recommend_outliers,
            InsightCategory.SKEWNESS: RecommendationEngine._recommend_skewness,
            InsightCategory.CARDINALITY: RecommendationEngine._recommend_cardinality,
            InsightCategory.CONSTANT: RecommendationEngine._recommend_constants,
            InsightCategory.NEAR_CONSTANT: RecommendationEngine._recommend_constants,
            InsightCategory.DUPLICATES: RecommendationEngine._recommend_duplicates,
            InsightCategory.BUSINESS_PATTERN: RecommendationEngine._recommend_business_rule,
            InsightCategory.ZERO_VALUES: RecommendationEngine._recommend_zero_values,
        }

        for insight in insights:
            converter = conversion_map.get(insight.category)
            if converter is not None:
                recommendations.extend(converter(insight))

        recommendations.sort(key=lambda rec: rec.priority)

        return recommendations
