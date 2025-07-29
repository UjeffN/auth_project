import os
import django

# Configura o settings do Django corretamente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifi_auth_project.settings')
django.setup()

# Agora pode importar modelos, admin e fazer alterações
from django.contrib.admin.sites import site

# Aqui você pode alterar o título, cabeçalho, etc do admin
site.site_header = "DTI - Departamento de Tecnologia da Informação"
site.site_title = "Painel DTI"
site.index_title = "Administração do UniFi Auth"

# Exemplo simples: print para confirmar
print("Admin personalizado com tema UniFi carregado!")
