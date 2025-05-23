import requests

class UniFiControllerAPI:
    def __init__(self, base_url, site, username, password, verify_ssl=False):
        self.base_url = base_url
        self.site = site
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self._login()

    def _login(self):
        login_url = f"{self.base_url}/api/login"
        data = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(login_url, json=data, verify=self.verify_ssl)
        response.raise_for_status()

    def add_mac_to_ssid_whitelist(self, mac, ssid_name):
        """
        Adiciona um MAC à lista de permissão (whitelist) do SSID especificado.
        """
        url = f"{self.base_url}/api/s/{self.site}/rest/wlanconf"
        response = self.session.get(url, verify=self.verify_ssl)
        response.raise_for_status()
        ssids = response.json().get('data', [])

        ssid_obj = next((s for s in ssids if s.get('name') == ssid_name), None)
        if not ssid_obj:
            raise Exception(f"SSID '{ssid_name}' não encontrado")

        ssid_id = ssid_obj.get('_id')

        # Pega a lista atual de MACs permitidos (whitelist) para esse SSID
        whitelist = ssid_obj.get('mac_filter_list', [])

        mac_upper = mac.upper()

        if mac_upper in whitelist:
            return {"msg": "MAC já está na whitelist"}

        whitelist.append(mac_upper)

        # Atualiza o SSID com a nova lista de MACs permitidos
        update_url = f"{self.base_url}/api/s/{self.site}/rest/wlanconf/{ssid_id}"
        data = {
            "mac_filter_list": whitelist,
            "mac_filter_enabled": True,
            "mac_filter_policy": "allow"  # Garante que a política seja whitelist
        }
        resp = self.session.put(update_url, json=data, verify=self.verify_ssl)
        resp.raise_for_status()
        return resp.json()

    def remove_mac_from_ssid_whitelist(self, mac, ssid_name):
        """
        Remove um MAC da lista de permissão (whitelist) do SSID especificado.
        """
        url = f"{self.base_url}/api/s/{self.site}/rest/wlanconf"
        response = self.session.get(url, verify=self.verify_ssl)
        response.raise_for_status()
        ssids = response.json().get('data', [])

        ssid_obj = next((s for s in ssids if s.get('name') == ssid_name), None)
        if not ssid_obj:
            raise Exception(f"SSID '{ssid_name}' não encontrado")

        ssid_id = ssid_obj.get('_id')

        whitelist = ssid_obj.get('mac_filter_list', [])

        mac_upper = mac.upper()

        if mac_upper not in whitelist:
            return {"msg": "MAC não está na whitelist"}

        whitelist.remove(mac_upper)

        update_url = f"{self.base_url}/api/s/{self.site}/rest/wlanconf/{ssid_id}"
        data = {
            "mac_filter_list": whitelist,
            "mac_filter_enabled": True,
            "mac_filter_policy": "allow"
        }
        resp = self.session.put(update_url, json=data, verify=self.verify_ssl)
        resp.raise_for_status()
        return resp.json()
