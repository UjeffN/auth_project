#!/opt/auth_project/venv/bin/python3
import os
import sys
import django

# Configura o Django (ajuste o nome do seu projeto aqui)
sys.path.append('/opt/auth_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifi_auth_project.settings')
django.setup()

from unifi_auth_app.models import UniFiUser

def main(mac):
    try:
        # Busca o usuário que tem dispositivo com MAC igual (case insensitive)
        user = UniFiUser.objects.get(dispositivos__mac_address__iexact=mac)
        print(f"MAC {mac} autorizado: dispositivo do usuário {user.nome}")
        sys.exit(0)
    except UniFiUser.DoesNotExist:
        print(f"MAC {mac} não encontrado no banco")
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: radius_mac_auth.py <MAC>")
        sys.exit(1)

    mac = sys.argv[1]
    main(mac)
