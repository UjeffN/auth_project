#!/usr/bin/env python3
"""
Script para testar a autorização de um visitante no UniFi Controller.
"""
import os
import sys
import logging
from pathlib import Path

# Adiciona o diretório raiz do projeto ao path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifi_auth_project.settings')

import django
django.setup()

# Agora importa as configurações do Django
from django.conf import settings

# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/unifi_auth/test_visitante_auth.log')
    ]
)
logger = logging.getLogger('test_visitante_auth')

# Importa o controlador UniFi
try:
    from unifi_auth_app.unifi import UnifiController
    from unifi_auth_app.models import Visitante
    from datetime import datetime, timedelta
    import random
    import string
    
    def generate_random_mac():
        """Gera um endereço MAC aleatório no formato XX:XX:XX:XX:XX:XX"""
        return ':'.join([''.join(random.choices('0123456789ABCDEF', k=2)) for _ in range(6)])
    
    def generate_random_ip():
        """Gera um endereço IP aleatório"""
        return f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
    
    def generate_random_phone():
        """Gera um número de telefone aleatório"""
        return f"({random.randint(10, 99)}) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    
    def generate_random_email(name):
        """Gera um e-mail aleatório baseado no nome"""
        domains = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']
        name = name.lower().replace(' ', '.')
        return f"{name}@{random.choice(domains)}"
    
    def test_visitante_auth():
        """Testa a autorização de um visitante no UniFi"""
        logger.info("=== Iniciando teste de autorização de visitante ===")
        
        # Cria um visitante de teste
        nome = "Visitante de Teste"
        email = generate_random_email(nome)
        telefone = generate_random_phone()
        mac_address = generate_random_mac()
        ip_address = generate_random_ip()
        
        logger.info(f"Dados do visitante de teste:")
        logger.info(f"- Nome: {nome}")
        logger.info(f"- E-mail: {email}")
        logger.info(f"- Telefone: {telefone}")
        logger.info(f"- MAC Address: {mac_address}")
        logger.info(f"- IP Address: {ip_address}")
        
        # Cria o registro do visitante no banco de dados
        try:
            visitante = Visitante.objects.create(
                nome=nome,
                email=email,
                telefone=telefone,
                mac_address=mac_address,
                ip_address=ip_address,
                autorizado=True
            )
            logger.info("Visitante criado com sucesso no banco de dados")
        except Exception as e:
            logger.error(f"Erro ao criar visitante no banco de dados: {str(e)}")
            return False
        
        # Inicializa o controlador UniFi
        try:
            unifi = UnifiController()
            logger.info("Controlador UniFi inicializado")
            
            # Tenta fazer login
            if unifi.login():
                logger.info("Login no UniFi Controller realizado com sucesso")
                
                # Tenta autorizar o dispositivo
                # Nota: Precisamos do AP MAC, que pode ser obtido listando os dispositivos
                # Para teste, podemos usar um AP conhecido ou tentar sem ele
                ap_mac = None  # Pode ser None para alguns controladores
                minutes = 1440  # 24 horas
                
                logger.info(f"Tentando autorizar o dispositivo {mac_address} por {minutes} minutos...")
                
                if unifi.authorize_guest(mac_address, ap_mac, minutes):
                    logger.info("Dispositivo autorizado com sucesso no UniFi Controller")
                    
                    # Atualiza o status do visitante
                    visitante.autorizado = True
                    visitante.save()
                    logger.info("Status do visitante atualizado para autorizado")
                    
                    logger.info("=== Teste de autorização concluído com sucesso ===")
                    return True
                else:
                    logger.error("Falha ao autorizar o dispositivo no UniFi Controller")
                    return False
            else:
                logger.error("Falha ao fazer login no UniFi Controller")
                return False
                
        except Exception as e:
            logger.error(f"Erro durante o teste de autorização: {str(e)}")
            return False
        finally:
            # Limpa o visitante de teste (opcional, descomente se necessário)
            # visitante.delete()
            pass
    
    if __name__ == "__main__":
        logger.info("Iniciando script de teste de autorização de visitante")
        if test_visitante_auth():
            logger.info("Teste concluído com sucesso!")
            sys.exit(0)
        else:
            logger.error("O teste falhou. Verifique os logs para mais detalhes.")
            sys.exit(1)

except ImportError as e:
    logger.error(f"Erro ao importar módulos: {str(e)}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Erro inesperado: {str(e)}")
    sys.exit(1)
