# Configuração padrão do aplicativo
default_app_config = 'unifi_auth_app.apps.UnifiAuthAppConfig'

# Não importamos mais os modelos aqui para evitar importações circulares
# Eles serão importados conforme necessário nos módulos que os utilizam
__all__ = ['UniFiUser', 'Dispositivo', 'UnifiUserStatus', 'Visitante']
