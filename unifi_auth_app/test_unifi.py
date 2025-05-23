import sys
import os

# Adiciona o diretório do projeto ao PYTHONPATH
sys.path.append("/opt/auth_project")

# Define o módulo de configurações do Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unifi_auth_project.settings")

# Inicializa o Django
import django
django.setup()

# Importa a API do UniFi
from unifi_api import UniFiControllerAPI

# Teste de autenticação de um MAC address
try:
    controller = UniFiControllerAPI()
    mac = "AA:BB:CC:DD:EE:FF"  # Substitua por um MAC válido para teste
    resultado = controller.authorize_guest(mac, minutes=60)  # Autoriza por 60 minutos
    print("Dispositivo autorizado com sucesso!")
except Exception as e:
    print("Erro ao conectar no UniFi:", e)
