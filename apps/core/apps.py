from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core Financiero'

    def ready(self):
        """
        Se ejecuta cuando Django inicia.
        Inicializa categorías del sistema automáticamente.
        """
        try:
            from apps.core.services import CategoryService
            CategoryService.get_or_create_system_categories()
        except Exception:
            # Ignorar errores durante migraciones iniciales
            pass