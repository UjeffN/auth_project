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

    def authorize_guest(self, mac, minutes=60):
        """
        Autoriza um dispositivo (por MAC address) na rede por um tempo definido.
        :param mac: Endereço MAC (ex: AA:BB:CC:DD:EE:FF)
        :param minutes: Tempo em minutos (0 = sem expiração)
        """
        auth_url = f"{self.base_url}/api/s/{self.site}/cmd/stamgr"
        data = {
            "cmd": "authorize-guest",
            "mac": mac,
            "minutes": minutes
        }
        response = self.session.post(auth_url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()
