from django.conf import settings
import os

UNIFI_CONTROLLER_CONFIG = {
    'IP': os.getenv('UNIFI_CONTROLLER_IP', 'unifi.parauapebas.pa.leg.br'),
    'PORT': os.getenv('UNIFI_CONTROLLER_PORT', '8447'),
    'VERSION': os.getenv('UNIFI_CONTROLLER_VERSION', 'api'),
    'SITE_ID': os.getenv('UNIFI_SITE_ID', 'default'),
    'USERNAME': os.getenv('UNIFI_USERNAME', 'jueferson.souto'),
    'PASSWORD': os.getenv('UNIFI_PASSWORD', 'cmp@2023'),
}

# UniFi API settings
UNIFI_BASE_URL = f'https://{UNIFI_CONTROLLER_CONFIG["IP"]}:{UNIFI_CONTROLLER_CONFIG["PORT"]}'
UNIFI_SITE = UNIFI_CONTROLLER_CONFIG['SITE_ID']
UNIFI_USERNAME = UNIFI_CONTROLLER_CONFIG['USERNAME']
UNIFI_PASSWORD = UNIFI_CONTROLLER_CONFIG['PASSWORD']
UNIFI_VERIFY_SSL = False  # Desabilita verificação SSL para certificados auto-assinados

