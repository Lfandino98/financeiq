"""
Context processors globales.
Inyectan datos en todos los templates automáticamente.
"""
from datetime import date
from apps.core.alerts import alert_manager


def global_context(request):
    """
    Contexto global disponible en todos los templates.
    """
    context = {
        'today': date.today(),
        'app_name': 'FinanceIQ',
        'app_version': '1.0.0',
    }

    # Agregar conteo de alertas si el usuario está autenticado
    if request.user.is_authenticated:
        try:
            context['unread_alerts_count'] = alert_manager.get_unread_count(
                request.user
            )
        except Exception:
            context['unread_alerts_count'] = 0

    return context