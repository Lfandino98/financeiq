from django.urls import path
from apps.core import views

urlpatterns = [
    # Auth
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Ingresos
    path('ingresos/', views.income_list_view, name='income_list'),
    path('ingresos/nuevo/', views.income_create_view, name='income_create'),
    path('ingresos/<uuid:income_id>/editar/', views.income_edit_view, name='income_edit'),
    path('ingresos/<uuid:income_id>/eliminar/', views.income_delete_view, name='income_delete'),

    # Gastos
    path('gastos/', views.expense_list_view, name='expense_list'),
    path('gastos/nuevo/', views.expense_create_view, name='expense_create'),
    path('gastos/<uuid:expense_id>/editar/', views.expense_edit_view, name='expense_edit'),
    path('gastos/<uuid:expense_id>/eliminar/', views.expense_delete_view, name='expense_delete'),

    # Objetivos
    path('metas/', views.goal_list_view, name='goal_list'),
    path('metas/nueva/', views.goal_create_view, name='goal_create'),
    path('metas/<uuid:goal_id>/editar/', views.goal_edit_view, name='goal_edit'),
    path('metas/<uuid:goal_id>/contribuir/', views.goal_contribute_view, name='goal_contribute'),
    path('metas/<uuid:goal_id>/eliminar/', views.goal_delete_view, name='goal_delete'),

    # Alertas
    path('alertas/', views.alerts_view, name='alerts'),
    path('alertas/<uuid:alert_id>/descartar/', views.alert_dismiss_view, name='alert_dismiss'),

    # Categorías
    path('categorias/', views.category_list_view, name='category_list'),
    path('categorias/nueva/', views.category_create_view, name='category_create'),

    # Análisis
    path('analisis/', views.analysis_view, name='analysis'),

    # AJAX
    path('ajax/clasificar/', views.ajax_classify_expense, name='ajax_classify'),
    path('ajax/dashboard-data/', views.ajax_dashboard_chart_data, name='ajax_dashboard_data'),
    path('ajax/resumen/', views.ajax_financial_summary, name='ajax_summary'),
]