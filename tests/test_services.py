# tests/test_classifier.py
"""
Tests del clasificador de gastos.
Ejecutar: python manage.py test tests.test_classifier
"""
from django.test import TestCase
from apps.core.classifiers import ExpenseClassifier


class TestExpenseClassifier(TestCase):

    def setUp(self):
        self.classifier = ExpenseClassifier()

    def test_classify_transport(self):
        """Prueba clasificación de transporte."""
        cases = ['uber al trabajo', 'taxi aeropuerto', 'gasolina moto']
        for case in cases:
            result = self.classifier.classify(case)
            self.assertEqual(
                result['category'], 'transporte',
                f"'{case}' debería clasificarse como transporte"
            )

    def test_classify_food(self):
        """Prueba clasificación de comida."""
        cases = ['pizza dominos', 'almuerzo restaurante', 'mercado semanal']
        for case in cases:
            result = self.classifier.classify(case)
            self.assertEqual(
                result['category'], 'comida',
                f"'{case}' debería clasificarse como comida"
            )

    def test_classify_entertainment(self):
        """Prueba clasificación de entretenimiento."""
        cases = ['netflix mensual', 'spotify premium', 'cine con amigos']
        for case in cases:
            result = self.classifier.classify(case)
            self.assertEqual(
                result['category'], 'entretenimiento',
                f"'{case}' debería clasificarse como entretenimiento"
            )

    def test_classify_health(self):
        """Prueba clasificación de salud."""
        cases = ['farmacia medicamentos', 'consulta medico', 'gym mensual']
        for case in cases:
            result = self.classifier.classify(case)
            self.assertEqual(
                result['category'], 'salud',
                f"'{case}' debería clasificarse como salud"
            )

    def test_fallback_unknown(self):
        """Prueba fallback para descripciones desconocidas."""
        result = self.classifier.classify('xyzabc123')
        self.assertEqual(result['category'], 'otros')
        self.assertEqual(result['method'], 'fallback')

    def test_empty_description(self):
        """Prueba con descripción vacía."""
        result = self.classifier.classify('')
        self.assertEqual(result['category'], 'otros')
        self.assertEqual(result['confidence'], 0.0)

    def test_confidence_score(self):
        """Prueba que la confianza esté entre 0 y 1."""
        result = self.classifier.classify('netflix')
        self.assertGreaterEqual(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)

    def test_batch_classify(self):
        """Prueba clasificación en lote."""
        descriptions = ['uber', 'netflix', 'farmacia']
        results = self.classifier.batch_classify(descriptions)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('description', result)
            self.assertIn('classification', result)


# tests/test_analyzers.py
"""
Tests del motor de análisis financiero.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import MagicMock

from apps.core.analyzers import (
    FinancialCalculator,
    FinancialHealthEvaluator,
    RecommendationEngine,
    FinancialProjectionEngine,
)


class TestFinancialCalculator(TestCase):

    def setUp(self):
        self.calculator = FinancialCalculator()

    def _make_income(self, amount):
        income = MagicMock()
        income.amount = Decimal(str(amount))
        return income

    def _make_expense(self, amount, category_name='comida'):
        expense = MagicMock()
        expense.amount = Decimal(str(amount))
        expense.category = MagicMock()
        expense.category.name = category_name
        expense.description = 'Test expense'
        expense.date = date.today()
        expense.id = '123'
        return expense

    def test_total_income(self):
        """Prueba cálculo de ingresos totales."""
        incomes = [
            self._make_income(1000000),
            self._make_income(500000),
            self._make_income(250000),
        ]
        total = self.calculator.total_income(incomes)
        self.assertEqual(total, Decimal('1750000'))

    def test_total_expenses(self):
        """Prueba cálculo de gastos totales."""
        expenses = [
            self._make_expense(300000),
            self._make_expense(150000),
            self._make_expense(50000),
        ]
        total = self.calculator.total_expenses(expenses)
        self.assertEqual(total, Decimal('500000'))

    def test_net_savings_positive(self):
        """Prueba ahorro neto positivo."""
        savings = self.calculator.net_savings(
            Decimal('1000000'),
            Decimal('700000')
        )
        self.assertEqual(savings, Decimal('300000'))

    def test_net_savings_negative(self):
        """Prueba ahorro neto negativo (déficit)."""
        savings = self.calculator.net_savings(
            Decimal('500000'),
            Decimal('700000')
        )
        self.assertEqual(savings, Decimal('-200000'))

    def test_savings_rate(self):
        """Prueba cálculo de tasa de ahorro."""
        rate = self.calculator.savings_rate(
            Decimal('1000000'),
            Decimal('200000')
        )
        self.assertAlmostEqual(rate, 0.20, places=2)

    def test_savings_rate_zero_income(self):
        """Prueba tasa de ahorro con ingreso cero."""
        rate = self.calculator.savings_rate(
            Decimal('0'),
            Decimal('0')
        )
        self.assertEqual(rate, 0.0)

    def test_expense_ratio(self):
        """Prueba ratio de gastos."""
        ratio = self.calculator.expense_ratio(
            Decimal('800000'),
            Decimal('1000000')
        )
        self.assertAlmostEqual(ratio, 0.80, places=2)


class TestFinancialHealthEvaluator(TestCase):

    def setUp(self):
        self.evaluator = FinancialHealthEvaluator()

    def test_healthy_status(self):
        """Prueba estado saludable."""
        result = self.evaluator.evaluate(
            savings_rate=0.25,
            expense_ratio=0.75,
            category_percentages={},
            has_goals=True,
        )
        self.assertEqual(result['status'], 'healthy')
        self.assertGreaterEqual(result['score'], 70)

    def test_risky_status(self):
        """Prueba estado riesgoso."""
        result = self.evaluator.evaluate(
            savings_rate=-0.10,
            expense_ratio=1.10,
            category_percentages={
                'entretenimiento': {'percentage': 30},
            },
            has_goals=False,
        )
        self.assertEqual(result['status'], 'risky')

    def test_stable_status(self):
        """Prueba estado estable."""
        result = self.evaluator.evaluate(
            savings_rate=0.12,
            expense_ratio=0.88,
            category_percentages={},
            has_goals=True,
        )
        self.assertEqual(result['status'], 'stable')

    def test_score_range(self):
        """Prueba que el score esté entre 0 y 100."""
        result = self.evaluator.evaluate(
            savings_rate=0.05,
            expense_ratio=0.95,
            category_percentages={},
            has_goals=False,
        )
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)


class TestFinancialProjectionEngine(TestCase):

    def setUp(self):
        self.engine = FinancialProjectionEngine()

    def test_projection_keys(self):
        """Prueba que las proyecciones tengan las claves correctas."""
        projections = self.engine.project(
            monthly_income=Decimal('3000000'),
            monthly_expenses=Decimal('2400000'),
            current_savings=Decimal('500000'),
        )
        self.assertIn('3_months', projections)
        self.assertIn('6_months', projections)
        self.assertIn('12_months', projections)

    def test_projection_scenarios(self):
        """Prueba que cada proyección tenga escenarios."""
        projections = self.engine.project(
            monthly_income=Decimal('3000000'),
            monthly_expenses=Decimal('2400000'),
            current_savings=Decimal('500000'),
        )
        for key, projection in projections.items():
            self.assertIn('scenarios', projection)
            self.assertIn('optimistic', projection['scenarios'])
            self.assertIn('base', projection['scenarios'])
            self.assertIn('pessimistic', projection['scenarios'])

    def test_optimistic_greater_than_pessimistic(self):
        """Prueba que el escenario optimista sea mayor al pesimista."""
        projections = self.engine.project(
            monthly_income=Decimal('3000000'),
            monthly_expenses=Decimal('2400000'),
            current_savings=Decimal('500000'),
        )
        for key, projection in projections.items():
            self.assertGreater(
                projection['scenarios']['optimistic'],
                projection['scenarios']['pessimistic'],
            )


# tests/test_services.py
"""
Tests de los servicios financieros.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta

from apps.core.models import Category, Income, Expense, FinancialGoal
from apps.core.services import (
    CategoryService, IncomeService,
    ExpenseService, GoalService,
    FinancialAnalysisService,
)


class TestCategoryService(TestCase):

    def test_create_system_categories(self):
        """Prueba creación de categorías del sistema."""
        categories = CategoryService.get_or_create_system_categories()
        self.assertGreater(len(categories), 0)

        # Verificar que existen categorías clave
        slugs = Category.objects.filter(
            is_system=True
        ).values_list('slug', flat=True)

        self.assertIn('transporte', slugs)
        self.assertIn('comida', slugs)
        self.assertIn('entretenimiento', slugs)
        self.assertIn('salud', slugs)

    def test_suggest_category(self):
        """Prueba sugerencia de categoría."""
        CategoryService.get_or_create_system_categories()
        suggestion = CategoryService.suggest_category_for_description('uber')
        self.assertIsNotNone(suggestion['category'])
        self.assertEqual(suggestion['category'].slug, 'transporte')


class TestGoalService(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

    def test_create_goal(self):
        """Prueba creación de objetivo financiero."""
        data = {
            'name': 'Fondo de emergencia',
            'goal_type': 'emergency_fund',
            'target_amount': Decimal('5000000'),
            'target_date': date.today() + timedelta(days=180),
            'description': 'Mi fondo de emergencia',
        }
        goal = GoalService.create_goal(user=self.user, data=data)

        self.assertEqual(goal.name, 'Fondo de emergencia')
        self.assertEqual(goal.target_amount, Decimal('5000000'))
        self.assertEqual(goal.status, 'active')
        self.assertGreater(goal.monthly_contribution, 0)

    def test_add_contribution(self):
        """Prueba agregar contribución a objetivo."""
        goal = GoalService.create_goal(
            user=self.user,
            data={
                'name': 'Test Goal',
                'goal_type': 'savings',
                'target_amount': Decimal('1000000'),
                'target_date': date.today() + timedelta(days=90),
            }
        )

        updated_goal = GoalService.add_contribution(
            goal=goal,
            amount=Decimal('300000'),
        )

        self.assertEqual(updated_goal.current_amount, Decimal('300000'))
        self.assertAlmostEqual(updated_goal.progress_percentage, 30.0, places=1)

    def test_goal_completion(self):
        """Prueba que el objetivo se marque como completado."""
        goal = GoalService.create_goal(
            user=self.user,
            data={
                'name': 'Test Goal',
                'goal_type': 'savings',
                'target_amount': Decimal('100000'),
                'target_date': date.today() + timedelta(days=30),
            }
        )

        updated_goal = GoalService.add_contribution(
            goal=goal,
            amount=Decimal('100000'),
        )

        self.assertEqual(updated_goal.status, 'completed')
        self.assertEqual(updated_goal.progress_percentage, 100.0)

    def test_goals_summary(self):
        """Prueba resumen de objetivos."""
        GoalService.create_goal(
            user=self.user,
            data={
                'name': 'Meta 1',
                'goal_type': 'savings',
                'target_amount': Decimal('1000000'),
                'target_date': date.today() + timedelta(days=90),
            }
        )
        GoalService.create_goal(
            user=self.user,
            data={
                'name': 'Meta 2',
                'goal_type': 'purchase',
                'target_amount': Decimal('2000000'),
                'target_date': date.today() + timedelta(days=180),
            }
        )

        summary = GoalService.get_goals_summary(self.user)

        self.assertEqual(summary['total_goals'], 2)
        self.assertEqual(summary['active_goals'], 2)
        self.assertEqual(summary['total_target'], 3000000.0)


class TestIncomeService(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser2',
            password='testpass123',
        )
        CategoryService.get_or_create_system_categories()

    def test_create_income(self):
        """Prueba creación de ingreso."""
        data = {
            'amount': Decimal('3500000'),
            'description': 'Salario mensual',
            'date': date.today(),
            'recurrence': 'monthly',
            'source': 'Empresa ABC',
        }
        income = IncomeService.create_income(user=self.user, data=data)

        self.assertEqual(income.amount, Decimal('3500000'))
        self.assertEqual(income.user, self.user)
        self.assertEqual(income.recurrence, 'monthly')

    def test_get_user_incomes_filtered(self):
        """Prueba filtrado de ingresos por período."""
        # Crear ingresos en diferentes fechas
        IncomeService.create_income(
            user=self.user,
            data={
                'amount': Decimal('1000000'),
                'description': 'Ingreso 1',
                'date': date.today(),
                'recurrence': 'once',
            }
        )
        IncomeService.create_income(
            user=self.user,
            data={
                'amount': Decimal('500000'),
                'description': 'Ingreso 2',
                'date': date.today() - timedelta(days=60),
                'recurrence': 'once',
            }
        )

        # Filtrar solo el mes actual
        start = date.today().replace(day=1)
        end = date.today()
        incomes = IncomeService.get_user_incomes(
            user=self.user,
            start_date=start,
            end_date=end,
        )

        self.assertEqual(len(incomes), 1)
        self.assertEqual(incomes[0].description, 'Ingreso 1')


class TestExpenseService(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser3',
            password='testpass123',
        )
        CategoryService.get_or_create_system_categories()

    def test_create_expense_with_auto_classify(self):
        """Prueba creación de gasto con clasificación automática."""
        data = {
            'amount': Decimal('25000'),
            'description': 'Uber al aeropuerto',
            'date': date.today(),
            'is_essential': True,
            'is_recurring': False,
        }
        expense = ExpenseService.create_expense(
            user=self.user,
            data=data,
            auto_classify=True,
        )

        self.assertIsNotNone(expense.category)
        self.assertEqual(expense.category.slug, 'transporte')
        self.assertTrue(expense.auto_classified)

    def test_create_expense_without_auto_classify(self):
        """Prueba creación de gasto sin clasificación automática."""
        category = Category.objects.get(slug='comida', is_system=True)
        data = {
            'amount': Decimal('50000'),
            'description': 'Mercado',
            'date': date.today(),
            'category': category,
            'is_essential': True,
            'is_recurring': False,
        }
        expense = ExpenseService.create_expense(
            user=self.user,
            data=data,
            auto_classify=False,
        )

        self.assertEqual(expense.category, category)
        self.assertFalse(expense.auto_classified)

    def test_update_expense(self):
        """Prueba actualización de gasto."""
        expense = ExpenseService.create_expense(
            user=self.user,
            data={
                'amount': Decimal('30000'),
                'description': 'Pizza',
                'date': date.today(),
                'is_essential': False,
                'is_recurring': False,
            }
        )

        updated = ExpenseService.update_expense(
            expense=expense,
            data={'amount': Decimal('45000'), 'description': 'Pizza grande'},
        )

        self.assertEqual(updated.amount, Decimal('45000'))
        self.assertEqual(updated.description, 'Pizza grande')

    def test_delete_expense(self):
        """Prueba eliminación de gasto."""
        expense = ExpenseService.create_expense(
            user=self.user,
            data={
                'amount': Decimal('20000'),
                'description': 'Test',
                'date': date.today(),
                'is_essential': False,
                'is_recurring': False,
            }
        )
        expense_id = expense.id
        ExpenseService.delete_expense(expense)

        from apps.core.models import Expense
        self.assertFalse(
            Expense.objects.filter(id=expense_id).exists()
        )


class TestFinancialAnalysisService(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser4',
            password='testpass123',
        )
        CategoryService.get_or_create_system_categories()
        self._create_test_data()

    def _create_test_data(self):
        """Crea datos de prueba."""
        # Ingresos
        IncomeService.create_income(
            user=self.user,
            data={
                'amount': Decimal('3500000'),
                'description': 'Salario',
                'date': date.today(),
                'recurrence': 'monthly',
            }
        )

        # Gastos
        category = Category.objects.get(slug='comida', is_system=True)
        ExpenseService.create_expense(
            user=self.user,
            data={
                'amount': Decimal('800000'),
                'description': 'Mercado mensual',
                'date': date.today(),
                'category': category,
                'is_essential': True,
                'is_recurring': True,
            },
            auto_classify=False,
        )

        transport = Category.objects.get(slug='transporte', is_system=True)
        ExpenseService.create_expense(
            user=self.user,
            data={
                'amount': Decimal('300000'),
                'description': 'Transporte mensual',
                'date': date.today(),
                'category': transport,
                'is_essential': True,
                'is_recurring': True,
            },
            auto_classify=False,
        )

    def test_full_analysis_structure(self):
        """Prueba que el análisis tenga la estructura correcta."""
        analysis = FinancialAnalysisService.run_full_analysis(
            user=self.user,
            period='month',
        )

        # Verificar claves principales
        self.assertIn('summary', analysis)
        self.assertIn('health', analysis)
        self.assertIn('categories', analysis)
        self.assertIn('recommendations', analysis)
        self.assertIn('projections', analysis)
        self.assertIn('trend', analysis)
        self.assertIn('anomalies', analysis)

    def test_summary_values(self):
        """Prueba valores del resumen financiero."""
        analysis = FinancialAnalysisService.run_full_analysis(
            user=self.user,
            period='month',
        )
        summary = analysis['summary']

        self.assertGreater(summary['total_income'], 0)
        self.assertGreater(summary['total_expenses'], 0)
        self.assertIn('savings_rate', summary)
        self.assertIn('expense_ratio', summary)

    def test_health_evaluation(self):
        """Prueba evaluación de salud financiera."""
        analysis = FinancialAnalysisService.run_full_analysis(
            user=self.user,
            period='month',
        )
        health = analysis['health']

        self.assertIn('status', health)
        self.assertIn(health['status'], ['healthy', 'stable', 'risky'])
        self.assertIn('score', health)
        self.assertGreaterEqual(health['score'], 0)
        self.assertLessEqual(health['score'], 100)

    def test_projections_exist(self):
        """Prueba que existan proyecciones."""
        analysis = FinancialAnalysisService.run_full_analysis(
            user=self.user,
            period='month',
        )
        projections = analysis['projections']

        self.assertIn('3_months', projections)
        self.assertIn('6_months', projections)
        self.assertIn('12_months', projections)

    def test_get_period_dates(self):
        """Prueba obtención de fechas por período."""
        periods = ['week', 'month', 'quarter', 'year', 'all']
        for period in periods:
            start, end = FinancialAnalysisService.get_period_dates(period)
            self.assertLessEqual(start, end)
            self.assertLessEqual(end, date.today())