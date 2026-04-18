"""
Serializers de Django REST Framework.
Validan y transforman datos entre Python y JSON.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from apps.core.models import (
    Category, Income, Expense,
    FinancialGoal, Alert, MonthlySnapshot
)
from apps.core.classifiers import expense_classifier


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'color', 'category_type', 'is_system',
            'keywords', 'is_owner', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'is_system', 'created_at']

    def get_is_owner(self, obj) -> bool:
        request = self.context.get('request')
        if request and obj.user:
            return obj.user == request.user
        return False


class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'name', 'description', 'icon',
            'color', 'category_type', 'keywords',
        ]

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 2 caracteres."
            )
        return value.strip()


class IncomeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name', read_only=True
    )
    category_icon = serializers.CharField(
        source='category.icon', read_only=True
    )

    class Meta:
        model = Income
        fields = [
            'id', 'amount', 'description', 'source',
            'date', 'recurrence', 'notes',
            'category', 'category_name', 'category_icon',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El monto debe ser mayor a 0."
            )
        return value

    def validate_date(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError(
                "No puedes registrar ingresos en el futuro."
            )
        return value


class IncomeCreateSerializer(IncomeSerializer):
    class Meta(IncomeSerializer.Meta):
        fields = [
            'amount', 'description', 'source',
            'date', 'recurrence', 'notes', 'category',
        ]


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name', read_only=True
    )
    category_icon = serializers.CharField(
        source='category.icon', read_only=True
    )
    category_color = serializers.CharField(
        source='category.color', read_only=True
    )
    suggested_category = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            'id', 'amount', 'description', 'date',
            'is_recurring', 'is_essential', 'auto_classified',
            'notes', 'tags', 'category', 'category_name',
            'category_icon', 'category_color',
            'suggested_category', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'auto_classified',
            'created_at', 'updated_at',
        ]

    def get_suggested_category(self, obj) -> dict:
        """Sugiere categoría basada en la descripción."""
        if obj.description:
            result = expense_classifier.classify(obj.description)
            return {
                'category': result['category'],
                'confidence': result['confidence'],
            }
        return {}

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El monto debe ser mayor a 0."
            )
        return value

    def validate_date(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError(
                "No puedes registrar gastos en el futuro."
            )
        return value


class ExpenseCreateSerializer(ExpenseSerializer):
    class Meta(ExpenseSerializer.Meta):
        fields = [
            'amount', 'description', 'date',
            'is_recurring', 'is_essential',
            'notes', 'tags', 'category',
        ]


class FinancialGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()
    days_remaining = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    monthly_contribution = serializers.ReadOnlyField()

    class Meta:
        model = FinancialGoal
        fields = [
            'id', 'name', 'description', 'goal_type',
            'target_amount', 'current_amount', 'remaining_amount',
            'target_date', 'status', 'monthly_contribution',
            'progress_percentage', 'days_remaining',
            'is_overdue', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'current_amount', 'monthly_contribution',
            'created_at', 'updated_at',
        ]

    def get_days_remaining(self, obj) -> int:
        from datetime import date
        return (obj.target_date - date.today()).days

    def get_is_overdue(self, obj) -> bool:
        from datetime import date
        return obj.target_date < date.today() and obj.status == 'active'

    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El monto objetivo debe ser mayor a 0."
            )
        return value

    def validate_target_date(self, value):
        from datetime import date
        if value <= date.today():
            raise serializers.ValidationError(
                "La fecha objetivo debe ser en el futuro."
            )
        return value


class GoalContributionSerializer(serializers.Serializer):
    """Serializer para agregar contribuciones a un objetivo."""
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
    )
    notes = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            'id', 'alert_type', 'alert_category',
            'title', 'message', 'is_read',
            'is_dismissed', 'metadata', 'created_at',
        ]
        read_only_fields = [
            'id', 'alert_type', 'alert_category',
            'title', 'message', 'metadata', 'created_at',
        ]


class MonthlySnapshotSerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()

    class Meta:
        model = MonthlySnapshot
        fields = [
            'id', 'year', 'month', 'month_name',
            'total_income', 'total_expenses', 'net_savings',
            'savings_rate', 'health_status',
            'category_breakdown', 'recommendations_count',
            'created_at',
        ]
        read_only_fields = fields

    def get_month_name(self, obj) -> str:
        import calendar
        return calendar.month_name[obj.month]


class FinancialSummarySerializer(serializers.Serializer):
    """Serializer para el resumen financiero del análisis."""
    total_income = serializers.FloatField()
    total_expenses = serializers.FloatField()
    net_savings = serializers.FloatField()
    savings_rate = serializers.FloatField()
    expense_ratio = serializers.FloatField()
    daily_avg_expense = serializers.FloatField()
    monthly_income = serializers.FloatField()
    monthly_expenses = serializers.FloatField()
    period_days = serializers.IntegerField()
    transactions_count = serializers.IntegerField()


class ClassifyExpenseSerializer(serializers.Serializer):
    """Serializer para clasificar un gasto por descripción."""
    description = serializers.CharField(max_length=255)

    def validate_description(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "La descripción debe tener al menos 2 caracteres."
            )
        return value.strip()