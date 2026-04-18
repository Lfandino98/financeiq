"""
Modelos de base de datos para FinanceIQ.
Todos los modelos usan UUID como clave primaria.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class TimeStampedModel(models.Model):
    """Modelo base con timestamps automáticos."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """Categorías para clasificar ingresos y gastos."""

    CATEGORY_TYPES = [
        ('expense', 'Gasto'),
        ('income', 'Ingreso'),
        ('both', 'Ambos'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='categories',
        verbose_name='Usuario',
    )
    name = models.CharField(max_length=100, verbose_name='Nombre')
    slug = models.SlugField(max_length=100, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Descripción')
    icon = models.CharField(max_length=10, default='📦', verbose_name='Icono')
    color = models.CharField(max_length=7, default='#94a3b8', verbose_name='Color')
    category_type = models.CharField(
        max_length=10,
        choices=CATEGORY_TYPES,
        default='expense',
        verbose_name='Tipo',
    )
    is_system = models.BooleanField(default=False, verbose_name='Es del sistema')
    keywords = models.JSONField(default=list, blank=True, verbose_name='Palabras clave')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_system']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.icon} {self.name}"


class Income(TimeStampedModel):
    """Registro de ingresos del usuario."""

    RECURRENCE_CHOICES = [
        ('once', 'Una vez'),
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
        ('yearly', 'Anual'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='incomes',
        verbose_name='Usuario',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incomes',
        verbose_name='Categoría',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto',
    )
    description = models.CharField(
        max_length=255,
        verbose_name='Descripción',
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Fuente',
    )
    date = models.DateField(verbose_name='Fecha')
    recurrence = models.CharField(
        max_length=10,
        choices=RECURRENCE_CHOICES,
        default='once',
        verbose_name='Recurrencia',
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        verbose_name = 'Ingreso'
        verbose_name_plural = 'Ingresos'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.user.username} - ${self.amount} - {self.date}"


class Expense(TimeStampedModel):
    """Registro de gastos del usuario."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='Usuario',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name='Categoría',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto',
    )
    description = models.CharField(
        max_length=255,
        verbose_name='Descripción',
    )
    date = models.DateField(verbose_name='Fecha')
    is_recurring = models.BooleanField(
        default=False,
        verbose_name='Es recurrente',
    )
    is_essential = models.BooleanField(
        default=True,
        verbose_name='Es esencial',
    )
    auto_classified = models.BooleanField(
        default=False,
        verbose_name='Auto-clasificado',
    )
    notes = models.TextField(blank=True, verbose_name='Notas')
    tags = models.JSONField(default=list, blank=True, verbose_name='Etiquetas')

    class Meta:
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['category']),
            models.Index(fields=['is_essential']),
        ]

    def __str__(self):
        return f"{self.user.username} - ${self.amount} - {self.description}"


class FinancialGoal(TimeStampedModel):
    """Objetivos financieros del usuario."""

    GOAL_TYPES = [
        ('savings', 'Ahorro general'),
        ('emergency_fund', 'Fondo de emergencia'),
        ('debt_payment', 'Pago de deuda'),
        ('investment', 'Inversión'),
        ('purchase', 'Compra específica'),
        ('other', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('completed', 'Completada'),
        ('paused', 'Pausada'),
        ('cancelled', 'Cancelada'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='goals',
        verbose_name='Usuario',
    )
    name = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    goal_type = models.CharField(
        max_length=20,
        choices=GOAL_TYPES,
        default='savings',
        verbose_name='Tipo de meta',
    )
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto objetivo',
    )
    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto actual',
    )
    monthly_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Contribución mensual sugerida',
    )
    target_date = models.DateField(verbose_name='Fecha objetivo')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Estado',
    )

    class Meta:
        verbose_name = 'Meta Financiera'
        verbose_name_plural = 'Metas Financieras'
        ordering = ['target_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['target_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    @property
    def progress_percentage(self) -> float:
        if self.target_amount <= 0:
            return 0.0
        return min(
            float(self.current_amount / self.target_amount * 100),
            100.0
        )

    @property
    def remaining_amount(self) -> Decimal:
        return max(self.target_amount - self.current_amount, Decimal('0.00'))


class Alert(TimeStampedModel):
    """Alertas automáticas del sistema."""

    ALERT_TYPES = [
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('danger', 'Peligro'),
        ('success', 'Éxito'),
    ]

    ALERT_CATEGORIES = [
        ('budget_exceeded', 'Presupuesto excedido'),
        ('low_savings', 'Ahorro bajo'),
        ('negative_balance', 'Balance negativo'),
        ('goal_progress', 'Progreso de meta'),
        ('negative_trend', 'Tendencia negativa'),
        ('positive_trend', 'Tendencia positiva'),
        ('anomaly', 'Anomalía detectada'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name='Usuario',
    )
    alert_type = models.CharField(
        max_length=10,
        choices=ALERT_TYPES,
        default='info',
        verbose_name='Tipo',
    )
    alert_category = models.CharField(
        max_length=20,
        choices=ALERT_CATEGORIES,
        default='general',
        verbose_name='Categoría',
    )
    title = models.CharField(max_length=200, verbose_name='Título')
    message = models.TextField(verbose_name='Mensaje')
    is_read = models.BooleanField(default=False, verbose_name='Leída')
    is_dismissed = models.BooleanField(default=False, verbose_name='Descartada')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata')

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'is_dismissed']),
            models.Index(fields=['alert_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class MonthlySnapshot(TimeStampedModel):
    """Snapshot mensual del estado financiero."""

    HEALTH_STATUS_CHOICES = [
        ('healthy', 'Saludable'),
        ('stable', 'Estable'),
        ('risky', 'En riesgo'),
        ('critical', 'Crítico'),
        ('unknown', 'Desconocido'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='snapshots',
        verbose_name='Usuario',
    )
    year = models.IntegerField(verbose_name='Año')
    month = models.IntegerField(verbose_name='Mes')
    total_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total ingresos',
    )
    total_expenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total gastos',
    )
    net_savings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Ahorro neto',
    )
    savings_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Tasa de ahorro',
    )
    health_status = models.CharField(
        max_length=10,
        choices=HEALTH_STATUS_CHOICES,
        default='unknown',
        verbose_name='Estado de salud',
    )
    category_breakdown = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Desglose por categoría',
    )
    recommendations_count = models.IntegerField(
        default=0,
        verbose_name='Número de recomendaciones',
    )

    class Meta:
        verbose_name = 'Snapshot Mensual'
        verbose_name_plural = 'Snapshots Mensuales'
        ordering = ['-year', '-month']
        unique_together = ['user', 'year', 'month']
        indexes = [
            models.Index(fields=['user', 'year', 'month']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.year}/{self.month:02d}"