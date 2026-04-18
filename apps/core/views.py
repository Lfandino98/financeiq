"""
Vistas web (Django Templates).
Solo coordinan entre servicios y templates.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from datetime import date
from decimal import Decimal
import json
import logging

from apps.core.models import (
    Category, Income, Expense,
    FinancialGoal, Alert
)
from apps.core.services import (
    CategoryService, IncomeService,
    ExpenseService, FinancialAnalysisService,
    GoalService,
)
from apps.core.alerts import alert_manager

logger = logging.getLogger(__name__)


# ============================================================
# AUTENTICACIÓN
# ============================================================

def login_view(request):
    """Vista de login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.first_name or user.username}!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'auth/login.html')


def register_view(request):
    """Vista de registro."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        # Validaciones
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'auth/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'auth/register.html')

        if len(password1) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return render(request, 'auth/register.html')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            # Crear categorías del sistema
            CategoryService.get_or_create_system_categories()
            login(request, user)
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('dashboard')
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            messages.error(request, 'Error al crear la cuenta. Intenta de nuevo.')

    return render(request, 'auth/register.html')


@login_required
def logout_view(request):
    """Vista de logout."""
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('login')


# ============================================================
# DASHBOARD
# ============================================================

@login_required
def dashboard_view(request):
    """Vista principal del dashboard."""
    period = request.GET.get('period', 'month')

    try:
        dashboard_data = FinancialAnalysisService.get_dashboard_data(
            user=request.user
        )
        analysis = FinancialAnalysisService.run_full_analysis(
            user=request.user,
            period=period,
        )
    except Exception as e:
        logger.error(f"Error en dashboard para {request.user.username}: {e}")
        dashboard_data = {}
        analysis = {}
        messages.error(request, 'Error al cargar el análisis financiero.')

    context = {
        'dashboard_data': dashboard_data,
        'analysis': analysis,
        'period': period,
        'period_options': [
            {'value': 'week', 'label': 'Esta semana'},
            {'value': 'month', 'label': 'Este mes'},
            {'value': 'quarter', 'label': 'Último trimestre'},
            {'value': 'year', 'label': 'Este año'},
        ],
        'active_page': 'dashboard',
    }

    return render(request, 'dashboard/index.html', context)


# ============================================================
# INGRESOS
# ============================================================

@login_required
def income_list_view(request):
    """Lista de ingresos."""
    period = request.GET.get('period', 'month')
    start_date, end_date = FinancialAnalysisService.get_period_dates(period)

    incomes = IncomeService.get_user_incomes(
        user=request.user,
        start_date=start_date,
        end_date=end_date,
    )

    categories = CategoryService.get_categories_for_user(request.user)
    income_categories = [
        c for c in categories
        if c.category_type in ['income', 'both']
    ]

    total = sum(i.amount for i in incomes)

    context = {
        'incomes': incomes,
        'categories': income_categories,
        'total': total,
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'active_page': 'incomes',
    }

    return render(request, 'transactions/income_list.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def income_create_view(request):
    """Crear nuevo ingreso."""
    categories = CategoryService.get_categories_for_user(request.user)
    income_categories = [
        c for c in categories
        if c.category_type in ['income', 'both']
    ]

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            category = None
            if category_id:
                category = get_object_or_404(Category, id=category_id)

            data = {
                'amount': Decimal(request.POST.get('amount', '0')),
                'description': request.POST.get('description', '').strip(),
                'source': request.POST.get('source', '').strip(),
                'date': request.POST.get('date', date.today().isoformat()),
                'recurrence': request.POST.get('recurrence', 'once'),
                'notes': request.POST.get('notes', '').strip(),
                'category': category,
            }

            income = IncomeService.create_income(
                user=request.user,
                data=data,
            )
            messages.success(
                request,
                f'Ingreso de ${income.amount:,.0f} registrado exitosamente.'
            )
            return redirect('income_list')

        except Exception as e:
            logger.error(f"Error creando ingreso: {e}")
            messages.error(request, f'Error al registrar el ingreso: {str(e)}')

    context = {
        'categories': income_categories,
        'today': date.today().isoformat(),
        'active_page': 'incomes',
    }

    return render(request, 'transactions/income_create.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def income_edit_view(request, income_id):
    """Editar ingreso existente."""
    income = get_object_or_404(Income, id=income_id, user=request.user)
    categories = CategoryService.get_categories_for_user(request.user)
    income_categories = [
        c for c in categories
        if c.category_type in ['income', 'both']
    ]

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            category = None
            if category_id:
                category = get_object_or_404(Category, id=category_id)

            data = {
                'amount': Decimal(request.POST.get('amount', '0')),
                'description': request.POST.get('description', '').strip(),
                'source': request.POST.get('source', '').strip(),
                'date': request.POST.get('date'),
                'recurrence': request.POST.get('recurrence', 'once'),
                'notes': request.POST.get('notes', '').strip(),
                'category': category,
            }

            IncomeService.update_income(income=income, data=data)
            messages.success(request, 'Ingreso actualizado exitosamente.')
            return redirect('income_list')

        except Exception as e:
            logger.error(f"Error actualizando ingreso: {e}")
            messages.error(request, f'Error al actualizar el ingreso: {str(e)}')

    context = {
        'income': income,
        'categories': income_categories,
        'active_page': 'incomes',
    }

    return render(request, 'transactions/income_edit.html', context)


@login_required
@require_http_methods(['POST'])
def income_delete_view(request, income_id):
    """Eliminar ingreso."""
    income = get_object_or_404(Income, id=income_id, user=request.user)
    try:
        amount = income.amount
        IncomeService.delete_income(income)
        messages.success(request, f'Ingreso de ${amount:,.0f} eliminado.')
    except Exception as e:
        logger.error(f"Error eliminando ingreso: {e}")
        messages.error(request, 'Error al eliminar el ingreso.')
    return redirect('income_list')


# ============================================================
# GASTOS
# ============================================================

@login_required
def expense_list_view(request):
    """Lista de gastos."""
    period = request.GET.get('period', 'month')
    category_filter = request.GET.get('category', None)
    start_date, end_date = FinancialAnalysisService.get_period_dates(period)

    expenses = ExpenseService.get_user_expenses(
        user=request.user,
        start_date=start_date,
        end_date=end_date,
        category_id=category_filter,
    )

    categories = CategoryService.get_categories_for_user(request.user)
    expense_categories = [
        c for c in categories
        if c.category_type in ['expense', 'both']
    ]

    total = sum(e.amount for e in expenses)

    context = {
        'expenses': expenses,
        'categories': expense_categories,
        'total': total,
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'category_filter': category_filter,
        'active_page': 'expenses',
    }

    return render(request, 'transactions/expense_list.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def expense_create_view(request):
    """Crear nuevo gasto."""
    categories = CategoryService.get_categories_for_user(request.user)
    expense_categories = [
        c for c in categories
        if c.category_type in ['expense', 'both']
    ]

    # Sugerencia de categoría por descripción (AJAX)
    description = request.GET.get('description', '')
    suggested = None
    if description:
        suggested = CategoryService.suggest_category_for_description(description)

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            category = None
            if category_id:
                category = get_object_or_404(Category, id=category_id)

            data = {
                'amount': Decimal(request.POST.get('amount', '0')),
                'description': request.POST.get('description', '').strip(),
                'date': request.POST.get('date', date.today().isoformat()),
                'is_recurring': request.POST.get('is_recurring') == 'on',
                'is_essential': request.POST.get('is_essential') == 'on',
                'notes': request.POST.get('notes', '').strip(),
                'tags': json.loads(request.POST.get('tags', '[]')),
                'category': category,
            }

            expense = ExpenseService.create_expense(
                user=request.user,
                data=data,
                auto_classify=not bool(category_id),
            )

            messages.success(
                request,
                f'Gasto de ${expense.amount:,.0f} registrado exitosamente.'
            )
            return redirect('expense_list')

        except Exception as e:
            logger.error(f"Error creando gasto: {e}")
            messages.error(request, f'Error al registrar el gasto: {str(e)}')

    context = {
        'categories': expense_categories,
        'today': date.today().isoformat(),
        'suggested': suggested,
        'active_page': 'expenses',
    }

    return render(request, 'transactions/expense_create.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def expense_edit_view(request, expense_id):
    """Editar gasto existente."""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    categories = CategoryService.get_categories_for_user(request.user)
    expense_categories = [
        c for c in categories
        if c.category_type in ['expense', 'both']
    ]

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            category = None
            if category_id:
                category = get_object_or_404(Category, id=category_id)

            data = {
                'amount': Decimal(request.POST.get('amount', '0')),
                'description': request.POST.get('description', '').strip(),
                'date': request.POST.get('date'),
                'is_recurring': request.POST.get('is_recurring') == 'on',
                'is_essential': request.POST.get('is_essential') == 'on',
                'notes': request.POST.get('notes', '').strip(),
                'tags': json.loads(request.POST.get('tags', '[]')),
                'category': category,
            }

            ExpenseService.update_expense(expense=expense, data=data)
            messages.success(request, 'Gasto actualizado exitosamente.')
            return redirect('expense_list')

        except Exception as e:
            logger.error(f"Error actualizando gasto: {e}")
            messages.error(request, f'Error al actualizar el gasto: {str(e)}')

    context = {
        'expense': expense,
        'categories': expense_categories,
        'active_page': 'expenses',
    }

    return render(request, 'transactions/expense_edit.html', context)


@login_required
@require_http_methods(['POST'])
def expense_delete_view(request, expense_id):
    """Eliminar gasto."""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    try:
        amount = expense.amount
        ExpenseService.delete_expense(expense)
        messages.success(request, f'Gasto de ${amount:,.0f} eliminado.')
    except Exception as e:
        logger.error(f"Error eliminando gasto: {e}")
        messages.error(request, 'Error al eliminar el gasto.')
    return redirect('expense_list')


# ============================================================
# OBJETIVOS FINANCIEROS
# ============================================================

@login_required
def goal_list_view(request):
    """Lista de objetivos financieros."""
    goals = GoalService.get_user_goals(user=request.user)
    summary = GoalService.get_goals_summary(user=request.user)

    context = {
        'goals': goals,
        'summary': summary,
        'active_page': 'goals',
    }

    return render(request, 'goals/list.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def goal_create_view(request):
    """Crear nuevo objetivo financiero."""
    if request.method == 'POST':
        try:
            data = {
                'name': request.POST.get('name', '').strip(),
                'description': request.POST.get('description', '').strip(),
                'goal_type': request.POST.get('goal_type', 'savings'),
                'target_amount': Decimal(request.POST.get('target_amount', '0')),
                'target_date': request.POST.get('target_date'),
            }

            goal = GoalService.create_goal(user=request.user, data=data)
            messages.success(
                request,
                f'Meta "{goal.name}" creada exitosamente.'
            )
            return redirect('goal_list')

        except Exception as e:
            logger.error(f"Error creando objetivo: {e}")
            messages.error(request, f'Error al crear la meta: {str(e)}')

    context = {
        'goal_types': FinancialGoal.GOAL_TYPES,
        'today': date.today().isoformat(),
        'active_page': 'goals',
    }

    return render(request, 'goals/create.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def goal_edit_view(request, goal_id):
    """Editar objetivo financiero."""
    goal = get_object_or_404(FinancialGoal, id=goal_id, user=request.user)

    if request.method == 'POST':
        try:
            data = {
                'name': request.POST.get('name', '').strip(),
                'description': request.POST.get('description', '').strip(),
                'goal_type': request.POST.get('goal_type', 'savings'),
                'target_amount': Decimal(request.POST.get('target_amount', '0')),
                'target_date': request.POST.get('target_date'),
                'status': request.POST.get('status', 'active'),
            }

            GoalService.update_goal(goal=goal, data=data)
            messages.success(request, 'Meta actualizada exitosamente.')
            return redirect('goal_list')

        except Exception as e:
            logger.error(f"Error actualizando objetivo: {e}")
            messages.error(request, f'Error al actualizar la meta: {str(e)}')

    context = {
        'goal': goal,
        'goal_types': FinancialGoal.GOAL_TYPES,
        'status_choices': FinancialGoal.STATUS_CHOICES,
        'active_page': 'goals',
    }

    return render(request, 'goals/edit.html', context)


@login_required
@require_http_methods(['POST'])
def goal_contribute_view(request, goal_id):
    """Agregar contribución a un objetivo."""
    goal = get_object_or_404(FinancialGoal, id=goal_id, user=request.user)

    try:
        amount = Decimal(request.POST.get('amount', '0'))
        if amount <= 0:
            raise ValueError("El monto debe ser mayor a 0")

        GoalService.add_contribution(goal=goal, amount=amount)
        messages.success(
            request,
            f'Contribución de ${amount:,.0f} agregada a "{goal.name}".'
        )
    except Exception as e:
        logger.error(f"Error agregando contribución: {e}")
        messages.error(request, f'Error al agregar contribución: {str(e)}')

    return redirect('goal_list')


@login_required
@require_http_methods(['POST'])
def goal_delete_view(request, goal_id):
    """Eliminar objetivo financiero."""
    goal = get_object_or_404(FinancialGoal, id=goal_id, user=request.user)
    try:
        name = goal.name
        GoalService.delete_goal(goal)
        messages.success(request, f'Meta "{name}" eliminada.')
    except Exception as e:
        logger.error(f"Error eliminando objetivo: {e}")
        messages.error(request, 'Error al eliminar la meta.')
    return redirect('goal_list')


# ============================================================
# ALERTAS
# ============================================================

@login_required
def alerts_view(request):
    """Vista de alertas del usuario."""
    alerts = Alert.objects.filter(
        user=request.user,
        is_dismissed=False,
    ).order_by('-created_at')

    context = {
        'alerts': alerts,
        'unread_count': alert_manager.get_unread_count(request.user),
        'active_page': 'alerts',
    }

    alert_manager.mark_all_read(request.user)
    return render(request, 'alerts/list.html', context)


@login_required
@require_http_methods(['POST'])
def alert_dismiss_view(request, alert_id):
    """Descartar una alerta."""
    alert_manager.dismiss_alert(user=request.user, alert_id=str(alert_id))
    return JsonResponse({'status': 'ok'})


# ============================================================
# CATEGORÍAS
# ============================================================

@login_required
def category_list_view(request):
    """Lista de categorías."""
    categories = CategoryService.get_categories_for_user(request.user)

    context = {
        'categories': categories,
        'active_page': 'categories',
    }

    return render(request, 'categories/list.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def category_create_view(request):
    """Crear nueva categoría."""
    if request.method == 'POST':
        try:
            data = {
                'name': request.POST.get('name', '').strip(),
                'description': request.POST.get('description', '').strip(),
                'icon': request.POST.get('icon', '📦'),
                'color': request.POST.get('color', '#94a3b8'),
                'category_type': request.POST.get('category_type', 'expense'),
                'keywords': json.loads(request.POST.get('keywords', '[]')),
            }

            category = CategoryService.create_user_category(
                user=request.user,
                data=data,
            )
            messages.success(
                request,
                f'Categoría "{category.name}" creada exitosamente.'
            )
            return redirect('category_list')

        except Exception as e:
            logger.error(f"Error creando categoría: {e}")
            messages.error(request, f'Error al crear la categoría: {str(e)}')

    context = {
        'category_types': Category.CATEGORY_TYPES,
        'active_page': 'categories',
    }

    return render(request, 'categories/create.html', context)


# ============================================================
# ANÁLISIS
# ============================================================

@login_required
def analysis_view(request):
    """Vista de análisis financiero detallado."""
    period = request.GET.get('period', 'month')

    try:
        analysis = FinancialAnalysisService.run_full_analysis(
            user=request.user,
            period=period,
        )
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        analysis = {}
        messages.error(request, 'Error al generar el análisis.')

    context = {
        'analysis': analysis,
        'period': period,
        'active_page': 'analysis',
    }

    return render(request, 'analysis/index.html', context)


# ============================================================
# AJAX ENDPOINTS
# ============================================================

@login_required
def ajax_classify_expense(request):
    """Endpoint AJAX para clasificar gasto por descripción."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    description = request.GET.get('description', '').strip()
    if not description:
        return JsonResponse({'error': 'Descripción requerida'}, status=400)

    suggestion = CategoryService.suggest_category_for_description(description)

    return JsonResponse({
        'category_id': str(suggestion['category'].id) if suggestion['category'] else None,
        'category_name': suggestion['category'].name if suggestion['category'] else None,
        'category_icon': suggestion['category'].icon if suggestion['category'] else None,
        'confidence': suggestion['confidence'],
        'method': suggestion['method'],
    })


@login_required
def ajax_dashboard_chart_data(request):
    """Endpoint AJAX para datos de gráficas del dashboard."""
    period = request.GET.get('period', 'month')

    try:
        analysis = FinancialAnalysisService.run_full_analysis(
            user=request.user,
            period=period,
        )

        # Datos para gráfica de categorías
        categories_data = {
            'labels': list(analysis.get('categories', {}).keys()),
            'values': [
                v['percentage']
                for v in analysis.get('categories', {}).values()
            ],
            'totals': [
                v['total']
                for v in analysis.get('categories', {}).values()
            ],
        }

        # Datos para gráfica de resumen
        summary = analysis.get('summary', {})
        summary_data = {
            'income': summary.get('total_income', 0),
            'expenses': summary.get('total_expenses', 0),
            'savings': summary.get('net_savings', 0),
            'savings_rate': summary.get('savings_rate', 0),
        }

        # Datos de proyecciones
        projections = analysis.get('projections', {})
        projection_data = {
            'labels': ['3 meses', '6 meses', '12 meses'],
            'base': [
                projections.get('3_months', {}).get('projected_savings', 0),
                projections.get('6_months', {}).get('projected_savings', 0),
                projections.get('12_months', {}).get('projected_savings', 0),
            ],
            'optimistic': [
                projections.get('3_months', {}).get('scenarios', {}).get('optimistic', 0),
                projections.get('6_months', {}).get('scenarios', {}).get('optimistic', 0),
                projections.get('12_months', {}).get('scenarios', {}).get('optimistic', 0),
            ],
            'pessimistic': [
                projections.get('3_months', {}).get('scenarios', {}).get('pessimistic', 0),
                projections.get('6_months', {}).get('scenarios', {}).get('pessimistic', 0),
                projections.get('12_months', {}).get('scenarios', {}).get('pessimistic', 0),
            ],
        }

        return JsonResponse({
            'categories': categories_data,
            'summary': summary_data,
            'projections': projection_data,
            'health': analysis.get('health', {}),
        })

    except Exception as e:
        logger.error(f"Error obteniendo datos de gráficas: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def ajax_financial_summary(request):
    """Endpoint AJAX para resumen financiero rápido."""
    try:
        analysis = FinancialAnalysisService.run_full_analysis(
            user=request.user,
            period='month',
        )
        return JsonResponse({
            'summary': analysis.get('summary', {}),
            'health': analysis.get('health', {}),
            'recommendations_count': len(analysis.get('recommendations', [])),
            'alerts_count': alert_manager.get_unread_count(request.user),
        })
    except Exception as e:
        logger.error(f"Error en resumen financiero: {e}")
        return JsonResponse({'error': str(e)}, status=500)