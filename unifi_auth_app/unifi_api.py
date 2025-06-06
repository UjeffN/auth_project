import requests
import time
from typing import List, Dict, Set
from . import metrics

class UniFiControllerAPI:
    def __init__(self, base_url, site, username, password, verify_ssl=False):
        self.base_url = base_url
        self.site = site
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        # Cache de SSIDs
        self._ssid_cache: Dict[str, dict] = {}
        self._cache_timeout = 300  # 5 minutos
        self._last_cache_update = 0
        self._login()

    def _login(self):
        login_url = f"{self.base_url}/api/login"
        data = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(login_url, json=data, verify=self.verify_ssl)
        response.raise_for_status()

    def _get_ssid_info(self, ssid_name: str) -> dict:
        """Obtém informações do SSID com cache"""
        now = time.time()
        if now - self._last_cache_update > self._cache_timeout:
            metrics.track_cache_access(hit=False)
            url = f"{self.base_url}/api/s/{self.site}/rest/wlanconf"
            response = self.session.get(url, verify=self.verify_ssl)
            response.raise_for_status()
            ssids = response.json().get('data', [])
            self._ssid_cache = {s['name']: s for s in ssids}
            self._last_cache_update = now
            # Atualiza o contador total de MACs na whitelist
            total_macs = sum(len(s.get('mac_filter_list', [])) for s in ssids)
            metrics.update_mac_count(total_macs)
        else:
            metrics.track_cache_access(hit=True)
        
        ssid_obj = self._ssid_cache.get(ssid_name)
        if not ssid_obj:
            raise Exception(f"SSID '{ssid_name}' não encontrado")
        return ssid_obj

    @metrics.track_api_call('update_whitelist')
    def _update_whitelist(self, ssid_id: str, whitelist: List[str]) -> dict:
        """Atualiza a whitelist de um SSID"""
        update_url = f"{self.base_url}/api/s/{self.site}/rest/wlanconf/{ssid_id}"
        data = {
            "mac_filter_list": whitelist,
            "mac_filter_enabled": True,
            "mac_filter_policy": "allow"
        }
        resp = self.session.put(update_url, json=data, verify=self.verify_ssl)
        resp.raise_for_status()
        metrics.update_mac_count(len(whitelist))
        return resp.json()

    @metrics.track_api_call('add_single')
    def add_mac_to_ssid_whitelist(self, mac: str, ssid_name: str) -> dict:
        """Adiciona um MAC à lista de permissão (whitelist) do SSID especificado."""
        try:
            ssid_obj = self._get_ssid_info(ssid_name)
            whitelist = ssid_obj.get('mac_filter_list', [])
            mac_upper = mac.upper()

            if mac_upper in whitelist:
                return {"msg": "MAC já está na whitelist"}

            whitelist.append(mac_upper)
            result = self._update_whitelist(ssid_obj['_id'], whitelist)
            metrics.track_bulk_operation('add_single', success=True)
            return result
        except Exception as e:
            metrics.track_bulk_operation('add_single', success=False)
            raise

    @metrics.track_api_call('bulk_add')
    def bulk_add_macs_to_ssid_whitelist(self, macs: List[str], ssid_name: str) -> dict:
        """Adiciona múltiplos MACs à whitelist de uma vez"""
        try:
            ssid_obj = self._get_ssid_info(ssid_name)
            whitelist = set(ssid_obj.get('mac_filter_list', []))
            
            # Converte todos os MACs para maiúsculo e adiciona ao set
            new_macs = {mac.upper() for mac in macs}
            whitelist.update(new_macs)
            
            result = self._update_whitelist(ssid_obj['_id'], list(whitelist))
            metrics.track_bulk_operation('add', success=True)
            return result
        except Exception as e:
            metrics.track_bulk_operation('add', success=False)
            raise

    @metrics.track_api_call('remove_single')
    def remove_mac_from_ssid_whitelist(self, mac: str, ssid_name: str) -> dict:
        """Remove um MAC da lista de permissão (whitelist) do SSID especificado."""
        try:
            ssid_obj = self._get_ssid_info(ssid_name)
            whitelist = ssid_obj.get('mac_filter_list', [])
            mac_upper = mac.upper()

            if mac_upper not in whitelist:
                return {"msg": "MAC não está na whitelist"}

            whitelist.remove(mac_upper)
            result = self._update_whitelist(ssid_obj['_id'], whitelist)
            metrics.track_bulk_operation('remove_single', success=True)
            return result
        except Exception as e:
            metrics.track_bulk_operation('remove_single', success=False)
            raise

    @metrics.track_api_call('bulk_remove')
    def bulk_remove_macs_from_ssid_whitelist(self, macs: List[str], ssid_name: str) -> dict:
        """Remove múltiplos MACs da whitelist de uma vez"""
        try:
            ssid_obj = self._get_ssid_info(ssid_name)
            whitelist = set(ssid_obj.get('mac_filter_list', []))
            
            # Converte todos os MACs para maiúsculo e remove do set
            macs_to_remove = {mac.upper() for mac in macs}
            whitelist.difference_update(macs_to_remove)
            
            result = self._update_whitelist(ssid_obj['_id'], list(whitelist))
            metrics.track_bulk_operation('remove', success=True)
            return result
        except Exception as e:
            metrics.track_bulk_operation('remove', success=False)
            raise
