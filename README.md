# 📶 API de Autorização Wi-Fi com Django e UniFi

Este projeto é uma aplicação Django projetada para gerenciar a autorização de usuários e dispositivos em uma rede Wi-Fi controlada por um UniFi Controller. Ele fornece um portal cativo para autenticação e um painel administrativo para gerenciamento.

## ✨ Funcionalidades

- Portal cativo para autenticação de usuários na rede Wi-Fi.
- Integração com o UniFi Controller para autorizar e desautorizar dispositivos.
- Painel de administração para gerenciar usuários, dispositivos e permissões.
- Sistema de backup automático para o banco de dados.

---

## 🚀 Guia de Instalação

Siga os passos abaixo para configurar e executar o projeto em um novo ambiente (testado em Ubuntu/Debian).

### 1. Pré-requisitos do Sistema

Primeiro, instale as dependências essenciais do sistema:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv mariadb-server build-essential libmysqlclient-dev
sudo apt install pkg-config default-libmysqlclient-dev build-essential python3-dev
```

### 2. Configuração do Banco de Dados (MariaDB)

Faça login no MariaDB e crie o banco de dados e o usuário para a aplicação.

```bash
sudo mysql -u root -p
```

Dentro do console do MariaDB, execute os seguintes comandos. Substitua `sua_senha_segura` por uma senha forte:

```sql
CREATE DATABASE auth_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON auth_db.* TO 'root'@'localhost' IDENTIFIED BY 'sua_senha_segura';
FLUSH PRIVILEGES;
EXIT;
```

> **Nota**: Estamos usando o usuário `root` para simplificar a configuração. Em produção, é recomendado criar um usuário específico para a aplicação.

### 3. Configuração das Variáveis de Ambiente

Copie o arquivo de exemplo `.env.example` para `.env` e preencha as configurações necessárias:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com as seguintes configurações:

```ini
# Configurações do Django
SECRET_KEY=sua_chave_secreta_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,seu-ip-aqui

# Configurações do Banco de Dados
DB_ENGINE=django.db.backends.mysql
DB_NAME=auth_db
DB_USER=root
DB_PASSWORD=sua_senha_segura
DB_HOST=localhost
DB_PORT=3306

# Configurações do UniFi Controller (opcional)
UNIFI_URL=https://endereco-do-seu-unifi:8443
UNIFI_USER=seu_usuario_unifi
UNIFI_PASSWORD=sua_senha_unifi
UNIFI_SITE_ID=default
```

### 4. Configuração do Ambiente Virtual e Instalação de Dependências

Crie e ative o ambiente virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

### 5. Aplicando Migrações

Execute as migrações do banco de dados:

```bash
python manage.py migrate
```

### 6. Criando um Superusuário

Crie um superusuário para acessar o painel administrativo:

```bash
python manage.py createsuperuser
```

Siga as instruções para criar o usuário administrador.

### 7. Criando Diretório de Logs

Crie o diretório para armazenar os logs da aplicação:

```bash
mkdir -p logs
```

### 8. Iniciando o Servidor de Desenvolvimento

Para iniciar o servidor de desenvolvimento, execute:

```bash
python manage.py runserver 0.0.0.0:8000
```

Acesse o painel administrativo em: http://localhost:8000/admin/

### 9. Configuração do UniFi Controller (Opcional)

Se você deseja integrar com um controlador UniFi, certifique-se de que as seguintes configurações estejam corretas no arquivo `.env`:

- `UNIFI_URL`: URL completa do seu controlador UniFi (incluindo a porta)
- `UNIFI_USER`: Nome de usuário do UniFi
- `UNIFI_PASSWORD`: Senha do usuário do UniFi
- `UNIFI_SITE_ID`: Nome do site no UniFi (geralmente 'default')

## 👥 Primeiros Passos

Agora que você configurou o ambiente, você pode acessar o painel administrativo em:

- **URL do Admin**: http://localhost:8000/admin/
- **Usuário**: O que você criou com `createsuperuser`
- **Senha**: A senha que você definiu

### Acessando de Outros Dispositivos

Para acessar a aplicação de outros dispositivos na mesma rede, use o endereço IP da máquina onde o servidor está rodando:

```
http://seu-ip:8000/admin/
```

## 🚀 Implantação em Produção

Para um ambiente de produção, é recomendado usar um servidor de aplicação como o Gunicorn com Nginx como proxy reverso.

### 1. Instalando o Gunicorn

```bash
pip install gunicorn
```

### 2. Iniciando o Gunicorn

```bash
gunicorn --workers 3 --bind 0.0.0.0:8000 unifi_auth_project.wsgi:application
```

### 3. Configurando o Nginx (Exemplo)

Crie um arquivo de configuração para o Nginx em `/etc/nginx/sites-available/unifi_auth`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /caminho/para/seu/projeto/staticfiles/;
    }
}
```

### 4. Configurando o Systemd (Opcional)

Para manter o Gunicorn rodando em segundo plano e iniciar automaticamente com o sistema, você pode criar um serviço systemd. Um exemplo de arquivo de serviço (`gunicorn.service`) está incluído no diretório `docs/` do projeto.

---

## 💾 Backup e Restauração

O projeto está configurado com um script (`scripts/backup.sh`) que realiza backups diários e automáticos do banco de dados via `cron`.

- **Localização**: Os backups são armazenados em `/opt/auth_project/backups/`.
- **Formato**: São arquivos SQL compactados (`.sql.gz`) com a data e hora no nome.
- **Retenção**: Backups com mais de 7 dias são automaticamente excluídos para economizar espaço.

### Como Restaurar um Backup

Siga os passos abaixo para restaurar o banco de dados a partir de um arquivo de backup. **Atenção: este processo substituirá todos os dados atuais do banco de dados.**

1.  **Navegue até o diretório de backups** e liste os arquivos para escolher qual restaurar:

    ```bash
    cd /opt/auth_project/backups/
    ls -l
    ```

2.  **Descompacte o arquivo de backup escolhido**. Substitua `nome_do_arquivo.sql.gz` pelo nome do seu arquivo:

    ```bash
    gunzip nome_do_arquivo.sql.gz
    ```

    Isso criará um arquivo `.sql` descompactado (ex: `unifi_auth_db_2024-07-29_03-00-01.sql`).

3.  **Importe o backup para o MariaDB**. Você precisará das credenciais do banco de dados, que estão no seu arquivo `.env`. O comando abaixo carrega as variáveis do `.env` e executa a importação:

    ```bash
    # Carrega as variáveis de ambiente do .env
    set -a; source /opt/auth_project/.env; set +a

    # Importa o banco de dados (substitua o nome do arquivo)
    mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < nome_do_arquivo.sql
    ```

4.  **Verifique a restauração**: Acesse a aplicação ou o painel de administração para confirmar que os dados foram restaurados corretamente.

5.  **(Opcional) Limpeza**: Após confirmar que a restauração foi bem-sucedida, você pode apagar o arquivo `.sql` descompactado para economizar espaço:

    ```bash
    rm nome_do_arquivo.sql
    ```
