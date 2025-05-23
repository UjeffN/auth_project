import requests
import logging
from django.conf import settings

logger = logging.getLogger('unifi_auth_app')

class UnifiController:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.base_url = f"https://{settings.UNIFI_CONTROLLER_CONFIG['IP']}:{settings.UNIFI_CONTROLLER_CONFIG['PORT']}"
        self.site_id = settings.UNIFI_CONTROLLER_CONFIG['SITE_ID']
        self.username = settings.UNIFI_CONTROLLER_CONFIG['USERNAME']
        self.password = settings.UNIFI_CONTROLLER_CONFIG['PASSWORD']
        self.logged_in = False
        logger.info(f'UnifiController initialized with base_url={self.base_url}, site_id={self.site_id}, username={self.username}')

    def login(self):
        """Faz login no UniFi Controller"""
        try:
            login_url = f"{self.base_url}/api/login"
            login_data = {
                "username": self.username,
                "password": self.password
            }

            logger.info('=== Iniciando login no UniFi Controller ===')
            logger.info(f'Login URL: {login_url}')
            logger.info(f'Login Data: {login_data}')

            response = self.session.post(
                login_url,
                json=login_data,
                headers={"Content-Type": "application/json"}
            )

            logger.info(f'Login Response Status: {response.status_code}')
            logger.info(f'Login Response: {response.text}')
            logger.info(f'Login Cookies: {dict(response.cookies)}')

            if response.status_code == 200:
                self.logged_in = True
                logger.info('Login no UniFi Controller realizado com sucesso')
                return True
            else:
                logger.error('Erro ao fazer login no UniFi Controller')
                return False

        except Exception as e:
            logger.error(f'Erro ao fazer login no UniFi Controller: {str(e)}')
            return False

    def authorize_guest(self, mac_address, ap_mac, minutes):
        """Autoriza um cliente no UniFi Controller"""
        try:
            if not self.logged_in:
                logger.info('Não está logado, fazendo login primeiro...')
                if not self.login():
                    logger.error('Falha ao fazer login')
                    return False

            authorize_url = f"{self.base_url}/api/s/{self.site_id}/cmd/stamgr/authorize-guest"
            payload = {
                "mac": mac_address,
                "ap_mac": ap_mac,
                "minutes": minutes
            }

            logger.info('=== Iniciando autorização no UniFi Controller ===')
            logger.info(f'Authorize URL: {authorize_url}')
            logger.info(f'Authorize Payload: {payload}')
            logger.info(f'Session Cookies: {dict(self.session.cookies)}')

            response = self.session.post(
                authorize_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            logger.info(f'Authorize Response Status: {response.status_code}')
            logger.info(f'Authorize Response: {response.text}')

            response_data = response.json() if response.status_code == 200 else None
            logger.info(f'Response Headers: {dict(response.headers)}')
            
            if response.status_code == 200 and response_data:
                if response_data.get('meta', {}).get('rc') == 'ok':
                    logger.info('Autorização realizada com sucesso')
                    return True
                else:
                    error_msg = response_data.get('meta', {}).get('msg', 'Erro desconhecido')
                    logger.error(f'Erro na resposta do UniFi Controller: {error_msg}')
                    logger.error(f'Response completa: {response_data}')
                    return False
            else:
                logger.error(f'Erro ao autorizar no UniFi Controller. Status: {response.status_code}')
                logger.error(f'Response: {response.text}')
                return False

        except Exception as e:
            logger.error(f'Erro ao autorizar no UniFi Controller: {str(e)}')
            return False
