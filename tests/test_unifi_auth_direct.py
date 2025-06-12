#!/usr/bin/env python3
"""
Script para testar diretamente a autenticação no UniFi Controller.
"""
import os
import sys
import logging
import requests
import urllib3
from pathlib import Path

# Desativa avisos de certificado SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/unifi_auth/test_unifi_auth_direct.log')
    ]
)
logger = logging.getLogger('test_unifi_auth_direct')

class UnifiControllerTest:
    def __init__(self, ip, port, username, password, site_id='default'):
        self.session = requests.Session()
        self.session.verify = False  # Ignora erros de certificado SSL
        self.base_url = f"https://{ip}:{port}"
        self.site_id = site_id
        self.username = username
        self.password = password
        self.logged_in = False
        logger.info(f'UnifiController inicializado com URL: {self.base_url}, site: {self.site_id}')

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
            logger.info(f'Usuário: {self.username}')

            response = self.session.post(
                login_url,
                json=login_data,
                headers={"Content-Type": "application/json"}
            )

            logger.info(f'Status da resposta: {response.status_code}')
            logger.debug(f'Resposta: {response.text}')

            if response.status_code == 200:
                self.logged_in = True
                logger.info('Login realizado com sucesso')
                return True
            else:
                logger.error('Falha no login')
                return False

        except Exception as e:
            logger.error(f'Erro ao fazer login: {str(e)}')
            return False

    def authorize_guest(self, mac_address, minutes=1440, ap_mac=None):
        """Autoriza um cliente no UniFi Controller"""
        if not self.logged_in:
            logger.info('Não está logado, fazendo login...')
            if not self.login():
                return False

        try:
            authorize_url = f"{self.base_url}/api/s/{self.site_id}/cmd/stamgr/authorize-guest"
            payload = {
                "mac": mac_address,
                "minutes": minutes
            }
            
            # Adiciona o AP MAC se fornecido
            if ap_mac:
                payload["ap_mac"] = ap_mac

            logger.info('=== Iniciando autorização ===')
            logger.info(f'URL: {authorize_url}')
            logger.info(f'MAC: {mac_address}')
            logger.info(f'Minutos: {minutes}')
            if ap_mac:
                logger.info(f'AP MAC: {ap_mac}')

            response = self.session.post(
                authorize_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            logger.info(f'Status da resposta: {response.status_code}')
            logger.info(f'Resposta: {response.text}')

            if response.status_code == 200:
                result = response.json()
                if result.get('meta', {}).get('rc') == 'ok':
                    logger.info('Dispositivo autorizado com sucesso')
                    return True
                else:
                    error_msg = result.get('meta', {}).get('msg', 'Erro desconhecido')
                    logger.error(f'Erro na resposta: {error_msg}')
                    return False
            else:
                logger.error(f'Erro na requisição. Status: {response.status_code}')
                return False

        except Exception as e:
            logger.error(f'Erro ao autorizar dispositivo: {str(e)}')
            return False

def main():
    # Configuração do UniFi Controller
    UNIFI_CONFIG = {
        'ip': '192.168.48.2',  # IP do controlador UniFi
        'port': '8447',         # Porta do controlador
        'username': 'jueferson.souto',  # Substitua pelo nome de usuário
        'password': 'cmp@2023',         # Substitua pela senha
        'site_id': 'default'    # ID do site no UniFi (geralmente 'default')
    }


    # MAC de teste (substitua por um MAC real para teste)
    # Formato: 'XX:XX:XX:XX:XX:XX' ou 'XX-XX-XX-XX-XX-XX'
    test_mac = '00:11:22:33:44:55'  # Substitua por um MAC real para teste
    test_minutes = 60  # 1 hora para teste

    logger.info("=== Iniciando teste de autorização UniFi ===")
    logger.info(f"Controlador: {UNIFI_CONFIG['ip']}:{UNIFI_CONFIG['port']}")
    logger.info(f"Site: {UNIFI_CONFIG['site_id']}")
    logger.info(f"Usuário: {UNIFI_CONFIG['username']}")
    logger.info(f"MAC de teste: {test_mac}")
    logger.info(f"Duração: {test_minutes} minutos")

    # Inicializa o controlador
    unifi = UnifiControllerTest(
        ip=UNIFI_CONFIG['ip'],
        port=UNIFI_CONFIG['port'],
        username=UNIFI_CONFIG['username'],
        password=UNIFI_CONFIG['password'],
        site_id=UNIFI_CONFIG['site_id']
    )

    # Testa o login
    if unifi.login():
        logger.info("Login bem-sucedido!")
        
        # Testa a autorização
        if unifi.authorize_guest(test_mac, test_minutes):
            logger.info("Teste de autorização concluído com sucesso!")
            return True
        else:
            logger.error("Falha na autorização do dispositivo")
            return False
    else:
        logger.error("Falha no login")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
