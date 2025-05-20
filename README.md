# 📶 Projeto de Autenticação Wi-Fi com Django e UniFi

## 📌 Visão Geral
Este projeto automatiza a autorização de dispositivos para acesso à rede Wi-Fi **"Câmara"**, com base em um banco de dados gerenciado por um sistema Django. A integração com o **UniFi Controller** permite que dispositivos cadastrados sejam autorizados automaticamente, e removidos ao serem excluídos do sistema.

---

## ⚙️ Tecnologias Utilizadas
- **Backend:** Django + SQLite (ou PostgreSQL)
- **Gerenciamento de rede:** UniFi Controller (sem UniFi Gateway)
- **Switches:** Gerenciáveis
- **Roteador/DHCP:** MikroTik RouterBoard
- **Rede Wi-Fi alvo:** SSID `"Câmara"`

---

## 🗃️ Estrutura do Banco de Dados

### Usuário (`User`)
- `nome`: nome completo
- `matricula`: código de identificação
- `departamento`: setor ou área de atuação
- `vinculo`: efetivo ou comissionado
- `dispositivos`: lista de dispositivos com MACs

### Dispositivo (`Dispositivo`)
- `mac_address`: endereço MAC do dispositivo
- `user`: relacionamento com usuário

---

## 🔁 Funcionalidades da API Django
- ✅ Ao cadastrar um usuário:
  - Adiciona automaticamente os dispositivos (MACs) ao **MAC Filtering da rede "Câmara"**
  - Autoriza os dispositivos na rede via API do UniFi Controller

- ❌ Ao excluir um usuário comissionado:
  - Remove os MACs da lista de filtragem
  - Revoga a autorização do dispositivo

---

## 🔧 Integração com UniFi Controller

### Requisições
- **Autorização:**  
  Endpoint: `/api/s/default/cmd/stamgr`  
  Payload: `{ "cmd": "authorize-guest", "mac": "<mac_address>", "minutes": 0 }`

- **Revogação:**  
  Endpoint: `/api/s/default/cmd/stamgr`  
  Payload: `{ "cmd": "unauthorize-guest", "mac": "<mac_address>" }`

- **MAC Filtering:**  
  Endpoint: `/api/s/default/rest/wlanconf/<wlan_id>`  
  Campos utilizados:
  - `"mac_filter_enabled": true`
  - `"mac_filter_policy": "allow"`
  - `"mac_filter_list"`: lista de MACs autorizados
  - `"name"` (SSID alvo): `"wifi"`

### Requisitos de Configuração
- A rede "wifi" deve estar com:
  - MAC Filtering **habilitado**
  - Modo **"Allow"** selecionado
- O sistema usa autenticação por sessão com o UniFi Controller (sem necessidade de Gateway)

---

## 🧠 Lógica de Sinais (`signals.py`)
- Após salvar um usuário:
  - Se vínculo for `comissionado`, os dispositivos são automaticamente autorizados e incluídos na whitelist.
- Após deletar um usuário `comissionado`:
  - Seus dispositivos são removidos da whitelist e têm o acesso revogado.
- Usuários `efetivos` não são automaticamente removidos (segurança institucional).

---

## ✅ Como Testar
1. Crie um novo usuário com MACs válidos no Django Admin.
2. Acesse o UniFi Controller e verifique:
   - A presença dos MACs no MAC Filter da rede "Câmara"
   - A autorização ativa dos dispositivos
3. Delete o usuário (se comissionado) e confirme a remoção dos dispositivos do sistema.

---

## 🛡️ Segurança
- A comunicação com o UniFi Controller é autenticada por sessão segura.
- Nenhuma credencial sensível é exposta no código-fonte (use variáveis de ambiente).
- Apenas usuários autorizados podem acessar o Django Admin.

---

## 📌 Observações
- O sistema **funciona sem o uso de um UniFi Gateway**.
- O roteador MikroTik é responsável pelo DHCP.
- A autenticação se baseia **exclusivamente no MAC Address** do dispositivo.

---


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
