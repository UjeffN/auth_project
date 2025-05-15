# UniFi Auth Project

Sistema de gerenciamento de usuários e dispositivos para UniFi Controller.

## Requisitos

- Python 3.8 ou superior
- Pip (gerenciador de pacotes Python)
- UniFi Controller configurado e acessível

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd auth_project
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```
UNIFI_BASE_URL=https://[seu-controller-unifi]
UNIFI_USERNAME=[seu-usuario]
UNIFI_PASSWORD=[sua-senha]
DJANGO_SECRET_KEY=[sua-chave-secreta]
```

5. Execute as migrações:
```bash
python manage.py migrate
```

6. Crie um superusuário:
```bash
python manage.py createsuperuser
```

7. Inicie o servidor:
```bash
python manage.py runserver
```

O sistema estará disponível em `http://localhost:8000/admin`

## Funcionalidades

- Cadastro de usuários com departamentos
- Gerenciamento de múltiplos dispositivos por usuário
- Integração automática com UniFi Controller
- Suporte a MAC addresses em diversos formatos
- Interface administrativa completa

## Departamentos Disponíveis

- CER - Cerimonial
- ASC - Assessoria de Comunicação
- PRO - Procuradoria
- CNT - Controladoria Interna
- DIF - Diretoria Financeira
- DIL - Diretoria Legislativa
- DIA - Diretoria Administrativa
- OUV - Ouvidoria
- ILCM - Instituto Legislativo
- ARQ - Arquivo e Registro
- CONT - Contabilidade
- PAT - Patrimônio
- AUT - Automação
- MBL - Memorial e Biblioteca Legislativa
- RTV - Rádio e TV
- PLN - Planejamento de Contratações
- SIC - Serviço de Informação ao Cidadão
- LIC - Licitações e Contratos
- POL - Polícia Legislativa
- RH - Recursos Humanos
- MTS - Materiais e Serviços
- COM - Compras
- DTI - Departamento de Tecnologia da Informação
