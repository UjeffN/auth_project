from django.apps import AppConfig


class UnifiAuthAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unifi_auth_app'

    def ready(self):
        # Importa os sinais para que eles sejam conectados quando a app estiver pronta.
        import unifi_auth_app.signals
