import requests
from django.conf import settings
import urllib3
from datetime import datetime, timedelta

# Desabilitar avisos de SSL para certificados auto-assinados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UniFiGuestAPI:
    GUEST_SSID = 'VISITANTES'  # Nome da rede de visitantes
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = settings.UNIFI_BASE_URL
        self.username = settings.UNIFI_USERNAME
        self.password = settings.UNIFI_PASSWORD
        self.site = 'default'
        self.verify_ssl = False
        self._ssid_id = None  # Cache do ID da rede VISITANTES

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()

    def login(self):
        """Realiza login no UniFi Controller"""
        login_url = f"{self.base_url}/api/login"
        self.session.post(
            login_url,
            json={"username": self.username, "password": self.password},
            verify=self.verify_ssl
        )

    def logout(self):
        """Realiza logout do UniFi Controller"""
        try:
            logout_url = f"{self.base_url}/api/logout"
            self.session.get(logout_url, verify=self.verify_ssl)
        except:
            pass

    def get_mac_from_ip(self, ip_address):
        """
        Obtém o MAC address de um cliente a partir do seu IP.
        Retorna None se não encontrar.
        """
        # Busca todos os clientes ativos
        clients_url = f"{self.base_url}/api/s/{self.site}/stat/sta"
        response = self.session.get(clients_url, verify=self.verify_ssl)
        response.raise_for_status()
        
        clients = response.json().get('data', [])
        
        # Procura um cliente com o IP especificado
        for client in clients:
            if client.get('ip', '') == ip_address:
                return client.get('mac', '').upper()
        
        return None

    def _get_ssid_id(self):
        """Obtém o ID da rede VISITANTES"""
        if self._ssid_id is None:
            url = f"{self.base_url}/api/s/{self.site}/rest/wlanconf"
            response = self.session.get(url, verify=self.verify_ssl)
            response.raise_for_status()
            ssids = response.json().get('data', [])
            
            ssid_obj = next((s for s in ssids if s.get('name') == self.GUEST_SSID), None)
            if not ssid_obj:
                raise Exception(f"SSID '{self.GUEST_SSID}' não encontrado")
            
            self._ssid_id = ssid_obj.get('_id')
        
        return self._ssid_id

    def _update_whitelist(self, mac_address, add=True):
        """Atualiza a whitelist da rede VISITANTES"""
        ssid_id = self._get_ssid_id()
        url = f"{self.base_url}/api/s/{self.site}/rest/wlanconf"
        
        # Obtém a configuração atual da rede
        response = self.session.get(url, verify=self.verify_ssl)
        response.raise_for_status()
        ssids = response.json().get('data', [])
        ssid_obj = next((s for s in ssids if s.get('_id') == ssid_id), None)
        
        # Obtém a whitelist atual
        whitelist = ssid_obj.get('mac_filter_list', [])
        mac_upper = mac_address.upper()
        
        if add and mac_upper not in whitelist:
            whitelist.append(mac_upper)
        elif not add and mac_upper in whitelist:
            whitelist.remove(mac_upper)
        
        # Atualiza a whitelist
        update_url = f"{self.base_url}/api/s/{self.site}/rest/wlanconf/{ssid_id}"
        data = {
            "mac_filter_list": whitelist,
            "mac_filter_enabled": True,
            "mac_filter_policy": "allow"  # Política de whitelist
        }
        
        response = self.session.put(update_url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()

    def authorize_guest(self, mac_address, minutes=60):
        """
        Autoriza um visitante por um período determinado na rede VISITANTES.
        Por padrão, autoriza por 60 minutos.
        """
        # Primeiro, adiciona o MAC à whitelist da rede VISITANTES
        self._update_whitelist(mac_address, add=True)
        
        # Depois, autoriza o cliente com as restrições de tempo e banda
        auth_url = f"{self.base_url}/api/s/{self.site}/cmd/stamgr"
        expire_time = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        
        data = {
            "cmd": "authorize-guest",
            "mac": mac_address.upper(),
            "minutes": minutes,
            "up": 1024,  # Upload limit: 1 Mbps
            "down": 2048,  # Download limit: 2 Mbps
            "bytes": 0,  # Sem limite de dados
            "expire_time": expire_time
        }
        
        response = self.session.post(auth_url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()

    def unauthorize_guest(self, mac_address):
        """Remove a autorização de um visitante e o remove da whitelist"""
        # Primeiro, remove o MAC da whitelist
        self._update_whitelist(mac_address, add=False)
        
        # Depois, desautoriza o cliente
        auth_url = f"{self.base_url}/api/s/{self.site}/cmd/stamgr"
        data = {
            "cmd": "unauthorize-guest",
            "mac": mac_address.upper()
        }
        
        response = self.session.post(auth_url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()

    def get_guest_status(self, mac_address):
        """
        Verifica o status de autorização de um visitante.
        Retorna um dicionário com informações do cliente ou None se não encontrar.
        """
        clients_url = f"{self.base_url}/api/s/{self.site}/stat/guest"
        response = self.session.get(clients_url, verify=self.verify_ssl)
        response.raise_for_status()
        
        guests = response.json().get('data', [])
        mac_upper = mac_address.upper()
        
        for guest in guests:
            if guest.get('mac', '').upper() == mac_upper:
                return {
                    'authorized': guest.get('authorized', False),
                    'expire_time': guest.get('end', 0),
                    'hostname': guest.get('hostname', ''),
                    'ip': guest.get('ip', ''),
                    'upload_bytes': guest.get('tx_bytes', 0),
                    'download_bytes': guest.get('rx_bytes', 0),
                    'last_seen': guest.get('last_seen', 0)
                }
        
        return None
