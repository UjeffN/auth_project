import requests
import urllib3
from django.conf import settings
import json

# Desabilitar avisos de SSL para certificados auto-assinados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UniFiControllerAPI:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = settings.UNIFI_BASE_URL
        self.username = settings.UNIFI_USERNAME
        self.password = settings.UNIFI_PASSWORD
        self.site = settings.UNIFI_SITE
        self.verify_ssl = settings.UNIFI_VERIFY_SSL
        self._login()

    def _login(self):
        """Faz login no UniFi Controller"""
        login_url = f"{self.base_url}/api/login"
        response = self.session.post(
            login_url,
            json={
                "username": self.username,
                "password": self.password
            },
            verify=self.verify_ssl
        )
        response.raise_for_status()

    def _logout(self):
        """Faz logout do UniFi Controller"""
        try:
            logout_url = f"{self.base_url}/api/logout"
            self.session.get(logout_url, verify=self.verify_ssl)
        except:
            pass

    def authorize_guest(self, mac, minutes=0):
        """
        Autoriza um dispositivo na rede guest
        :param mac: MAC address do dispositivo
        :param minutes: Tempo em minutos para expirar (0 = sem expiração)
        """
        auth_url = f"{self.base_url}/api/s/{self.site}/cmd/stamgr"
        data = {
            "cmd": "authorize-guest",
            "mac": mac
        }
        if minutes > 0:
            data["minutes"] = minutes

        response = self.session.post(
            auth_url,
            json=data,
            verify=self.verify_ssl
        )
        response.raise_for_status()
        return response.json()

    def unauthorize_guest(self, mac):
        """
        Remove a autorização de um dispositivo na rede guest
        :param mac: MAC address do dispositivo
        """
        auth_url = f"{self.base_url}/api/s/{self.site}/cmd/stamgr"
        response = self.session.post(
            auth_url,
            json={
                "cmd": "unauthorize-guest",
                "mac": mac
            },
            verify=self.verify_ssl
        )
        response.raise_for_status()
        return response.json()

    def get_client(self, mac):
        """
        Obtém informações de um cliente específico
        :param mac: MAC address do cliente
        """
        client_url = f"{self.base_url}/api/s/{self.site}/stat/sta/{mac}"
        response = self.session.get(
            client_url,
            verify=self.verify_ssl
        )
        response.raise_for_status()
        return response.json()

    def get_all_clients(self):
        """Obtém lista de todos os clientes"""
        clients_url = f"{self.base_url}/api/s/{self.site}/stat/sta"
        response = self.session.get(
            clients_url,
            verify=self.verify_ssl
        )
        response.raise_for_status()
        return response.json()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logout()

    def block_client(self, mac):
        """
        Bloqueia um cliente específico
        :param mac: MAC address do cliente
        """
        block_url = f"{self.base_url}/api/s/{self.site}/cmd/stamgr"
        response = self.session.post(
            block_url,
            json={
                "cmd": "block-sta",
                "mac": mac
            },
            verify=self.verify_ssl
        )
        response.raise_for_status()
        return response.json()

    def unblock_client(self, mac):
        """
        Desbloqueia um cliente específico
        :param mac: MAC address do cliente
        """
        unblock_url = f"{self.base_url}/api/s/{self.site}/cmd/stamgr"
        response = self.session.post(
            unblock_url,
            json={
                "cmd": "unblock-sta",
                "mac": mac
            },
            verify=self.verify_ssl
        )
        response.raise_for_status()
        return response.json()
