from django.apps import AppConfig


class UnifiAuthAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unifi_auth_app'

    def ready(self):
        import unifi_auth_app.signals
