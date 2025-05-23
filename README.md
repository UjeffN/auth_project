# 📶 API de Autorização Wi-Fi com Django e UniFi

## 📌 Visão Geral
Este projeto fornece uma API para autorizar dispositivos na rede Wi-Fi **"Câmara"** através do UniFi Controller. A API permite que sistemas externos autorizem dispositivos por um período específico.

---

## ⚙️ Tecnologias Utilizadas
- **Backend:** Django + SQLite
- **Gerenciamento de rede:** UniFi Controller
- **Rede Wi-Fi alvo:** SSID `"Câmara"`

---

## 🔁 API de Autorização

### Endpoint
```
POST /api/authorize/
```

### Parâmetros
```json
{
    "mac": "00:11:22:33:44:55",  // MAC address do cliente
    "ap_mac": "AA:BB:CC:DD:EE:FF",  // MAC address do AP
    "minutes": 60  // Duração do acesso 
}
```

### Resposta de Sucesso
```json
{
    "status": "success",
    "message": "Cliente autorizado com sucesso"
}
```

### Resposta de Erro
```json
{
    "error": "Mensagem de erro"
}
```

---

## 🔧 Integração com UniFi Controller

### Configuração
O sistema requer as seguintes variáveis de ambiente:

```bash
UNIFI_CONTROLLER_IP=unifi.example.com
UNIFI_CONTROLLER_PORT=8443
UNIFI_USERNAME=admin
UNIFI_PASSWORD=senha
UNIFI_SITE_ID=default
```

### Autenticação
- A comunicação com o UniFi Controller é feita via HTTPS
- A API usa autenticação por sessão com o UniFi Controller
- Todas as credenciais são armazenadas em variáveis de ambiente

---

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/unifi-auth-api.git
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente no arquivo `.env`:
```bash
DJANGO_SECRET_KEY=sua-chave-secreta
UNIFI_CONTROLLER_IP=unifi.example.com
UNIFI_CONTROLLER_PORT=8443
UNIFI_USERNAME=admin
UNIFI_PASSWORD=senha
UNIFI_SITE_ID=default
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

---

## 🔒 Segurança
- A comunicação com o UniFi Controller é feita via HTTPS
- Todas as credenciais são armazenadas em variáveis de ambiente
- A API usa CSRF token para proteção contra ataques CSRF
