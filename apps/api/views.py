"""
API REST con Django REST Framework.
Endpoints para integración con apps móviles o frontends externos.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from datetime import date
from decimal import Decimal
import logging

from apps.core.models import (
    Category, Income, Expense,
    FinancialGoal, Alert,
)
from apps.core.serializers import (
    CategorySerializer, CategoryCreateSerializer,
    IncomeSerializer, IncomeCreateSerializer,
    ExpenseSerializer, ExpenseCreateSerializer,
    FinancialGoalSerializer, GoalContributionSerializer,
    AlertSerializer, ClassifyExpenseSerializer,
    MonthlySnapshotSerializer,
)
from apps.core.services import (
    CategoryService, IncomeService,
    ExpenseService, FinancialAnalysisService,
    GoalService,
)
from apps.core.alerts import alert_manager

logger = logging.getLogger(__name__)


# ============================================================
# CATEGORÍAS API
# ============================================================

class CategoryListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista todas las categorías disponibles para el usuario."""
        categories = CategoryService.get_categories_for_user(request.user)
        serializer = CategorySerializer(
            categories,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    def post(self, request):
        """Crea una nueva categoría personalizada."""
        serializer = CategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                category = CategoryService.create_user_category(
                    user=request.user,
                    data=serializer.validated_data,
                )
                return Response(
                    CategorySerializer(category, context={'request': request}).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, category_id):
        return get_object_or_404(
            Category,
            id=category_id,
        )

    def get(self, request, category_id):
        """Detalle de una categoría."""
        category = self.get_object(request, category_id)
        serializer = CategorySerializer(category, context={'request': request})
        return Response(serializer.data)

    def put(self, request, category_id):
        """Actualiza una categoría del usuario."""
        category = get_object_or_404(
            Category,
            id=category_id,
            user=request.user,
        )
        serializer = CategoryCreateSerializer(
            category,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            for field, value in serializer.validated_data.items():
                setattr(category, field, value)
            category.save()
            return Response(
                CategorySerializer(category, context={'request': request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, category_id):
        """Elimina una categoría del usuario."""
        category = get_object_or_404(
            Category,
            id=category_id,
            user=request.user,
            is_system=False,
        )
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# INGRESOS API
# ============================================================

class IncomeListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista ingresos del usuario con filtros opcionales."""
        period = request.query_params.get('period', 'month')
        start_date, end_date = FinancialAnalysisService.get_period_dates(period)

        incomes = IncomeService.get_user_incomes(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
        )

        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(incomes, request)

        serializer = IncomeSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """Registra un nuevo ingreso."""
        serializer = IncomeCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                income = IncomeService.create_income(
                    user=request.user,
                    data=serializer.validated_data,
                )
                return Response(
                    IncomeSerializer(income).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncomeDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, income_id):
        return get_object_or_404(Income, id=income_id, user=request.user)

    def get(self, request, income_id):
        """Detalle de un ingreso."""
        income = self.get_object(request, income_id)
        return Response(IncomeSerializer(income).data)

    def put(self, request, income_id):
        """Actualiza un ingreso."""
        income = self.get_object(request, income_id)
        serializer = IncomeCreateSerializer(
            income, data=request.data, partial=True
        )
        if serializer.is_valid():
            updated = IncomeService.update_income(
                income=income,
                data=serializer.validated_data,
            )
            return Response(IncomeSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, income_id):
        """Elimina un ingreso."""
        income = self.get_object(request, income_id)
        IncomeService.delete_income(income)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# GASTOS API
# ============================================================

class ExpenseListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista gastos del usuario con filtros opcionales."""
        period = request.query_params.get('period', 'month')
        category_id = request.query_params.get('category', None)
        start_date, end_date = FinancialAnalysisService.get_period_dates(period)

        expenses = ExpenseService.get_user_expenses(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
        )

        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(expenses, request)

        serializer = ExpenseSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """Registra un nuevo gasto."""
        serializer = ExpenseCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                auto_classify = not bool(
                    serializer.validated_data.get('category')
                )
                expense = ExpenseService.create_expense(
                    user=request.user,
                    data=serializer.validated_data,
                    auto_classify=auto_classify,
                )
                return Response(
                    ExpenseSerializer(expense).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExpenseDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, expense_id):
        return get_object_or_404(Expense, id=expense_id, user=request.user)

    def get(self, request, expense_id):
        """Detalle de un gasto."""
        expense = self.get_object(request, expense_id)
        return Response(ExpenseSerializer(expense).data)

    def put(self, request, expense_id):
        """Actualiza un gasto."""
        expense = self.get_object(request, expense_id)
        serializer = ExpenseCreateSerializer(
            expense, data=request.data, partial=True
        )
        if serializer.is_valid():
            updated = ExpenseService.update_expense(
                expense=expense,
                data=serializer.validated_data,
            )
            return Response(ExpenseSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, expense_id):
        """Elimina un gasto."""
        expense = self.get_object(request, expense_id)
        ExpenseService.delete_expense(expense)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# ANÁLISIS FINANCIERO API
# ============================================================

class FinancialAnalysisAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna análisis financiero completo."""
        period = request.query_params.get('period', 'month')

        try:
            analysis = FinancialAnalysisService.run_full_analysis(
                user=request.user,
                period=period,
            )
            return Response(analysis)
        except Exception as e:
            logger.error(f"Error en análisis API: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FinancialSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna resumen financiero del mes actual."""
        try:
            analysis = FinancialAnalysisService.run_full_analysis(
                user=request.user,
                period='month',
            )
            return Response({
                'summary': analysis.get('summary', {}),
                'health': analysis.get('health', {}),
                'top_recommendations': analysis.get('recommendations', [])[:3],
                'alerts_count': alert_manager.get_unread_count(request.user),
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ClassifyExpenseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Clasifica un gasto por su descripción."""
        serializer = ClassifyExpenseSerializer(data=request.data)
        if serializer.is_valid():
            description = serializer.validated_data['description']
            suggestion = CategoryService.suggest_category_for_description(
                description
            )
            return Response({
                'description': description,
                'suggested_category': {
                    'id': str(suggestion['category'].id) if suggestion['category'] else None,
                    'name': suggestion['category'].name if suggestion['category'] else None,
                    'icon': suggestion['category'].icon if suggestion['category'] else None,
                    'slug': suggestion['category'].slug if suggestion['category'] else None,
                },
                'confidence': suggestion['confidence'],
                'method': suggestion['method'],
                'alternatives': suggestion['alternatives'],
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# OBJETIVOS FINANCIEROS API
# ============================================================

class GoalListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista objetivos financieros del usuario."""
        status_filter = request.query_params.get('status', None)
        goals = GoalService.get_user_goals(
            user=request.user,
            status=status_filter,
        )
        serializer = FinancialGoalSerializer(goals, many=True)
        summary = GoalService.get_goals_summary(request.user)
        return Response({
            'goals': serializer.data,
            'summary': summary,
        })

    def post(self, request):
        """Crea un nuevo objetivo financiero."""
        serializer = FinancialGoalSerializer(data=request.data)
        if serializer.is_valid():
            try:
                goal = GoalService.create_goal(
                    user=request.user,
                    data=serializer.validated_data,
                )
                return Response(
                    FinancialGoalSerializer(goal).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoalDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, goal_id):
        return get_object_or_404(
            FinancialGoal,
            id=goal_id,
            user=request.user,
        )

    def get(self, request, goal_id):
        """Detalle de un objetivo."""
        goal = self.get_object(request, goal_id)
        return Response(FinancialGoalSerializer(goal).data)

    def put(self, request, goal_id):
        """Actualiza un objetivo."""
        goal = self.get_object(request, goal_id)
        serializer = FinancialGoalSerializer(
            goal, data=request.data, partial=True
        )
        if serializer.is_valid():
            updated = GoalService.update_goal(
                goal=goal,
                data=serializer.validated_data,
            )
            return Response(FinancialGoalSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, goal_id):
        """Elimina un objetivo."""
        goal = self.get_object(request, goal_id)
        GoalService.delete_goal(goal)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoalContributeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, goal_id):
        """Agrega una contribución a un objetivo."""
        goal = get_object_or_404(
            FinancialGoal,
            id=goal_id,
            user=request.user,
        )
        serializer = GoalContributionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                updated_goal = GoalService.add_contribution(
                    goal=goal,
                    amount=serializer.validated_data['amount'],
                )
                return Response({
                    'goal': FinancialGoalSerializer(updated_goal).data,
                    'message': f'Contribución agregada exitosamente.',
                    'new_progress': updated_goal.progress_percentage,
                })
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# ALERTAS API
# ============================================================

class AlertListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista alertas del usuario."""
        alerts = Alert.objects.filter(
            user=request.user,
            is_dismissed=False,
        ).order_by('-created_at')[:20]

        serializer = AlertSerializer(alerts, many=True)
        return Response({
            'alerts': serializer.data,
            'unread_count': alert_manager.get_unread_count(request.user),
        })


class AlertDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, alert_id):
        """Marca alerta como leída o descartada."""
        alert = get_object_or_404(
            Alert,
            id=alert_id,
            user=request.user,
        )
        action = request.data.get('action', 'read')

        if action == 'dismiss':
            alert_manager.dismiss_alert(
                user=request.user,
                alert_id=str(alert_id),
            )
            return Response({'status': 'dismissed'})
        else:
            alert.is_read = True
            alert.save()
            return Response({'status': 'read'})


# ============================================================
# SNAPSHOTS MENSUALES API
# ============================================================

class MonthlySnapshotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista snapshots mensuales del usuario."""
        from apps.core.models import MonthlySnapshot
        snapshots = MonthlySnapshot.objects.filter(
            user=request.user,
        ).order_by('-year', '-month')[:12]

        serializer = MonthlySnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Genera snapshot del mes actual."""
        from datetime import date
        today = date.today()
        try:
            snapshot = FinancialAnalysisService.generate_monthly_snapshot(
                user=request.user,
                year=today.year,
                month=today.month,
            )
            return Response(
                MonthlySnapshotSerializer(snapshot).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )