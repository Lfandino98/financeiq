from django.contrib import admin
from django.utils.html import format_html
from apps.core.models import (
    Category, Income, Expense,
    FinancialGoal, Alert, MonthlySnapshot
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'colored_icon', 'name', 'category_type',
        'is_system', 'user', 'created_at'
    ]
    list_filter = ['category_type', 'is_system']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    ordering = ['name']

    def colored_icon(self, obj):
        return format_html(
            '<span style="background-color: {}20; padding: 4px 8px; '
            'border-radius: 8px; font-size: 18px;">{}</span>',
            obj.color, obj.icon
        )
    colored_icon.short_description = 'Icono'


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'description', 'amount_display',
        'category', 'date', 'recurrence', 'created_at'
    ]
    list_filter = ['recurrence', 'category', 'date']
    search_fields = ['description', 'source', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']

    def amount_display(self, obj):
        return format_html(
            '<span style="color: #16a34a; font-weight: bold;">+${}</span>',
            f'{obj.amount:,.0f}'
        )
    amount_display.short_description = 'Monto'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'description', 'amount_display', 'category',
        'date', 'is_essential', 'is_recurring',
        'auto_classified', 'created_at'
    ]
    list_filter = [
        'category', 'is_essential', 'is_recurring',
        'auto_classified', 'date'
    ]
    search_fields = ['description', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']

    def amount_display(self, obj):
        return format_html(
            '<span style="color: #dc2626; font-weight: bold;">-${}</span>',
            f'{obj.amount:,.0f}'
        )
    amount_display.short_description = 'Monto'


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'name', 'goal_type', 'target_amount',
        'current_amount', 'progress_bar', 'target_date', 'status'
    ]
    list_filter = ['goal_type', 'status']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'monthly_contribution']
    ordering = ['target_date']

    def progress_bar(self, obj):
        pct = obj.progress_percentage
        color = '#16a34a' if pct >= 75 else '#f59e0b' if pct >= 25 else '#dc2626'
        return format_html(
            '<div style="width:100px; background:#e5e7eb; border-radius:4px; height:8px;">'
            '<div style="width:{}%; background:{}; border-radius:4px; height:8px;"></div>'
            '</div> <small>{}%</small>',
            min(pct, 100), color, f'{pct:.1f}'
        )
    progress_bar.short_description = 'Progreso'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'alert_type', 'alert_category',
        'title', 'is_read', 'is_dismissed', 'created_at'
    ]
    list_filter = ['alert_type', 'alert_category', 'is_read', 'is_dismissed']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    actions = ['mark_as_read', 'mark_as_dismissed']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'{queryset.count()} alertas marcadas como leídas.')
    mark_as_read.short_description = 'Marcar como leídas'

    def mark_as_dismissed(self, request, queryset):
        queryset.update(is_dismissed=True)
        self.message_user(request, f'{queryset.count()} alertas descartadas.')
    mark_as_dismissed.short_description = 'Descartar alertas'


@admin.register(MonthlySnapshot)
class MonthlySnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'year', 'month', 'total_income',
        'total_expenses', 'net_savings', 'savings_rate',
        'health_status', 'created_at'
    ]
    list_filter = ['health_status', 'year', 'month']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-year', '-month']