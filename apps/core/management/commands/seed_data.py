"""
Comando de Django para poblar la base de datos con datos de ejemplo.
Uso: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de ejemplo para pruebas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='demo',
            help='Username del usuario demo'
        )
        parser.add_argument(
            '--months',
            type=int,
            default=3,
            help='Número de meses de datos históricos'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpiar datos existentes antes de crear nuevos'
        )

    def handle(self, *args, **options):
        username = options['username']
        months = options['months']
        clear = options['clear']

        self.stdout.write(
            self.style.NOTICE(f'🌱 Iniciando seed de datos para usuario: {username}')
        )

        # Crear o obtener usuario
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@financeiq.com',
                'first_name': 'Usuario',
                'last_name': 'Demo',
                'is_active': True,
            }
        )

        if created:
            user.set_password('demo1234')
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario creado: {username} / demo1234')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Usuario existente: {username}')
            )

        # Limpiar datos si se solicita
        if clear:
            self._clear_user_data(user)

        # Crear categorías del sistema
        from apps.core.services import CategoryService
        CategoryService.get_or_create_system_categories()
        self.stdout.write(self.style.SUCCESS('✅ Categorías del sistema creadas'))

        # Obtener categorías
        from apps.core.models import Category
        categories = {
            cat.slug: cat
            for cat in Category.objects.filter(is_system=True)
        }

        # Crear ingresos y gastos históricos
        self._create_historical_data(user, categories, months)

        # Crear objetivos financieros
        self._create_goals(user)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Seed completado exitosamente!\n'
                f'   Usuario: {username}\n'
                f'   Contraseña: demo1234\n'
                f'   URL: http://localhost:8000\n'
            )
        )

    def _clear_user_data(self, user):
        """Limpia todos los datos del usuario."""
        from apps.core.models import Income, Expense, FinancialGoal, Alert, MonthlySnapshot

        Income.objects.filter(user=user).delete()
        Expense.objects.filter(user=user).delete()
        FinancialGoal.objects.filter(user=user).delete()
        Alert.objects.filter(user=user).delete()
        MonthlySnapshot.objects.filter(user=user).delete()
        self.stdout.write(self.style.WARNING('🗑️ Datos anteriores eliminados'))

    def _create_historical_data(self, user, categories, months):
        """Crea datos históricos de ingresos y gastos."""
        from apps.core.models import Income, Expense

        today = date.today()
        incomes_created = 0
        expenses_created = 0

        # Datos de ingresos por mes
        income_data = [
            {
                'description': 'Salario mensual',
                'amount': Decimal('3500000'),
                'source': 'Empresa ABC',
                'category_slug': 'salario',
                'recurrence': 'monthly',
                'day': 1,
            },
            {
                'description': 'Proyecto freelance',
                'amount': Decimal('800000'),
                'source': 'Cliente XYZ',
                'category_slug': 'freelance',
                'recurrence': 'once',
                'day': 15,
                'probability': 0.6,
            },
            {
                'description': 'Bonificación trimestral',
                'amount': Decimal('500000'),
                'source': 'Empresa ABC',
                'category_slug': 'salario',
                'recurrence': 'once',
                'day': 28,
                'probability': 0.3,
            },
        ]

        # Datos de gastos por categoría
        expense_templates = [
            # Hogar
            {
                'description': 'Arriendo apartamento',
                'amount_range': (900000, 900000),
                'category_slug': 'hogar',
                'is_essential': True,
                'is_recurring': True,
                'day': 5,
                'probability': 1.0,
            },
            {
                'description': 'Servicios públicos (agua, luz, gas)',
                'amount_range': (150000, 220000),
                'category_slug': 'hogar',
                'is_essential': True,
                'is_recurring': True,
                'day': 10,
                'probability': 1.0,
            },
            {
                'description': 'Internet hogar',
                'amount_range': (80000, 80000),
                'category_slug': 'hogar',
                'is_essential': True,
                'is_recurring': True,
                'day': 12,
                'probability': 1.0,
            },
            # Transporte
            {
                'description': 'Uber al trabajo',
                'amount_range': (15000, 35000),
                'category_slug': 'transporte',
                'is_essential': True,
                'is_recurring': False,
                'frequency_per_month': 12,
                'probability': 1.0,
            },
            {
                'description': 'Gasolina moto',
                'amount_range': (80000, 120000),
                'category_slug': 'transporte',
                'is_essential': True,
                'is_recurring': True,
                'day': 8,
                'probability': 0.8,
            },
            # Comida
            {
                'description': 'Mercado semanal',
                'amount_range': (150000, 250000),
                'category_slug': 'comida',
                'is_essential': True,
                'is_recurring': True,
                'frequency_per_month': 4,
                'probability': 1.0,
            },
            {
                'description': 'Almuerzo restaurante',
                'amount_range': (12000, 25000),
                'category_slug': 'comida',
                'is_essential': False,
                'is_recurring': False,
                'frequency_per_month': 8,
                'probability': 0.9,
            },
            {
                'description': 'Dominos Pizza',
                'amount_range': (35000, 65000),
                'category_slug': 'comida',
                'is_essential': False,
                'is_recurring': False,
                'frequency_per_month': 2,
                'probability': 0.7,
            },
            {
                'description': 'Rappi - Comida a domicilio',
                'amount_range': (25000, 55000),
                'category_slug': 'comida',
                'is_essential': False,
                'is_recurring': False,
                'frequency_per_month': 3,
                'probability': 0.8,
            },
            # Entretenimiento
            {
                'description': 'Netflix',
                'amount_range': (17000, 17000),
                'category_slug': 'entretenimiento',
                'is_essential': False,
                'is_recurring': True,
                'day': 15,
                'probability': 1.0,
            },
            {
                'description': 'Spotify Premium',
                'amount_range': (16900, 16900),
                'category_slug': 'entretenimiento',
                'is_essential': False,
                'is_recurring': True,
                'day': 20,
                'probability': 1.0,
            },
            {
                'description': 'Cine con amigos',
                'amount_range': (25000, 45000),
                'category_slug': 'entretenimiento',
                'is_essential': False,
                'is_recurring': False,
                'frequency_per_month': 2,
                'probability': 0.6,
            },
            # Salud
            {
                'description': 'Gym mensual',
                'amount_range': (80000, 80000),
                'category_slug': 'salud',
                'is_essential': True,
                'is_recurring': True,
                'day': 1,
                'probability': 0.9,
            },
            {
                'description': 'Farmacia - medicamentos',
                'amount_range': (20000, 80000),
                'category_slug': 'salud',
                'is_essential': True,
                'is_recurring': False,
                'frequency_per_month': 1,
                'probability': 0.5,
            },
            # Educación
                        {
                'description': 'Curso Platzi',
                'amount_range': (100000, 100000),
                'category_slug': 'educacion',
                'is_essential': False,
                'is_recurring': True,
                'day': 25,
                'probability': 0.7,
            },
            {
                'description': 'Libro técnico',
                'amount_range': (40000, 90000),
                'category_slug': 'educacion',
                'is_essential': False,
                'is_recurring': False,
                'frequency_per_month': 1,
                'probability': 0.3,
            },
            # Ropa
            {
                'description': 'Ropa y accesorios',
                'amount_range': (80000, 250000),
                'category_slug': 'ropa',
                'is_essential': False,
                'is_recurring': False,
                'frequency_per_month': 1,
                'probability': 0.4,
            },
            # Tecnología
            {
                'description': 'Accesorios tecnológicos',
                'amount_range': (50000, 300000),
                'category_slug': 'tecnologia',
                'is_essential': False,
                'is_recurring': False,
                'frequency_per_month': 1,
                'probability': 0.2,
            },
        ]

        # Generar datos para cada mes
        for month_offset in range(months - 1, -1, -1):
            # Calcular fecha del mes
            target_date = today.replace(day=1) - timedelta(days=month_offset * 30)
            year = target_date.year
            month = target_date.month

            import calendar as cal
            last_day = cal.monthrange(year, month)[1]

            # Crear ingresos del mes
            for income_template in income_data:
                probability = income_template.get('probability', 1.0)
                if random.random() > probability:
                    continue

                day = income_template.get('day', 1)
                day = min(day, last_day)
                income_date = date(year, month, day)

                # No crear fechas futuras
                if income_date > today:
                    continue

                Income.objects.get_or_create(
                    user=user,
                    description=income_template['description'],
                    date=income_date,
                    defaults={
                        'amount': income_template['amount'],
                        'source': income_template.get('source', ''),
                        'category': categories.get(income_template['category_slug']),
                        'recurrence': income_template.get('recurrence', 'once'),
                    }
                )
                incomes_created += 1

            # Crear gastos del mes
            for template in expense_templates:
                probability = template.get('probability', 1.0)
                if random.random() > probability:
                    continue

                frequency = template.get('frequency_per_month', 1)
                day = template.get('day', None)

                if day:
                    # Gasto en día fijo
                    expense_day = min(day, last_day)
                    expense_date = date(year, month, expense_day)

                    if expense_date > today:
                        continue

                    amount = Decimal(str(random.randint(
                        template['amount_range'][0],
                        template['amount_range'][1]
                    )))

                    Expense.objects.get_or_create(
                        user=user,
                        description=template['description'],
                        date=expense_date,
                        defaults={
                            'amount': amount,
                            'category': categories.get(template['category_slug']),
                            'is_essential': template.get('is_essential', True),
                            'is_recurring': template.get('is_recurring', False),
                            'auto_classified': False,
                        }
                    )
                    expenses_created += 1
                else:
                    # Gastos múltiples en el mes
                    for _ in range(frequency):
                        if random.random() > probability:
                            continue

                        expense_day = random.randint(1, last_day)
                        expense_date = date(year, month, expense_day)

                        if expense_date > today:
                            continue

                        amount = Decimal(str(random.randint(
                            template['amount_range'][0],
                            template['amount_range'][1]
                        )))

                        Expense.objects.create(
                            user=user,
                            description=template['description'],
                            date=expense_date,
                            amount=amount,
                            category=categories.get(template['category_slug']),
                            is_essential=template.get('is_essential', True),
                            is_recurring=template.get('is_recurring', False),
                            auto_classified=False,
                        )
                        expenses_created += 1

            # Generar snapshot mensual
            try:
                from apps.core.services import FinancialAnalysisService
                FinancialAnalysisService.generate_monthly_snapshot(
                    user=user,
                    year=year,
                    month=month,
                )
                self.stdout.write(
                    self.style.SUCCESS(f'  📸 Snapshot {year}-{month:02d} generado')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️ Error en snapshot {year}-{month:02d}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Datos creados: {incomes_created} ingresos, '
                f'{expenses_created} gastos'
            )
        )

    def _create_goals(self, user):
        """Crea objetivos financieros de ejemplo."""
        from apps.core.models import FinancialGoal
        from apps.core.services import GoalService

        goals_data = [
            {
                'name': 'Fondo de Emergencia',
                'description': '3 meses de gastos como colchón de seguridad',
                'goal_type': 'emergency_fund',
                'target_amount': Decimal('5000000'),
                'current_amount': Decimal('1500000'),
                'target_date': date.today() + timedelta(days=180),
                'status': 'active',
            },
            {
                'name': 'Viaje a Europa',
                'description': 'Vacaciones soñadas por 15 días',
                'goal_type': 'purchase',
                'target_amount': Decimal('8000000'),
                'current_amount': Decimal('2000000'),
                'target_date': date.today() + timedelta(days=365),
                'status': 'active',
            },
            {
                'name': 'Laptop nueva',
                'description': 'MacBook Pro para trabajo',
                'goal_type': 'purchase',
                'target_amount': Decimal('4500000'),
                'current_amount': Decimal('4500000'),
                'target_date': date.today() - timedelta(days=30),
                'status': 'completed',
            },
            {
                'name': 'Inversión en acciones',
                'description': 'Portafolio inicial de inversión',
                'goal_type': 'investment',
                'target_amount': Decimal('3000000'),
                'current_amount': Decimal('500000'),
                'target_date': date.today() + timedelta(days=270),
                'status': 'active',
            },
        ]

        goals_created = 0
        for goal_data in goals_data:
            goal, created = FinancialGoal.objects.get_or_create(
                user=user,
                name=goal_data['name'],
                defaults=goal_data,
            )
            if created:
                GoalService._calculate_monthly_contribution(goal)
                goals_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'✅ {goals_created} metas financieras creadas')
        )