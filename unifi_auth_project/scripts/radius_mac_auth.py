import sys
import os

# Ajuste para importar o Django do seu projeto
sys.path.append('/opt/auth_project')  # caminho do seu projeto Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifi_auth_project.settings')

import django
django.setup()

from unifi_auth_app.models import Dispositivo

def authorize(passed_mac):
    # Garante formato maiúsculo e padrão com ':'
    mac = passed_mac.upper()
    if len(mac) == 12 and ':' not in mac:
        mac = ':'.join(mac[i:i+2] for i in range(0, 12, 2))

    try:
        # Consulta MAC no banco
        device = Dispositivo.objects.get(mac_address=mac)
        print(f"MAC {mac} autorizado: dispositivo {device.nome_dispositivo}")
        return True
    except Dispositivo.DoesNotExist:
        print(f"MAC {mac} não encontrado no banco")
        return False

if __name__ == '__main__':
    # O FreeRADIUS normalmente passa username no argv[1]
    if len(sys.argv) < 2:
        print("Uso: script.py <MAC_address>")
        sys.exit(1)

    mac_input = sys.argv[1]
    if authorize(mac_input):
        sys.exit(0)  # sucesso (ACCEPT)
    else:
        sys.exit(1)  # falha (REJECT)
