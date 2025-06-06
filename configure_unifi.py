#!/usr/bin/env python3
import os
import requests
import urllib3
import json
from dotenv import load_dotenv

# Desabilita avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurações do UniFi Controller
UNIFI_BASE_URL = 'https://192.168.48.100:8447'
UNIFI_USERNAME = 'jueferson.souto'
UNIFI_PASSWORD = 'cmp@2023'
UNIFI_SITE = 'default'

# URL do nosso portal cativo
PORTAL_URL = 'http://portal.parauapebas.pa.leg.br'

def unifi_api_call(session, method, endpoint, data=None):
    url = f"{UNIFI_BASE_URL}/api/s/{UNIFI_SITE}/{endpoint}"
    try:
        if method == 'GET':
            response = session.get(url, verify=False)
        elif method == 'POST':
            response = session.post(url, json=data, verify=False)
        elif method == 'PUT':
            response = session.put(url, json=data, verify=False)
        
        print(f"API Call {method} {endpoint}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}\n")
        
        return response
    except Exception as e:
        print(f"Error in API call: {str(e)}")
        return None

def configure_unifi():
    session = requests.Session()
    
    # Login
    print("\nFazendo login...")
    login_response = session.post(
        f"{UNIFI_BASE_URL}/api/login",
        json={"username": UNIFI_USERNAME, "password": UNIFI_PASSWORD},
        verify=False
    )
    if login_response.status_code != 200:
        print("Falha no login")
        return
    
    # Configurar portal cativo global
    print("\nConfigurando portal cativo global...")
    portal_settings = {
        "portal_enabled": True,
        "auth": "password",
        "x_password": "123456",
        "expire": 480,
        "redirect_enabled": True,
        "portal_customized": False,
        "portal_type": "external",
        "bypass_mode": False,
        "voucher_enabled": False,
        "payment_enabled": False,
        "custom_ip": ["192.168.48.101"],
        "custom_ports": ["8880"],
        "gateway_ip": "192.168.48.101",
        "ip_subnet": "192.168.48.0/22",
        "hostname": "portal.parauapebas.pa.leg.br",
        "portal_hostname": "portal.parauapebas.pa.leg.br",
        "portal_port": "8880",
        "portal_https": False,
        "redirect_https": False,
        "portal_use_hostname": True,
        "portal_redirect_https": False,
        "force_https_redirect": False,
        "force_https_portal": False,
        "force_https_all": False,
        "redirect_to_portal": True,
        "redirect_to_https": False,
        "portal_redirect_port": "8880",
        "portal_url": "http://portal.parauapebas.pa.leg.br:8880",
        "portal_ip": "192.168.48.101",
        "portal_interface": "br0",
        "portal_bind_ip": "192.168.48.101",
        "portal_bind_https": False,
        "portal_bind_port": "8880",
        "portal_bind_hostname": "portal.parauapebas.pa.leg.br"
    }
    unifi_api_call(session, 'POST', 'set/setting/guest_access', portal_settings)
    
    # Configurar rede VISITANTES
    print("\nConfigurando rede VISITANTES...")
    wlan_response = unifi_api_call(session, 'GET', 'rest/wlanconf')
    if wlan_response and wlan_response.status_code == 200:
        wlans = wlan_response.json().get('data', [])
        for wlan in wlans:
            if wlan['name'] == 'VISITANTES':
                wlan_id = wlan['_id']
                # Configura a rede
                wlan_config = {
                    "name": "VISITANTES",
                    "enabled": True,
                    "security": "open",
                    "is_guest": True,
                    "networkconf_id": wlan.get('networkconf_id', ''),
                    "portal_enabled": True,
                    "portal_customized": False,
                    "portal_type": "default",
                    "auth": "password",
                    "x_password": "123456",
                    "mac_filter_enabled": False,
                    "no_auth": False,
                    "guest_lan": False,
                    "guest_lan_only": False,
                    "ap_isolation": False,
                    "schedule": [],
                    "wlangroup_id": wlan.get('wlangroup_id', ''),
                    "usergroup_id": "",
                    "group_rekey": 3600,
                    "network_access": "unlimited",
                    "network_optimization": False
                }
                unifi_api_call(session, 'PUT', f'rest/wlanconf/{wlan_id}', wlan_config)
                break
    
    # Forçar provisioning
    print("\nForçando provisioning dos APs...")
    devices_response = unifi_api_call(session, 'GET', 'stat/device')
    if devices_response and devices_response.status_code == 200:
        devices = devices_response.json().get('data', [])
        for device in devices:
            if device.get('type') == 'uap':
                unifi_api_call(session, 'POST', 'cmd/devmgr', {
                    "cmd": "force-provision",
                    "mac": device['mac']
                })
    
    # Logout
    print("\nFazendo logout...")
    session.get(f"{UNIFI_BASE_URL}/logout", verify=False)

if __name__ == "__main__":
    try:
        configure_unifi()
        print("\nConfigurações aplicadas com sucesso!")
    except Exception as e:
        print(f"\nErro: {str(e)}")
