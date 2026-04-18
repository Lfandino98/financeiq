"""
Motor de análisis financiero inteligente.
Toda la lógica de análisis, proyecciones y recomendaciones.
NO depende de APIs externas de IA.
"""
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
from collections import defaultdict
import calendar
import logging

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTES DEL MOTOR DE ANÁLISIS
# ============================================================

SAVINGS_RATE_HEALTHY = 0.20      # >= 20% = saludable
SAVINGS_RATE_STABLE = 0.10       # >= 10% = estable
SAVINGS_RATE_RISKY = 0.0         # < 10% = riesgoso

CATEGORY_THRESHOLDS = {
    'entretenimiento': 0.15,
    'comida': 0.40,
    'ropa': 0.10,
    'tecnologia': 0.15,
    'viajes': 0.20,
    'transporte': 0.20,
}

HEALTH_LABELS = {
    'healthy': {
        'label': 'Saludable',
        'color': 'green',
        'icon': '✅',
        'description': 'Excelente manejo financiero',
    },
    'stable': {
        'label': 'Estable',
        'color': 'yellow',
        'icon': '⚠️',
        'description': 'Finanzas aceptables, hay margen de mejora',
    },
    'risky': {
        'label': 'Riesgoso',
        'color': 'red',
        'icon': '🚨',
        'description': 'Situación financiera crítica, acción inmediata requerida',
    },
}


# ============================================================
# CALCULADORA FINANCIERA BASE
# ============================================================

class FinancialCalculator:
    """
    Cálculos financieros fundamentales.
    Todos los métodos son estáticos y puros (sin efectos secundarios).
    """

    @staticmethod
    def total_income(incomes: list) -> Decimal:
        """Suma total de ingresos."""
        return sum(
            (Decimal(str(i.amount)) for i in incomes),
            Decimal('0.00')
        )

    @staticmethod
    def total_expenses(expenses: list) -> Decimal:
        """Suma total de gastos."""
        return sum(
            (Decimal(str(e.amount)) for e in expenses),
            Decimal('0.00')
        )

    @staticmethod
    def net_savings(total_income: Decimal, total_expenses: Decimal) -> Decimal:
        """Ahorro neto = ingresos - gastos."""
        return total_income - total_expenses

    @staticmethod
    def savings_rate(total_income: Decimal, net_savings: Decimal) -> float:
        """
        Porcentaje de ahorro sobre ingresos.
        Retorna valor entre -1.0 y 1.0
        """
        if total_income == 0:
            return 0.0
        rate = float(net_savings / total_income)
        return round(rate, 4)

    @staticmethod
    def expense_ratio(total_expenses: Decimal, total_income: Decimal) -> float:
        """Ratio gastos/ingresos."""
        if total_income == 0:
            return 0.0
        return round(float(total_expenses / total_income), 4)

    @staticmethod
    def category_breakdown(expenses: list) -> dict:
        """
        Desglose de gastos por categoría.
        
        Returns:
            dict con nombre de categoría como clave y datos como valor
        """
        breakdown = defaultdict(lambda: {
            'total': Decimal('0.00'),
            'count': 0,
            'expenses': [],
        })

        for expense in expenses:
            cat_name = (
                expense.category.name
                if expense.category
                else 'Sin categoría'
            )
            breakdown[cat_name]['total'] += Decimal(str(expense.amount))
            breakdown[cat_name]['count'] += 1
            breakdown[cat_name]['expenses'].append({
                'id': str(expense.id),
                'description': expense.description,
                'amount': float(expense.amount),
                'date': expense.date.isoformat(),
            })

        return dict(breakdown)

    @staticmethod
    def category_percentages(
        breakdown: dict,
        total_expenses: Decimal
    ) -> dict:
        """Calcula porcentaje de cada categoría sobre el total."""
        if total_expenses == 0:
            return {}

        result = {}
        for category, data in breakdown.items():
            percentage = float(data['total'] / total_expenses * 100)
            result[category] = {
                'total': float(data['total']),
                'count': data['count'],
                'percentage': round(percentage, 2),
            }

        # Ordenar por porcentaje descendente
        return dict(
            sorted(result.items(), key=lambda x: x[1]['percentage'], reverse=True)
        )

    @staticmethod
    def daily_average_expense(
        total_expenses: Decimal,
        days: int
    ) -> Decimal:
        """Gasto promedio diario."""
        if days == 0:
            return Decimal('0.00')
        return total_expenses / days

    @staticmethod
    def monthly_average_income(
        total_income: Decimal,
        months: int
    ) -> Decimal:
        """Ingreso promedio mensual."""
        if months == 0:
            return Decimal('0.00')
        return total_income / months


# ============================================================
# EVALUADOR DE SALUD FINANCIERA
# ============================================================

class FinancialHealthEvaluator:
    """
    Evalúa el estado de salud financiera del usuario.
    Genera un score y clasificación basada en múltiples factores.
    """

    def evaluate(
        self,
        savings_rate: float,
        expense_ratio: float,
        category_percentages: dict,
        has_goals: bool = False,
    ) -> dict:
        """
        Evaluación completa de salud financiera.
        
        Returns:
            dict con status, score, factores y detalles
        """
        score = 100  # Empezamos con score perfecto
        factors = []

        # Factor 1: Tasa de ahorro (peso: 40 puntos)
        score, factors = self._evaluate_savings_rate(
            score, factors, savings_rate
        )

        # Factor 2: Ratio de gastos (peso: 20 puntos)
        score, factors = self._evaluate_expense_ratio(
            score, factors, expense_ratio
        )

        # Factor 3: Distribución de categorías (peso: 30 puntos)
        score, factors = self._evaluate_category_distribution(
            score, factors, category_percentages
        )

        # Factor 4: Objetivos financieros (peso: 10 puntos)
        score, factors = self._evaluate_goals(
            score, factors, has_goals
        )

        # Normalizar score
        score = max(0, min(100, score))

        # Determinar status
        status = self._determine_status(savings_rate, score)

        return {
            'status': status,
            'score': round(score, 1),
            'label': HEALTH_LABELS[status]['label'],
            'color': HEALTH_LABELS[status]['color'],
            'icon': HEALTH_LABELS[status]['icon'],
            'description': HEALTH_LABELS[status]['description'],
            'factors': factors,
        }

    def _evaluate_savings_rate(
        self,
        score: float,
        factors: list,
        savings_rate: float
    ) -> tuple:
        if savings_rate >= SAVINGS_RATE_HEALTHY:
            factors.append({
                'name': 'Tasa de ahorro',
                'status': 'good',
                'message': f'Ahorrando {savings_rate*100:.1f}% de ingresos ✅',
            })
        elif savings_rate >= SAVINGS_RATE_STABLE:
            score -= 20
            factors.append({
                'name': 'Tasa de ahorro',
                'status': 'warning',
                'message': f'Ahorrando {savings_rate*100:.1f}%, meta: 20% ⚠️',
            })
        elif savings_rate >= 0:
            score -= 35
            factors.append({
                'name': 'Tasa de ahorro',
                'status': 'danger',
                'message': f'Ahorro muy bajo: {savings_rate*100:.1f}% 🚨',
            })
        else:
            score -= 50
            factors.append({
                'name': 'Tasa de ahorro',
                'status': 'critical',
                'message': f'Gastos superan ingresos en {abs(savings_rate)*100:.1f}% 🔴',
            })
        return score, factors

    def _evaluate_expense_ratio(
        self,
        score: float,
        factors: list,
        expense_ratio: float
    ) -> tuple:
        if expense_ratio > 1.0:
            score -= 20
            factors.append({
                'name': 'Control de gastos',
                'status': 'critical',
                'message': 'Gastos superan ingresos 🔴',
            })
        elif expense_ratio > 0.90:
            score -= 10
            factors.append({
                'name': 'Control de gastos',
                'status': 'warning',
                'message': 'Gastos muy cercanos a ingresos ⚠️',
            })
        else:
            factors.append({
                'name': 'Control de gastos',
                'status': 'good',
                'message': 'Buen control de gastos ✅',
            })
        return score, factors

    def _evaluate_category_distribution(
        self,
        score: float,
        factors: list,
        category_percentages: dict
    ) -> tuple:
        problematic = []
        for category, threshold in CATEGORY_THRESHOLDS.items():
            cat_data = category_percentages.get(category, {})
            percentage = cat_data.get('percentage', 0) / 100

            if percentage > threshold:
                excess = (percentage - threshold) * 100
                score -= min(10, excess * 2)
                problematic.append(
                    f"{category} ({percentage*100:.1f}% > {threshold*100:.0f}%)"
                )

        if problematic:
            factors.append({
                'name': 'Distribución de gastos',
                'status': 'warning',
                'message': f'Exceso en: {", ".join(problematic)} ⚠️',
            })
        else:
            factors.append({
                'name': 'Distribución de gastos',
                'status': 'good',
                'message': 'Distribución de gastos equilibrada ✅',
            })
        return score, factors

    def _evaluate_goals(
        self,
        score: float,
        factors: list,
        has_goals: bool
    ) -> tuple:
        if has_goals:
            factors.append({
                'name': 'Objetivos financieros',
                'status': 'good',
                'message': 'Tienes metas financieras activas ✅',
            })
        else:
            score -= 10
            factors.append({
                'name': 'Objetivos financieros',
                'status': 'info',
                'message': 'Define metas financieras para mejorar ℹ️',
            })
        return score, factors

    def _determine_status(self, savings_rate: float, score: float) -> str:
        if savings_rate >= SAVINGS_RATE_HEALTHY and score >= 70:
            return 'healthy'
        elif savings_rate >= SAVINGS_RATE_STABLE and score >= 40:
            return 'stable'
        else:
            return 'risky'


# ============================================================
# GENERADOR DE RECOMENDACIONES
# ============================================================

class RecommendationEngine:
    """
    Motor de recomendaciones financieras basado en reglas.
    Genera recomendaciones personalizadas según el perfil del usuario.
    """

    def generate(
        self,
        savings_rate: float,
        category_percentages: dict,
        total_income: Decimal,
        total_expenses: Decimal,
        health_status: str,
        goals: list = None,
    ) -> list:
        """
        Genera lista de recomendaciones priorizadas.
        
        Returns:
            Lista de dicts con recomendaciones ordenadas por prioridad
        """
        recommendations = []

        # Recomendaciones por ahorro
        recommendations.extend(
            self._savings_recommendations(savings_rate, total_income)
        )

        # Recomendaciones por categorías
        recommendations.extend(
            self._category_recommendations(category_percentages, total_expenses)
        )

        # Recomendaciones por estado general
        recommendations.extend(
            self._health_recommendations(health_status, savings_rate)
        )

        # Recomendaciones por objetivos
        if goals:
            recommendations.extend(
                self._goal_recommendations(goals, savings_rate, total_income)
            )

        # Ordenar por prioridad y eliminar duplicados
        seen = set()
        unique_recommendations = []
        for rec in sorted(recommendations, key=lambda x: x['priority']):
            key = rec['title']
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)

        return unique_recommendations[:8]  # Máximo 8 recomendaciones

    def _savings_recommendations(
        self,
        savings_rate: float,
        total_income: Decimal
    ) -> list:
        recs = []

        if savings_rate < 0:
            recs.append({
                'title': '🚨 Déficit financiero crítico',
                'description': (
                    f'Tus gastos superan tus ingresos en '
                    f'{abs(savings_rate)*100:.1f}%. '
                                        f'Debes reducir gastos inmediatamente o buscar '
                    f'fuentes adicionales de ingreso.'
                ),
                'action': 'Revisa todos tus gastos y elimina los no esenciales',
                'priority': 1,
                'type': 'danger',
                'category': 'savings',
            })
        elif savings_rate < SAVINGS_RATE_STABLE:
            recs.append({
                'title': '⚠️ Ahorro insuficiente',
                'description': (
                    f'Estás ahorrando solo el {savings_rate*100:.1f}% '
                    f'de tus ingresos. La meta recomendada es el 20%.'
                ),
                'action': 'Intenta reducir gastos no esenciales un 10%',
                'priority': 2,
                'type': 'warning',
                'category': 'savings',
            })
        elif savings_rate < SAVINGS_RATE_HEALTHY:
            monthly_gap = float(total_income) * (SAVINGS_RATE_HEALTHY - savings_rate)
            recs.append({
                'title': '💡 Mejora tu tasa de ahorro',
                'description': (
                    f'Ahorras el {savings_rate*100:.1f}%. '
                    f'Con ${monthly_gap:,.0f} más al mes alcanzarías el 20%.'
                ),
                'action': f'Busca reducir ${monthly_gap:,.0f} en gastos variables',
                'priority': 3,
                'type': 'info',
                'category': 'savings',
            })
        else:
            recs.append({
                'title': '✅ Excelente tasa de ahorro',
                'description': (
                    f'Ahorras el {savings_rate*100:.1f}% de tus ingresos. '
                    f'Considera invertir el excedente.'
                ),
                'action': 'Explora opciones de inversión para hacer crecer tu dinero',
                'priority': 8,
                'type': 'success',
                'category': 'savings',
            })

        return recs

    def _category_recommendations(
        self,
        category_percentages: dict,
        total_expenses: Decimal
    ) -> list:
        recs = []

        for category, threshold in CATEGORY_THRESHOLDS.items():
            cat_data = category_percentages.get(category, {})
            percentage = cat_data.get('percentage', 0) / 100
            amount = cat_data.get('total', 0)

            if percentage > threshold:
                excess_pct = (percentage - threshold) * 100
                excess_amount = float(total_expenses) * (percentage - threshold)

                recs.append({
                    'title': f'📊 Gasto elevado en {category.capitalize()}',
                    'description': (
                        f'Gastas el {percentage*100:.1f}% en {category} '
                        f'(límite recomendado: {threshold*100:.0f}%). '
                        f'Exceso aproximado: ${excess_amount:,.0f}'
                    ),
                    'action': (
                        f'Reduce gastos en {category} un {excess_pct:.1f}% '
                        f'para equilibrar tu presupuesto'
                    ),
                    'priority': 4,
                    'type': 'warning',
                    'category': category,
                    'excess_amount': round(excess_amount, 2),
                })

        # Detectar categoría dominante
        if category_percentages:
            dominant = max(
                category_percentages.items(),
                key=lambda x: x[1]['percentage']
            )
            dom_name, dom_data = dominant
            if dom_data['percentage'] > 50:
                recs.append({
                    'title': f'🔍 Categoría dominante: {dom_name.capitalize()}',
                    'description': (
                        f'{dom_name.capitalize()} representa el '
                        f'{dom_data["percentage"]:.1f}% de tus gastos totales.'
                    ),
                    'action': (
                        f'Diversifica tus gastos reduciendo la dependencia '
                        f'en {dom_name}'
                    ),
                    'priority': 5,
                    'type': 'info',
                    'category': dom_name,
                })

        return recs

    def _health_recommendations(
        self,
        health_status: str,
        savings_rate: float
    ) -> list:
        recs = []

        if health_status == 'risky':
            recs.append({
                'title': '🆘 Plan de emergencia financiera',
                'description': (
                    'Tu situación financiera requiere atención inmediata. '
                    'Crea un presupuesto estricto y elimina gastos superfluos.'
                ),
                'action': 'Aplica la regla 50/30/20: necesidades/deseos/ahorro',
                'priority': 1,
                'type': 'danger',
                'category': 'general',
            })
        elif health_status == 'stable':
            recs.append({
                'title': '📈 Optimiza tus finanzas',
                'description': (
                    'Tus finanzas son estables pero hay margen de mejora. '
                    'Pequeños ajustes pueden tener gran impacto.'
                ),
                'action': 'Identifica 3 gastos no esenciales que puedas eliminar',
                'priority': 4,
                'type': 'info',
                'category': 'general',
            })

        # Recomendación de fondo de emergencia
        if savings_rate < 0.15:
            recs.append({
                'title': '🛡️ Construye tu fondo de emergencia',
                'description': (
                    'Un fondo de emergencia de 3-6 meses de gastos '
                    'te protege ante imprevistos.'
                ),
                'action': 'Abre una cuenta de ahorro separada para emergencias',
                'priority': 3,
                'type': 'warning',
                'category': 'emergency_fund',
            })

        return recs

    def _goal_recommendations(
        self,
        goals: list,
        savings_rate: float,
        total_income: Decimal
    ) -> list:
        recs = []

        for goal in goals:
            if goal.status != 'active':
                continue

            progress = goal.progress_percentage
            days_remaining = (goal.target_date - date.today()).days

            if days_remaining <= 0:
                recs.append({
                    'title': f'⏰ Meta vencida: {goal.name}',
                    'description': (
                        f'La meta "{goal.name}" venció. '
                        f'Progreso alcanzado: {progress:.1f}%'
                    ),
                    'action': 'Revisa y actualiza la fecha de tu meta',
                    'priority': 2,
                    'type': 'warning',
                    'category': 'goals',
                })
            elif progress < 25 and days_remaining < 90:
                monthly_needed = float(goal.remaining_amount) / max(days_remaining / 30, 1)
                recs.append({
                    'title': f'🎯 Meta en riesgo: {goal.name}',
                    'description': (
                        f'Solo llevas el {progress:.1f}% de "{goal.name}" '
                        f'con {days_remaining} días restantes.'
                    ),
                    'action': (
                        f'Necesitas ahorrar ${monthly_needed:,.0f}/mes '
                        f'para alcanzar tu meta'
                    ),
                    'priority': 3,
                    'type': 'warning',
                    'category': 'goals',
                })
            elif progress >= 75:
                recs.append({
                    'title': f'🎉 ¡Casi logras tu meta: {goal.name}!',
                    'description': (
                        f'Llevas el {progress:.1f}% de "{goal.name}". '
                        f'¡Sigue así!'
                    ),
                    'action': f'Te faltan ${float(goal.remaining_amount):,.0f} para completar tu meta',
                    'priority': 7,
                    'type': 'success',
                    'category': 'goals',
                })

        return recs


# ============================================================
# MOTOR DE PROYECCIONES FINANCIERAS
# ============================================================

class FinancialProjectionEngine:
    """
    Genera proyecciones financieras basadas en comportamiento actual.
    Usa modelos matemáticos simples pero efectivos.
    """

    def project(
        self,
        monthly_income: Decimal,
        monthly_expenses: Decimal,
        current_savings: Decimal,
        months_list: list = None,
    ) -> dict:
        """
        Proyecta el estado financiero a futuro.
        
        Args:
            monthly_income: Ingreso mensual promedio
            monthly_expenses: Gasto mensual promedio
            current_savings: Ahorro acumulado actual
            months_list: Lista de meses a proyectar [3, 6, 12]
        
        Returns:
            dict con proyecciones para cada período
        """
        if months_list is None:
            months_list = [3, 6, 12]

        monthly_net = monthly_income - monthly_expenses
        projections = {}

        for months in months_list:
            projected_savings = current_savings + (monthly_net * months)
            projected_income = monthly_income * months
            projected_expenses = monthly_expenses * months

            # Escenarios
            optimistic = self._optimistic_scenario(
                monthly_income, monthly_expenses, current_savings, months
            )
            pessimistic = self._pessimistic_scenario(
                monthly_income, monthly_expenses, current_savings, months
            )

            projections[f'{months}_months'] = {
                'months': months,
                'label': self._get_period_label(months),
                'projected_income': round(float(projected_income), 2),
                'projected_expenses': round(float(projected_expenses), 2),
                'projected_savings': round(float(projected_savings), 2),
                'monthly_net': round(float(monthly_net), 2),
                'scenarios': {
                    'optimistic': round(float(optimistic), 2),
                    'base': round(float(projected_savings), 2),
                    'pessimistic': round(float(pessimistic), 2),
                },
                'end_date': (
                    date.today() + timedelta(days=months * 30)
                ).isoformat(),
            }

        return projections

    def _optimistic_scenario(
        self,
        monthly_income: Decimal,
        monthly_expenses: Decimal,
        current_savings: Decimal,
        months: int,
        improvement_rate: float = 0.05,
    ) -> Decimal:
        """Escenario optimista: reducción del 5% en gastos."""
        optimistic_expenses = monthly_expenses * Decimal(str(1 - improvement_rate))
        monthly_net = monthly_income - optimistic_expenses
        return current_savings + (monthly_net * months)

    def _pessimistic_scenario(
        self,
        monthly_income: Decimal,
        monthly_expenses: Decimal,
        current_savings: Decimal,
        months: int,
        increase_rate: float = 0.05,
    ) -> Decimal:
        """Escenario pesimista: aumento del 5% en gastos."""
        pessimistic_expenses = monthly_expenses * Decimal(str(1 + increase_rate))
        monthly_net = monthly_income - pessimistic_expenses
        return current_savings + (monthly_net * months)

    def _get_period_label(self, months: int) -> str:
        labels = {3: '3 meses', 6: '6 meses', 12: '1 año'}
        return labels.get(months, f'{months} meses')

    def project_goal_completion(
        self,
        goal,
        monthly_savings: Decimal,
    ) -> dict:
        """
        Proyecta cuándo se completará un objetivo financiero.
        """
        remaining = goal.remaining_amount

        if monthly_savings <= 0:
            return {
                'achievable': False,
                'message': 'No es posible con el ahorro actual',
                'months_needed': None,
                'completion_date': None,
            }

        months_needed = float(remaining / monthly_savings)
        completion_date = date.today() + timedelta(days=int(months_needed * 30))

        return {
            'achievable': True,
            'months_needed': round(months_needed, 1),
            'completion_date': completion_date.isoformat(),
            'monthly_needed': float(monthly_savings),
            'message': (
                f'Alcanzarás tu meta en {months_needed:.1f} meses '
                f'({completion_date.strftime("%B %Y")})'
            ),
        }


# ============================================================
# DETECTOR DE ANOMALÍAS Y TENDENCIAS
# ============================================================

class TrendAnalyzer:
    """
    Analiza tendencias y detecta anomalías en el comportamiento financiero.
    """

    def analyze_trend(self, snapshots: list) -> dict:
        """
        Analiza la tendencia financiera basada en snapshots históricos.
        
        Args:
            snapshots: Lista de MonthlySnapshot ordenados por fecha
        
        Returns:
            dict con tendencia y análisis
        """
        if len(snapshots) < 2:
            return {
                'trend': 'insufficient_data',
                'label': 'Datos insuficientes',
                'message': 'Necesitas al menos 2 meses de datos',
                'income_trend': 0,
                'expense_trend': 0,
                'savings_trend': 0,
            }

        # Calcular tendencias
        income_values = [float(s.total_income) for s in snapshots]
        expense_values = [float(s.total_expenses) for s in snapshots]
        savings_values = [float(s.net_savings) for s in snapshots]

        income_trend = self._calculate_trend(income_values)
        expense_trend = self._calculate_trend(expense_values)
        savings_trend = self._calculate_trend(savings_values)

        # Determinar tendencia general
        overall_trend = self._determine_overall_trend(
            income_trend, expense_trend, savings_trend
        )

        return {
            'trend': overall_trend['status'],
            'label': overall_trend['label'],
            'message': overall_trend['message'],
            'income_trend': round(income_trend, 2),
            'expense_trend': round(expense_trend, 2),
            'savings_trend': round(savings_trend, 2),
            'months_analyzed': len(snapshots),
        }

    def _calculate_trend(self, values: list) -> float:
        """
        Calcula la tendencia porcentual entre primer y último valor.
        Positivo = crecimiento, Negativo = decrecimiento.
        """
        if len(values) < 2 or values[0] == 0:
            return 0.0

        first = values[0]
        last = values[-1]
        return ((last - first) / abs(first)) * 100

    def _determine_overall_trend(
        self,
        income_trend: float,
        expense_trend: float,
                savings_trend: float,
    ) -> dict:
        """Determina la tendencia general del usuario."""

        # Caso ideal: ingresos suben, gastos bajan, ahorro sube
        if income_trend >= 0 and expense_trend <= 0 and savings_trend >= 0:
            return {
                'status': 'improving',
                'label': 'Mejorando',
                'message': 'Tus finanzas muestran una tendencia positiva 📈',
            }
        # Caso crítico: ingresos bajan, gastos suben
        elif income_trend < 0 and expense_trend > 0:
            return {
                'status': 'deteriorating',
                'label': 'Deteriorando',
                'message': 'Tus finanzas muestran una tendencia negativa 📉',
            }
        # Caso estable
        elif abs(savings_trend) < 5:
            return {
                'status': 'stable',
                'label': 'Estable',
                'message': 'Tus finanzas se mantienen estables ➡️',
            }
        # Caso mixto positivo
        elif savings_trend > 0:
            return {
                'status': 'slightly_improving',
                'label': 'Levemente mejorando',
                'message': 'Pequeña mejora en tus finanzas 📊',
            }
        else:
            return {
                'status': 'slightly_deteriorating',
                'label': 'Levemente deteriorando',
                'message': 'Leve deterioro en tus finanzas, toma acción ⚠️',
            }

    def detect_anomalies(self, expenses: list, avg_monthly: Decimal) -> list:
        """
        Detecta gastos anómalos comparando con el promedio mensual.
        """
        anomalies = []
        threshold = float(avg_monthly) * 0.30  # 30% sobre el promedio

        for expense in expenses:
            if float(expense.amount) > threshold:
                anomalies.append({
                    'id': str(expense.id),
                    'description': expense.description,
                    'amount': float(expense.amount),
                    'date': expense.date.isoformat(),
                    'category': (
                        expense.category.name
                        if expense.category else 'Sin categoría'
                    ),
                    'excess_amount': float(expense.amount) - threshold,
                    'excess_percentage': round(
                        (float(expense.amount) - threshold) / threshold * 100, 1
                    ),
                })

        return sorted(anomalies, key=lambda x: x['amount'], reverse=True)


# ============================================================
# ORQUESTADOR PRINCIPAL DEL ANÁLISIS
# ============================================================

class FinancialAnalysisOrchestrator:
    """
    Orquestador principal que coordina todos los motores de análisis.
    Punto de entrada único para el análisis financiero completo.
    """

    def __init__(self):
        self.calculator = FinancialCalculator()
        self.health_evaluator = FinancialHealthEvaluator()
        self.recommendation_engine = RecommendationEngine()
        self.projection_engine = FinancialProjectionEngine()
        self.trend_analyzer = TrendAnalyzer()

    def full_analysis(
        self,
        incomes: list,
        expenses: list,
        goals: list = None,
        snapshots: list = None,
        period_days: int = 30,
    ) -> dict:
        """
        Análisis financiero completo.

        Args:
            incomes: Lista de objetos Income
            expenses: Lista de objetos Expense
            goals: Lista de objetos FinancialGoal
            snapshots: Lista de MonthlySnapshot históricos
            period_days: Días del período analizado

        Returns:
            dict completo con todo el análisis
        """
        goals = goals or []
        snapshots = snapshots or []

        # ── Cálculos base ──────────────────────────────────────
        total_income = self.calculator.total_income(incomes)
        total_expenses = self.calculator.total_expenses(expenses)
        net_savings = self.calculator.net_savings(total_income, total_expenses)
        savings_rate = self.calculator.savings_rate(total_income, net_savings)
        expense_ratio = self.calculator.expense_ratio(total_expenses, total_income)
        daily_avg = self.calculator.daily_average_expense(
            total_expenses, period_days
        )
        months = max(Decimal(period_days) / Decimal("30"), Decimal("1"))

        monthly_income = self.calculator.monthly_average_income(
            total_income, months
        )
        monthly_expenses = daily_avg * 30

        # ── Análisis por categorías ────────────────────────────
        breakdown = self.calculator.category_breakdown(expenses)
        category_pct = self.calculator.category_percentages(
            breakdown, total_expenses
        )

        # ── Salud financiera ───────────────────────────────────
        health = self.health_evaluator.evaluate(
            savings_rate=savings_rate,
            expense_ratio=expense_ratio,
            category_percentages=category_pct,
            has_goals=len(goals) > 0,
        )

        # ── Recomendaciones ────────────────────────────────────
        recommendations = self.recommendation_engine.generate(
            savings_rate=savings_rate,
            category_percentages=category_pct,
            total_income=total_income,
            total_expenses=total_expenses,
            health_status=health['status'],
            goals=goals,
        )

        # ── Proyecciones ───────────────────────────────────────
        projections = self.projection_engine.project(
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            current_savings=net_savings,
        )

        # ── Tendencias ─────────────────────────────────────────
        trend = self.trend_analyzer.analyze_trend(snapshots)

        # ── Anomalías ──────────────────────────────────────────
        anomalies = self.trend_analyzer.detect_anomalies(
            expenses, monthly_expenses
        )

        # ── Análisis de objetivos ──────────────────────────────
        goals_analysis = self._analyze_goals(goals, net_savings / 30)

        return {
            'summary': {
                'total_income': float(total_income),
                'total_expenses': float(total_expenses),
                'net_savings': float(net_savings),
                'savings_rate': round(savings_rate * 100, 2),
                'expense_ratio': round(expense_ratio * 100, 2),
                'daily_avg_expense': float(daily_avg),
                'monthly_income': float(monthly_income),
                'monthly_expenses': float(monthly_expenses),
                'period_days': period_days,
                'transactions_count': len(incomes) + len(expenses),
            },
            'health': health,
            'categories': category_pct,
            'recommendations': recommendations,
            'projections': projections,
            'trend': trend,
            'anomalies': anomalies[:5],
            'goals_analysis': goals_analysis,
            'generated_at': date.today().isoformat(),
        }

    def _analyze_goals(self, goals: list, daily_savings: Decimal) -> list:
        """Analiza el progreso de cada objetivo financiero."""
        monthly_savings = daily_savings * 30
        analysis = []

        for goal in goals:
            if goal.status != 'active':
                continue

            projection = self.projection_engine.project_goal_completion(
                goal=goal,
                monthly_savings=monthly_savings,
            )

            analysis.append({
                'id': str(goal.id),
                'name': goal.name,
                'target_amount': float(goal.target_amount),
                'current_amount': float(goal.current_amount),
                'remaining_amount': float(goal.remaining_amount),
                'progress_percentage': round(goal.progress_percentage, 1),
                'target_date': goal.target_date.isoformat(),
                'days_remaining': (goal.target_date - date.today()).days,
                'projection': projection,
                'status': goal.status,
                'goal_type': goal.goal_type,
            })

        return analysis


# Instancia global del orquestador
financial_orchestrator = FinancialAnalysisOrchestrator()