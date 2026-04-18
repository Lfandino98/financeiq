"""
Capa de servicios: orquesta modelos, análisis y alertas.
Las vistas SOLO deben llamar a estos servicios.
"""
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import logging

from apps.core.models import (
    Category, Income, Expense,
    FinancialGoal, Alert, MonthlySnapshot
)
from apps.core.classifiers import expense_classifier
from apps.core.analyzers import financial_orchestrator
from apps.core.alerts import alert_manager

logger = logging.getLogger(__name__)


# ============================================================
# SERVICIO DE CATEGORÍAS
# ============================================================

class CategoryService:

    @staticmethod
    def get_or_create_system_categories() -> list:
        """
        Crea las categorías del sistema si no existen.
        Se llama al inicializar la aplicación.
        """
        system_categories = [
            {
                'name': 'Transporte',
                'slug': 'transporte',
                'icon': '🚗',
                'color': '#3b82f6',
                'category_type': 'expense',
                'keywords': ['uber', 'taxi', 'bus', 'metro', 'gasolina'],
            },
            {
                'name': 'Comida',
                'slug': 'comida',
                'icon': '🍔',
                'color': '#f59e0b',
                'category_type': 'expense',
                'keywords': ['restaurante', 'pizza', 'mercado', 'supermercado'],
            },
            {
                'name': 'Entretenimiento',
                'slug': 'entretenimiento',
                'icon': '🎬',
                'color': '#8b5cf6',
                'category_type': 'expense',
                'keywords': ['netflix', 'cine', 'spotify', 'juego'],
            },
            {
                'name': 'Salud',
                'slug': 'salud',
                'icon': '🏥',
                'color': '#10b981',
                'category_type': 'expense',
                'keywords': ['farmacia', 'doctor', 'gym', 'medicina'],
            },
            {
                'name': 'Educación',
                'slug': 'educacion',
                'icon': '📚',
                'color': '#06b6d4',
                'category_type': 'expense',
                'keywords': ['universidad', 'curso', 'libro', 'udemy'],
            },
            {
                'name': 'Hogar',
                'slug': 'hogar',
                'icon': '🏠',
                'color': '#f97316',
                'category_type': 'expense',
                'keywords': ['arriendo', 'servicios', 'agua', 'luz'],
            },
            {
                'name': 'Ropa',
                'slug': 'ropa',
                'icon': '👕',
                'color': '#ec4899',
                'category_type': 'expense',
                'keywords': ['ropa', 'zapatos', 'zara', 'nike'],
            },
            {
                'name': 'Tecnología',
                'slug': 'tecnologia',
                'icon': '💻',
                'color': '#6366f1',
                'category_type': 'expense',
                'keywords': ['celular', 'computador', 'apple', 'samsung'],
            },
            {
                'name': 'Viajes',
                'slug': 'viajes',
                'icon': '✈️',
                'color': '#14b8a6',
                'category_type': 'expense',
                'keywords': ['hotel', 'airbnb', 'vuelo', 'viaje'],
            },
            {
                'name': 'Finanzas',
                'slug': 'finanzas',
                'icon': '💳',
                'color': '#64748b',
                'category_type': 'both',
                'keywords': ['banco', 'transferencia', 'credito'],
            },
            {
                'name': 'Salario',
                'slug': 'salario',
                'icon': '💼',
                'color': '#22c55e',
                'category_type': 'income',
                'keywords': ['salario', 'sueldo', 'nomina', 'pago'],
            },
            {
                'name': 'Freelance',
                'slug': 'freelance',
                'icon': '💡',
                'color': '#a855f7',
                'category_type': 'income',
                'keywords': ['freelance', 'proyecto', 'cliente', 'honorarios'],
            },
            {
                'name': 'Otros',
                'slug': 'otros',
                'icon': '📦',
                'color': '#94a3b8',
                'category_type': 'both',
                'keywords': [],
            },
        ]

        created = []
        for cat_data in system_categories:
            category, was_created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                is_system=True,
                defaults={
                    'user': None,
                    **cat_data,
                }
            )
            if was_created:
                created.append(category)

        return created

    @staticmethod
    def get_categories_for_user(user: User) -> list:
        """Retorna todas las categorías disponibles para el usuario."""
        return list(
            Category.objects.filter(
                Q(is_system=True) | Q(user=user)
            ).order_by('name')
        )

    @staticmethod
    def create_user_category(user: User, data: dict) -> Category:
        """Crea una categoría personalizada para el usuario."""
        from django.utils.text import slugify
        slug = slugify(data['name'])

        # Asegurar slug único para el usuario
        base_slug = slug
        counter = 1
        while Category.objects.filter(user=user, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return Category.objects.create(
            user=user,
            slug=slug,
            is_system=False,
            **data,
        )

    @staticmethod
    def suggest_category_for_description(description: str) -> dict:
        """
        Sugiere una categoría basada en la descripción del gasto.
        Usa el clasificador inteligente.
        """
        classification = expense_classifier.classify(description)
        suggested_slug = classification['category']

        try:
            category = Category.objects.get(
                slug=suggested_slug,
                is_system=True
            )
            return {
                'category': category,
                'confidence': classification['confidence'],
                'method': classification['method'],
                'alternatives': classification['alternatives'],
            }
        except Category.DoesNotExist:
            otros = Category.objects.filter(slug='otros', is_system=True).first()
            return {
                'category': otros,
                'confidence': 0.0,
                'method': 'fallback',
                'alternatives': [],
            }


# ============================================================
# SERVICIO DE INGRESOS
# ============================================================

class IncomeService:

    @staticmethod
    def create_income(user: User, data: dict) -> Income:
        """Crea un nuevo ingreso."""
        return Income.objects.create(user=user, **data)

    @staticmethod
    def update_income(income: Income, data: dict) -> Income:
        """Actualiza un ingreso existente."""
        for field, value in data.items():
            setattr(income, field, value)
        income.save()
        return income

    @staticmethod
    def delete_income(income: Income) -> None:
        """Elimina un ingreso."""
        income.delete()

    @staticmethod
    def get_user_incomes(
        user: User,
        start_date: date = None,
        end_date: date = None,
        category_id: str = None,
    ) -> list:
        """Retorna ingresos filtrados del usuario."""
        qs = Income.objects.filter(user=user).select_related('category')

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        if category_id:
            qs = qs.filter(category_id=category_id)

        return list(qs.order_by('-date'))

    @staticmethod
    def get_monthly_income_summary(user: User, year: int, month: int) -> dict:
        """Resumen de ingresos de un mes específico."""
        incomes = Income.objects.filter(
            user=user,
            date__year=year,
            date__month=month,
        )
        total = incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return {
            'year': year,
            'month': month,
            'total': float(total),
            'count': incomes.count(),
            'incomes': list(incomes.values(
                'id', 'amount', 'description', 'date', 'source'
            )),
        }


# ============================================================
# SERVICIO DE GASTOS
# ============================================================

class ExpenseService:

    @staticmethod
    def create_expense(user: User, data: dict, auto_classify: bool = True) -> Expense:
        """
        Crea un nuevo gasto.
        Si auto_classify=True, intenta clasificar automáticamente.
        """
        if auto_classify and not data.get('category'):
            suggestion = CategoryService.suggest_category_for_description(
                data.get('description', '')
            )
            if suggestion['category'] and suggestion['confidence'] > 0.3:
                data['category'] = suggestion['category']
                data['auto_classified'] = True

        return Expense.objects.create(user=user, **data)

    @staticmethod
    def update_expense(expense: Expense, data: dict) -> Expense:
        """Actualiza un gasto existente."""
        for field, value in data.items():
            setattr(expense, field, value)
        expense.save()
        return expense

    @staticmethod
    def delete_expense(expense: Expense) -> None:
        """Elimina un gasto."""
        expense.delete()

    @staticmethod
    def get_user_expenses(
        user: User,
        start_date: date = None,
        end_date: date = None,
        category_id: str = None,
        is_essential: bool = None,
    ) -> list:
        """Retorna gastos filtrados del usuario."""
        qs = Expense.objects.filter(user=user).select_related('category')

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if is_essential is not None:
            qs = qs.filter(is_essential=is_essential)

        return list(qs.order_by('-date'))

    @staticmethod
    def get_monthly_expense_summary(user: User, year: int, month: int) -> dict:
        """Resumen de gastos de un mes específico."""
        expenses = Expense.objects.filter(
            user=user,
            date__year=year,
            date__month=month,
        ).select_related('category')

        total = expenses.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # Agrupar por categoría
        by_category = {}
        for expense in expenses:
            cat_name = (
                expense.category.name
                if expense.category else 'Sin categoría'
            )
            if cat_name not in by_category:
                by_category[cat_name] = {
                    'total': Decimal('0.00'),
                    'count': 0,
                    'icon': expense.category.icon if expense.category else '📦',
                    'color': expense.category.color if expense.category else '#94a3b8',
                }
            by_category[cat_name]['total'] += expense.amount
            by_category[cat_name]['count'] += 1

        return {
            'year': year,
            'month': month,
            'total': float(total),
            'count': expenses.count(),
            'by_category': {
                k: {**v, 'total': float(v['total'])}
                for k, v in by_category.items()
            },
        }


# ============================================================
# SERVICIO DE ANÁLISIS FINANCIERO
# ============================================================

class FinancialAnalysisService:

    @staticmethod
    def get_period_dates(period: str = 'month') -> tuple:
        """
        Retorna fechas de inicio y fin según el período.

        Args:
            period: 'week', 'month', 'quarter', 'year', 'all'

        Returns:
            Tuple (start_date, end_date)
        """
        today = date.today()

        periods = {
            'week': (today - timedelta(days=7), today),
            'month': (today.replace(day=1), today),
            'quarter': (
                (today - timedelta(days=90)).replace(day=1),
                today
            ),
            'year': (today.replace(month=1, day=1), today),
            'all': (date(2000, 1, 1), today),
        }

        return periods.get(period, periods['month'])

    @staticmethod
    def run_full_analysis(
        user: User,
        period: str = 'month',
        start_date: date = None,
        end_date: date = None,
    ) -> dict:
        """
        Ejecuta el análisis financiero completo para un usuario.

        Args:
            user: Usuario de Django
            period: Período de análisis
            start_date: Fecha inicio personalizada
            end_date: Fecha fin personalizada

        Returns:
            dict con análisis completo
        """
        # Determinar fechas
        if not start_date or not end_date:
            start_date, end_date = FinancialAnalysisService.get_period_dates(period)

        period_days = (end_date - start_date).days + 1

        # Obtener datos
        incomes = list(
            Income.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            ).select_related('category')
        )

        expenses = list(
            Expense.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            ).select_related('category')
        )

        goals = list(
            FinancialGoal.objects.filter(
                user=user,
                status='active',
            )
        )

        snapshots = list(
            MonthlySnapshot.objects.filter(
                user=user,
            ).order_by('year', 'month')[:12]
        )

        # Ejecutar análisis
        analysis = financial_orchestrator.full_analysis(
            incomes=incomes,
            expenses=expenses,
            goals=goals,
            snapshots=snapshots,
            period_days=period_days,
        )

        # Agregar metadata del período
        analysis['period'] = {
            'type': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': period_days,
        }

        # Generar alertas automáticas
        try:
            alert_manager.generate_alerts(user=user, analysis=analysis)
        except Exception as e:
            logger.error(f"Error generando alertas para {user.username}: {e}")

        return analysis

    @staticmethod
    def get_dashboard_data(user: User) -> dict:
        """
        Obtiene todos los datos necesarios para el dashboard.
        Optimizado para minimizar queries a la base de datos.
        """
        today = date.today()
        current_month_start = today.replace(day=1)

        # Análisis del mes actual
        current_analysis = FinancialAnalysisService.run_full_analysis(
            user=user,
            period='month',
        )

        # Análisis del mes anterior para comparación
        last_month_end = current_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        last_month_analysis = FinancialAnalysisService.run_full_analysis(
            user=user,
            start_date=last_month_start,
            end_date=last_month_end,
        )

        # Alertas no leídas
        unread_alerts = list(
            Alert.objects.filter(
                user=user,
                is_read=False,
                is_dismissed=False,
            ).order_by('-created_at')[:5]
        )

        # Últimas transacciones
        recent_expenses = list(
            Expense.objects.filter(user=user)
            .select_related('category')
            .order_by('-date', '-created_at')[:5]
        )

        recent_incomes = list(
            Income.objects.filter(user=user)
            .select_related('category')
            .order_by('-date', '-created_at')[:5]
        )

        # Objetivos activos
        active_goals = list(
            FinancialGoal.objects.filter(
                user=user,
                status='active',
            ).order_by('target_date')[:4]
        )

        # Comparación mes actual vs anterior
        current_summary = current_analysis.get('summary', {})
        last_summary = last_month_analysis.get('summary', {})

        def calc_change(current, previous):
            if previous == 0:
                return 0
            return round(((current - previous) / abs(previous)) * 100, 1)

        comparison = {
            'income_change': calc_change(
                current_summary.get('total_income', 0),
                last_summary.get('total_income', 0),
            ),
            'expense_change': calc_change(
                current_summary.get('total_expenses', 0),
                last_summary.get('total_expenses', 0),
            ),
            'savings_change': calc_change(
                current_summary.get('net_savings', 0),
                last_summary.get('net_savings', 0),
            ),
        }

        return {
            'analysis': current_analysis,
            'last_month_analysis': last_month_analysis,
            'comparison': comparison,
            'unread_alerts': unread_alerts,
            'recent_expenses': recent_expenses,
            'recent_incomes': recent_incomes,
            'active_goals': active_goals,
            'unread_alerts_count': alert_manager.get_unread_count(user),
            'today': today,
        }

    @staticmethod
    def generate_monthly_snapshot(user: User, year: int, month: int) -> MonthlySnapshot:
        """
        Genera y guarda un snapshot mensual del estado financiero.
        """
        import calendar as cal

        last_day = cal.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        analysis = FinancialAnalysisService.run_full_analysis(
            user=user,
            start_date=start_date,
            end_date=end_date,
        )

        summary = analysis.get('summary', {})
        health = analysis.get('health', {})
        categories = analysis.get('categories', {})
        recommendations = analysis.get('recommendations', [])

        snapshot, _ = MonthlySnapshot.objects.update_or_create(
            user=user,
            year=year,
            month=month,
            defaults={
                'total_income': Decimal(str(summary.get('total_income', 0))),
                'total_expenses': Decimal(str(summary.get('total_expenses', 0))),
                'net_savings': Decimal(str(summary.get('net_savings', 0))),
                'savings_rate': Decimal(str(summary.get('savings_rate', 0))),
                'health_status': health.get('status', 'unknown'),
                'category_breakdown': categories,
                'recommendations_count': len(recommendations),
            }
        )

        return snapshot


# ============================================================
# SERVICIO DE OBJETIVOS FINANCIEROS
# ============================================================

class GoalService:

    @staticmethod
    def create_goal(user: User, data: dict) -> FinancialGoal:
        """Crea un nuevo objetivo financiero."""
        goal = FinancialGoal.objects.create(user=user, **data)
        GoalService._calculate_monthly_contribution(goal)
        return goal

    @staticmethod
    def update_goal(goal: FinancialGoal, data: dict) -> FinancialGoal:
        """Actualiza un objetivo financiero."""
        for field, value in data.items():
            setattr(goal, field, value)
        goal.save()
        GoalService._calculate_monthly_contribution(goal)
        return goal

    @staticmethod
    def delete_goal(goal: FinancialGoal) -> None:
        """Elimina un objetivo financiero."""
        goal.delete()

    @staticmethod
    def add_contribution(
        goal: FinancialGoal,
        amount: Decimal,
    ) -> FinancialGoal:
        """
        Agrega una contribución al objetivo.
        Actualiza el estado si se completa.
        """
        goal.current_amount += amount

        if goal.current_amount >= goal.target_amount:
            goal.current_amount = goal.target_amount
            goal.status = 'completed'

        goal.save()
        return goal

    @staticmethod
    def _calculate_monthly_contribution(goal: FinancialGoal) -> None:
        """Calcula la contribución mensual necesaria para alcanzar la meta."""
        days_remaining = (goal.target_date - date.today()).days

        if days_remaining <= 0:
            goal.monthly_contribution = goal.remaining_amount
        else:
            months_remaining = max(days_remaining / 30, 1)
            goal.monthly_contribution = (
                goal.remaining_amount / Decimal(str(months_remaining))
            )

        goal.save(update_fields=['monthly_contribution'])

    @staticmethod
    def get_user_goals(
        user: User,
        status: str = None,
    ) -> list:
        """Retorna objetivos del usuario filtrados por estado."""
        qs = FinancialGoal.objects.filter(user=user)

        if status:
            qs = qs.filter(status=status)

        return list(qs.order_by('target_date'))

    @staticmethod
    def get_goals_summary(user: User) -> dict:
        """Resumen de todos los objetivos del usuario."""
        goals = FinancialGoal.objects.filter(user=user)

        total_target = goals.aggregate(
            total=Sum('target_amount')
        )['total'] or Decimal('0.00')

        total_current = goals.aggregate(
            total=Sum('current_amount')
        )['total'] or Decimal('0.00')

        return {
            'total_goals': goals.count(),
            'active_goals': goals.filter(status='active').count(),
            'completed_goals': goals.filter(status='completed').count(),
            'total_target': float(total_target),
            'total_current': float(total_current),
            'overall_progress': round(
                float(total_current / total_target * 100)
                if total_target > 0 else 0,
                1
            ),
        }