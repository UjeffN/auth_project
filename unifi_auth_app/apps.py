from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class UnifiAuthAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unifi_auth_app'
    verbose_name = 'UniFi Auth App'

    def ready(self):
        # Importa os sinais apenas quando o aplicativo estiver pronto
        try:
            # Importa os sinais principais
            import unifi_auth_app.signals
            # Importa os sinais específicos para visitantes
            import unifi_auth_app.visitante_signals
            logger.info("Sinais do aplicativo carregados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar sinais: {e}", exc_info=True)
