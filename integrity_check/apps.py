from django.apps import AppConfig


class IntegrityCheckConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'integrity_check'
    verbose_name = 'Contrôle d\'Intégrité'
