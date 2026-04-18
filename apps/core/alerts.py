"""
Sistema de alertas financieras automáticas.
Genera y gestiona alertas basadas en el análisis financiero.
"""
from django.contrib.auth.models import User
from datetime import date
import logging

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Gestor de alertas financieras.
    Crea, actualiza y gestiona alertas para el usuario.
    """

    def generate_alerts(self, user: User, analysis: dict) -> list:
        """
        Genera alertas basadas en el análisis financiero.

        Args:
            user: Usuario de Django
            analysis: Resultado del análisis financiero completo

        Returns:
            Lista de alertas creadas
        """
        from apps.core.models import Alert

        alerts_created = []
        existing_titles = set(
            Alert.objects.filter(
                user=user,
                is_dismissed=False,
                created_at__date=date.today(),
            ).values_list('title', flat=True)
        )

        potential_alerts = []

        # Alertas de salud financiera
        potential_alerts.extend(
            self._health_alerts(analysis.get('health', {}))
        )

        # Alertas de categorías
        potential_alerts.extend(
            self._category_alerts(analysis.get('categories', {}))
        )

        # Alertas de anomalías
        potential_alerts.extend(
            self._anomaly_alerts(analysis.get('anomalies', []))
        )

        # Alertas de objetivos
        potential_alerts.extend(
            self._goal_alerts(analysis.get('goals_analysis', []))
        )

        # Alertas de tendencia
        potential_alerts.extend(
            self._trend_alerts(analysis.get('trend', {}))
        )

        # Crear alertas no duplicadas
        for alert_data in potential_alerts:
            if alert_data['title'] not in existing_titles:
                try:
                    alert = Alert.objects.create(
                        user=user,
                        alert_type=alert_data['alert_type'],
                        alert_category=alert_data['alert_category'],
                        title=alert_data['title'],
                        message=alert_data['message'],
                        metadata=alert_data.get('metadata', {}),
                    )
                    alerts_created.append(alert)
                    existing_titles.add(alert_data['title'])
                except Exception as e:
                    logger.error(f"Error creando alerta: {e}")

        return alerts_created

    def _health_alerts(self, health: dict) -> list:
        alerts = []
        status = health.get('status', '')
        score = health.get('score', 100)

        if status == 'risky':
            alerts.append({
                'alert_type': 'danger',
                'alert_category': 'negative_trend',
                'title': '🚨 Situación financiera crítica',
                'message': (
                    f'Tu score financiero es {score}/100. '
                    f'{health.get("description", "")} '
                    f'Revisa tus recomendaciones inmediatamente.'
                ),
                'metadata': {'score': score, 'status': status},
            })
        elif status == 'stable':
            alerts.append({
                'alert_type': 'warning',
                'alert_category': 'low_savings',
                'title': '⚠️ Finanzas estables con margen de mejora',
                'message': (
                    f'Tu score financiero es {score}/100. '
                    f'Hay oportunidades para mejorar tu situación.'
                ),
                'metadata': {'score': score, 'status': status},
            })
        elif status == 'healthy' and score >= 85:
            alerts.append({
                'alert_type': 'success',
                'alert_category': 'positive_trend',
                'title': '✅ ¡Excelente salud financiera!',
                'message': (
                    f'Tu score financiero es {score}/100. '
                    f'Sigue así y considera opciones de inversión.'
                ),
                'metadata': {'score': score, 'status': status},
            })

        return alerts

    def _category_alerts(self, categories: dict) -> list:
        alerts = []
        from apps.core.analyzers import CATEGORY_THRESHOLDS

        for category, threshold in CATEGORY_THRESHOLDS.items():
            cat_data = categories.get(category, {})
            percentage = cat_data.get('percentage', 0) / 100

            if percentage > threshold * 1.5:  # 50% sobre el límite
                alerts.append({
                    'alert_type': 'danger',
                    'alert_category': 'overspending',
                    'title': f'🔴 Gasto crítico en {category.capitalize()}',
                    'message': (
                        f'Estás gastando el {percentage*100:.1f}% en {category}. '
                        f'El límite recomendado es {threshold*100:.0f}%. '
                        f'Esto representa un exceso significativo.'
                    ),
                    'metadata': {
                        'category': category,
                        'percentage': percentage * 100,
                        'threshold': threshold * 100,
                    },
                })
            elif percentage > threshold:
                alerts.append({
                    'alert_type': 'warning',
                    'alert_category': 'overspending',
                    'title': f'⚠️ Gasto elevado en {category.capitalize()}',
                    'message': (
                        f'Estás gastando el {percentage*100:.1f}% en {category}. '
                        f'El límite recomendado es {threshold*100:.0f}%.'
                    ),
                    'metadata': {
                        'category': category,
                        'percentage': percentage * 100,
                        'threshold': threshold * 100,
                    },
                })

        return alerts

    def _anomaly_alerts(self, anomalies: list) -> list:
        alerts = []

        for anomaly in anomalies[:3]:  # Máximo 3 alertas de anomalías
            alerts.append({
                'alert_type': 'warning',
                'alert_category': 'overspending',
                'title': f'💸 Gasto inusual detectado',
                'message': (
                    f'Se detectó un gasto inusual: "{anomaly["description"]}" '
                    f'por ${anomaly["amount"]:,.0f} en {anomaly["category"]}. '
                    f'Es {anomaly["excess_percentage"]:.0f}% mayor al promedio.'
                ),
                'metadata': anomaly,
            })

        return alerts

    def _goal_alerts(self, goals_analysis: list) -> list:
        alerts = []

        for goal in goals_analysis:
            days_remaining = goal.get('days_remaining', 0)
            progress = goal.get('progress_percentage', 0)
            projection = goal.get('projection', {})

            if days_remaining <= 30 and progress < 90:
                alerts.append({
                                        'alert_type': 'danger',
                    'alert_category': 'goal_progress',
                    'title': f'⏰ Meta próxima a vencer: {goal["name"]}',
                    'message': (
                        f'Tu meta "{goal["name"]}" vence en {days_remaining} días '
                        f'y solo llevas el {progress:.1f}% completado. '
                        f'Necesitas acelerar tu ahorro.'
                    ),
                    'metadata': {
                        'goal_id': goal['id'],
                        'progress': progress,
                        'days_remaining': days_remaining,
                    },
                })
            elif progress >= 100:
                alerts.append({
                    'alert_type': 'success',
                    'alert_category': 'goal_progress',
                    'title': f'🎉 ¡Meta completada: {goal["name"]}!',
                    'message': (
                        f'¡Felicitaciones! Has completado tu meta "{goal["name"]}". '
                        f'Es momento de establecer un nuevo objetivo.'
                    ),
                    'metadata': {
                        'goal_id': goal['id'],
                        'progress': progress,
                    },
                })
            elif not projection.get('achievable', True):
                alerts.append({
                    'alert_type': 'warning',
                    'alert_category': 'goal_progress',
                    'title': f'🎯 Meta en riesgo: {goal["name"]}',
                    'message': (
                        f'Con tu ritmo actual de ahorro, no podrás alcanzar '
                        f'"{goal["name"]}". Considera aumentar tus ahorros mensuales.'
                    ),
                    'metadata': {
                        'goal_id': goal['id'],
                        'progress': progress,
                    },
                })

        return alerts

    def _trend_alerts(self, trend: dict) -> list:
        alerts = []
        status = trend.get('trend', '')

        if status == 'deteriorating':
            alerts.append({
                'alert_type': 'danger',
                'alert_category': 'negative_trend',
                'title': '📉 Tendencia financiera negativa',
                'message': (
                    f'{trend.get("message", "")} '
                    f'Tus ingresos han cambiado {trend.get("income_trend", 0):.1f}% '
                    f'y tus gastos {trend.get("expense_trend", 0):.1f}%.'
                ),
                'metadata': trend,
            })
        elif status == 'improving':
            alerts.append({
                'alert_type': 'success',
                'alert_category': 'positive_trend',
                'title': '📈 Tendencia financiera positiva',
                'message': (
                    f'{trend.get("message", "")} '
                    f'¡Sigue manteniendo estos buenos hábitos!'
                ),
                'metadata': trend,
            })

        return alerts

    def mark_all_read(self, user: User) -> int:
        """Marca todas las alertas del usuario como leídas."""
        from apps.core.models import Alert
        return Alert.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True)

    def dismiss_alert(self, user: User, alert_id: str) -> bool:
        """Descarta una alerta específica."""
        from apps.core.models import Alert
        try:
            alert = Alert.objects.get(id=alert_id, user=user)
            alert.is_dismissed = True
            alert.save()
            return True
        except Alert.DoesNotExist:
            return False

    def get_unread_count(self, user: User) -> int:
        """Retorna el número de alertas no leídas."""
        from apps.core.models import Alert
        return Alert.objects.filter(
            user=user,
            is_read=False,
            is_dismissed=False
        ).count()


# Instancia global del gestor de alertas
alert_manager = AlertManager()