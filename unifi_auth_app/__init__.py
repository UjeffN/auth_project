# Configuração padrão do aplicativo
default_app_config = 'unifi_auth_app.apps.UnifiAuthAppConfig'

# Não importamos mais os modelos aqui para evitar importações circulares
# Eles serão importados conforme necessário nos módulos que os utilizam
__all__ = [
    'UniFiUser', 
    'Dispositivo', 
    'UnifiUserStatus', 
    'Visitante',
    'APIAuditMiddleware',
    'SecurityHeadersMiddleware',
    'ErrorHandlingMiddleware',
    'PortalMiddleware'
]

# Importa os middlewares para disponibilizá-los no namespace do pacote
from .audit_logger import APIAuditMiddleware
from .security_headers import SecurityHeadersMiddleware
from .request_timing import RequestTimingMiddleware
from .middleware import ErrorHandlingMiddleware, PortalMiddleware
